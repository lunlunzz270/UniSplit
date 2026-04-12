const API_BASE_URL = 'http://127.0.0.1:5000';

function normalizeUser(user) {
    if (!user || typeof user !== 'object') {
        return null;
    }

    return {
        id: user.id ?? null,
        name: user.name || user.full_name || '',
        full_name: user.full_name || user.name || '',
        email: user.email || '',
    };
}

function getCurrentUser() {
    try {
        return normalizeUser(JSON.parse(localStorage.getItem('user') || 'null'));
    } catch (error) {
        return null;
    }
}

function setCurrentUser(user) {
    const normalized = normalizeUser(user);
    if (!normalized) {
        return null;
    }

    localStorage.setItem('user', JSON.stringify(normalized));
    return normalized;
}

function clearCurrentUser() {
    localStorage.removeItem('user');
}

function apiUrl(path) {
    if (!path) {
        return API_BASE_URL;
    }

    return `${API_BASE_URL}${path.startsWith('/') ? path : `/${path}`}`;
}

function normalizeExpenseList(payload) {
    if (Array.isArray(payload)) {
        return payload;
    }

    if (payload && Array.isArray(payload.expenses)) {
        return payload.expenses;
    }

    return [];
}

window.UniSplitApp = {
    API_BASE_URL,
    normalizeUser,
    getCurrentUser,
    setCurrentUser,
    clearCurrentUser,
    apiUrl,
    normalizeExpenseList,
};
