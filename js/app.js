/**
 * WebStory Core Engine - Ultra-Fast Chapter Loading & High-Performance PWA Reader
 * Advanced Features:
 * - Persistent IndexedDB Chapter Storage (0ms offline retrieval)
 * - Multi-Chapter Predictive Background Prefetcher (Prefetches 5-10 chapters ahead)
 * - Hardware-Accelerated 60fps Slide Transitions
 * - Mobile Touch Swipe Gestures for Instant Page Flipping
 * - Dual-Mode Visual Reading & Audio TTS Scrubber Bar
 * - Screen WakeLock & MediaSession API for Background Audio
 */

document.addEventListener('DOMContentLoaded', () => {
  'use strict';

  // --- 1. PERSISTENT INDEXEDDB CHAPTER STORAGE ENGINE ---
  const ChapterDB = {
    db: null,
    DB_NAME: 'webstory_idb',
    STORE_NAME: 'chapters',
    DB_VERSION: 1,

    async init() {
      if (!('indexedDB' in window)) return null;
      return new Promise((resolve) => {
        const req = indexedDB.open(this.DB_NAME, this.DB_VERSION);
        req.onupgradeneeded = (e) => {
          const db = e.target.result;
          if (!db.objectStoreNames.contains(this.STORE_NAME)) {
            db.createObjectStore(this.STORE_NAME, { keyPath: 'key' });
          }
        };
        req.onsuccess = (e) => {
          this.db = e.target.result;
          resolve(this.db);
        };
        req.onerror = () => resolve(null);
      });
    },

    async get(key) {
      if (!this.db) await this.init();
      if (!this.db) return null;
      return new Promise((resolve) => {
        try {
          const tx = this.db.transaction(this.STORE_NAME, 'readonly');
          const store = tx.objectStore(this.STORE_NAME);
          const req = store.get(key);
          req.onsuccess = () => resolve(req.result ? req.result.data : null);
          req.onerror = () => resolve(null);
        } catch (e) {
          resolve(null);
        }
      });
    },

    async set(key, data) {
      if (!this.db) await this.init();
      if (!this.db) return;
      try {
        const tx = this.db.transaction(this.STORE_NAME, 'readwrite');
        const store = tx.objectStore(this.STORE_NAME);
        store.put({ key, data, updated_at: Date.now() });
      } catch (e) {}
    }
  };

  // Global Application State
  const state = {
    stories: [],
    filteredStories: [],
    categories: [],
    selectedCategory: 'all',
    sortMode: 'default',
    renderedStoriesCount: 0,
    BATCH_SIZE: 24,
    currentStoryId: 'than_nu_tieu_dao_luc',
    storyMeta: null,
    toc: [],
    currentChapIndex: 1,
    chapterCache: new Map(), // In-memory LRU Cache
    MAX_CACHE_SIZE: 80,
    prefetchedIndices: new Set(),
    hasTriggeredDeepPrefetch: false,
    autoScrollInterval: null,
    autoScrollSpeed: 2,
    lastScrollY: 0,
    isHeaderHidden: false,
    wakeLock: null,
    deferredPrompt: null,
    isSeekingManually: false,
    touchStartX: 0,
    touchStartY: 0,
    touchEndX: 0,
    touchEndY: 0,
    bookmarks: JSON.parse(localStorage.getItem('tn_bookmarks') || '[]'),
    readingHistory: JSON.parse(localStorage.getItem('tn_reading_history') || '[]'),
    settings: {
      theme: localStorage.getItem('tn_theme') || 'theme-dark',
      fontFamily: localStorage.getItem('tn_font') || "'Lora', Georgia, serif",
      fontSize: parseInt(localStorage.getItem('tn_fontSize') || '18', 10)
    },
    tts: {
      synth: window.speechSynthesis,
      utterance: null,
      isPlaying: false,
      isPaused: false,
      currentParaIndex: 0,
      paragraphs: [],
      voices: [],
      selectedVoice: null,
      rate: 1.0,
      pitch: 1.0,
      preset: 'custom',
      watchdogTimer: null,
      isWarmedUp: false
    }
  };

  // Cached DOM Elements
  const DOM = {
    body: document.body,
    appHeader: document.getElementById('appHeader'),
    progressBar: document.getElementById('progressBar'),
    brandLogo: document.getElementById('brandLogo'),
    brandTitle: document.getElementById('brandTitle'),
    quickStorySelect: document.getElementById('quickStorySelect'),
    btnNavLibrary: document.getElementById('btnNavLibrary'),
    btnNavRead: document.getElementById('btnNavRead'),
    navReadText: document.getElementById('navReadText'),
    btnOpenToc: document.getElementById('btnOpenToc'),
    btnCloseToc: document.getElementById('btnCloseToc'),
    modalToc: document.getElementById('modalToc'),
    drawerStoryTitle: document.getElementById('drawerStoryTitle'),
    searchTocInput: document.getElementById('searchTocInput'),
    tocList: document.getElementById('tocList'),
    btnToggleTheme: document.getElementById('btnToggleTheme'),
    selectTheme: document.getElementById('selectTheme'),
    selectFont: document.getElementById('selectFont'),
    btnFontDec: document.getElementById('btnFontDec'),
    btnFontInc: document.getElementById('btnFontInc'),
    fontSizeDisplay: document.getElementById('fontSizeDisplay'),
    
    // Library Section
    librarySection: document.getElementById('librarySection'),
    searchLibraryInput: document.getElementById('searchLibraryInput'),
    recentShelfContainer: document.getElementById('recentShelfContainer'),
    recentGrid: document.getElementById('recentGrid'),
    categoryPillsWrapper: document.getElementById('categoryPillsWrapper'),
    selectStorySort: document.getElementById('selectStorySort'),
    showingStoriesCount: document.getElementById('showingStoriesCount'),
    totalStoriesBadge: document.getElementById('totalStoriesBadge'),
    storiesGrid: document.getElementById('storiesGrid'),
    loadMoreContainer: document.getElementById('loadMoreContainer'),
    btnLoadMoreStories: document.getElementById('btnLoadMoreStories'),

    // Story Details Section
    overviewSection: document.getElementById('overviewSection'),
    heroCover: document.getElementById('heroCover'),
    storyTitle: document.getElementById('storyTitle'),
    storyMetaTags: document.getElementById('storyMetaTags'),
    statTotalChap: document.getElementById('statTotalChap'),
    statTotalWords: document.getElementById('statTotalWords'),
    statStoryStatus: document.getElementById('statStoryStatus'),
    storyDescText: document.getElementById('storyDescText'),
    btnStartRead: document.getElementById('btnStartRead'),
    btnStartReadText: document.getElementById('btnStartReadText'),
    btnHeroListen: document.getElementById('btnHeroListen'),
    btnHeroToc: document.getElementById('btnHeroToc'),
    
    // Reader Section
    readerSection: document.getElementById('readerSection'),
    readerPaper: document.getElementById('readerPaper'),
    readingScrubberCard: document.getElementById('readingScrubberCard'),
    readingSeekRange: document.getElementById('readingSeekRange'),
    scrubberParaDisplay: document.getElementById('scrubberParaDisplay'),
    scrubberPercentDisplay: document.getElementById('scrubberPercentDisplay'),
    chapSubtitle: document.getElementById('chapSubtitle'),
    chapTitle: document.getElementById('chapTitle'),
    chapWordCount: document.getElementById('chapWordCount'),
    chapEstTime: document.getElementById('chapEstTime'),
    chapContent: document.getElementById('chapContent'),
    btnPrevChap: document.getElementById('btnPrevChap'),
    btnNextChap: document.getElementById('btnNextChap'),
    selectJumpChap: document.getElementById('selectJumpChap'),
    btnBookmark: document.getElementById('btnBookmark'),
    
    // Auto Scroll
    btnToggleAutoScroll: document.getElementById('btnToggleAutoScroll'),
    autoScrollPanel: document.getElementById('autoScrollPanel'),
    autoScrollSpeedText: document.getElementById('autoScrollSpeedText'),
    btnAutoScrollDec: document.getElementById('btnAutoScrollDec'),
    btnAutoScrollInc: document.getElementById('btnAutoScrollInc'),
    btnAutoScrollStop: document.getElementById('btnAutoScrollStop'),
    
    // TTS Audio & Scrubber
    btnToggleTTS: document.getElementById('btnToggleTTS'),
    audioPlayerBar: document.getElementById('audioPlayerBar'),
    ttsPulseIndicator: document.getElementById('ttsPulseIndicator'),
    ttsParaCounter: document.getElementById('ttsParaCounter'),
    ttsSeekRange: document.getElementById('ttsSeekRange'),
    ttsProgressPercent: document.getElementById('ttsProgressPercent'),
    btnTtsPrevPara: document.getElementById('btnTtsPrevPara'),
    btnTtsPlayPause: document.getElementById('btnTtsPlayPause'),
    ttsPlayPauseIcon: document.getElementById('ttsPlayPauseIcon'),
    ttsPlayPauseText: document.getElementById('ttsPlayPauseText'),
    btnTtsNextPara: document.getElementById('btnTtsNextPara'),
    selectTtsPreset: document.getElementById('selectTtsPreset'),
    selectTtsSpeed: document.getElementById('selectTtsSpeed'),
    selectTtsVoice: document.getElementById('selectTtsVoice'),
    selectTtsPitch: document.getElementById('selectTtsPitch'),
    btnTtsStop: document.getElementById('btnTtsStop'),

    // Floating
    fabToggleScrubber: document.getElementById('fabToggleScrubber'),
    fabScrollTop: document.getElementById('fabScrollTop')
  };

  // Create Toast Element
  let toastEl = document.querySelector('.fast-toast');
  if (!toastEl) {
    toastEl = document.createElement('div');
    toastEl.className = 'fast-toast';
    document.body.appendChild(toastEl);
  }

  function showToast(msg, duration = 1800) {
    toastEl.textContent = msg;
    toastEl.classList.add('show');
    clearTimeout(toastEl._timer);
    toastEl._timer = setTimeout(() => {
      toastEl.classList.remove('show');
    }, duration);
  }

  // --- INITIALIZATION ---
  async function initApp() {
    ChapterDB.init();
    applySettings();
    initTTSVoices();
    await loadLibraryStories();
    setupEventListeners();
    setupMobileAudioGestureWarmup();
    setupTouchGestures();
    handleHashRoute();

    window.addEventListener('hashchange', handleHashRoute, { passive: true });
    window.addEventListener('scroll', onScrollThrottled, { passive: true });
    
    window.addEventListener('beforeinstallprompt', (e) => {
      e.preventDefault();
      state.deferredPrompt = e;
    });
  }

  // --- SETTINGS MANAGEMENT ---
  function applySettings() {
    DOM.body.className = state.settings.theme;
    DOM.selectTheme.value = state.settings.theme;
    DOM.selectFont.value = state.settings.fontFamily;
    DOM.fontSizeDisplay.textContent = `${state.settings.fontSize}px`;
    document.documentElement.style.setProperty('--reader-font-size', `${state.settings.fontSize}px`);
    document.documentElement.style.setProperty('--font-reader', state.settings.fontFamily);
  }

  function saveSettings() {
    localStorage.setItem('tn_theme', state.settings.theme);
    localStorage.setItem('tn_font', state.settings.fontFamily);
    localStorage.setItem('tn_fontSize', state.settings.fontSize);
  }

  function getStoryLastChap(storyId) {
    const progress = JSON.parse(localStorage.getItem(`tn_progress_${storyId}`) || '{}');
    return progress.lastChap || 1;
  }

  function saveStoryProgress(storyId, chapIndex) {
    localStorage.setItem(`tn_progress_${storyId}`, JSON.stringify({
      lastChap: chapIndex,
      timestamp: Date.now()
    }));

    if (state.storyMeta) {
      const existingIdx = state.readingHistory.findIndex(h => h.storyId === storyId);
      const historyItem = {
        storyId: storyId,
        title: state.storyMeta.title,
        lastChap: chapIndex,
        totalChaps: state.storyMeta.total_chapters || state.toc.length,
        coverImage: state.storyMeta.cover_image || 'images/cover.jpg',
        timestamp: Date.now()
      };

      if (existingIdx > -1) {
        state.readingHistory.splice(existingIdx, 1);
      }
      state.readingHistory.unshift(historyItem);
      state.readingHistory = state.readingHistory.slice(0, 10);
      localStorage.setItem('tn_reading_history', JSON.stringify(state.readingHistory));
    }
  }

  // --- WAKE LOCK API ---
  async function acquireWakeLock() {
    try {
      if ('wakeLock' in navigator && !state.wakeLock) {
        state.wakeLock = await navigator.wakeLock.request('screen');
        state.wakeLock.addEventListener('release', () => {
          state.wakeLock = null;
        });
      }
    } catch (err) {
      console.log('WakeLock not granted:', err);
    }
  }

  function releaseWakeLock() {
    if (state.wakeLock) {
      state.wakeLock.release().then(() => {
        state.wakeLock = null;
      }).catch(() => {});
    }
  }

  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible' && state.tts.isPlaying && !state.tts.isPaused) {
      acquireWakeLock();
    }
  });

  // --- MEDIA SESSION API ---
  function updateMediaSessionMetadata(chapTitle) {
    if ('mediaSession' in navigator && state.storyMeta) {
      navigator.mediaSession.metadata = new MediaMetadata({
        title: chapTitle,
        artist: state.storyMeta.title,
        album: 'Kho Truyện Audio Online',
        artwork: [
          { src: state.storyMeta.cover_image || 'images/cover.jpg', sizes: '512x512', type: 'image/jpeg' }
        ]
      });

      navigator.mediaSession.setActionHandler('play', resumeTTS);
      navigator.mediaSession.setActionHandler('pause', pauseTTS);
      navigator.mediaSession.setActionHandler('previoustrack', () => {
        if (state.tts.currentParaIndex > 0) startTTS(state.tts.currentParaIndex - 1);
      });
      navigator.mediaSession.setActionHandler('nexttrack', () => {
        if (state.tts.currentParaIndex < state.tts.paragraphs.length - 1) {
          startTTS(state.tts.currentParaIndex + 1);
        }
      });
    }
  }

  // --- MOBILE SPEECH GESTURE WARMUP ---
  function setupMobileAudioGestureWarmup() {
    const warmup = () => {
      if (state.tts.isWarmedUp || !state.tts.synth) return;
      try {
        const dummyUtterance = new SpeechSynthesisUtterance(' ');
        dummyUtterance.volume = 0.01;
        state.tts.synth.speak(dummyUtterance);
        state.tts.isWarmedUp = true;
        initTTSVoices();
      } catch (e) {}
      document.removeEventListener('touchstart', warmup);
      document.removeEventListener('click', warmup);
    };

    document.addEventListener('touchstart', warmup, { passive: true, once: true });
    document.addEventListener('click', warmup, { passive: true, once: true });
  }

  // --- MOBILE TOUCH SWIPE GESTURES ---
  function setupTouchGestures() {
    document.addEventListener('touchstart', (e) => {
      if (DOM.readerSection.classList.contains('hidden')) return;
      state.touchStartX = e.changedTouches[0].screenX;
      state.touchStartY = e.changedTouches[0].screenY;
    }, { passive: true });

    document.addEventListener('touchend', (e) => {
      if (DOM.readerSection.classList.contains('hidden')) return;
      state.touchEndX = e.changedTouches[0].screenX;
      state.touchEndY = e.changedTouches[0].screenY;
      handleSwipeGesture();
    }, { passive: true });
  }

  function handleSwipeGesture() {
    const diffX = state.touchEndX - state.touchStartX;
    const diffY = state.touchEndY - state.touchStartY;
    
    // Check if horizontal swipe is dominant (not vertical scrolling)
    if (Math.abs(diffX) > 75 && Math.abs(diffX) > Math.abs(diffY) * 1.8) {
      if (diffX < 0) {
        // Swipe Left -> Next Chapter
        if (state.currentChapIndex < state.toc.length) {
          window.location.hash = `#read/${state.currentStoryId}/${state.currentChapIndex + 1}`;
        }
      } else {
        // Swipe Right -> Prev Chapter
        if (state.currentChapIndex > 1) {
          window.location.hash = `#read/${state.currentStoryId}/${state.currentChapIndex - 1}`;
        }
      }
    }
  }

  // --- HIGH-SCALE LIBRARY CATALOGUE ENGINE ---
  async function loadLibraryStories() {
    try {
      const res = await fetch('data/stories.json');
      if (res.ok) {
        const libData = await res.json();
        state.stories = libData.stories || [];
        state.categories = libData.categories || [];
      } else {
        state.stories = [{
          id: 'than_nu_tieu_dao_luc',
          title: 'Thần Nữ Tiêu Dao Lục',
          author: 'Vô Danh',
          category: 'Tiên Hiệp, Huyền Huyễn, Tu Chân',
          status: 'Hoàn Thành',
          total_chapters: 102,
          total_words: 445599,
          description: 'Hành trình tu chân và kỳ duyên tại Long tộc cấm địa.',
          cover_image: 'images/cover.jpg'
        }];
        state.categories = ['Tiên Hiệp', 'Huyền Huyễn', 'Tu Chân'];
      }

      DOM.totalStoriesBadge.textContent = state.stories.length;
      renderCategoryPills(state.categories);
      populateQuickStorySelect(state.stories);
      applyFilterAndSort();
      renderRecentShelf();
    } catch (err) {
      console.warn('Could not load stories.json:', err);
    }
  }

  function renderCategoryPills(categories) {
    const frag = document.createDocumentFragment();
    
    const allBtn = document.createElement('button');
    allBtn.className = 'cat-pill active';
    allBtn.dataset.category = 'all';
    allBtn.textContent = `Tất Cả (${state.stories.length})`;
    frag.appendChild(allBtn);

    categories.forEach(cat => {
      const count = state.stories.filter(s => (s.category || '').includes(cat)).length;
      if (count > 0) {
        const btn = document.createElement('button');
        btn.className = 'cat-pill';
        btn.dataset.category = cat;
        btn.textContent = `${cat} (${count})`;
        frag.appendChild(btn);
      }
    });

    DOM.categoryPillsWrapper.replaceChildren(frag);
  }

  function populateQuickStorySelect(stories) {
    if (stories.length > 1) {
      DOM.quickStorySelect.style.display = 'inline-block';
      const frag = document.createDocumentFragment();
      stories.forEach(s => {
        const opt = document.createElement('option');
        opt.value = s.id;
        opt.textContent = s.title;
        if (s.id === state.currentStoryId) opt.selected = true;
        frag.appendChild(opt);
      });
      DOM.quickStorySelect.replaceChildren(frag);
    } else {
      DOM.quickStorySelect.style.display = 'none';
    }
  }

  function renderRecentShelf() {
    if (state.readingHistory.length === 0) {
      DOM.recentShelfContainer.classList.add('hidden');
      return;
    }

    DOM.recentShelfContainer.classList.remove('hidden');
    const frag = document.createDocumentFragment();

    state.readingHistory.forEach(item => {
      const a = document.createElement('a');
      a.className = 'recent-card';
      a.href = `#read/${item.storyId}/${item.lastChap}`;
      a.innerHTML = `
        <img src="${item.coverImage}" class="recent-card-img" alt="${escapeHTML(item.title)}" onerror="this.src='images/cover.jpg'">
        <div class="recent-card-info">
          <div class="recent-card-title">${escapeHTML(item.title)}</div>
          <div class="recent-card-progress">📖 Đang đọc Chương ${item.lastChap} / ${item.totalChaps}</div>
        </div>
      `;
      frag.appendChild(a);
    });

    DOM.recentGrid.replaceChildren(frag);
  }

  function applyFilterAndSort() {
    const query = (DOM.searchLibraryInput.value || '').toLowerCase().trim();
    let result = state.stories;

    if (state.selectedCategory !== 'all') {
      result = result.filter(s => (s.category || '').includes(state.selectedCategory));
    }

    if (query) {
      result = result.filter(s => 
        s.title.toLowerCase().includes(query) || 
        (s.author && s.author.toLowerCase().includes(query)) ||
        (s.category && s.category.toLowerCase().includes(query))
      );
    }

    if (state.sortMode === 'chaps_desc') {
      result = [...result].sort((a, b) => (b.total_chapters || 0) - (a.total_chapters || 0));
    } else if (state.sortMode === 'words_desc') {
      result = [...result].sort((a, b) => (b.total_words || 0) - (a.total_words || 0));
    } else if (state.sortMode === 'title_asc') {
      result = [...result].sort((a, b) => a.title.localeCompare(b.title, 'vi'));
    }

    state.filteredStories = result;
    state.renderedStoriesCount = 0;
    DOM.storiesGrid.innerHTML = '';
    
    renderNextStoryBatch();
  }

  function renderNextStoryBatch() {
    const startIndex = state.renderedStoriesCount;
    const nextBatch = state.filteredStories.slice(startIndex, startIndex + state.BATCH_SIZE);
    
    if (nextBatch.length === 0 && startIndex === 0) {
      DOM.storiesGrid.innerHTML = '<div style="grid-column: 1/-1; text-align: center; padding: 40px; color: var(--text-muted);">Không tìm thấy bộ truyện nào phù hợp.</div>';
      DOM.showingStoriesCount.textContent = '0';
      DOM.loadMoreContainer.classList.add('hidden');
      return;
    }

    const frag = document.createDocumentFragment();

    nextBatch.forEach(story => {
      const card = document.createElement('a');
      card.className = 'story-card';
      card.href = `#story/${story.id}`;

      const coverSrc = story.cover_image || 'images/cover.jpg';
      const wordsK = story.total_words ? `${(story.total_words / 1000).toFixed(1)}K từ` : '';

      card.innerHTML = `
        <div class="story-card-cover-box">
          <img src="${coverSrc}" class="story-card-cover" alt="${escapeHTML(story.title)}" onerror="this.src='images/cover.jpg'" loading="lazy">
          <span class="story-card-badge">${escapeHTML(story.status || 'Hoàn Thành')}</span>
        </div>
        <div class="story-card-body">
          <h3 class="story-card-title">${escapeHTML(story.title)}</h3>
          <div class="story-card-author">Tác giả: ${escapeHTML(story.author || 'Đang cập nhật')}</div>
          <p class="story-card-desc">${escapeHTML(story.description || 'Bộ truyện đặc sắc.')}</p>
          <div class="story-card-footer">
            <span>📚 ${story.total_chapters || 0} Chương</span>
            <span>${wordsK}</span>
          </div>
        </div>
      `;
      frag.appendChild(card);
    });

    DOM.storiesGrid.appendChild(frag);
    state.renderedStoriesCount += nextBatch.length;
    DOM.showingStoriesCount.textContent = state.renderedStoriesCount;

    if (state.renderedStoriesCount < state.filteredStories.length) {
      DOM.loadMoreContainer.classList.remove('hidden');
    } else {
      DOM.loadMoreContainer.classList.add('hidden');
    }
  }

  // --- STORY DETAILS & TOC LOADING ---
  async function loadStoryTOC(storyId) {
    if (state.currentStoryId === storyId && state.storyMeta) {
      return state.storyMeta;
    }

    state.currentStoryId = storyId;
    if (DOM.quickStorySelect) DOM.quickStorySelect.value = storyId;

    try {
      let res = await fetch(`data/stories/${storyId}/toc.json`);
      if (!res.ok) {
        res = await fetch('data/toc.json');
      }

      state.storyMeta = await res.json();
      state.toc = state.storyMeta.chapters || [];

      DOM.brandTitle.textContent = state.storyMeta.title;
      DOM.drawerStoryTitle.textContent = `Mục Lục: ${state.storyMeta.title}`;
      DOM.storyTitle.textContent = state.storyMeta.title;
      DOM.heroCover.src = state.storyMeta.cover_image || 'images/cover.jpg';
      DOM.statTotalChap.textContent = state.storyMeta.total_chapters || state.toc.length;
      DOM.statTotalWords.textContent = `${((state.storyMeta.total_words || 0) / 1000).toFixed(1)}K`;
      DOM.statStoryStatus.textContent = state.storyMeta.status || 'Hoàn Thành';
      DOM.storyDescText.textContent = state.storyMeta.description || 'Bộ truyện đặc sắc.';

      const tags = (state.storyMeta.category || 'Tiên Hiệp, Huyền Huyễn').split(',').map(t => t.trim());
      DOM.storyMetaTags.innerHTML = tags.map(t => `<span class="tag">${escapeHTML(t)}</span>`).join('');

      renderTOCList(state.toc);
      populateJumpSelect(state.toc);
      updateNavReadButtons();

      return state.storyMeta;
    } catch (err) {
      console.error(`Failed to load TOC for story ${storyId}:`, err);
      return null;
    }
  }

  function renderTOCList(chapters) {
    const fragment = document.createDocumentFragment();
    chapters.forEach(chap => {
      const a = document.createElement('a');
      a.className = `toc-item ${chap.index === state.currentChapIndex ? 'active' : ''}`;
      a.href = `#read/${state.currentStoryId}/${chap.index}`;
      a.dataset.index = chap.index;
      
      const bookmarkKey = `${state.currentStoryId}_${chap.index}`;
      const isBookmarked = state.bookmarks.includes(bookmarkKey);
      
      a.innerHTML = `
        <div>
          <span style="font-weight: 500;">${chap.title}</span>
          ${isBookmarked ? ' <span title="Đã bookmark">🔖</span>' : ''}
        </div>
        <div class="toc-item-words">${(chap.word_count || 0).toLocaleString()} từ</div>
      `;
      
      a.addEventListener('click', closeTocDrawer, { passive: true });
      fragment.appendChild(a);
    });

    DOM.tocList.replaceChildren(fragment);
  }

  function populateJumpSelect(chapters) {
    const fragment = document.createDocumentFragment();
    chapters.forEach(chap => {
      const opt = document.createElement('option');
      opt.value = chap.index;
      opt.textContent = chap.title;
      if (chap.index === state.currentChapIndex) opt.selected = true;
      fragment.appendChild(opt);
    });
    DOM.selectJumpChap.replaceChildren(fragment);
  }

  // --- MULTI-TIER ULTRA-FAST CHAPTER FETCHER (RAM LRU + INDEXEDDB + NETWORK) ---
  async function fetchChapter(storyId, index) {
    const cacheKey = `${storyId}_${index}`;
    
    // 1. Check RAM LRU Cache (0.01ms response)
    if (state.chapterCache.has(cacheKey)) {
      const cached = state.chapterCache.get(cacheKey);
      state.chapterCache.delete(cacheKey);
      state.chapterCache.set(cacheKey, cached);
      return cached;
    }

    // 2. Check IndexedDB Persistent Cache (1-2ms response)
    const idbData = await ChapterDB.get(cacheKey);
    if (idbData) {
      putInRAMCache(cacheKey, idbData);
      return idbData;
    }

    // 3. Fallback to Network Request
    try {
      let res = await fetch(`data/stories/${storyId}/chapters/${index}.json`);
      if (!res.ok) {
        res = await fetch(`data/chapters/${index}.json`);
      }
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      
      const data = await res.json();
      
      putInRAMCache(cacheKey, data);
      ChapterDB.set(cacheKey, data);

      return data;
    } catch (err) {
      console.error(`Error loading chapter ${storyId}/${index}:`, err);
      return null;
    }
  }

  function putInRAMCache(key, data) {
    if (state.chapterCache.size >= state.MAX_CACHE_SIZE) {
      const oldestKey = state.chapterCache.keys().next().value;
      state.chapterCache.delete(oldestKey);
    }
    state.chapterCache.set(key, data);
  }

  // --- PREDICTIVE AGGRESSIVE MULTI-CHAPTER PREFETCHER ---
  function prefetchBatch(storyId, startIndex, count = 5) {
    const indicesToFetch = [];
    
    // Prefetch forward chapters (N+1 -> N+count)
    for (let i = 1; i <= count; i++) {
      const targetIdx = startIndex + i;
      if (targetIdx <= state.toc.length && !state.prefetchedIndices.has(`${storyId}_${targetIdx}`)) {
        indicesToFetch.push(targetIdx);
      }
    }

    // Prefetch backward chapter (N-1)
    if (startIndex > 1 && !state.prefetchedIndices.has(`${storyId}_${startIndex - 1}`)) {
      indicesToFetch.push(startIndex - 1);
    }

    if (indicesToFetch.length === 0) return;

    const runPrefetch = async () => {
      for (const idx of indicesToFetch) {
        const key = `${storyId}_${idx}`;
        state.prefetchedIndices.add(key);

        if (!state.chapterCache.has(key)) {
          const inIdb = await ChapterDB.get(key);
          if (inIdb) {
            putInRAMCache(key, inIdb);
            continue;
          }

          fetch(`data/stories/${storyId}/chapters/${idx}.json`)
            .then(r => r.ok ? r.json() : fetch(`data/chapters/${idx}.json`).then(res => res.json()))
            .then(data => {
              putInRAMCache(key, data);
              ChapterDB.set(key, data);
            })
            .catch(() => {});
        }
      }
    };

    if ('requestIdleCallback' in window) {
      requestIdleCallback(runPrefetch, { timeout: 1500 });
    } else {
      setTimeout(runPrefetch, 250);
    }
  }

  // --- READER CONTROLLER ---
  async function loadChapter(storyId, index, autoStartTTS = false) {
    await loadStoryTOC(storyId);

    if (index < 1 || index > state.toc.length) return;
    
    const prevIndex = state.currentChapIndex;
    const isNext = index > prevIndex;
    
    stopAutoScroll();
    stopTTS();
    
    state.currentChapIndex = index;
    state.hasTriggeredDeepPrefetch = false;
    saveStoryProgress(storyId, index);

    DOM.librarySection.classList.add('hidden');
    DOM.overviewSection.classList.add('hidden');
    DOM.readerSection.classList.remove('hidden');

    const cacheKey = `${storyId}_${index}`;
    const isInstant = state.chapterCache.has(cacheKey);

    if (!isInstant) {
      DOM.chapTitle.textContent = 'Đang tải...';
      DOM.chapContent.innerHTML = '<p>Đang tải nội dung chương...</p>';
    }

    const chapData = await fetchChapter(storyId, index);

    if (!chapData) {
      DOM.chapTitle.textContent = 'Lỗi Tải Chương';
      DOM.chapContent.innerHTML = '<p>Không thể tải nội dung chương. Vui lòng thử lại sau.</p>';
      return;
    }

    // Hardware-accelerated slide transition animation
    DOM.readerPaper.classList.remove('slide-in-right', 'slide-in-left');
    void DOM.readerPaper.offsetWidth; // Force reflow
    DOM.readerPaper.classList.add(isNext ? 'slide-in-right' : 'slide-in-left');

    DOM.chapSubtitle.textContent = `${state.storyMeta.title} • Chương ${index} / ${state.toc.length}`;
    DOM.chapTitle.textContent = chapData.title;
    DOM.chapWordCount.textContent = `${(chapData.word_count || 0).toLocaleString()} từ`;
    
    const estMinutes = Math.max(1, Math.round((chapData.word_count || 0) / 250));
    DOM.chapEstTime.textContent = `~${estMinutes} phút đọc`;

    const paragraphs = chapData.content.split('\n\n').filter(p => p.trim().length > 0);
    
    const frag = document.createDocumentFragment();
    paragraphs.forEach((pText, i) => {
      const p = document.createElement('p');
      p.dataset.paraIndex = i;
      p.title = 'Nhấp để nghe đọc từ đoạn này';
      p.textContent = pText;
      frag.appendChild(p);
    });
    DOM.chapContent.replaceChildren(frag);

    state.tts.paragraphs = paragraphs;
    state.tts.currentParaIndex = 0;

    if (DOM.readingSeekRange) {
      DOM.readingSeekRange.min = 0;
      DOM.readingSeekRange.max = Math.max(0, paragraphs.length - 1);
      DOM.readingSeekRange.value = 0;
    }
    if (DOM.ttsSeekRange) {
      DOM.ttsSeekRange.min = 0;
      DOM.ttsSeekRange.max = Math.max(0, paragraphs.length - 1);
      DOM.ttsSeekRange.value = 0;
    }
    updateScrubberUI(0);

    DOM.btnPrevChap.disabled = (index <= 1);
    DOM.btnNextChap.disabled = (index >= state.toc.length);
    DOM.selectJumpChap.value = index;

    updateBookmarkIcon();
    updateTOCActiveState();
    updateNavReadButtons();

    window.scrollTo({ top: 0, behavior: 'instant' });

    // Kick off predictive prefetch of next 5 chapters
    prefetchBatch(storyId, index, 5);

    if (autoStartTTS) {
      setTimeout(() => startTTS(0), 300);
    }
  }

  function updateTOCActiveState() {
    const items = DOM.tocList.querySelectorAll('.toc-item');
    items.forEach(item => {
      const idx = parseInt(item.dataset.index, 10);
      item.classList.toggle('active', idx === state.currentChapIndex);
    });
  }

  function updateNavReadButtons() {
    const lastChap = getStoryLastChap(state.currentStoryId);
    const text = `Đọc Chương ${lastChap}`;
    DOM.navReadText.textContent = text;
    DOM.btnNavRead.href = `#read/${state.currentStoryId}/${lastChap}`;
    DOM.btnStartReadText.textContent = (lastChap > 1) ? text : 'Đọc Từ Chương 1';
  }

  function updateBookmarkIcon() {
    const bookmarkKey = `${state.currentStoryId}_${state.currentChapIndex}`;
    const isBookmarked = state.bookmarks.includes(bookmarkKey);
    DOM.btnBookmark.style.color = isBookmarked ? '#f59e0b' : 'inherit';
  }

  function toggleBookmark() {
    const bookmarkKey = `${state.currentStoryId}_${state.currentChapIndex}`;
    const pos = state.bookmarks.indexOf(bookmarkKey);
    if (pos > -1) {
      state.bookmarks.splice(pos, 1);
      showToast('Đã xóa đánh dấu');
    } else {
      state.bookmarks.push(bookmarkKey);
      showToast('🔖 Đã đánh dấu trang');
    }
    localStorage.setItem('tn_bookmarks', JSON.stringify(state.bookmarks));
    updateBookmarkIcon();
    renderTOCList(state.toc);
  }

  // --- ROUTING ENGINE ---
  async function handleHashRoute() {
    const hash = window.location.hash || '#library';

    if (hash.startsWith('#read/')) {
      const parts = hash.replace('#read/', '').split('/');
      const storyId = parts[0] || state.currentStoryId;
      const chapIndex = parseInt(parts[1] || '1', 10);
      loadChapter(storyId, chapIndex);
      return;
    }

    if (hash.startsWith('#story/')) {
      const storyId = hash.replace('#story/', '').trim();
      await loadStoryTOC(storyId || state.currentStoryId);
      stopTTS();
      stopAutoScroll();
      DOM.librarySection.classList.add('hidden');
      DOM.readerSection.classList.add('hidden');
      DOM.overviewSection.classList.remove('hidden');
      window.scrollTo({ top: 0, behavior: 'instant' });
      return;
    }

    if (hash.startsWith('#chap-')) {
      const chapIndex = parseInt(hash.replace('#chap-', ''), 10);
      if (!isNaN(chapIndex)) {
        loadChapter(state.currentStoryId, chapIndex);
        return;
      }
    }

    if (hash === '#reader') {
      const lastChap = getStoryLastChap(state.currentStoryId);
      loadChapter(state.currentStoryId, lastChap);
      return;
    }

    if (hash === '#overview') {
      await loadStoryTOC(state.currentStoryId);
      DOM.librarySection.classList.add('hidden');
      DOM.readerSection.classList.add('hidden');
      DOM.overviewSection.classList.remove('hidden');
      window.scrollTo({ top: 0, behavior: 'instant' });
      return;
    }

    // Default Route: #library
    stopTTS();
    stopAutoScroll();
    renderRecentShelf();
    DOM.overviewSection.classList.add('hidden');
    DOM.readerSection.classList.add('hidden');
    DOM.librarySection.classList.remove('hidden');
    window.scrollTo({ top: 0, behavior: 'instant' });
  }

  // --- MULTI-VOICE TEXT-TO-SPEECH (TTS) ENGINE ---
  function initTTSVoices() {
    if (!state.tts.synth) return;

    function populateVoices() {
      state.tts.voices = state.tts.synth.getVoices();
      if (!DOM.selectTtsVoice) return;
      DOM.selectTtsVoice.innerHTML = '';
      
      const viVoices = state.tts.voices.filter(v => 
        v.lang.toLowerCase().includes('vi') || 
        v.name.toLowerCase().includes('vietnam') ||
        v.name.toLowerCase().includes('tiếng việt') ||
        v.name.toLowerCase().includes('linh') ||
        v.name.toLowerCase().includes('an') ||
        v.name.toLowerCase().includes('mai')
      );
      const otherVoices = state.tts.voices.filter(v => !viVoices.includes(v));

      if (viVoices.length > 0) {
        const groupVi = document.createElement('optgroup');
        groupVi.label = '🇻🇳 Giọng Tiếng Việt (iOS & Android)';

        viVoices.forEach(voice => {
          const opt = document.createElement('option');
          opt.value = voice.name;
          
          let displayTitle = voice.name;
          if (voice.name.includes('HoaiMy')) displayTitle = '🇻🇳 Hoài Mỹ (Nữ Truyền Cảm)';
          else if (voice.name.includes('NamMinh')) displayTitle = '🇻🇳 Nam Minh (Nam Trầm Ấm)';
          else if (voice.name.toLowerCase().includes('google')) displayTitle = '🇻🇳 Google Tiếng Việt (Android)';
          else if (voice.name.toLowerCase().includes('linh') || voice.name.toLowerCase().includes('apple')) displayTitle = '🇻🇳 Siri Tiếng Việt (iOS)';
          else displayTitle = `🇻🇳 ${voice.name}`;

          opt.textContent = displayTitle;
          groupVi.appendChild(opt);
        });

        DOM.selectTtsVoice.appendChild(groupVi);
        state.tts.selectedVoice = viVoices[0];
      }

      if (otherVoices.length > 0) {
        const groupOther = document.createElement('optgroup');
        groupOther.label = '🌐 Giọng Quốc Tế Khác';

        otherVoices.slice(0, 6).forEach(voice => {
          const opt = document.createElement('option');
          opt.value = voice.name;
          opt.textContent = `${voice.name} (${voice.lang})`;
          groupOther.appendChild(opt);
        });

        DOM.selectTtsVoice.appendChild(groupOther);
      }

      if (viVoices.length === 0 && otherVoices.length > 0) {
        state.tts.selectedVoice = otherVoices[0];
      }
    }

    populateVoices();
    if (speechSynthesis.onvoiceschanged !== undefined) {
      speechSynthesis.onvoiceschanged = populateVoices;
    }
  }

  function applyPreset(presetType) {
    state.tts.preset = presetType;
    if (presetType === 'male_deep') {
      state.tts.pitch = 0.75;
      state.tts.rate = 0.95;
      const maleVoice = state.tts.voices.find(v => v.name.toLowerCase().includes('namminh') || v.name.toLowerCase().includes('male'));
      if (maleVoice) state.tts.selectedVoice = maleVoice;
    } else if (presetType === 'female_warm') {
      state.tts.pitch = 1.25;
      state.tts.rate = 1.05;
      const femaleVoice = state.tts.voices.find(v => v.name.toLowerCase().includes('hoaimy') || v.name.toLowerCase().includes('female') || v.name.toLowerCase().includes('linh'));
      if (femaleVoice) state.tts.selectedVoice = femaleVoice;
    } else if (presetType === 'storyteller') {
      state.tts.pitch = 1.0;
      state.tts.rate = 1.0;
    }

    DOM.selectTtsPitch.value = state.tts.pitch.toString();
    DOM.selectTtsSpeed.value = state.tts.rate.toString();
    if (state.tts.selectedVoice) {
      DOM.selectTtsVoice.value = state.tts.selectedVoice.name;
    }
  }

  function startTTS(paraIndex = 0) {
    if (!state.tts.synth) {
      alert('Trình duyệt của bạn không hỗ trợ đọc giọng nói SpeechSynthesis API.');
      return;
    }

    if (state.tts.paragraphs.length === 0) return;

    if (paraIndex < 0) paraIndex = 0;
    if (paraIndex >= state.tts.paragraphs.length) {
      if (state.currentChapIndex < state.toc.length) {
        window.location.hash = `#read/${state.currentStoryId}/${state.currentChapIndex + 1}`;
        setTimeout(() => loadChapter(state.currentStoryId, state.currentChapIndex + 1, true), 400);
      } else {
        stopTTS();
        alert('Đã đọc xong toàn bộ chương!');
      }
      return;
    }

    if (state.tts.synth.paused) {
      state.tts.synth.resume();
    }
    state.tts.synth.cancel();
    clearTimeout(state.tts.watchdogTimer);

    state.tts.currentParaIndex = paraIndex;
    const textToRead = state.tts.paragraphs[paraIndex];
    state.tts.utterance = new SpeechSynthesisUtterance(textToRead);

    if (state.tts.selectedVoice) {
      state.tts.utterance.voice = state.tts.selectedVoice;
    }
    state.tts.utterance.rate = state.tts.rate;
    state.tts.utterance.pitch = state.tts.pitch;
    state.tts.utterance.lang = 'vi-VN';

    highlightParagraph(paraIndex);
    updateScrubberUI(paraIndex);
    acquireWakeLock();
    updateMediaSessionMetadata(DOM.chapTitle.textContent);

    let isAdvancing = false;
    const advanceNext = () => {
      if (isAdvancing) return;
      isAdvancing = true;
      clearTimeout(state.tts.watchdogTimer);
      if (state.tts.isPlaying && !state.tts.isPaused) {
        startTTS(state.tts.currentParaIndex + 1);
      }
    };

    state.tts.utterance.onend = advanceNext;
    state.tts.utterance.onerror = (e) => {
      console.warn('TTS event error:', e);
      advanceNext();
    };

    const estimatedDurationMs = Math.max(3000, (textToRead.length / 10) * 1000 / state.tts.rate) + 4000;
    state.tts.watchdogTimer = setTimeout(() => {
      if (state.tts.isPlaying && !state.tts.isPaused) {
        advanceNext();
      }
    }, estimatedDurationMs);

    state.tts.isPlaying = true;
    state.tts.isPaused = false;
    
    updateTTSControlsUI();
    state.tts.synth.speak(state.tts.utterance);
  }

  function pauseTTS() {
    if (state.tts.synth && state.tts.isPlaying) {
      state.tts.synth.pause();
      state.tts.isPaused = true;
      clearTimeout(state.tts.watchdogTimer);
      releaseWakeLock();
      updateTTSControlsUI();
    }
  }

  function resumeTTS() {
    if (state.tts.synth && state.tts.isPaused) {
      state.tts.synth.resume();
      state.tts.isPaused = false;
      acquireWakeLock();
      updateTTSControlsUI();
    } else {
      startTTS(state.tts.currentParaIndex);
    }
  }

  function stopTTS() {
    if (state.tts.synth) {
      state.tts.synth.cancel();
    }
    clearTimeout(state.tts.watchdogTimer);
    state.tts.isPlaying = false;
    state.tts.isPaused = false;
    removeParagraphHighlights();
    releaseWakeLock();
    updateTTSControlsUI();
  }

  function highlightParagraph(index) {
    removeParagraphHighlights();
    const targetEl = DOM.chapContent.querySelector(`p[data-para-index="${index}"]`);
    if (targetEl) {
      targetEl.classList.add('tts-highlight');
      targetEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  }

  function removeParagraphHighlights() {
    const activeEl = DOM.chapContent.querySelector('.tts-highlight');
    if (activeEl) activeEl.classList.remove('tts-highlight');
  }

  function updateScrubberUI(currentIdx) {
    const total = state.tts.paragraphs.length;
    const current = (currentIdx !== undefined) ? currentIdx : state.tts.currentParaIndex;
    
    if (total > 0) {
      const displayCurrent = Math.min(current + 1, total);
      const percent = Math.round((displayCurrent / total) * 100);
      const progressRatio = (current / Math.max(1, total - 1)) * 100;
      const gradientStyle = `linear-gradient(90deg, var(--accent-color) ${progressRatio}%, var(--bg-main) ${progressRatio}%)`;

      if (DOM.scrubberParaDisplay) DOM.scrubberParaDisplay.textContent = `Đoạn ${displayCurrent} / ${total}`;
      if (DOM.scrubberPercentDisplay) DOM.scrubberPercentDisplay.textContent = `${percent}%`;
      if (DOM.readingSeekRange && !state.isSeekingManually) {
        DOM.readingSeekRange.value = current;
        DOM.readingSeekRange.style.background = gradientStyle;
      }

      if (DOM.ttsParaCounter) DOM.ttsParaCounter.textContent = `Đoạn ${displayCurrent} / ${total}`;
      if (DOM.ttsProgressPercent) DOM.ttsProgressPercent.textContent = `${percent}%`;
      if (DOM.ttsSeekRange) {
        DOM.ttsSeekRange.value = current;
        DOM.ttsSeekRange.style.background = gradientStyle;
      }
    } else {
      if (DOM.scrubberParaDisplay) DOM.scrubberParaDisplay.textContent = 'Đoạn 0 / 0';
      if (DOM.scrubberPercentDisplay) DOM.scrubberPercentDisplay.textContent = '0%';
      if (DOM.ttsParaCounter) DOM.ttsParaCounter.textContent = 'Đoạn 0 / 0';
      if (DOM.ttsProgressPercent) DOM.ttsProgressPercent.textContent = '0%';
    }
  }

  function updateTTSControlsUI() {
    if (state.tts.isPlaying || state.tts.isPaused) {
      DOM.audioPlayerBar.classList.remove('hidden');
      DOM.btnToggleTTS.classList.add('active');
    } else {
      DOM.audioPlayerBar.classList.add('hidden');
      DOM.btnToggleTTS.classList.remove('active');
    }

    if (state.tts.isPlaying && !state.tts.isPaused) {
      DOM.ttsPlayPauseIcon.textContent = '⏸️';
      DOM.ttsPlayPauseText.textContent = 'Tạm dừng';
      DOM.ttsPulseIndicator.style.animationPlayState = 'running';
    } else if (state.tts.isPaused) {
      DOM.ttsPlayPauseIcon.textContent = '▶️';
      DOM.ttsPlayPauseText.textContent = 'Tiếp tục';
      DOM.ttsPulseIndicator.style.animationPlayState = 'paused';
    }

    updateScrubberUI();
  }

  // --- AUTO SCROLL ENGINE ---
  function startAutoScroll() {
    if (state.autoScrollInterval) clearInterval(state.autoScrollInterval);
    DOM.autoScrollPanel.classList.remove('hidden');
    
    state.autoScrollInterval = setInterval(() => {
      window.scrollBy({ top: state.autoScrollSpeed, behavior: 'smooth' });
      if ((window.innerHeight + window.scrollY) >= document.body.offsetHeight - 20) {
        stopAutoScroll();
      }
    }, 50);
  }

  function stopAutoScroll() {
    if (state.autoScrollInterval) {
      clearInterval(state.autoScrollInterval);
      state.autoScrollInterval = null;
    }
    DOM.autoScrollPanel.classList.add('hidden');
  }

  // --- EVENT LISTENERS ---
  function setupEventListeners() {
    DOM.quickStorySelect.addEventListener('change', (e) => {
      const selectedId = e.target.value;
      const lastChap = getStoryLastChap(selectedId);
      window.location.hash = `#read/${selectedId}/${lastChap}`;
    });

    // Category Filter Pills
    DOM.categoryPillsWrapper.addEventListener('click', (e) => {
      const pill = e.target.closest('.cat-pill');
      if (pill) {
        DOM.categoryPillsWrapper.querySelectorAll('.cat-pill').forEach(p => p.classList.remove('active'));
        pill.classList.add('active');
        state.selectedCategory = pill.dataset.category || 'all';
        applyFilterAndSort();
      }
    });

    // Sort Selector
    DOM.selectStorySort.addEventListener('change', (e) => {
      state.sortMode = e.target.value;
      applyFilterAndSort();
    });

    // Load More Button
    DOM.btnLoadMoreStories.addEventListener('click', renderNextStoryBatch);

    // Debounced Search Input
    let libSearchTimeout = null;
    DOM.searchLibraryInput.addEventListener('input', () => {
      clearTimeout(libSearchTimeout);
      libSearchTimeout = setTimeout(() => {
        applyFilterAndSort();
      }, 70);
    });

    // Navigation & Modals
    DOM.btnOpenToc.addEventListener('click', openTocDrawer);
    DOM.btnCloseToc.addEventListener('click', closeTocDrawer);
    DOM.modalToc.addEventListener('click', (e) => {
      if (e.target === DOM.modalToc) closeTocDrawer();
    });

    DOM.btnHeroToc.addEventListener('click', openTocDrawer);
    DOM.btnStartRead.addEventListener('click', () => {
      const lastChap = getStoryLastChap(state.currentStoryId);
      window.location.hash = `#read/${state.currentStoryId}/${lastChap}`;
    });

    DOM.btnHeroListen.addEventListener('click', () => {
      const lastChap = getStoryLastChap(state.currentStoryId);
      window.location.hash = `#read/${state.currentStoryId}/${lastChap}`;
      setTimeout(() => startTTS(0), 300);
    });

    let searchTimeout = null;
    DOM.searchTocInput.addEventListener('input', (e) => {
      clearTimeout(searchTimeout);
      searchTimeout = setTimeout(() => {
        const query = e.target.value.toLowerCase().trim();
        const filtered = state.toc.filter(chap => 
          chap.title.toLowerCase().includes(query) || 
          chap.index.toString() === query
        );
        renderTOCList(filtered);
      }, 60);
    });

    DOM.btnToggleTheme.addEventListener('click', () => {
      const themes = ['theme-dark', 'theme-oled', 'theme-sepia', 'theme-cream', 'theme-emerald'];
      const currentIdx = themes.indexOf(state.settings.theme);
      const nextTheme = themes[(currentIdx + 1) % themes.length];
      state.settings.theme = nextTheme;
      applySettings();
      saveSettings();
    });

    DOM.selectTheme.addEventListener('change', (e) => {
      state.settings.theme = e.target.value;
      applySettings();
      saveSettings();
    });

    DOM.selectFont.addEventListener('change', (e) => {
      state.settings.fontFamily = e.target.value;
      applySettings();
      saveSettings();
    });

    DOM.btnFontDec.addEventListener('click', () => {
      if (state.settings.fontSize > 13) {
        state.settings.fontSize -= 1;
        applySettings();
        saveSettings();
      }
    });

    DOM.btnFontInc.addEventListener('click', () => {
      if (state.settings.fontSize < 30) {
        state.settings.fontSize += 1;
        applySettings();
        saveSettings();
      }
    });

    DOM.btnPrevChap.addEventListener('click', () => {
      if (state.currentChapIndex > 1) {
        window.location.hash = `#read/${state.currentStoryId}/${state.currentChapIndex - 1}`;
      }
    });

    DOM.btnNextChap.addEventListener('click', () => {
      if (state.currentChapIndex < state.toc.length) {
        window.location.hash = `#read/${state.currentStoryId}/${state.currentChapIndex + 1}`;
      }
    });

    DOM.selectJumpChap.addEventListener('change', (e) => {
      const targetChap = parseInt(e.target.value, 10);
      window.location.hash = `#read/${state.currentStoryId}/${targetChap}`;
    });

    DOM.btnBookmark.addEventListener('click', toggleBookmark);

    // Event Delegation for Paragraph Clicks
    DOM.chapContent.addEventListener('click', (e) => {
      const p = e.target.closest('p[data-para-index]');
      if (p) {
        const paraIndex = parseInt(p.dataset.paraIndex, 10);
        if (!isNaN(paraIndex)) {
          startTTS(paraIndex);
        }
      }
    });

    // --- VISUAL READING SCRUBBER SEEK HANDLERS ---
    DOM.readingSeekRange.addEventListener('input', (e) => {
      state.isSeekingManually = true;
      const targetIndex = parseInt(e.target.value, 10);
      updateScrubberUI(targetIndex);
      
      const targetEl = DOM.chapContent.querySelector(`p[data-para-index="${targetIndex}"]`);
      if (targetEl) {
        targetEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    });

    DOM.readingSeekRange.addEventListener('change', (e) => {
      state.isSeekingManually = false;
      const targetIndex = parseInt(e.target.value, 10);
      if (state.tts.isPlaying || state.tts.isPaused) {
        startTTS(targetIndex);
      }
    });

    // --- AUDIO PLAYER BAR CONTROLS ---
    DOM.btnToggleTTS.addEventListener('click', () => {
      if (state.tts.isPlaying) {
        stopTTS();
      } else {
        startTTS(state.tts.currentParaIndex || 0);
      }
    });

    DOM.btnTtsPlayPause.addEventListener('click', () => {
      if (state.tts.isPlaying && !state.tts.isPaused) {
        pauseTTS();
      } else {
        resumeTTS();
      }
    });

    DOM.btnTtsStop.addEventListener('click', stopTTS);

    DOM.btnTtsPrevPara.addEventListener('click', () => {
      if (state.tts.currentParaIndex > 0) {
        startTTS(state.tts.currentParaIndex - 1);
      }
    });

    DOM.btnTtsNextPara.addEventListener('click', () => {
      if (state.tts.currentParaIndex < state.tts.paragraphs.length - 1) {
        startTTS(state.tts.currentParaIndex + 1);
      }
    });

    // Audio Scrubber Range Input
    DOM.ttsSeekRange.addEventListener('input', (e) => {
      const targetIndex = parseInt(e.target.value, 10);
      state.tts.currentParaIndex = targetIndex;
      updateScrubberUI(targetIndex);
      highlightParagraph(targetIndex);
    });

    DOM.ttsSeekRange.addEventListener('change', (e) => {
      const targetIndex = parseInt(e.target.value, 10);
      startTTS(targetIndex);
    });

    DOM.selectTtsSpeed.addEventListener('change', (e) => {
      state.tts.rate = parseFloat(e.target.value);
      if (state.tts.isPlaying && !state.tts.isPaused) {
        startTTS(state.tts.currentParaIndex);
      }
    });

    DOM.selectTtsPitch.addEventListener('change', (e) => {
      state.tts.pitch = parseFloat(e.target.value);
      if (state.tts.isPlaying && !state.tts.isPaused) {
        startTTS(state.tts.currentParaIndex);
      }
    });

    DOM.selectTtsVoice.addEventListener('change', (e) => {
      const voiceName = e.target.value;
      state.tts.selectedVoice = state.tts.voices.find(v => v.name === voiceName) || null;
      if (state.tts.isPlaying && !state.tts.isPaused) {
        startTTS(state.tts.currentParaIndex);
      }
    });

    DOM.selectTtsPreset.addEventListener('change', (e) => {
      applyPreset(e.target.value);
      if (state.tts.isPlaying && !state.tts.isPaused) {
        startTTS(state.tts.currentParaIndex);
      }
    });

    // Auto Scroll listeners
    DOM.btnToggleAutoScroll.addEventListener('click', () => {
      if (state.autoScrollInterval) {
        stopAutoScroll();
      } else {
        startAutoScroll();
      }
    });

    DOM.btnAutoScrollStop.addEventListener('click', stopAutoScroll);
    DOM.btnAutoScrollDec.addEventListener('click', () => {
      if (state.autoScrollSpeed > 1) {
        state.autoScrollSpeed -= 1;
        DOM.autoScrollSpeedText.textContent = `Tốc độ: ${state.autoScrollSpeed}`;
      }
    });
    DOM.btnAutoScrollInc.addEventListener('click', () => {
      if (state.autoScrollSpeed < 10) {
        state.autoScrollSpeed += 1;
        DOM.autoScrollSpeedText.textContent = `Tốc độ: ${state.autoScrollSpeed}`;
      }
    });

    // Floating Scrubber Toggle
    DOM.fabToggleScrubber.addEventListener('click', () => {
      DOM.readingScrubberCard.scrollIntoView({ behavior: 'smooth', block: 'center' });
      DOM.readingSeekRange.focus();
    });

    DOM.fabScrollTop.addEventListener('click', () => {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });

    // Keyboard Hotkeys for Instant Chapter Transition (A/D, J/K, Left/Right)
    document.addEventListener('keydown', (e) => {
      if (e.target.tagName === 'INPUT' || e.target.tagName === 'SELECT') return;

      const isReaderActive = !DOM.readerSection.classList.contains('hidden');

      if ((e.key === 'ArrowLeft' || e.key === 'a' || e.key === 'A') && isReaderActive) {
        if (e.shiftKey && (state.tts.isPlaying || state.tts.isPaused)) {
          if (state.tts.currentParaIndex > 0) startTTS(state.tts.currentParaIndex - 1);
        } else if (state.currentChapIndex > 1) {
          window.location.hash = `#read/${state.currentStoryId}/${state.currentChapIndex - 1}`;
        }
      } else if ((e.key === 'ArrowRight' || e.key === 'd' || e.key === 'D') && isReaderActive) {
        if (e.shiftKey && (state.tts.isPlaying || state.tts.isPaused)) {
          if (state.tts.currentParaIndex < state.tts.paragraphs.length - 1) startTTS(state.tts.currentParaIndex + 1);
        } else if (state.currentChapIndex < state.toc.length) {
          window.location.hash = `#read/${state.currentStoryId}/${state.currentChapIndex + 1}`;
        }
      } else if (e.key === 'Escape') {
        if (DOM.modalToc.classList.contains('active')) {
          closeTocDrawer();
        } else {
          openTocDrawer();
        }
      } else if (e.key === ' ') {
        if (state.tts.isPlaying || state.tts.isPaused) {
          e.preventDefault();
          if (state.tts.isPlaying && !state.tts.isPaused) {
            pauseTTS();
          } else {
            resumeTTS();
          }
        }
      }
    });
  }

  function openTocDrawer() {
    DOM.modalToc.classList.add('active');
    DOM.searchTocInput.focus();
  }

  function closeTocDrawer() {
    DOM.modalToc.classList.remove('active');
  }

  let scrollTicking = false;
  function onScrollThrottled() {
    if (!scrollTicking) {
      window.requestAnimationFrame(() => {
        handleScroll();
        scrollTicking = false;
      });
      scrollTicking = true;
    }
  }

  function handleScroll() {
    const currentY = window.scrollY;
    const totalHeight = document.documentElement.scrollHeight - window.innerHeight;
    
    if (totalHeight > 0) {
      const progress = (currentY / totalHeight) * 100;
      DOM.progressBar.style.width = `${progress}%`;

      // Auto update reading progress scrubber
      if (!DOM.readerSection.classList.contains('hidden') && !state.isSeekingManually && state.tts.paragraphs.length > 0) {
        const totalParas = state.tts.paragraphs.length;
        const approxParaIndex = Math.min(totalParas - 1, Math.floor((currentY / Math.max(1, totalHeight)) * totalParas));
        updateScrubberUI(approxParaIndex);

        // Predictive deep prefetch trigger when reader reaches 50% of current chapter
        if (progress > 50 && !state.hasTriggeredDeepPrefetch) {
          state.hasTriggeredDeepPrefetch = true;
          prefetchBatch(state.currentStoryId, state.currentChapIndex + 5, 5);
        }
      }
    }

    if (currentY > 120) {
      if (currentY > state.lastScrollY + 10 && !state.isHeaderHidden) {
        DOM.appHeader.classList.add('header-hidden');
        state.isHeaderHidden = true;
      } else if (currentY < state.lastScrollY - 10 && state.isHeaderHidden) {
        DOM.appHeader.classList.remove('header-hidden');
        state.isHeaderHidden = false;
      }
    } else if (state.isHeaderHidden) {
      DOM.appHeader.classList.remove('header-hidden');
      state.isHeaderHidden = false;
    }

    state.lastScrollY = currentY;
  }

  function escapeHTML(str) {
    if (!str) return '';
    return str.replace(/[&<>'"]/g, 
      tag => ({
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        "'": '&#39;',
        '"': '&quot;'
      }[tag] || tag)
    );
  }

  // Start app
  initApp();
});
