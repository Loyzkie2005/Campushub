(function () {
    const TOKEN_KEY = 'campushub_admin_tab_token';
    const QUERY_PARAM = '__at';
    const LOGOUT_URL = '/admin-logout/';
    const LOGIN_URL = '/';

    function getTabToken() {
        return sessionStorage.getItem(TOKEN_KEY) || '';
    }

    function setTabToken(token) {
        if (!token) {
            sessionStorage.removeItem(TOKEN_KEY);
            return;
        }
        sessionStorage.setItem(TOKEN_KEY, token);
    }

    function clearTabToken() {
        sessionStorage.removeItem(TOKEN_KEY);
    }

    function isAdminPath(pathname) {
        if (!pathname || pathname === '/' || pathname === '') return false;
        if (pathname.includes('admin-logout')) return false;
        return pathname.startsWith('/admin') || pathname.startsWith('/api/admin');
    }

    function urlWithToken(url) {
        const token = getTabToken();
        if (!token || !url) return url;

        try {
            const resolved = new URL(url, window.location.origin);
            if (resolved.origin !== window.location.origin) return url;
            if (resolved.searchParams.has(QUERY_PARAM)) return url;
            resolved.searchParams.set(QUERY_PARAM, token);
            return resolved.pathname + resolved.search + resolved.hash;
        } catch (_) {
            return url;
        }
    }

    function bootstrapTokenFromUrl() {
        const params = new URLSearchParams(window.location.search);
        const urlToken = params.get(QUERY_PARAM);

        if (urlToken) {
            setTabToken(urlToken);
            return;
        }

        const stored = getTabToken();
        if (stored && isAdminPath(window.location.pathname)) {
            params.set(QUERY_PARAM, stored);
            const nextUrl = window.location.pathname + '?' + params.toString() + window.location.hash;
            window.history.replaceState({}, document.title, nextUrl);
        }
    }

    function injectTokenIntoForms() {
        const token = getTabToken();
        if (!token) return;

        document.querySelectorAll('form').forEach((form) => {
            const method = (form.getAttribute('method') || 'get').toLowerCase();
            if (method !== 'post') return;

            if (!form.querySelector(`input[name="${QUERY_PARAM}"]`)) {
                const input = document.createElement('input');
                input.type = 'hidden';
                input.name = QUERY_PARAM;
                input.value = token;
                form.appendChild(input);
            }

            const action = form.getAttribute('action');
            if (action) {
                form.setAttribute('action', urlWithToken(action));
            }
        });
    }

    window.CampusHubAdminSession = {
        getTabToken,
        setTabToken,
        clearTabToken,
        urlWithToken,
    };

    bootstrapTokenFromUrl();

    const nativeFetch = window.fetch.bind(window);
    window.fetch = function (input, init) {
        init = init || {};
        const token = getTabToken();
        if (token) {
            const headers = new Headers(init.headers || {});
            if (!headers.has('X-Admin-Tab-Token')) {
                headers.set('X-Admin-Tab-Token', token);
            }
            init.headers = headers;
            if (!init.credentials) {
                init.credentials = 'same-origin';
            }
        }
        return nativeFetch(input, init);
    };

    document.addEventListener('click', (event) => {
        const link = event.target.closest('a[href]');
        if (!link) return;

        const href = link.getAttribute('href');
        if (!href || href.startsWith('#') || href.startsWith('javascript:')) return;

        try {
            const resolved = new URL(href, window.location.origin);
            if (resolved.origin !== window.location.origin) return;
            const updated = urlWithToken(href);
            if (updated !== href) {
                link.setAttribute('href', updated);
            }
        } catch (_) {
            /* ignore malformed href */
        }
    }, true);

    document.addEventListener('click', (event) => {
        const logoutLink = event.target.closest('a[href*="admin-logout"]');
        if (!logoutLink) return;
        logoutLink.setAttribute('href', urlWithToken(logoutLink.getAttribute('href') || LOGOUT_URL));
    }, true);

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', injectTokenIntoForms);
    } else {
        injectTokenIntoForms();
    }

    const header = document.querySelector('.dashboard-header[data-admin-user-id]');
    const pageUserId = header ? header.getAttribute('data-admin-user-id') : '';

    function goToLogin() {
        clearTabToken();
        const path = window.location.pathname;
        if (path === '/' || path === '') return;
        window.location.replace(LOGIN_URL);
    }

    async function verifySession() {
        const token = getTabToken();
        if (!token || !pageUserId) return;

        try {
            const response = await fetch('/api/admin/session/', {
                credentials: 'same-origin',
                headers: {
                    Accept: 'application/json',
                    'X-Admin-Tab-Token': token,
                },
            });
            if (!response.ok) {
                goToLogin();
                return;
            }
            const data = await response.json();
            if (!data.authenticated) {
                goToLogin();
            }
        } catch (_) {
            /* ignore transient network errors */
        }
    }

    if (pageUserId) {
        document.addEventListener('visibilitychange', () => {
            if (document.visibilityState === 'visible') {
                verifySession();
            }
        });
        window.addEventListener('focus', verifySession);
    }
})();
