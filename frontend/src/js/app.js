const API_BASE_URL = 'http://127.0.0.1:5000';
const DEFAULT_LOGIN_REDIRECT = 'login.html';
const DEFAULT_DASHBOARD_REDIRECT = 'dashboard.html';

function normalizeUser(user) {
    if (!user || typeof user !== 'object') {
        return null;
    }

    const session = user.session && typeof user.session === 'object' ? user.session : null;
    const isAdmin = Boolean(user.is_admin);
    const roleValue = String(user.role || '').toLowerCase();
    const role = roleValue.startsWith('admin') || isAdmin ? 'admin' : 'user';
    return {
        id: user.id ?? null,
        name: user.name || user.full_name || '',
        full_name: user.full_name || user.name || '',
        email: user.email || '',
        is_admin: isAdmin,
        role,
        session_token: user.session_token || user.token || session?.token || '',
        session_expires_at: user.session_expires_at || user.expires_at || session?.expires_at || '',
        balance: Number(user.balance || 0),
        is_active: user.is_active !== false,
        is_vip: Boolean(user.is_vip),
        vip_expiry: user.vip_expiry || null,
    };
}

function getCurrentUser() {
    try {
        return normalizeUser(JSON.parse(localStorage.getItem('user') || 'null'));
    } catch (error) {
        return null;
    }
}

function getCurrentSessionToken() {
    const currentUser = getCurrentUser();
    return currentUser?.session_token || '';
}

function setCurrentUser(user, sessionToken = '') {
    const normalized = normalizeUser(user);
    if (!normalized) {
        return null;
    }

    if (sessionToken) {
        normalized.session_token = sessionToken;
    }

    localStorage.setItem('user', JSON.stringify(normalized));
    return normalized;
}

function clearCurrentUser() {
    localStorage.removeItem('user');
}

function getUserDisplayName(user) {
    const normalized = normalizeUser(user);
    if (!normalized) {
        return 'Guest';
    }

    return normalized.full_name || normalized.name || normalized.email || 'Guest';
}

function getUserRoleLabel(user) {
    const normalized = normalizeUser(user);
    if (!normalized) {
        return 'Guest';
    }

    return normalized.role === 'admin' ? 'Administrator' : 'User';
}

function createAuthActionButton(label, href, className = 'btn-secondary') {
    const link = document.createElement('a');
    link.href = href;
    link.className = className;
    link.textContent = label;
    return link;
}

function createLogoutButton(label = 'Logout') {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'btn-secondary';
    button.textContent = label;
    button.setAttribute('onclick', 'window.UniSplitApp.clearAuthAndRedirect(); return false;');
    return button;
}

function getCurrentPageName() {
    const path = window.location.pathname || '';
    const pageName = path.split('/').pop();
    return pageName || 'index.html';
}

function normalizeHrefForComparison(href) {
    if (!href || href === '#') {
        return '';
    }

    try {
        const resolved = new URL(href, window.location.href);
        return resolved.pathname.split('/').pop();
    } catch (error) {
        return href.split('/').pop();
    }
}

function isActiveHref(href, currentPage = getCurrentPageName()) {
    return normalizeHrefForComparison(href) === currentPage;
}

function createNavbarLink(template, {
    href,
    label,
    active = false,
    onClick = null,
} = {}) {
    const link = template ? template.cloneNode(false) : document.createElement('a');
    link.href = href;
    link.textContent = label;
    link.className = template ? template.className : '';
    link.dataset.authAction = template?.dataset?.authAction || '';

    if (active) {
        link.classList.add('active');
    } else {
        link.classList.remove('active');
    }

    if (onClick) {
        link.addEventListener('click', onClick);
    }

    return link;
}

function syncNavbarAuthState() {
    const currentUser = getCurrentUser();
    const currentPage = getCurrentPageName();
    const signedIn = Boolean(currentUser);

    const navLinksNodes = document.querySelectorAll('.navbar .nav-links');
    if (navLinksNodes.length > 0) {
        navLinksNodes.forEach((navLinks) => {
            navLinks.innerHTML = '';
            navLinks.style.display = 'flex';
            navLinks.style.alignItems = 'center';
            navLinks.style.flex = '1 1 auto';
            navLinks.style.minWidth = '0';
            navLinks.style.width = 'auto';
            navLinks.style.gap = '22px';

            const leftGroup = document.createElement('div');
            leftGroup.className = 'nav-group nav-left';
            const rightGroup = document.createElement('div');
            rightGroup.className = 'nav-group nav-right';

            if (signedIn) {
                const isAdminPage = currentPage === 'admin.html';
                let visibleOrder = [
                    'dashboard.html',
                    'add_expense.html',
                    'history.html',
                    'insights.html',
                    'report.html',
                    'billing.html',
                    'reminders.html',
                ];

                const labels = {
                    'admin.html': 'Admin Console', // New professional name
                    'dashboard.html': 'Dashboard',
                    'add_expense.html': 'Add Expense',
                    'history.html': 'Transaction History',
                    'insights.html': 'Expense Insights',
                    'report.html': 'Reports',
                    'billing.html': 'Billing',
                    'reminders.html': 'Reminders',
                };

                if (currentUser?.is_admin) {
                    // Admins see the Console as their home
                    visibleOrder = [
                        'admin.html',
                        'history.html',
                        'report.html',
                        'billing.html',
                    ];
                } else if (isAdminPage) {
                    visibleOrder = ['dashboard.html'];
                }

                visibleOrder.forEach((href) => {
                    leftGroup.appendChild(createNavbarLink(null, {
                        href,
                        label: labels[href],
                        active: isActiveHref(href, currentPage),
                    }));
                });

                // Restore Currency for everyone including admins
                rightGroup.appendChild(createNavbarLink(null, {
                    href: '#',
                    label: 'Currency',
                    active: false,
                    onClick: (e) => { e.preventDefault(); showCurrencyModal(); }
                }));

                rightGroup.appendChild(createNavbarLink(null, {
                    href: '#',
                    label: 'Logout',
                    active: false,
                    onClick: async (event) => {
                        event.preventDefault();
                        await logoutCurrentUser();
                    },
                }));
            } else {
                leftGroup.appendChild(createNavbarLink(null, {
                    href: 'index.html',
                    label: 'Home',
                    active: isActiveHref('index.html', currentPage),
                }));

                rightGroup.appendChild(createNavbarLink(null, {
                    href: 'register.html',
                    label: 'Register',
                    active: isActiveHref('register.html', currentPage),
                }));

                rightGroup.appendChild(createNavbarLink(null, {
                    href: 'login.html',
                    label: 'Login',
                    active: isActiveHref('login.html', currentPage),
                }));
            }

            navLinks.appendChild(leftGroup);
            navLinks.appendChild(rightGroup);
        });
    }

    const simpleHome = document.querySelector('.simple-home');
    if (simpleHome) {
        const heroLoginLink = simpleHome.querySelector('.button-group a[href="login.html"]');
        if (heroLoginLink) {
            if (signedIn) {
                const logoutHeroLink = heroLoginLink.cloneNode(false);
                logoutHeroLink.textContent = 'Logout';
                logoutHeroLink.href = '#';
                logoutHeroLink.classList.remove('secondary');
                logoutHeroLink.classList.add('secondary');
                logoutHeroLink.dataset.authAction = 'logout';
                logoutHeroLink.addEventListener('click', async (event) => {
                    event.preventDefault();
                    await logoutCurrentUser();
                });
                heroLoginLink.replaceWith(logoutHeroLink);
            } else if (heroLoginLink.dataset.authAction === 'logout') {
                const loginHeroLink = heroLoginLink.cloneNode(false);
                loginHeroLink.textContent = 'Login';
                loginHeroLink.href = 'login.html';
                loginHeroLink.classList.add('secondary');
                loginHeroLink.dataset.authAction = '';
                loginHeroLink.addEventListener('click', () => {});
                heroLoginLink.replaceWith(loginHeroLink);
            }
        }
    }

    return currentUser;
}

async function logoutCurrentUser(redirectTo = DEFAULT_LOGIN_REDIRECT) {
    const sessionToken = getCurrentSessionToken();
    if (sessionToken) {
        try {
            await fetch(apiUrl('/api/logout'), {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    Authorization: `Bearer ${sessionToken}`,
                    'X-Session-Token': sessionToken,
                },
                body: JSON.stringify({ session_token: sessionToken }),
            });
        } catch (error) {
            // Ignore network issues and clear local state anyway.
        }
    }

    clearCurrentUser();
    window.location.href = redirectTo;
}

function ensureAuthBanner(options = {}) {
    const {
        title = 'Account status',
        requireLogin = false,
        redirectTo = DEFAULT_LOGIN_REDIRECT,
        loginHref = DEFAULT_LOGIN_REDIRECT,
        dashboardHref = DEFAULT_DASHBOARD_REDIRECT,
        mountSelector = 'main',
        inline = false,
    } = options;

    const currentUser = getCurrentUser();
    const mount = document.querySelector(mountSelector);

    if (!mount) {
        return currentUser;
    }

    let banner = document.getElementById('authStatusBanner');
    if (!banner) {
        banner = document.createElement('section');
        banner.id = 'authStatusBanner';
        banner.className = 'panel';
        banner.style.marginBottom = '18px';
        banner.style.padding = '18px 20px';
        if (inline) {
            mount.prepend(banner);
        } else {
            mount.parentElement?.insertBefore(banner, mount);
        }
    }

    const signedIn = Boolean(currentUser);
    const statusClass = signedIn ? 'positive' : 'warning';
    const statusText = signedIn ? 'Signed in' : 'Sign in required';
    
    let introText = '';
    if (signedIn) {
        const roleLabel = getUserRoleLabel(currentUser);
        const roleClass = currentUser.is_admin ? 'role-admin' : 'role-user';
        introText = `You are signed in as ${getUserDisplayName(currentUser)} <span class="role-badge ${roleClass}">${roleLabel}</span>.`;
    } else {
        introText = 'You are not signed in yet. If you don\'t have an account, please <a href="register.html" style="color: var(--primary-2); font-weight: bold;">register here</a> to continue.';
    }

    const dashboardUrl = currentUser?.is_admin ? 'admin.html' : dashboardHref;
    const dashboardLabel = currentUser?.is_admin ? 'Go to admin panel' : 'Go to dashboard';

    banner.innerHTML = `
        <div class="panel-header">
            <h2>${title}</h2>
            <span class="status ${statusClass}">${statusText}</span>
        </div>
        <p>${introText}</p>
        <div class="button-row" style="margin-top: 14px; flex-wrap: wrap;">
            ${signedIn
                ? `
                    <a href="${dashboardUrl}" class="btn">${dashboardLabel}</a>
                    <button type="button" class="btn-secondary" data-logout-action onclick="window.UniSplitApp.clearAuthAndRedirect(); return false;">Logout</button>
                `
                : `
                    <a href="${loginHref}" class="btn">Go to login</a>
                `}
        </div>
    `;

    if (requireLogin && !signedIn) {
        window.setTimeout(() => {
            window.location.href = redirectTo;
        }, 1200);
    }

    return currentUser;
}

function requireCurrentUser(options = {}) {
    const {
        redirectTo = DEFAULT_LOGIN_REDIRECT,
        messageElementId = '',
        message = 'Please log in to continue.',
        autoRedirect = true,
    } = options;

    const currentUser = getCurrentUser();
    if (currentUser) {
        return currentUser;
    }

    if (messageElementId) {
        const messageElement = document.getElementById(messageElementId);
        if (messageElement) {
            messageElement.textContent = message;
            messageElement.style.color = '#ffb3b3';
        }
    }

    if (autoRedirect) {
        window.setTimeout(() => {
            window.location.href = redirectTo;
        }, 1200);
    }

    return null;
}

function clearAuthAndRedirect(redirectTo = DEFAULT_LOGIN_REDIRECT) {
    clearCurrentUser();
    window.location.href = redirectTo;
}

async function refreshCurrentUser() {
    const sessionToken = getCurrentSessionToken();
    if (!sessionToken) {
        return null;
    }

    try {
        const response = await apiFetch('/api/me');
        const payload = await response.json().catch(() => ({}));
        if (!response.ok) {
            throw new Error(payload.error || 'Unable to refresh user session');
        }
        return setCurrentUser(payload);
    } catch (error) {
        return getCurrentUser();
    }
}

async function apiFetch(path, options = {}) {
    const headers = new Headers(options.headers || {});
    const sessionToken = getCurrentSessionToken();
    if (sessionToken && !headers.has('Authorization')) {
        headers.set('Authorization', `Bearer ${sessionToken}`);
    }
    if (sessionToken && !headers.has('X-Session-Token')) {
        headers.set('X-Session-Token', sessionToken);
    }

    return fetch(apiUrl(path), {
        ...options,
        headers,
    });
}

function apiUrl(path) {
    if (!path) {
        return API_BASE_URL;
    }

    return `${API_BASE_URL}${path.startsWith('/') ? path : `/${path}`}`;
}

async function downloadResponseAsFile(response, filename) {
    if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        throw new Error(payload.error || `Request failed with status ${response.status}`);
    }

    const blob = await response.blob();
    const objectUrl = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = objectUrl;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(objectUrl);
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

/* ===== CURRENCY MODAL LOGIC ===== */
function initCurrencyModal() {
    if (document.getElementById('currencyModalOverlay')) return;

    const modalHtml = `
        <div class="currency-modal-overlay" id="currencyModalOverlay">
            <div class="currency-modal">
                <div class="currency-modal-header">
                    <h2>Live Exchange Rates</h2>
                    <button class="close-modal" onclick="hideCurrencyModal()">&times;</button>
                </div>
                <div class="currency-controls">
                    <input type="number" id="currencyAmount" class="currency-input" value="1.00" step="0.01">
                    <select id="baseCurrency" class="currency-select">
                        <option value="USD" selected>USD</option>
                        <option value="EUR">EUR</option>
                        <option value="CNY">CNY</option>
                        <option value="GBP">GBP</option>
                        <option value="JPY">JPY</option>
                        <option value="AUD">AUD</option>
                        <option value="CAD">CAD</option>
                        <option value="HKD">HKD</option>
                    </select>
                </div>
                <div class="rates-list" id="ratesList">
                    <p style="text-align:center; opacity:0.6;">Loading latest rates...</p>
                </div>
                <div class="modal-footer">
                    Data provided by Frankfurter API (European Central Bank)
                </div>
            </div>
        </div>
    `;
    document.body.insertAdjacentHTML('beforeend', modalHtml);

    // Listen for changes
    document.getElementById('baseCurrency').addEventListener('change', updateRates);
    document.getElementById('currencyAmount').addEventListener('input', updateRates);
}

function showCurrencyModal() {
    initCurrencyModal();
    document.getElementById('currencyModalOverlay').style.display = 'flex';
    updateRates();
}

function hideCurrencyModal() {
    document.getElementById('currencyModalOverlay').style.display = 'none';
}

async function updateRates() {
    const base = document.getElementById('baseCurrency').value;
    const amount = parseFloat(document.getElementById('currencyAmount').value) || 1;
    const list = document.getElementById('ratesList');

    try {
        // Now calling our own backend instead of external URL
        const res = await fetch(window.UniSplitApp.apiUrl(`/api/currencies?from=${base}`));
        const data = await res.json();
        
        if (data.rates) {
            let html = '';
            const sortedRates = Object.entries(data.rates).sort();
            for (const [code, rate] of sortedRates) {
                const converted = (rate * amount).toFixed(2);
                html += `
                    <div class="rate-item">
                        <span class="rate-currency">${code}</span>
                        <span class="rate-value">${converted}</span>
                    </div>
                `;
            }
            list.innerHTML = html;
        } else if (data.error) {
            throw new Error(data.error);
        }
    } catch (error) {
        console.error("Currency Proxy Error:", error);
        list.innerHTML = '<p style="color:#ff9d9d; text-align:center;">Could not sync with rates server.</p>';
    }
}

async function respondToExpense(expenseId, status, appealReason = '') {
    const sessionToken = getCurrentSessionToken();
    try {
        const response = await fetch(apiUrl(`/api/expenses/${expenseId}/respond`), {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                Authorization: `Bearer ${sessionToken}`,
                'X-Session-Token': sessionToken,
            },
            body: JSON.stringify({ status, appeal_reason: appealReason }),
        });
        return await response.json();
    } catch (error) {
        console.error("Respond Error:", error);
        return { error: "Network error" };
    }
}

async function payExpense(groupId, expenseId, payeeId, amount) {
    const sessionToken = getCurrentSessionToken();
    const currentUser = getCurrentUser();
    try {
        const response = await fetch(apiUrl(`/api/groups/${groupId}/settlements`), {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                Authorization: `Bearer ${sessionToken}`,
                'X-Session-Token': sessionToken,
            },
            body: JSON.stringify({
                expense_id: expenseId,
                payer_id: currentUser.id,
                payee_id: payeeId,
                amount: amount,
                note: `Payment for expense #${expenseId}`
            }),
        });
        return await response.json();
    } catch (error) {
        console.error("Payment Error:", error);
        return { error: "Network error" };
    }
}

window.UniSplitApp = {
    API_BASE_URL,
    normalizeUser,
    getCurrentUser,
    setCurrentUser,
    clearCurrentUser,
    getCurrentSessionToken,
    getUserDisplayName,
    getUserRoleLabel,
    createAuthActionButton,
    createLogoutButton,
    logoutCurrentUser,
    ensureAuthBanner,
    requireCurrentUser,
    clearAuthAndRedirect,
    refreshCurrentUser,
    apiUrl,
    apiFetch,
    downloadResponseAsFile,
    normalizeExpenseList,
    syncNavbarAuthState,
    showCurrencyModal,
    respondToExpense,
    payExpense
};

if (typeof document !== 'undefined') {
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            syncNavbarAuthState();
            initCurrencyModal();
        }, { once: true });
    } else {
        syncNavbarAuthState();
        initCurrencyModal();
    }
}
