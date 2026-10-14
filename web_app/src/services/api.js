/**
 * API Service
 * Centralized API calls with auth token handling
 */

// Use relative URL in production (Docker/nginx proxies to backend)
// Use localhost:8000 in development
const API_BASE = import.meta.env.PROD ? '/api/v1' : 'http://localhost:8000/api/v1';

// Get token from localStorage
const getToken = () => localStorage.getItem('auth_token');

// Set token to localStorage
export const setToken = (token) => {
    if (token) {
        localStorage.setItem('auth_token', token);
    } else {
        localStorage.removeItem('auth_token');
    }
};

// Get stored user info
export const getStoredUser = () => {
    const user = localStorage.getItem('user');
    return user ? JSON.parse(user) : null;
};

// Set stored user info
export const setStoredUser = (user) => {
    if (user) {
        localStorage.setItem('user', JSON.stringify(user));
    } else {
        localStorage.removeItem('user');
    }
};

// Fetch wrapper with auth header
const authFetch = async (url, options = {}) => {
    const token = getToken();
    const headers = {
        'Content-Type': 'application/json',
        ...options.headers,
    };

    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(url, {
        ...options,
        headers,
    });

    // Handle 401 - token expired
    if (response.status === 401) {
        setToken(null);
        setStoredUser(null);
        window.location.href = '/login';
        throw new Error('Session expired. Please login again.');
    }

    return response;
};

// Auth API
export const authAPI = {
    async signup(email, password) {
        const response = await fetch(`${API_BASE}/auth/signup`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password }),
        });

        if (!response.ok) {
            const error = await response.json();
            let message = 'Signup failed';
            if (typeof error.detail === 'string') {
                message = error.detail;
            } else if (Array.isArray(error.detail) && error.detail.length > 0) {
                message = error.detail[0].msg || error.detail[0].message || JSON.stringify(error.detail[0]);
            } else if (error.message) {
                message = error.message;
            }
            throw new Error(message);
        }

        const data = await response.json();
        setToken(data.access_token);
        setStoredUser(data.user);
        return data;
    },

    async login(email, password) {
        const response = await fetch(`${API_BASE}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password }),
        });

        if (!response.ok) {
            const error = await response.json();
            // Handle various error formats
            let message = 'Login failed';
            if (typeof error.detail === 'string') {
                message = error.detail;
            } else if (Array.isArray(error.detail) && error.detail.length > 0) {
                message = error.detail[0].msg || error.detail[0].message || JSON.stringify(error.detail[0]);
            } else if (error.message) {
                message = error.message;
            }
            throw new Error(message);
        }

        const data = await response.json();
        setToken(data.access_token);
        setStoredUser(data.user);
        return data;
    },

    async getMe() {
        const response = await authFetch(`${API_BASE}/auth/me`);

        if (!response.ok) {
            throw new Error('Failed to get user info');
        }

        return response.json();
    },

    logout() {
        setToken(null);
        setStoredUser(null);
    }
};

// Video Generation API
export const videoAPI = {
    async generate(params) {
        const response = await authFetch(`${API_BASE}/generate`, {
            method: 'POST',
            body: JSON.stringify(params),
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Generation failed');
        }

        return response.json();
    },

    async magicGenerate(topic) {
        const response = await authFetch(`${API_BASE}/magic`, {
            method: 'POST',
            body: JSON.stringify({ topic }),
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Magic generation failed');
        }

        return response.json();
    },

    async getTrends(niche = 'technology') {
        const response = await fetch(`${API_BASE}/trends/now?niche=${niche}`);
        if (!response.ok) {
            throw new Error('Failed to fetch trends');
        }
        return response.json();
    },

    async getJobStatus(jobId) {
        const response = await authFetch(`${API_BASE}/generate/${jobId}`);

        if (!response.ok) {
            throw new Error('Failed to get job status');
        }

        return response.json();
    },

    async getMyVideos() {
        const response = await authFetch(`${API_BASE}/my-videos`);

        if (!response.ok) {
            throw new Error('Failed to get videos');
        }

        return response.json();
    },

    async getStyles() {
        const response = await fetch(`${API_BASE}/styles`);
        return response.json();
    },

    async getVoices() {
        const response = await fetch(`${API_BASE}/voices`);
        return response.json();
    }
};

// Admin API
export const adminAPI = {
    async getAnalytics() {
        const response = await authFetch(`${API_BASE}/admin/analytics`);

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to get analytics');
        }

        return response.json();
    },

    async getUsers(skip = 0, limit = 50) {
        const response = await authFetch(`${API_BASE}/admin/users?skip=${skip}&limit=${limit}`);

        if (!response.ok) {
            throw new Error('Failed to get users');
        }

        return response.json();
    },

    async getVideos(skip = 0, limit = 50, userId = null) {
        let url = `${API_BASE}/admin/videos?skip=${skip}&limit=${limit}`;
        if (userId) url += `&user_id=${userId}`;

        const response = await authFetch(url);

        if (!response.ok) {
            throw new Error('Failed to get videos');
        }

        return response.json();
    },

    async getUserDetails(userId) {
        const response = await authFetch(`${API_BASE}/admin/user/${userId}`);

        if (!response.ok) {
            throw new Error('Failed to get user details');
        }

        return response.json();
    }
};
