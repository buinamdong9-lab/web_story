/**
 * WebStory Client-Side Authentication & RBAC Module v2.0
 * =========================================================
 * - SHA-256 Password Hashing via Web Crypto API
 * - Super Admin: duy nhất có quyền tạo/xóa tài khoản
 * - User Database: auth.json (gốc) + localStorage (tk tạo thêm)
 * - Lock Screen: khóa toàn bộ giao diện khi chưa đăng nhập
 * - Session Management: localStorage / sessionStorage (7 ngày)
 */

(function () {
  'use strict';

  // ─────────────────────────────────────────
  //  CRYPTO
  // ─────────────────────────────────────────
  async function sha256(message) {
    const buf = new TextEncoder().encode(message);
    const hash = await crypto.subtle.digest('SHA-256', buf);
    return Array.from(new Uint8Array(hash))
      .map(b => b.toString(16).padStart(2, '0')).join('');
  }

  function generateId() {
    return 'usr_' + Date.now().toString(36) + '_' + Math.random().toString(36).slice(2, 7);
  }

  // ─────────────────────────────────────────
  //  CONSTANTS
  // ─────────────────────────────────────────
  const SESSION_KEY   = 'webstory_auth_session';
  const USERS_DB_KEY  = 'webstory_users_db';      // tk do super admin tạo
  const AUTH_JSON_URL = 'data/auth.json';
  const SESSION_TTL   = 7 * 24 * 60 * 60 * 1000; // 7 ngày

  // ─────────────────────────────────────────
  //  AUTH MANAGER
  // ─────────────────────────────────────────
  const Auth = {
    baseConfig: null,   // dữ liệu từ auth.json
    currentUser: null,
    listeners: [],

    // ── KHỞI TẠO ──────────────────────────
    async init() {
      try {
        const res = await fetch(AUTH_JSON_URL);
        if (res.ok) this.baseConfig = await res.json();
      } catch (e) {
        console.warn('[Auth] Không tải được auth.json:', e);
      }

      this.restoreSession();
      this.bindUI();
      this.bindLockScreen();
      this.updateUI();

      if (!this.currentUser) {
        this.showLockScreen();
      } else {
        this.hideLockScreen();
      }
    },

    // ── SESSION ────────────────────────────
    restoreSession() {
      const raw = localStorage.getItem(SESSION_KEY) || sessionStorage.getItem(SESSION_KEY);
      if (!raw) return;
      try {
        const s = JSON.parse(raw);
        if (Date.now() - s.timestamp < SESSION_TTL) {
          this.currentUser = s.user;
        } else {
          this.logout();
        }
      } catch { this.currentUser = null; }
    },

    saveSession(user, remember) {
      const payload = { user, timestamp: Date.now() };
      const store = remember ? localStorage : sessionStorage;
      const other = remember ? sessionStorage : localStorage;
      store.setItem(SESSION_KEY, JSON.stringify(payload));
      other.removeItem(SESSION_KEY);
    },

    // ── USER DB (localStorage mở rộng) ────
    getExtraUsers() {
      try {
        return JSON.parse(localStorage.getItem(USERS_DB_KEY) || '[]');
      } catch { return []; }
    },

    saveExtraUsers(users) {
      localStorage.setItem(USERS_DB_KEY, JSON.stringify(users));
    },

    getAllUsers() {
      const base = this.baseConfig?.users || [];
      const extra = this.getExtraUsers();
      return [...base, ...extra];
    },

    // ── ĐĂNG NHẬP ────────────────────────
    async login(email, password, remember = true) {
      if (!this.baseConfig) {
        try {
          const res = await fetch(AUTH_JSON_URL);
          if (res.ok) this.baseConfig = await res.json();
        } catch { return { success: false, message: 'Lỗi tải tệp xác thực.' }; }
      }

      const cleanEmail = (email || '').trim().toLowerCase();
      const inputHash  = await sha256(password);
      const allUsers   = this.getAllUsers();
      const user       = allUsers.find(u => u.email.toLowerCase() === cleanEmail);

      if (!user)                      return { success: false, message: 'Tài khoản không tồn tại.' };
      if (user.passwordHash !== inputHash) return { success: false, message: 'Mật khẩu không chính xác.' };
      if (user.disabled)              return { success: false, message: 'Tài khoản đã bị vô hiệu hoá.' };

      const session = {
        id:           user.id,
        email:        user.email,
        displayName:  user.displayName,
        role:         user.role,
        roleName:     user.roleName || user.role,
        avatar:       user.avatar || '👤',
        permissions:  user.permissions || [],
        isSuperAdmin: !!user.isSuperAdmin,
        canManageUsers: !!user.canManageUsers
      };

      this.currentUser = session;
      this.saveSession(session, remember);
      this.notify();
      this.updateUI();
      return { success: true, user: session };
    },

    // ── ĐĂNG XUẤT ────────────────────────
    logout() {
      this.currentUser = null;
      localStorage.removeItem(SESSION_KEY);
      sessionStorage.removeItem(SESSION_KEY);
      this.notify();
      this.updateUI();
    },

    // ── KIỂM TRA QUYỀN ───────────────────
    isAuthenticated()  { return !!this.currentUser; },
    isSuperAdmin()     { return !!this.currentUser?.isSuperAdmin; },
    canManageUsers()   { return !!this.currentUser?.canManageUsers; },
    hasRole(r)         { return this.currentUser?.role === r; },
    hasPermission(p)   {
      if (!this.currentUser) return false;
      if (this.isSuperAdmin()) return true;
      return this.currentUser.permissions?.includes(p);
    },
    getUser()          { return this.currentUser; },

    // ── QUẢN LÝ TÀI KHOẢN (Super Admin) ─
    /** Tạo tài khoản mới. Chỉ super admin mới gọi được. */
    async createUser({ displayName, email, password, role }) {
      if (!this.isSuperAdmin()) {
        return { success: false, message: 'Không đủ quyền hạn.' };
      }

      const cleanEmail = (email || '').trim().toLowerCase();
      if (!cleanEmail || !password || !displayName) {
        return { success: false, message: 'Vui lòng điền đầy đủ thông tin.' };
      }

      const allUsers = this.getAllUsers();
      if (allUsers.find(u => u.email.toLowerCase() === cleanEmail)) {
        return { success: false, message: 'Email này đã tồn tại trong hệ thống.' };
      }

      const roles = this.baseConfig?.roles || {};
      const roleData = roles[role] || roles['member'];
      const hashPwd  = await sha256(password);

      const newUser = {
        id:             generateId(),
        email:          cleanEmail,
        displayName:    displayName.trim(),
        role:           role || 'member',
        roleName:       roleData.name || role,
        avatar:         this._roleAvatar(role),
        passwordHash:   hashPwd,
        isSuperAdmin:   false,       // tuyệt đối không thể là super admin
        canManageUsers: false,       // tuyệt đối không thể tạo tk khác
        permissions:    roleData.permissions || ['story:read'],
        disabled:       false,
        createdAt:      new Date().toISOString(),
        createdBy:      this.currentUser.email
      };

      const extra = this.getExtraUsers();
      extra.push(newUser);
      this.saveExtraUsers(extra);

      this.renderUserManagementTable();
      return { success: true, user: newUser };
    },

    /** Xóa tài khoản. Chỉ super admin, không xóa được chính mình / super admin. */
    deleteUser(userId) {
      if (!this.isSuperAdmin()) return { success: false, message: 'Không đủ quyền.' };

      // Chặn xóa super admin gốc (trong base config)
      const baseUser = (this.baseConfig?.users || []).find(u => u.id === userId);
      if (baseUser) return { success: false, message: 'Không thể xóa tài khoản hệ thống gốc.' };

      if (this.currentUser?.id === userId) return { success: false, message: 'Không thể xóa tài khoản đang đăng nhập.' };

      const extra = this.getExtraUsers().filter(u => u.id !== userId);
      this.saveExtraUsers(extra);
      this.renderUserManagementTable();
      return { success: true };
    },

    _roleAvatar(role) {
      const map = { admin: '🛡️', editor: '✍️', member: '🌟', guest: '👤' };
      return map[role] || '👤';
    },

    // ── NOTIFY ────────────────────────────
    onChange(cb) { this.listeners.push(cb); },
    notify() {
      this.listeners.forEach(cb => { try { cb(this.currentUser); } catch {} });
      window.dispatchEvent(new CustomEvent('auth:stateChanged', { detail: { user: this.currentUser } }));
    },

    // ─────────────────────────────────────────
    //  LOCK SCREEN
    // ─────────────────────────────────────────
    showLockScreen() {
      const el = document.getElementById('appLockScreen');
      if (!el) return;
      document.body.classList.add('is-locked');
      el.style.display = 'flex';
      setTimeout(() => {
        const inp = document.getElementById('lockEmailInput');
        if (inp) inp.focus();
      }, 150);
    },

    hideLockScreen() {
      const el = document.getElementById('appLockScreen');
      if (!el) return;
      el.classList.add('unlocking');
      document.body.classList.remove('is-locked');
      setTimeout(() => {
        el.style.display = 'none';
        el.classList.remove('unlocking');
      }, 420);
    },

    bindLockScreen() {
      const form      = document.getElementById('lockLoginForm');
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

      if (!form) return;
      form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const email    = document.getElementById('lockEmailInput').value;
        const pwd      = document.getElementById('lockPasswordInput').value;
        const remember = document.getElementById('lockRememberMe')?.checked ?? true;
        const msgBox   = document.getElementById('lockFormMessage');
        const btn      = document.getElementById('btnLockSubmit');

        if (btn) { btn.disabled = true; btn.querySelector('span').textContent = 'Đang xác thực...'; }

        const result = await this.login(email, pwd, remember);

        if (btn) { btn.disabled = false; btn.querySelector('span').textContent = 'Đăng Nhập & Mở Khoá'; }

        if (msgBox) {
          if (result.success) {
            msgBox.className = 'auth-message success';
            msgBox.textContent = `✅ Xin chào ${result.user.displayName}! Đang mở khoá...`;
            setTimeout(() => {
              this.hideLockScreen();
              form.reset();
              msgBox.textContent = ''; msgBox.className = 'auth-message';
              const pending = sessionStorage.getItem('auth_pending_hash');
              if (pending) {
                sessionStorage.removeItem('auth_pending_hash');
                setTimeout(() => { window.location.hash = pending; }, 450);
              } else {
                setTimeout(() => { window.dispatchEvent(new HashChangeEvent('hashchange')); }, 450);
              }
            }, 700);
          } else {
            msgBox.className = 'auth-message error';
            msgBox.textContent = `❌ ${result.message}`;
            const card = form.closest('.lock-form-card');
            if (card) { card.style.animation = 'none'; card.offsetHeight; card.style.animation = 'lockShake 0.4s ease'; }
          }
        }
      });
    },

    // ─────────────────────────────────────────
    //  AUTH MODAL UI (nút header)
    // ─────────────────────────────────────────
    bindUI() {
      const btnAuth   = document.getElementById('btnOpenAuthModal');
      const modal     = document.getElementById('modalAuth');
      const btnClose  = document.getElementById('btnCloseAuthModal');
      const form      = document.getElementById('authLoginForm');
      const btnLogout = document.getElementById('btnAuthLogout');
      const togglePwd = document.getElementById('btnTogglePasswordView');

      if (btnAuth && modal) {
        btnAuth.addEventListener('click', () => {
          modal.classList.add('active');
          if (!this.currentUser) setTimeout(() => document.getElementById('authEmailInput')?.focus(), 100);
        });
      }
      if (btnClose && modal) btnClose.addEventListener('click', () => modal.classList.remove('active'));
      if (modal) modal.addEventListener('click', e => { if (e.target === modal) modal.classList.remove('active'); });

      if (togglePwd) {
        togglePwd.addEventListener('click', () => {
          const pwd = document.getElementById('authPasswordInput');
          if (pwd) {
            pwd.type = pwd.type === 'password' ? 'text' : 'password';
            togglePwd.textContent = pwd.type === 'password' ? '👁️' : '🙈';
          }
        });
      }

      if (form) {
        form.addEventListener('submit', async (e) => {
          e.preventDefault();
          const email    = document.getElementById('authEmailInput').value;
          const pwd      = document.getElementById('authPasswordInput').value;
          const remember = document.getElementById('authRememberMe')?.checked ?? true;
          const msgBox   = document.getElementById('authFormMessage');
          const btn      = document.getElementById('btnAuthSubmit');

          if (btn) { btn.disabled = true; btn.innerHTML = '<span>⏳ Đang kiểm tra...</span>'; }
          const result = await this.login(email, pwd, remember);
          if (btn) { btn.disabled = false; btn.innerHTML = '<span>Đăng Nhập</span>'; }

          if (msgBox) {
            if (result.success) {
              msgBox.className = 'auth-message success';
              msgBox.textContent = `✅ Xin chào ${result.user.displayName}!`;
              setTimeout(() => {
                if (modal) modal.classList.remove('active');
                form.reset(); msgBox.textContent = ''; msgBox.className = 'auth-message';
                const pending = sessionStorage.getItem('auth_pending_hash');
                if (pending) { sessionStorage.removeItem('auth_pending_hash'); window.location.hash = pending; }
                else { window.dispatchEvent(new HashChangeEvent('hashchange')); }
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

      // Tab switching trong modal
      document.getElementById('tabProfile')?.addEventListener('click', () => this._switchTab('profile'));
      document.getElementById('tabUserMgmt')?.addEventListener('click', () => this._switchTab('usermgmt'));

      // Form tạo tài khoản mới
      document.getElementById('formCreateUser')?.addEventListener('submit', async (e) => {
        e.preventDefault();
        const displayName = document.getElementById('newUserName').value;
        const email       = document.getElementById('newUserEmail').value;
        const password    = document.getElementById('newUserPassword').value;
        const role        = document.getElementById('newUserRole').value;
        const msgBox      = document.getElementById('createUserMessage');
        const btn         = document.getElementById('btnCreateUser');

        if (btn) { btn.disabled = true; btn.textContent = 'Đang tạo...'; }
        const result = await this.createUser({ displayName, email, password, role });
        if (btn) { btn.disabled = false; btn.textContent = '✚ Tạo Tài Khoản'; }

        if (msgBox) {
          msgBox.className = result.success ? 'auth-message success' : 'auth-message error';
          msgBox.textContent = result.success
            ? `✅ Đã tạo tài khoản: ${result.user.displayName} (${result.user.role})`
            : `❌ ${result.message}`;
          if (result.success) {
            document.getElementById('formCreateUser').reset();
            setTimeout(() => { msgBox.textContent = ''; msgBox.className = 'auth-message'; }, 3000);
          }
        }
      });
    },

    _switchTab(tab) {
      const profilePanel  = document.getElementById('tabPanelProfile');
      const mgmtPanel     = document.getElementById('tabPanelUserMgmt');
      const tabProfile    = document.getElementById('tabProfile');
      const tabMgmt       = document.getElementById('tabUserMgmt');

      if (tab === 'profile') {
        if (profilePanel) profilePanel.style.display = 'block';
        if (mgmtPanel)    mgmtPanel.style.display    = 'none';
        tabProfile?.classList.add('active');
        tabMgmt?.classList.remove('active');
      } else {
        if (profilePanel) profilePanel.style.display = 'none';
        if (mgmtPanel)    mgmtPanel.style.display    = 'block';
        tabProfile?.classList.remove('active');
        tabMgmt?.classList.add('active');
        this.renderUserManagementTable();
      }
    },

    // ─────────────────────────────────────────
    //  RENDER BẢNG QUẢN LÝ NGƯỜI DÙNG
    // ─────────────────────────────────────────
    renderUserManagementTable() {
      const tbody = document.getElementById('userTableBody');
      if (!tbody) return;

      const users = this.getAllUsers();
      const rows  = users.map(u => {
        const isBase     = (this.baseConfig?.users || []).some(b => b.id === u.id);
        const isSuper    = !!u.isSuperAdmin;
        const deleteBtn  = (isBase || isSuper)
          ? `<span style="color:var(--text-muted); font-size:0.75rem;">Hệ thống</span>`
          : `<button class="btn-delete-user btn-icon" data-uid="${u.id}" title="Xóa tài khoản" style="color:#ef4444; font-size:0.8rem; padding:4px 8px;">🗑️ Xóa</button>`;

        return `
          <tr class="user-table-row">
            <td>${u.avatar || '👤'} ${this._escHTML(u.displayName)}</td>
            <td style="font-size:0.78rem; color:var(--text-muted);">${this._escHTML(u.email)}</td>
            <td><span class="badge-role badge-${u.role}" style="font-size:0.7rem;">${u.roleName || u.role}${isSuper ? ' 👑' : ''}</span></td>
            <td>${deleteBtn}</td>
          </tr>`;
      }).join('');

      tbody.innerHTML = rows || '<tr><td colspan="4" style="text-align:center;color:var(--text-muted);">Không có dữ liệu</td></tr>';

      // Gắn event xóa
      tbody.querySelectorAll('.btn-delete-user').forEach(btn => {
        btn.addEventListener('click', () => {
          const uid = btn.dataset.uid;
          if (!confirm('Bạn có chắc muốn xóa tài khoản này?')) return;
          const result = this.deleteUser(uid);
          if (!result.success) alert('❌ ' + result.message);
        });
      });
    },

    _escHTML(str) {
      return (str || '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
    },

    // ─────────────────────────────────────────
    //  CẬP NHẬT TOÀN BỘ GIAO DIỆN
    // ─────────────────────────────────────────
    updateUI() {
      const btnAuth    = document.getElementById('btnOpenAuthModal');
      const loginView  = document.getElementById('authLoginView');
      const profileView= document.getElementById('authProfileView');
      const userBadge  = document.getElementById('navUserBadge');
      const nameEl     = document.getElementById('authProfileName');
      const emailEl    = document.getElementById('authProfileEmail');
      const roleEl     = document.getElementById('authProfileRole');
      const permsEl    = document.getElementById('authProfilePerms');
      const tabsMgmt   = document.getElementById('tabUserMgmt');
      const adminEls   = document.querySelectorAll('.admin-only-feature');

      if (this.currentUser) {
        if (loginView)  loginView.style.display  = 'none';
        if (profileView)profileView.style.display = 'block';
        if (btnAuth) {
          btnAuth.classList.add('logged-in');
          btnAuth.title = `${this.currentUser.displayName} — ${this.currentUser.roleName}`;
        }
        if (userBadge) {
          userBadge.style.display = 'inline-flex';
          const superTag = this.isSuperAdmin() ? ' 👑' : '';
          userBadge.innerHTML = `<span class="auth-role-tag role-${this.currentUser.role}">${this.currentUser.avatar}${superTag} ${this.currentUser.displayName}</span>`;
        }
        if (nameEl)  nameEl.textContent  = this.currentUser.displayName + (this.isSuperAdmin() ? ' 👑' : '');
        if (emailEl) emailEl.textContent = this.currentUser.email;
        if (roleEl)  {
          roleEl.textContent  = `${this.currentUser.avatar} ${this.currentUser.roleName}`;
          roleEl.className    = `badge-role badge-${this.currentUser.role}`;
        }
        if (permsEl) {
          permsEl.innerHTML = (this.currentUser.permissions || [])
            .map(p => `<li class="perm-item">⚡ <code>${p}</code></li>`).join('');
        }

        // Tab quản lý user — chỉ super admin
        if (tabsMgmt) tabsMgmt.style.display = this.isSuperAdmin() ? 'flex' : 'none';

        // Đặt về tab Profile mỗi khi mở modal
        this._switchTab('profile');

        adminEls.forEach(el => { el.style.display = this.hasRole('admin') ? '' : 'none'; });

      } else {
        // Chưa đăng nhập → hiện lock screen
        if (loginView)  loginView.style.display  = 'block';
        if (profileView)profileView.style.display = 'none';
        if (btnAuth)    { btnAuth.classList.remove('logged-in'); btnAuth.title = 'Đăng nhập'; }
        if (userBadge)  { userBadge.style.display = 'none'; userBadge.innerHTML = ''; }
        if (tabsMgmt)   tabsMgmt.style.display = 'none';
        adminEls.forEach(el => { el.style.display = 'none'; });

        this.showLockScreen();
        if (window.location.hash && window.location.hash !== '#library') {
          window.location.hash = '#library';
        }
      }
    }
  };

  // ─────────────────────────────────────────
  //  EXPORT & AUTO-INIT
  // ─────────────────────────────────────────
  window.AuthManager = Auth;

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => Auth.init());
  } else {
    Auth.init();
  }
})();
