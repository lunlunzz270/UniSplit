const API_BASE_URL = 'http://127.0.0.1:5000';
const DEFAULT_LOGIN_REDIRECT = 'login.html';
const DEFAULT_DASHBOARD_REDIRECT = 'dashboard.html';

function normalizeUser(user) {
    if (!user || typeof user !== 'object') {
        return null;
    }

    const session = user.session && typeof user.session === 'object' ? user.session : null;
    return {
        id: user.id ?? null,
        name: user.name || user.full_name || '',
        full_name: user.full_name || user.name || '',
        email: user.email || '',
        session_token: user.session_token || user.token || session?.token || '',
        session_expires_at: user.session_expires_at || session?.expires_at || '',
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

    document.querySelectorAll('.navbar .nav-links').forEach((navLinks) => {
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

        leftGroup.appendChild(createNavbarLink(null, {
            href: 'index.html',
            label: 'Home',
            active: isActiveHref('index.html', currentPage),
        }));

        if (signedIn) {
            const visibleOrder = [
                'dashboard.html',
                'add_expense.html',
                'history.html',
                'report.html',
            ];

            visibleOrder.forEach((href) => {
                const labels = {
                    'dashboard.html': 'Dashboard',
                    'add_expense.html': 'Add Expense',
                    'history.html': 'Transaction History',
                    'report.html': 'Reports',
                };

                leftGroup.appendChild(createNavbarLink(null, {
                    href,
                    label: labels[href],
                    active: isActiveHref(href, currentPage),
                }));
            });

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

    const heroLoginLink = document.querySelector('.simple-home .button-group a[href="login.html"]');
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
    const introText = signedIn
        ? `You are signed in as ${getUserDisplayName(currentUser)}.`
        : 'You are not signed in yet. Please log in to continue.';

    banner.innerHTML = `
        <div class="panel-header">
            <h2>${title}</h2>
            <span class="status ${statusClass}">${statusText}</span>
        </div>
        <p>${introText}</p>
        <div class="button-row" style="margin-top: 14px; flex-wrap: wrap;">
            ${signedIn
                ? `
                    <a href="${dashboardHref}" class="btn">Go to dashboard</a>
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
    getCurrentSessionToken,
    getUserDisplayName,
    createAuthActionButton,
    createLogoutButton,
    logoutCurrentUser,
    ensureAuthBanner,
    requireCurrentUser,
    clearAuthAndRedirect,
    apiUrl,
    apiFetch,
    normalizeExpenseList,
    syncNavbarAuthState,
};

if (typeof document !== 'undefined') {
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', syncNavbarAuthState, { once: true });
    } else {
        syncNavbarAuthState();
    }
}
