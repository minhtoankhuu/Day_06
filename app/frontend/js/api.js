/* ============================================================
   ShopeeFood AI — API Client Module
   ============================================================ */

const API = {
  /** Base configuration */
  BASE_URL: '',  // Same origin — FastAPI serves frontend
  DEFAULT_TIMEOUT: 10000,   // 10s for normal requests
  CHAT_TIMEOUT: 30000,      // 30s for AI chat (Gemini can be slow)
  MAX_RETRIES: 2,
  RETRY_DELAY: 1000,

  /**
   * Core fetch wrapper with timeout, error handling, and retries
   * @param {string} endpoint - API endpoint path
   * @param {object} options - fetch options
   * @param {number} timeout - request timeout in ms
   * @param {number} retries - remaining retry attempts
   * @returns {Promise<any>} parsed JSON response
   */
  async _request(endpoint, options = {}, timeout = this.DEFAULT_TIMEOUT, retries = this.MAX_RETRIES) {
    const url = `${this.BASE_URL}${endpoint}`;
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);

    const defaultHeaders = {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    };

    const config = {
      ...options,
      headers: {
        ...defaultHeaders,
        ...options.headers,
      },
      signal: controller.signal,
    };

    try {
      const response = await fetch(url, config);
      clearTimeout(timeoutId);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        const error = new Error(errorData.detail || `API Error: ${response.status} ${response.statusText}`);
        error.status = response.status;
        error.data = errorData;
        throw error;
      }

      return await response.json();
    } catch (error) {
      clearTimeout(timeoutId);

      // Abort / timeout error
      if (error.name === 'AbortError') {
        const timeoutError = new Error('Yêu cầu đã hết thời gian chờ. Vui lòng thử lại.');
        timeoutError.isTimeout = true;
        
        // Retry on timeout
        if (retries > 0) {
          console.warn(`[API] Timeout, retrying... (${retries} attempts left)`);
          await this._delay(this.RETRY_DELAY);
          return this._request(endpoint, options, timeout, retries - 1);
        }
        throw timeoutError;
      }

      // Network error — retry
      if (!error.status && retries > 0) {
        console.warn(`[API] Network error, retrying... (${retries} attempts left)`);
        await this._delay(this.RETRY_DELAY);
        return this._request(endpoint, options, timeout, retries - 1);
      }

      // Re-throw the error
      throw error;
    }
  },

  /**
   * Promise-based delay utility
   * @param {number} ms
   */
  _delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  },

  /* ---- User Endpoints ---- */

  /**
   * GET /api/users — Fetch all user personas
   */
  async getUsers() {
    return this._request('/api/users');
  },

  /**
   * GET /api/users/{userId} — Fetch a single user by ID
   * @param {string} userId
   */
  async getUser(userId) {
    return this._request(`/api/users/${encodeURIComponent(userId)}`);
  },

  /* ---- Food Endpoints ---- */

  /**
   * GET /api/foods — Fetch food list with optional filters
   * @param {object} filters - { budget_tier, taste_tag, category }
   */
  async getFoods(filters = {}) {
    const params = new URLSearchParams();
    
    if (filters.budget_tier) params.append('budget_tier', filters.budget_tier);
    if (filters.taste_tag) params.append('taste_tag', filters.taste_tag);
    if (filters.category) params.append('category', filters.category);

    const queryStr = params.toString();
    const endpoint = `/api/foods${queryStr ? '?' + queryStr : ''}`;
    return this._request(endpoint);
  },

  /**
   * GET /api/foods/{foodId} — Fetch a single food item
   * @param {string} foodId
   */
  async getFood(foodId) {
    return this._request(`/api/foods/${encodeURIComponent(foodId)}`);
  },

  /* ---- AI Chat Endpoint ---- */

  /**
   * POST /api/chat — Send a message to AI and receive response
   * Uses longer timeout since Gemini can take time to respond.
   * 
   * @param {string} userId - Current user persona ID
   * @param {string} message - User's message text
   * @param {Array} conversationHistory - Previous messages for context
   * @returns {Promise<{reply: string, suggested_foods: Array}>}
   */
  async chat(userId, message, conversationHistory = []) {
    return this._request(
      '/api/chat',
      {
        method: 'POST',
        body: JSON.stringify({
          user_id: userId,
          message: message,
          conversation_history: conversationHistory,
        }),
      },
      this.CHAT_TIMEOUT,
      1  // Only 1 retry for chat (since messages might duplicate)
    );
  },

  /* ---- Health Check ---- */

  /**
   * GET /api/health — Check if backend is running
   */
  async healthCheck() {
    return this._request('/api/health', {}, 5000, 0);
  },
};
