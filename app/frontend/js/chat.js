/* ============================================================
   ShopeeFood AI — Chat Module (Gemini Interface)
   ============================================================ */

const ChatModule = {
  conversationHistory: [],
  currentUser: null,
  isTyping: false,
  messagesContainer: null,
  inputField: null,
  sendButton: null,
  chipsContainer: null,

  /**
   * Initialize Chat Module
   * @param {object} user - Current user object from backend
   */
  init(user) {
    this.currentUser = user;
    this.conversationHistory = [];
    this.isTyping = false;
    this.initialized = true;
    
    // Get DOM elements
    this.messagesContainer = document.getElementById('chat-messages-container');
    this.inputField = document.getElementById('chat-message-input');
    this.sendButton = document.getElementById('chat-send-btn');
    this.chipsContainer = document.getElementById('chat-suggestion-chips');

    // Reset UI
    this.messagesContainer.innerHTML = '';
    this.inputField.value = '';
    this.inputField.disabled = false;
    this.updateSendButtonState();

    // Bind event listeners
    this.setupListeners();

    // Start conversation with persona greeting
    this.startConversation();
  },

  /**
   * Event listeners setup
   */
  setupListeners() {
    // Clear temporary handlers used by the pre-chat personalization flow.
    this.inputField.oninput = null;
    this.inputField.onkeypress = null;
    this.sendButton.onclick = null;

    // Input keyup event (enable/disable send button)
    this.inputField.removeEventListener('input', this._handleInput);
    this._handleInput = () => this.updateSendButtonState();
    this.inputField.addEventListener('input', this._handleInput);

    // Press Enter to send
    this.inputField.removeEventListener('keypress', this._handleKeypress);
    this._handleKeypress = (e) => {
      if (e.key === 'Enter' && !e.shiftKey && this.inputField.value.trim() && !this.isTyping) {
        e.preventDefault();
        this.handleUserSend();
      }
    };
    this.inputField.addEventListener('keypress', this._handleKeypress);

    // Send button click
    this.sendButton.removeEventListener('click', this._handleSendClick);
    this._handleSendClick = () => this.handleUserSend();
    this.sendButton.addEventListener('click', this._handleSendClick);
  },

  /**
   * Enable/Disable send button based on input value
   */
  updateSendButtonState() {
    const hasText = this.inputField.value.trim().length > 0;
    this.sendButton.disabled = !hasText || this.isTyping;
  },

  /**
   * Renders the welcome greeting and initial suggestion chips based on user cohort
   */
  async startConversation() {
    if (!this.currentUser) return;
    
    const cohort = this.currentUser.cohort;
    let welcomeMessage = '';
    let chips = [];

    if (cohort === 'pupil') {
      welcomeMessage = `Hế lô cậu nhen! 🎒 Mình là Trợ lý AI Tìm Món của cậu nè. Hôm nay thèm món vặt ngọt mát hay trà sữa hạt dẻ thì bảo mình gợi ý nhen, bao ngon lun! 😋`;
      chips = ['Trà sữa ngọt 25k', 'Bánh tráng cuộn bơ', 'Ăn vặt rẻ nhen', 'Món gì ngọt ngọt á'];
    } else if (cohort === 'student') {
      welcomeMessage = `Chào đồng môn! 🎓 Có mặt Trợ lý AI cứu đói đây! Hỏi mình món gì no lâu, mì trộn, trà chanh giá cực sinh viên không lo ví khóc nha! 🔥`;
      chips = ['Mì trộn xá xíu', 'Cơm sườn ngon rẻ', 'Trà chanh tắc cứu đói', 'Món no lâu dưới 45k'];
    } else { // office
      welcomeMessage = `Kính chào anh/chị. 💼 Em là Trợ lý AI của ShopeeFood. Hôm nay em có thể hỗ trợ anh/chị tìm kiếm các phần cơm trưa văn phòng ngon miệng, cà phê nạp năng lượng hay các món healthy salad organic ít dầu mỡ ạ. Vui lòng cho em biết yêu cầu của anh/chị nhé.`;
      chips = ['Salad healthy ít béo', 'Cơm tấm sườn mật ong', 'Phở bò nóng hổi', 'Cà phê sữa tỉnh táo'];
    }

    // Render welcome message bubble
    this.addMessage(welcomeMessage, 'ai');
    
    // Save to history
    this.conversationHistory.push({
      role: 'assistant',
      content: welcomeMessage
    });

    // Render Suggestion Chips
    this.renderSuggestionChips(chips);
  },

  /**
   * Render quick reply chips
   * @param {Array<string>} chips 
   */
  renderSuggestionChips(chips) {
    this.chipsContainer.innerHTML = '';
    
    chips.forEach(chipText => {
      const chip = document.createElement('button');
      chip.className = 'category-pill';
      chip.textContent = chipText;
      chip.style.marginRight = '8px';
      chip.style.flexShrink = '0';
      
      chip.addEventListener('click', () => {
        if (this.isTyping) return;
        this.inputField.value = chipText;
        this.handleUserSend();
      });
      
      this.chipsContainer.appendChild(chip);
    });
  },

  /**
   * Handles user click send button or press enter
   */
  async handleUserSend() {
    const text = this.inputField.value.trim();
    if (!text || this.isTyping) return;

    this.inputField.value = '';
    this.updateSendButtonState();

    // 1. Add User Message to UI and history
    this.addMessage(text, 'user');
    this.conversationHistory.push({
      role: 'user',
      content: text
    });

    // 2. Show Typing Indicator
    this.showTyping();
    this.scrollToBottom();

    try {
      // 3. Request AI response from Backend API
      const result = await API.chat(
        this.currentUser.id,
        text,
        this.conversationHistory
      );

      // 4. Hide Typing Indicator
      this.hideTyping();

      // 5. Render AI Response and Foods
      this.addMessage(result.response, 'ai', result.suggested_foods);
      
      // Save AI reply to history
      this.conversationHistory.push({
        role: 'assistant',
        content: result.response
      });

    } catch (error) {
      console.error('[Chat] Error sending message:', error);
      this.hideTyping();
      
      let errorMsg = 'Xin lỗi cậu nhen, kết nối của mình đang chập chờn. Cậu thử lại tí nhé!';
      if (this.currentUser.cohort === 'office') {
        errorMsg = 'Rất tiếc, đã xảy ra sự cố kết nối tới máy chủ AI. Xin anh/chị vui lòng thử lại sau giây lát.';
      }
      
      this.addMessage(errorMsg, 'ai');
    }

    this.scrollToBottom();
  },

  /**
   * Helper to format markdown tags in the AI response (bold, bullet points)
   * @param {string} text
   * @returns {string} HTML formatted string
   */
  formatResponse(text) {
    if (!text) return '';
    
    let html = text;

    // Escaped HTML tags to prevent XSS
    html = html
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');

    // Handle food details pattern matching: replace food IDs in brackets [food_001] with nothing or styles
    html = html.replace(/\[(food_\d{3})\]/g, '');

    // Bold tags (**text** -> <strong>text</strong>)
    html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

    // Bullet list items (* or - at start of line)
    const lines = html.split('\n');
    let inList = false;
    
    for (let i = 0; i < lines.length; i++) {
      let line = lines[i].trim();
      
      // Match bullet list
      if (line.startsWith('- ') || line.startsWith('* ')) {
        const itemContent = line.substring(2);
        if (!inList) {
          lines[i] = '<ul><li>' + itemContent + '</li>';
          inList = true;
        } else {
          lines[i] = '<li>' + itemContent + '</li>';
        }
      } else {
        if (inList) {
          lines[i] = '</ul>' + lines[i];
          inList = false;
        }
      }
    }
    
    if (inList) {
      lines.push('</ul>');
    }

    html = lines.join('\n');

    // Newline to <br> (except when closing list tags)
    html = html.replace(/\n/g, '<br>');
    html = html.replace(/<\/ul><br>/g, '</ul>');
    html = html.replace(/<\/li><br>/g, '</li>');

    return html;
  },

  /**
   * Append message bubble to chat viewport
   * @param {string} content 
   * @param {string} sender - 'user' or 'ai'
   * @param {Array} suggestedFoods - Food objects returned from AI
   */
  addMessage(content, sender, suggestedFoods = []) {
    const bubble = document.createElement('div');
    bubble.className = `chat-bubble ${sender}`;

    // Get time string
    const now = new Date();
    const timeStr = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`;

    if (sender === 'ai') {
      const formattedHtml = this.formatResponse(content);
      bubble.innerHTML = `
        <div class="bubble-sender">
          <img class="ai-avatar-mini" src="/static/images/iconaichat.jpg" alt="AI">
          <span class="ai-name-mini">AI Copilot</span>
        </div>
        <div class="bubble-text">${formattedHtml}</div>
        <div class="chat-time">${timeStr}</div>
      `;

      // If there are food recommendations, render cards inside the message bubble area
      if (suggestedFoods && suggestedFoods.length > 0) {
        const cardsContainer = document.createElement('div');
        cardsContainer.className = 'chat-food-cards';
        
        suggestedFoods.forEach(food => {
          const cardHtml = this.renderFoodCard(food);
          cardsContainer.appendChild(cardHtml);
        });
        
        bubble.appendChild(cardsContainer);
      }
    } else {
      bubble.innerHTML = `
        <div class="bubble-text">${content}</div>
        <div class="chat-time">${timeStr}</div>
      `;
    }

    this.messagesContainer.appendChild(bubble);
    this.scrollToBottom();
  },

  /**
   * Generates a mini food card element
   * @param {object} food 
   */
  renderFoodCard(food) {
    const card = document.createElement('div');
    card.className = 'chat-food-card';
    
    const formattedPrice = `${food.price.toLocaleString('vi-VN')}đ`;
    
    card.innerHTML = `
      <img src="${food.image}" alt="${food.image_alt || food.name}" class="chat-food-card-img">
      <div class="chat-food-card-info">
        <div class="chat-food-card-name">${food.name}</div>
        <div class="chat-food-card-shop">${food.shop}</div>
        <div class="chat-food-card-bottom">
          <span class="chat-food-card-price">${formattedPrice}</span>
          <span class="chat-food-card-rating">⭐ ${food.rating}</span>
        </div>
      </div>
      <button class="chat-food-card-btn">Ghé Quán</button>
    `;

    // Click handler to open Food Details — đóng chatbox trước rồi chuyển trang
    const btnGheQuan = card.querySelector('.chat-food-card-btn');
    const openDetail = (e) => {
      e.stopPropagation();
      if (typeof App !== 'undefined') {
        App.closeChatBox();
        App.navigate('detail', { foodId: food.id, fromChat: true });
      }
    };

    // Bấm nút "Ghé Quán" hoặc bấm cả card đều mở detail
    if (btnGheQuan) {
      btnGheQuan.addEventListener('click', openDetail);
    }
    card.addEventListener('click', openDetail);

    return card;
  },

  /**
   * Appends typing indicator dots
   */
  showTyping() {
    if (this.isTyping) return;
    this.isTyping = true;
    this.updateSendButtonState();

    const indicator = document.createElement('div');
    indicator.className = 'typing-indicator';
    indicator.id = 'chat-typing-indicator';
    indicator.innerHTML = `
      <img class="ai-avatar-mini" src="/static/images/iconaichat.jpg" alt="AI">
      <div class="typing-dots">
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
      </div>
    `;

    this.messagesContainer.appendChild(indicator);
    this.scrollToBottom();
  },

  /**
   * Removes typing indicator dots
   */
  hideTyping() {
    if (!this.isTyping) return;
    this.isTyping = false;
    this.updateSendButtonState();

    const indicator = document.getElementById('chat-typing-indicator');
    if (indicator) {
      indicator.remove();
    }
  },

  /**
   * Smoothly scroll message container to bottom
   */
  scrollToBottom() {
    if (!this.messagesContainer) return;
    this.messagesContainer.scrollTo({
      top: this.messagesContainer.scrollHeight,
      behavior: 'smooth'
    });
  }
};
