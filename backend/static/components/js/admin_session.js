(function () {
    if (window.__campushubAdminSessionInitialized) return;
    window.__campushubAdminSessionInitialized = true;

    const TOKEN_KEY = 'campushub_admin_tab_token';
    const LOGGED_OUT_KEY = 'campushub_admin_logged_out';
    const QUERY_PARAM = '__at';
    const LOGOUT_URL = '/admin-logout/';
    const LOGIN_URL = '/';

    const nativeFetch = window.fetch.bind(window);

    function getTabToken() {
        return sessionStorage.getItem(TOKEN_KEY) || '';
    }

    function setTabToken(token) {
        if (!token) {
            sessionStorage.removeItem(TOKEN_KEY);
            return;
        }
        sessionStorage.setItem(TOKEN_KEY, token);
        sessionStorage.removeItem(LOGGED_OUT_KEY);
    }

    function clearTabToken() {
        sessionStorage.removeItem(TOKEN_KEY);
        sessionStorage.setItem(LOGGED_OUT_KEY, '1');
    }

    function isMarkedLoggedOut() {
        return sessionStorage.getItem(LOGGED_OUT_KEY) === '1';
    }

    function getUrlToken() {
        try {
            const params = new URLSearchParams(window.location.search);
            return params.get(QUERY_PARAM) || '';
        } catch (_) {
            return '';
        }
    }

    function isLoginPath(pathname) {
        return !pathname || pathname === '/' || pathname === '/admin-login/';
    }

    function isAdminPath(pathname) {
        if (isLoginPath(pathname)) return false;
        if (pathname.includes('admin-logout')) return false;
        return pathname.startsWith('/admin') || pathname.startsWith('/api/admin');
    }

    function isBackForwardNavigation(pageshowEvent) {
        if (pageshowEvent && pageshowEvent.persisted) {
            return true;
        }
        try {
            const entries =
                window.performance && typeof window.performance.getEntriesByType === 'function'
                    ? window.performance.getEntriesByType('navigation')
                    : [];
            if (entries && entries.length > 0 && entries[0].type === 'back_forward') {
                return true;
            }
            if (
                window.performance &&
                window.performance.navigation &&
                window.performance.navigation.type === 2
            ) {
                return true;
            }
        } catch (_) {
            /* ignore unsupported performance APIs */
        }
        return false;
    }

    function stripTokenFromAddressBar() {
        try {
            const params = new URLSearchParams(window.location.search);
            if (!params.has(QUERY_PARAM)) return;
            params.delete(QUERY_PARAM);
            const query = params.toString();
            const cleanUrl =
                window.location.pathname +
                (query ? '?' + query : '') +
                window.location.hash;
            window.history.replaceState({}, document.title, cleanUrl);
        } catch (_) {
            /* ignore history errors */
        }
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

    function revokeAndRedirectToLogin(redirectToLogin) {
        const token = getTabToken() || getUrlToken();
        clearTabToken();
        stripTokenFromAddressBar();

        if (redirectToLogin) {
            const target = token
                ? LOGOUT_URL + '?' + QUERY_PARAM + '=' + encodeURIComponent(token)
                : LOGIN_URL;
            window.location.replace(target);
            return;
        }

        if (token) {
            nativeFetch(
                LOGOUT_URL + '?' + QUERY_PARAM + '=' + encodeURIComponent(token),
                {
                    method: 'GET',
                    credentials: 'same-origin',
                    cache: 'no-store',
                    keepalive: true,
                }
            ).catch(() => {});
        }
    }

    function bootstrapTokenFromUrl() {
        const urlToken = getUrlToken();
        if (urlToken) {
            setTabToken(urlToken);
            stripTokenFromAddressBar();
        }
    }

    function injectTokenIntoForms() {
        const token = getTabToken();
        if (!token) return;

        document.querySelectorAll('form').forEach((form) => {
            const method = (form.getAttribute('method') || 'get').toLowerCase();
            if (method !== 'post') return;

            let input = form.querySelector(`input[name="${QUERY_PARAM}"]`);
            if (!input) {
                input = document.createElement('input');
                input.type = 'hidden';
                input.name = QUERY_PARAM;
                form.appendChild(input);
            }
            input.value = token;

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
        revokeAndRedirectToLogin,
    };

    if (isLoginPath(window.location.pathname)) {
        revokeAndRedirectToLogin(false);
    } else if (isAdminPath(window.location.pathname)) {
        if (isBackForwardNavigation() || (isMarkedLoggedOut() && !getUrlToken())) {
            revokeAndRedirectToLogin(true);
            return;
        }
        bootstrapTokenFromUrl();
    }

    const initialRouteKey = window.location.pathname + window.location.search;
    let lastHash = window.location.hash;

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
        const logoutLink = event.target.closest('a[href*="admin-logout"]');
        if (logoutLink) {
            const rawHref = logoutLink.getAttribute('href') || LOGOUT_URL;
            logoutLink.setAttribute('href', urlWithToken(rawHref));
            clearTabToken();
            return;
        }

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

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', injectTokenIntoForms);
    } else {
        injectTokenIntoForms();
    }

    const header = document.querySelector('.dashboard-header[data-admin-user-id]');
    const pageUserId = header ? header.getAttribute('data-admin-user-id') : '';

    function goToLogin() {
        revokeAndRedirectToLogin(!isLoginPath(window.location.pathname));
    }

    let sessionCheck = null;

    async function verifySession() {
        if (!isAdminPath(window.location.pathname)) return;
        const token = getTabToken();
        if (!token || !pageUserId) return;
        // Focus and visibility often fire together when returning to an idle tab.
        if (sessionCheck?.token === token) return sessionCheck.promise;

        const check = {token};
        sessionCheck = check;
        check.promise = (async () => {
            const controller = new AbortController();
            const timeout = window.setTimeout(() => controller.abort(), 15000);
            try {
                const response = await nativeFetch('/api/admin/session/', {
                    credentials: 'same-origin',
                    cache: 'no-store',
                    signal: controller.signal,
                    headers: {
                        Accept: 'application/json',
                        'X-Admin-Tab-Token': token,
                    },
                });
                // An old request must not revoke a newer login in this tab.
                if (getTabToken() !== token || isMarkedLoggedOut()) return;
                if (response.status === 401 || response.status === 403) {
                    goToLogin();
                    return;
                }
                // Rate limits and temporary server errors do not prove logout.
                if (!response.ok) return;
                const data = await response.json();
                if (getTabToken() !== token || isMarkedLoggedOut()) return;
                if (data.authenticated === false) goToLogin();
            } catch (_) {
                /* Network errors/timeouts keep the token; the next focus retries. */
            } finally {
                window.clearTimeout(timeout);
                if (sessionCheck === check) sessionCheck = null;
            }
        })();
        return check.promise;
    }

    window.addEventListener('pageshow', (event) => {
        if (isLoginPath(window.location.pathname)) {
            revokeAndRedirectToLogin(false);
            return;
        }
        if (isAdminPath(window.location.pathname)) {
            if (isBackForwardNavigation(event) || isMarkedLoggedOut()) {
                revokeAndRedirectToLogin(true);
                return;
            }
            verifySession();
        }
    });

    window.addEventListener('popstate', () => {
        if (isLoginPath(window.location.pathname)) {
            revokeAndRedirectToLogin(false);
            return;
        }
        if (!isAdminPath(window.location.pathname)) return;
        const currentRouteKey = window.location.pathname + window.location.search;
        if (currentRouteKey === initialRouteKey && window.location.hash !== lastHash) {
            lastHash = window.location.hash;
            return;
        }
        revokeAndRedirectToLogin(true);
    });

    if (pageUserId) {
        verifySession();
        document.addEventListener('visibilitychange', () => {
            if (document.visibilityState === 'visible') {
                verifySession();
            }
        });
        window.addEventListener('focus', verifySession);
    }
})();
