/* ============================================================
   ShopeeFood AI — Application Router & State Manager (SPA)
   ============================================================ */

const App = {
  currentScreen: 'home',
  currentUser: null,
  foods: [],
  selectedCategory: 'Tất cả',
  navigationHistory: [],
  chatBoxOpen: false,
  pendingPersonaId: null,
  onlyUnderBudget: true,
  cameFromChat: false,

  /**
   * Main entry point
   */
  async init() {
    console.log('[App] Initializing ShopeeFood AI App...');

    // Bind global DOM elements and event handlers
    this.setupListeners();

    // Check backend health
    try {
      const health = await API.healthCheck();
      console.log('[App] Backend status:', health);
    } catch (e) {
      console.warn('[App] Backend connection failed, check console logs.', e);
      this.showToast('⚠️ Không kết nối được với API server!');
    }

    try {
      const foodResponse = await API.getFoods();
      this.foods = foodResponse.foods || [];
    } catch (e) {
      console.warn('[App] Initial food catalog load failed.', e);
      this.foods = [];
    }

    // Default startup route
    this.navigate('home');
  },

  /**
   * Global event handlers
   */
  setupListeners() {
    // 1. Onboarding selector (Choose Persona Card)
    const cards = document.querySelectorAll('#persona-selector .persona-card');
    cards.forEach(card => {
      card.addEventListener('click', () => {
        const personaId = card.getAttribute('data-persona');
        this.selectPersona(personaId);
      });
    });

    // 2. Change persona button in Home header
    document.getElementById('btn-change-persona').addEventListener('click', () => {
      this.currentUser = null;
      this.renderHome();
      this.openChatBox();
    });

    // 3. AI Banner click to chat trigger
    const homeAiBanner = document.getElementById('home-ai-banner');
    if (homeAiBanner) {
      homeAiBanner.addEventListener('click', () => {
        this.openChatBox(true);
      });
    }

    // 3b. Campaign Banner click trigger
    const campaignBanner = document.getElementById('home-campaign-banner');
    if (campaignBanner) {
      campaignBanner.addEventListener('click', () => {
        this.showToast('🍜 Đang mở Deal Hot: Mì Trộn Xá Xíu Trứng Lòng Đào - Giảm 50%!');
        setTimeout(() => {
          this.navigate('detail', { foodId: 'food_003' });
        }, 800);
      });
    }

    // 4. Search bar wrapper click to chat trigger
    document.getElementById('search-bar-trigger').addEventListener('click', () => {
      this.openChatBox(true);
    });

    // 5. Header quick consultation button
    document.getElementById('btn-home-chat-trigger').addEventListener('click', () => {
      this.openChatBox(true);
    });

    // 6. Floating chat entry
    document.getElementById('floating-chat-btn').addEventListener('click', () => {
      this.openChatBox(true);
    });

    // 7. Navigation tabs at bottom
    const navItems = document.querySelectorAll('#app-bottom-nav .nav-item');
    navItems.forEach(item => {
      item.addEventListener('click', () => {
        const screen = item.getAttribute('data-screen');
        if (screen === 'profile') {
          // Just show profile info via toast for MVP
          if (this.currentUser) {
            this.showToast(`👤 ${this.currentUser.demographic}\n📍 ${this.currentUser.location}`);
          } else {
            this.openChatBox(true);
          }
        } else if (screen === 'orders') {
          this.showToast('📋 Tính năng Đơn hàng đang được phát triển!');
        } else if (screen === 'favorites') {
          this.showToast('❤️ Tính năng Yêu thích đang được phát triển!');
        } else if (screen === 'notifications') {
          this.showToast('🔔 Tính năng Thông báo đang được phát triển!');
        } else {
          this.navigate(screen);
        }
      });
    });

    // 8. Chat close button
    document.getElementById('chat-close-btn').addEventListener('click', () => {
      this.closeChatBox();
    });

    // 9. Food detail back button
    document.getElementById('detail-back-btn').addEventListener('click', () => {
      const wasFromChat = this.cameFromChat;
      this.cameFromChat = false;

      // Return to previous screen
      if (this.navigationHistory.length > 1) {
        this.navigationHistory.pop(); // Remove current
        const prev = this.navigationHistory.pop(); // Pop previous to navigate back
        this.navigate(prev);
      } else {
        this.navigate('home');
      }

      if (wasFromChat) {
        this.openChatBox(true);
      }
    });

    // 10. Order button click
    document.getElementById('detail-order-submit').addEventListener('click', () => {
      const foodName = document.getElementById('detail-food-name').textContent;
      this.showToast(`🛒 Đã đặt thành công món ${foodName}!`);

      // Return to home screen after delay
      setTimeout(() => {
        this.navigate('home');
      }, 1500);
    });

    // 11. Category filtering
    const categoryPills = document.querySelectorAll('#category-pills .category-pill');
    categoryPills.forEach(pill => {
      pill.addEventListener('click', () => {
        categoryPills.forEach(p => p.classList.remove('active'));
        pill.classList.add('active');
        this.selectedCategory = pill.getAttribute('data-category');
        this.renderFoodCatalog();
      });
    });

    // 12. Budget filter toggle
    const budgetToggle = document.getElementById('budget-filter-toggle');
    if (budgetToggle) {
      budgetToggle.addEventListener('change', (e) => {
        this.onlyUnderBudget = e.target.checked;
        this.renderFoodCatalog();
      });
    }
  },

  /**
   * Router to switch active screens
   * @param {string} screen - 'onboarding', 'home', 'chat', 'detail'
   * @param {object} params - Optional parameters (e.g. foodId)
   */
  async navigate(screen, params = {}) {
    console.log(`[Router] Navigating: ${this.currentScreen} ➔ ${screen}`, params);

    if (screen === 'chat') {
      this.openChatBox(true);
      return;
    }

    if (params.fromChat) {
      this.cameFromChat = true;
    } else if (screen === 'home') {
      this.cameFromChat = false;
    }

    this.currentScreen = screen;
    this.navigationHistory.push(screen);
    this.closeChatBox();

    // Hide all screens
    const screens = document.querySelectorAll('.screen');
    screens.forEach(s => s.classList.remove('active'));

    // Show destination screen
    const targetScreen = document.getElementById(`screen-${screen}`);
    if (targetScreen) {
      targetScreen.classList.add('active');
    }

    // Toggle Tab bar visibility
    const bottomNav = document.getElementById('app-bottom-nav');
    if (screen === 'home' || screen === 'chat') {
      bottomNav.style.display = 'flex';
      this.updateActiveNav(screen === 'chat' ? 'home' : screen);
    } else {
      bottomNav.style.display = 'none';
    }

    // Handle screen-specific renders
    if (screen === 'onboarding') {
      this.currentUser = null;
      document.getElementById('floating-chat-btn').classList.remove('visible');
    } else if (screen === 'home') {
      this.renderHome();
    } else if (screen === 'detail') {
      this.renderFoodDetail(params.foodId);
    }
  },

  /**
   * Highlight bottom nav active tab
   */
  updateActiveNav(screen) {
    const navItems = document.querySelectorAll('#app-bottom-nav .nav-item');
    navItems.forEach(item => {
      const itemScreen = item.getAttribute('data-screen');
      if (itemScreen === screen) {
        item.classList.add('active');
      } else {
        item.classList.remove('active');
      }
    });
  },

  /**
   * Load user details and navigate to Home screen
   * @param {string} userId 
   */
  async selectPersona(userId) {
    try {
      await this.setPersona(userId);
      this.navigate('home');
      this.showToast('Đã cá nhân hóa hồ sơ hiện tại 🍱');
    } catch (error) {
      console.error('[App] Error selecting persona:', error);
      this.showToast('Không thể tải hồ sơ người dùng!');
    }
  },

  /**
   * Load persona details and apply them to Home without forcing navigation.
   * @param {string} userId
   */
  async setPersona(userId) {
    this.currentUser = await API.getUser(userId);
    console.log('[App] Selected Persona:', this.currentUser);

    const foodResponse = await API.getFoods();
    this.foods = foodResponse.foods || [];
    this.selectedCategory = 'Tất cả';

    const categoryPills = document.querySelectorAll('#category-pills .category-pill');
    categoryPills.forEach((p, idx) => {
      if (idx === 0) p.classList.add('active');
      else p.classList.remove('active');
    });

    // Update budget toggle UI elements
    this.onlyUnderBudget = true;
    const budgetToggle = document.getElementById('budget-filter-toggle');
    if (budgetToggle) budgetToggle.checked = true;

    const budgetLabel = document.getElementById('current-budget-label');
    if (budgetLabel && this.currentUser) {
      budgetLabel.textContent = `${this.currentUser.avg_order_value_limit.toLocaleString('vi-VN')}đ`;
    }

    this.renderHome();
  },

  /**
   * Build Homepage layout details
   */
  renderHome() {
    document.getElementById('floating-chat-btn').classList.add('visible');

    // AI Banner adjustments according to age context (if present)
    const bannerTitle = document.querySelector('.ai-banner-title');
    const bannerDesc = document.querySelector('.ai-banner-desc');
    const toggleContainer = document.getElementById('budget-toggle-container');

    if (!this.currentUser) {
      document.getElementById('user-avatar').textContent = '👤';
      document.getElementById('home-location-text').textContent = 'Chọn hồ sơ trong AI Tìm Món';
      if (bannerTitle) bannerTitle.textContent = 'AI Tìm Món cá nhân hóa';
      if (bannerDesc) bannerDesc.textContent = 'Bấm để AI hỏi tuổi, nhóm người dùng và khẩu vị của bạn.';
      if (toggleContainer) toggleContainer.style.display = 'none';
      this.renderFoodCatalog();
      return;
    }

    if (toggleContainer) toggleContainer.style.display = 'flex';

    // User header bindings
    document.getElementById('user-avatar').textContent = this.currentUser.avatar;
    document.getElementById('home-location-text').textContent = this.currentUser.location;

    const cohort = this.currentUser.cohort;

    if (cohort === 'pupil') {
      if (bannerTitle) bannerTitle.textContent = 'Tìm món vặt bao ngon nhen 🎒';
      if (bannerDesc) bannerDesc.textContent = 'Hỏi AI tìm bánh tráng, trà sữa ngọt thơm siêu hạt dẻ!';
    } else if (cohort === 'student') {
      if (bannerTitle) bannerTitle.textContent = 'Đói bụng cày đêm à đồng môn? 🎓';
      if (bannerDesc) bannerDesc.textContent = 'AI giúp tìm mì trộn xá xíu, cơm sườn no nê không sợ ví khóc!';
    } else { // office
      if (bannerTitle) bannerTitle.textContent = 'Gợi ý cơm trưa Healthy văn phòng 💼';
      if (bannerDesc) bannerDesc.textContent = 'Tư vấn món ít dầu mỡ, organic salad & cảnh báo dị ứng.';
    }

    // Render list cards
    this.renderFoodCatalog();
  },

  /**
   * Open the personalized AI chat box without leaving the Home screen.
   */
  openChatBox(resume = false) {
    const overlay = document.getElementById('chatbox-overlay');
    const bottomNav = document.getElementById('app-bottom-nav');

    overlay.classList.add('active');
    overlay.setAttribute('aria-hidden', 'false');
    document.body.classList.add('chatbox-open');
    bottomNav.style.display = 'none';
    this.chatBoxOpen = true;

    if (!this.currentUser) {
      this.renderPersonalizationPersonaStep();
    } else if (typeof ChatModule !== 'undefined') {
      if (!resume || !ChatModule.initialized) {
        ChatModule.init(this.currentUser);
      }
    }
  },

  /**
   * Close the personalized AI chat box overlay.
   */
  closeChatBox() {
    const overlay = document.getElementById('chatbox-overlay');
    if (!overlay) return;

    overlay.classList.remove('active');
    overlay.setAttribute('aria-hidden', 'true');
    document.body.classList.remove('chatbox-open');
    this.chatBoxOpen = false;

    const bottomNav = document.getElementById('app-bottom-nav');
    if (this.currentScreen === 'home') {
      bottomNav.style.display = 'flex';
      this.updateActiveNav('home');
    }
  },

  /**
   * First chatbot step: ask user segment/persona.
   */
  renderPersonalizationPersonaStep() {
    const messages = document.getElementById('chat-messages-container');
    const chips = document.getElementById('chat-suggestion-chips');
    const inputBar = document.querySelector('.chat-input-bar');

    messages.innerHTML = `
      <div class="chat-bubble ai">
        <div class="bubble-sender">
          <img class="ai-avatar-mini" src="/static/images/iconaichat.jpg" alt="AI">
          <span class="ai-name-mini">AI Tìm Món</span>
        </div>
        <div class="bubble-text">
          Chào bạn, mình sẽ cá nhân hóa ShopeeFood trước khi gợi ý món. Bạn thuộc nhóm nào hôm nay?
        </div>
      </div>
    `;

    // Ẩn khung nhập tin nhắn khi chưa chọn persona
    if (inputBar) inputBar.style.display = 'none';
    chips.innerHTML = '';

    [
      { id: 'student_hoc_sinh', label: 'Học sinh', desc: 'Ngân sách ≤ 30k' },
      { id: 'university_student', label: 'Sinh viên', desc: 'Ngân sách 30k-50k' },
      { id: 'office_worker', label: 'Văn phòng', desc: 'Ngân sách lên tới 150k' },
    ].forEach(option => {
      const chip = document.createElement('button');
      chip.className = 'category-pill personalization-chip';
      chip.innerHTML = `<strong>${option.label}</strong><span>${option.desc}</span>`;
      chip.addEventListener('click', () => this.handlePersonalizationPersona(option.id));
      chips.appendChild(chip);
    });
  },

  async handlePersonalizationPersona(userId) {
    this.pendingPersonaId = userId;

    const messages = document.getElementById('chat-messages-container');
    const selectedLabel = {
      student_hoc_sinh: 'Học sinh',
      university_student: 'Sinh viên',
      office_worker: 'Nhân viên văn phòng',
    }[userId] || 'Người dùng';

    messages.insertAdjacentHTML('beforeend', `
      <div class="chat-bubble user">
        <div class="bubble-text">${selectedLabel}</div>
      </div>
      <div class="chat-bubble ai">
        <div class="bubble-sender">
          <img class="ai-avatar-mini" src="/static/images/iconaichat.jpg" alt="AI">
          <span class="ai-name-mini">AI Tìm Món</span>
        </div>
        <div class="bubble-text">
          Tuyệt. Vậy hôm nay bạn muốn AI ưu tiên khẩu vị hoặc món nào?
        </div>
      </div>
    `);

    try {
      await this.setPersona(userId);
      this.renderPersonalizationTasteStep();
    } catch (error) {
      console.error('[App] Error loading persona from chat:', error);
      this.showToast('Không thể tải hồ sơ người dùng!');
      this.renderPersonalizationPersonaStep();
    }
  },

  renderPersonalizationTasteStep() {
    const chips = document.getElementById('chat-suggestion-chips');
    const input = document.getElementById('chat-message-input');
    const send = document.getElementById('chat-send-btn');
    const inputBar = document.querySelector('.chat-input-bar');

    // Hiện lại khung nhập tin nhắn sau khi đã chọn persona
    if (inputBar) inputBar.style.display = '';

    chips.innerHTML = '';
    input.value = '';
    input.disabled = false;
    input.placeholder = 'Nhập tên món hoặc khẩu vị bạn muốn...';
    send.disabled = true;

    input.oninput = () => {
      send.disabled = !input.value.trim();
    };
    input.onkeypress = (event) => {
      if (event.key === 'Enter' && !event.shiftKey && input.value.trim()) {
        event.preventDefault();
        this.startPersonalizedChat(input.value.trim());
      }
    };
    send.onclick = () => {
      const text = input.value.trim();
      if (text) this.startPersonalizedChat(text);
    };

    // Gợi ý chung cho tất cả nhóm — user tự chọn khẩu vị, AI lọc theo ngân sách nhóm
    const options = ['Ăn vặt giao nhanh', 'Trà sữa ngọt mát', 'Cơm sườn ngon', 'Mì trộn xá xíu', 'Healthy ít dầu', 'Cà phê tỉnh táo'];

    options.forEach(text => {
      const chip = document.createElement('button');
      chip.className = 'category-pill';
      chip.textContent = text;
      chip.addEventListener('click', () => this.startPersonalizedChat(text));
      chips.appendChild(chip);
    });
  },

  startPersonalizedChat(initialMessage) {
    if (typeof ChatModule === 'undefined' || !this.currentUser) return;

    ChatModule.init(this.currentUser);
    ChatModule.inputField.value = initialMessage;
    ChatModule.updateSendButtonState();
    ChatModule.handleUserSend();
  },

  /**
   * Render grid of food recommendations
   */
  renderFoodCatalog() {
    const grid = document.getElementById('home-food-grid');
    grid.innerHTML = '';

    // Filter foods by Category and User Budget limit
    let filteredFoods = this.foods.filter(food => {
      // 1. Budget check
      const underBudget = !this.onlyUnderBudget || !this.currentUser || food.price <= this.currentUser.avg_order_value_limit;

      // 2. Category check
      if (this.selectedCategory === 'Tất cả') {
        return underBudget;
      }
      return underBudget && food.category.toLowerCase() === this.selectedCategory.toLowerCase();
    });

    // Render empty state if no matches
    if (filteredFoods.length === 0) {
      const budgetText = this.currentUser
        ? `ngân sách của bạn (${this.currentUser.avg_order_value_limit.toLocaleString('vi-VN')}đ)`
        : 'bộ lọc hiện tại';
      grid.innerHTML = `
        <div class="empty-state" style="grid-column: 1 / -1;">
          <div class="empty-icon">🍽️</div>
          <div class="empty-title">Không tìm thấy món ăn</div>
          <div class="empty-desc">Không có món ăn phù hợp với ${budgetText} trong danh mục này.</div>
        </div>
      `;
      return;
    }

    // Sort food items: prefer foods whose taste tags overlap with user's preferred tastes
    const preferredTastes = this.currentUser?.taste_preferences?.preferred || [];
    filteredFoods.sort((a, b) => {
      const matchA = a.taste_tags.filter(t => preferredTastes.includes(t)).length;
      const matchB = b.taste_tags.filter(t => preferredTastes.includes(t)).length;

      // Sort desc by preference match, then by rating
      if (matchA !== matchB) return matchB - matchA;
      return b.rating - a.rating;
    });

    // Render cards
    filteredFoods.forEach(food => {
      const card = document.createElement('div');
      card.className = 'food-card';

      const formattedPrice = `${food.price.toLocaleString('vi-VN')}đ`;

      // Check if food contains allergy tags that trigger user allergies
      const userAllergies = this.currentUser?.allergies || [];
      const hasAllergyRisk = food.allergy_tags.some(tag =>
        userAllergies.some(allergy => tag.toLowerCase().includes(allergy.toLowerCase()))
      );

      // Taste tag label (use first tag)
      const primaryTag = food.taste_tags[0] || food.category;

      card.innerHTML = `
        <div class="food-card-img-wrapper">
          <img src="${food.image}" alt="${food.name}" loading="lazy">
          <span class="food-card-price-badge">${formattedPrice}</span>
          <span class="food-card-eta">${food.eta}</span>
        </div>
        <div class="food-card-body">
          <div class="food-card-name">${food.name}</div>
          <div class="food-card-shop">${food.shop}</div>
          <div class="food-card-meta">
            <span class="food-card-rating">⭐ ${food.rating}</span>
            <span class="food-card-dot"></span>
            <span class="food-card-distance">${food.distance}</span>
          </div>
          <div class="detail-tags" style="margin-top: 8px; margin-bottom: 0; gap: 4px;">
            <span class="detail-tag" style="padding: 2px 6px; font-size: 10px;">${primaryTag}</span>
            ${hasAllergyRisk ? '<span class="detail-tag allergy" style="padding: 2px 6px; font-size: 10px; background: #ffebeb; color: #ff3b30;">⚠️ Dị ứng</span>' : ''}
          </div>
        </div>
      `;

      card.addEventListener('click', () => {
        this.navigate('detail', { foodId: food.id });
      });

      grid.appendChild(card);
    });
  },

  /**
   * Render single food details screen
   */
  async renderFoodDetail(foodId) {
    try {
      const food = await API.getFood(foodId);

      // Bind details
      document.getElementById('detail-food-img').src = food.image;
      document.getElementById('detail-food-name').textContent = food.name;
      document.getElementById('detail-food-shop').textContent = `🏬 ${food.shop}`;
      document.getElementById('detail-food-price').textContent = `${food.price.toLocaleString('vi-VN')}đ`;
      document.getElementById('detail-food-rating').textContent = food.rating;
      document.getElementById('detail-food-distance').textContent = food.distance;
      document.getElementById('detail-food-eta').textContent = food.eta;
      document.getElementById('detail-food-description').textContent = food.description || 'Chưa có mô tả chi tiết cho món ăn này.';

      // Render tags list
      const tagsContainer = document.getElementById('detail-food-tags');
      tagsContainer.innerHTML = '';

      // Taste tags
      food.taste_tags.forEach(tag => {
        const badge = document.createElement('span');
        badge.className = 'detail-tag';
        badge.textContent = tag;
        tagsContainer.appendChild(badge);
      });

      // Allergy tags
      food.allergy_tags.forEach(tag => {
        const badge = document.createElement('span');
        badge.className = 'detail-tag allergy';
        badge.textContent = `Chứa ${tag}`;
        tagsContainer.appendChild(badge);
      });

      // Show/Hide Allergy Warning Alert Box
      const allergyBox = document.getElementById('detail-allergy-box');
      const allergyText = document.getElementById('detail-allergy-text');

      const userAllergies = (this.currentUser && this.currentUser.allergies) || [];
      const triggeredAllergens = food.allergy_tags.filter(tag =>
        userAllergies.some(allergy => tag.toLowerCase().includes(allergy.toLowerCase()))
      );

      if (triggeredAllergens.length > 0) {
        allergyBox.style.display = 'flex';
        allergyText.innerHTML = `<strong>⚠️ Cảnh báo Dị ứng:</strong> Món này chứa <strong>${triggeredAllergens.join(', ')}</strong>, trùng với khai báo dị ứng của bạn (${userAllergies.join(', ')}). Vui lòng xác nhận kỹ với nhà hàng!`;
      } else {
        allergyBox.style.display = 'none';
      }

    } catch (e) {
      console.error('[App] Error rendering food details:', e);
      this.showToast('Không tải được chi tiết món ăn!');
      this.navigate('home');
    }
  },

  /**
   * Helper to display snackbar/toast popup
   * @param {string} message 
   */
  showToast(message) {
    const toast = document.getElementById('app-toast');
    toast.textContent = message;
    toast.classList.add('show');

    setTimeout(() => {
      toast.classList.remove('show');
    }, 2500);
  }
};

// Start application when DOM loaded
window.addEventListener('DOMContentLoaded', () => {
  App.init();
});
