/**
 * WebStory Client-Side Authentication & Role-Based Access Control (RBAC) Module
 * - SHA-256 Client-side Password Hashing via Web Crypto API
 * - Local Database verification from data/auth.json
 * - Session Management (localStorage / sessionStorage)
 * - Permission & Role Guards
 */

(function () {
  'use strict';

  // --- CRYPTO HELPER ---
  async function sha256(message) {
    const msgBuffer = new TextEncoder().encode(message);
    const hashBuffer = await crypto.subtle.digest('SHA-256', msgBuffer);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
  }

  const STORAGE_KEY = 'webstory_auth_session';
  const AUTH_CONFIG_URL = 'data/auth.json';

  const Auth = {
    config: null,
    currentUser: null,
    listeners: [],

    async init() {
      try {
        const res = await fetch(AUTH_CONFIG_URL);
        if (res.ok) {
          this.config = await res.json();
        }
      } catch (err) {
        console.warn('[Auth] Không thể tải auth.json trực tiếp, sử dụng cache dự phòng:', err);
      }

      // Khôi phục session từ storage
      this.restoreSession();
      this.bindUI();
      this.bindLockScreen();
      this.updateUI();

      // Hiển thị lock screen ngay nếu chưa đăng nhập
      if (!this.currentUser) {
        this.showLockScreen();
      } else {
        this.hideLockScreen();
      }
    },

    showLockScreen() {
      const lockEl = document.getElementById('appLockScreen');
      if (!lockEl) return;
      document.body.classList.add('is-locked');
      lockEl.style.display = 'flex';
      // Focus vào email input
      setTimeout(() => {
        const emailInput = document.getElementById('lockEmailInput');
        if (emailInput) emailInput.focus();
      }, 150);
    },

    hideLockScreen() {
      const lockEl = document.getElementById('appLockScreen');
      if (!lockEl) return;
      lockEl.classList.add('unlocking');
      document.body.classList.remove('is-locked');
      setTimeout(() => {
        lockEl.style.display = 'none';
        lockEl.classList.remove('unlocking');
      }, 420);
    },

    bindLockScreen() {
      const form = document.getElementById('lockLoginForm');
      const togglePwd = document.getElementById('btnToggleLockPwd');

      if (togglePwd) {
        togglePwd.addEventListener('click', () => {
          const pwd = document.getElementById('lockPasswordInput');
          if (pwd) {
            pwd.type = pwd.type === 'password' ? 'text' : 'password';
            togglePwd.textContent = pwd.type === 'password' ? '👁️' : '🙈';
          }
        });
      }

      if (form) {
        form.addEventListener('submit', async (e) => {
          e.preventDefault();
          const email = document.getElementById('lockEmailInput').value;
          const pwd = document.getElementById('lockPasswordInput').value;
          const remember = document.getElementById('lockRememberMe')?.checked ?? true;
          const msgBox = document.getElementById('lockFormMessage');
          const submitBtn = document.getElementById('btnLockSubmit');

          if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.innerHTML = `
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"></path>
              </svg>
              <span>Đang xác thực...</span>`;
          }

          const result = await this.login(email, pwd, remember);

          if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.innerHTML = `
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"></path>
                <polyline points="10 17 15 12 10 7"></polyline>
                <line x1="15" y1="12" x2="3" y2="12"></line>
              </svg>
              <span>Đăng Nhập & Mở Khoá</span>`;
          }

          if (msgBox) {
            if (result.success) {
              msgBox.className = 'auth-message success';
              msgBox.textContent = `✅ Xin chào ${result.user.displayName}! Đang mở khoá giao diện...`;
              setTimeout(() => {
                this.hideLockScreen();
                if (form) form.reset();
                msgBox.textContent = '';
                msgBox.className = 'auth-message';

                // Điều hướng lại pending hash nếu có
                const pendingHash = sessionStorage.getItem('auth_pending_hash');
                if (pendingHash) {
                  sessionStorage.removeItem('auth_pending_hash');
                  setTimeout(() => { window.location.hash = pendingHash; }, 450);
                } else {
                  setTimeout(() => { window.dispatchEvent(new HashChangeEvent('hashchange')); }, 450);
                }
              }, 700);
            } else {
              msgBox.className = 'auth-message error';
              msgBox.textContent = `❌ ${result.message}`;
              // Shake animation
              const card = form.closest('.lock-form-card');
              if (card) {
                card.style.animation = 'none';
                card.offsetHeight;
                card.style.animation = 'lockShake 0.4s ease';
              }
            }
          }
        });
      }
    },

    restoreSession() {
      let raw = localStorage.getItem(STORAGE_KEY) || sessionStorage.getItem(STORAGE_KEY);
      if (raw) {
        try {
          const session = JSON.parse(raw);
          // Kiểm tra thời hạn session (7 ngày)
          if (Date.now() - session.timestamp < 7 * 24 * 60 * 60 * 1000) {
            this.currentUser = session.user;
          } else {
            this.logout();
          }
        } catch (e) {
          this.currentUser = null;
        }
      }
    },

    async login(email, password, remember = true) {
      if (!this.config) {
        try {
          const res = await fetch(AUTH_CONFIG_URL);
          if (res.ok) this.config = await res.json();
        } catch (e) {
          return { success: false, message: 'Lỗi tải tệp xác thực hệ thống.' };
        }
      }

      const cleanEmail = (email || '').trim().toLowerCase();
      const inputHash = await sha256(password);

      const user = (this.config.users || []).find(
        u => u.email.toLowerCase() === cleanEmail
      );

      if (!user) {
        return { success: false, message: 'Tài khoản không tồn tại trên hệ thống.' };
      }

      if (user.passwordHash !== inputHash) {
        return { success: false, message: 'Mật khẩu không chính xác.' };
      }

      // Tạo object phiên đăng nhập an toàn (loại bỏ passwordHash)
      const userSession = {
        id: user.id,
        email: user.email,
        displayName: user.displayName,
        role: user.role,
        roleName: user.roleName || user.role,
        avatar: user.avatar || '👑',
        permissions: user.permissions || []
      };

      this.currentUser = userSession;

      const sessionPayload = {
        user: userSession,
        timestamp: Date.now()
      };

      if (remember) {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(sessionPayload));
        sessionStorage.removeItem(STORAGE_KEY);
      } else {
        sessionStorage.setItem(STORAGE_KEY, JSON.stringify(sessionPayload));
        localStorage.removeItem(STORAGE_KEY);
      }

      this.notify();
      this.updateUI();
      return { success: true, user: userSession };
    },

    logout() {
      this.currentUser = null;
      localStorage.removeItem(STORAGE_KEY);
      sessionStorage.removeItem(STORAGE_KEY);
      this.notify();
      this.updateUI();
    },

    isAuthenticated() {
      return !!this.currentUser;
    },

    getUser() {
      return this.currentUser;
    },

    hasRole(role) {
      if (!this.currentUser) return false;
      return this.currentUser.role === role;
    },

    hasPermission(permission) {
      if (!this.currentUser) return false;
      if (this.currentUser.role === 'admin') return true;
      if (this.currentUser.permissions.includes('*')) return true;
      return this.currentUser.permissions.includes(permission);
    },

    onChange(cb) {
      this.listeners.push(cb);
    },

    notify() {
      this.listeners.forEach(cb => {
        try { cb(this.currentUser); } catch (e) { console.error(e); }
      });
      window.dispatchEvent(new CustomEvent('auth:stateChanged', { detail: { user: this.currentUser } }));
    },

    // --- UI BINDINGS & RENDERING ---
    bindUI() {
      const btnAuth = document.getElementById('btnOpenAuthModal');
      const modal = document.getElementById('modalAuth');
      const btnClose = document.getElementById('btnCloseAuthModal');
      const form = document.getElementById('authLoginForm');
      const btnLogout = document.getElementById('btnAuthLogout');
      const togglePwdBtn = document.getElementById('btnTogglePasswordView');

      if (btnAuth && modal) {
        btnAuth.addEventListener('click', () => {
          modal.classList.add('active');
          const emailInput = document.getElementById('authEmailInput');
          if (emailInput && !this.currentUser) emailInput.focus();
        });
      }

      if (btnClose && modal) {
        btnClose.addEventListener('click', () => modal.classList.remove('active'));
      }

      if (modal) {
        modal.addEventListener('click', (e) => {
          if (e.target === modal) modal.classList.remove('active');
        });
      }

      if (togglePwdBtn) {
        togglePwdBtn.addEventListener('click', () => {
          const pwd = document.getElementById('authPasswordInput');
          if (pwd) {
            pwd.type = pwd.type === 'password' ? 'text' : 'password';
            togglePwdBtn.textContent = pwd.type === 'password' ? '👁️' : '🙈';
          }
        });
      }

      if (form) {
        form.addEventListener('submit', async (e) => {
          e.preventDefault();
          const email = document.getElementById('authEmailInput').value;
          const pwd = document.getElementById('authPasswordInput').value;
          const remember = document.getElementById('authRememberMe')?.checked ?? true;
          const msgBox = document.getElementById('authFormMessage');
          const submitBtn = document.getElementById('btnAuthSubmit');

          if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span>⏳ Đang kiểm tra...</span>';
          }

          const result = await this.login(email, pwd, remember);

          if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<span>Đăng Nhập</span>';
          }

          if (msgBox) {
            if (result.success) {
              msgBox.className = 'auth-message success';
              msgBox.textContent = `✅ Xin chào ${result.user.displayName}! Đang tải nội dung...`;
              setTimeout(() => {
                if (modal) modal.classList.remove('active');
                if (form) form.reset();
                msgBox.textContent = '';
                msgBox.className = 'auth-message';

                // Điều hướng lại trang đang chờ (nếu có)
                const pendingHash = sessionStorage.getItem('auth_pending_hash');
                if (pendingHash) {
                  sessionStorage.removeItem('auth_pending_hash');
                  window.location.hash = pendingHash;
                } else {
                  // Không có pending, reload handleHashRoute
                  window.dispatchEvent(new HashChangeEvent('hashchange'));
                }
              }, 800);
            } else {
              msgBox.className = 'auth-message error';
              msgBox.textContent = `❌ ${result.message}`;
            }
          }
        });
      }

      if (btnLogout) {
        btnLogout.addEventListener('click', () => {
          this.logout();
          if (modal) modal.classList.remove('active');
        });
      }
    },

    updateUI() {
      const btnAuth = document.getElementById('btnOpenAuthModal');
      const loginView = document.getElementById('authLoginView');
      const profileView = document.getElementById('authProfileView');
      const userBadge = document.getElementById('navUserBadge');
      const userNameDisplay = document.getElementById('authProfileName');
      const userEmailDisplay = document.getElementById('authProfileEmail');
      const userRoleDisplay = document.getElementById('authProfileRole');
      const userPermsList = document.getElementById('authProfilePerms');
      const adminToolsSection = document.querySelectorAll('.admin-only-feature');

      if (this.currentUser) {
        // Đã đăng nhập
        if (loginView) loginView.style.display = 'none';
        if (profileView) profileView.style.display = 'block';
        if (btnAuth) {
          btnAuth.classList.add('logged-in');
          btnAuth.title = `Đã đăng nhập: ${this.currentUser.displayName} (${this.currentUser.roleName})`;
        }
        if (userBadge) {
          userBadge.style.display = 'inline-flex';
          userBadge.innerHTML = `<span class="auth-role-tag role-${this.currentUser.role}">${this.currentUser.avatar || '👑'} ${this.currentUser.displayName}</span>`;
        }
        if (userNameDisplay) userNameDisplay.textContent = this.currentUser.displayName;
        if (userEmailDisplay) userEmailDisplay.textContent = this.currentUser.email;
        if (userRoleDisplay) {
          userRoleDisplay.textContent = `${this.currentUser.avatar || ''} ${this.currentUser.roleName}`;
          userRoleDisplay.className = `badge-role badge-${this.currentUser.role}`;
        }
        if (userPermsList) {
          userPermsList.innerHTML = (this.currentUser.permissions || [])
            .map(p => `<li class="perm-item">⚡ <code>${p}</code></li>`)
            .join('');
        }

        // Kích hoạt các tính năng chỉ dành cho Admin
        const isAdmin = this.hasRole('admin');
        adminToolsSection.forEach(el => {
          el.style.display = isAdmin ? '' : 'none';
        });
      } else {
        // Chưa đăng nhập → khoá giao diện lại
        if (loginView) loginView.style.display = 'block';
        if (profileView) profileView.style.display = 'none';
        if (btnAuth) {
          btnAuth.classList.remove('logged-in');
          btnAuth.title = 'Đăng nhập / Phân quyền';
        }
        if (userBadge) {
          userBadge.style.display = 'none';
          userBadge.innerHTML = '';
        }
        adminToolsSection.forEach(el => {
          el.style.display = 'none';
        });

        // Hiển thị lại lock screen & về library
        this.showLockScreen();
        if (window.location.hash && window.location.hash !== '#library') {
          window.location.hash = '#library';
        }
      }
    }
  };

  // Xuất ra window
  window.AuthManager = Auth;

  // Tự động khởi chạy khi DOM sẵn sàng
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => Auth.init());
  } else {
    Auth.init();
  }
})();
