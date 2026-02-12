// API wrapper with auth header
const API_BASE = (import.meta.env.VITE_API_URL || '/api').replace(/\/$/, '');

export function getToken() {
    return localStorage.getItem('token');
}

export function setToken(token) {
    localStorage.setItem('token', token);
}

export function clearToken() {
    localStorage.removeItem('token');
}

export function getUser() {
    const userStr = localStorage.getItem('user');
    try {
        return userStr ? JSON.parse(userStr) : null;
    } catch {
        return null;
    }
}

export function setUser(user) {
    localStorage.setItem('user', JSON.stringify(user));
}

export function clearUser() {
    localStorage.removeItem('user');
}

export async function api(endpoint, options = {}) {
    const token = getToken();
    const headers = {
        'Content-Type': 'application/json',
        ...(options.headers || {})
    };

    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    let response;
    try {
        response = await fetch(`${API_BASE}${endpoint}`, {
            ...options,
            headers
        });
    } catch (networkErr) {
        // fetch() itself failed: network error, CORS block, server down, timeout
        throw {
            _network: true,
            status: 0,
            error: 'network_error',
            message: 'Сервер недоступен (сетевая ошибка)'
        };
    }

    // Safe JSON parsing: check content-type first
    const contentType = response.headers.get('content-type') || '';
    let data = null;

    if (contentType.includes('application/json')) {
        try {
            data = await response.json();
        } catch (e) {
            data = { error: 'Invalid JSON response' };
        }
    } else {
        // Non-JSON response (e.g., 404 HTML page)
        const text = await response.text();
        data = { error: text.slice(0, 200) || `HTTP ${response.status}` };
    }

    if (!response.ok) {
        // Auto-logout on 401 (expired/invalid token) — but NOT on /auth/login
        if (response.status === 401 && !endpoint.includes('/auth/login')) {
            clearToken();
            clearUser();
            if (!window.location.hash.includes('login')) {
                window.location.hash = '#/login';
            }
        }
        throw {
            _network: false,
            status: response.status,
            message: data.error || data.message || `HTTP ${response.status}`,
            ...data
        };
    }

    return data;
}

// Cart state (in memory + localStorage backup)
let cart = JSON.parse(localStorage.getItem('cart') || '[]');

export function getCart() {
    return cart;
}

export function addToCart(item) {
    const existing = cart.find(c => c.id === item.id);
    if (existing) {
        existing.qty += 1;
    } else {
        cart.push({ ...item, qty: 1 });
    }
    localStorage.setItem('cart', JSON.stringify(cart));
}

export function removeFromCart(itemId) {
    cart = cart.filter(c => c.id !== itemId);
    localStorage.setItem('cart', JSON.stringify(cart));
}

export function clearCart() {
    cart = [];
    localStorage.setItem('cart', JSON.stringify(cart));
}

export function updateCartQty(itemId, qty) {
    const item = cart.find(c => c.id === itemId);
    if (item) {
        item.qty = qty;
        if (qty <= 0) {
            removeFromCart(itemId);
        } else {
            localStorage.setItem('cart', JSON.stringify(cart));
        }
    }
}

// ==================== Admin API ====================

export async function adminGetUsers() {
    return api('/admin/users');
}

export async function adminCreateUser(payload) {
    return api('/admin/users', {
        method: 'POST',
        body: JSON.stringify(payload)
    });
}

export async function adminUpdateUser(userId, payload) {
    return api(`/admin/users/${userId}`, {
        method: 'PUT',
        body: JSON.stringify(payload)
    });
}

export async function adminDeleteUser(userId) {
    return api(`/admin/users/${userId}`, {
        method: 'DELETE'
    });
}

// ==================== Daily Menu API ====================

export async function getCatalog(locationId) {
    return api(`/catalog?location_id=${locationId}`);
}

export async function getDailyMenu(locationId, date, mealSlot = 'lunch') {
    return api(`/cook/daily-menu?location_id=${locationId}&date=${date}&meal_slot=${mealSlot}`);
}

export async function saveDailyMenu(payload) {
    return api('/cook/daily-menu', {
        method: 'PUT',
        body: JSON.stringify(payload)
    });
}

// ==================== Orders API ====================

export async function getMyOrders() {
    return api('/orders/my');
}
