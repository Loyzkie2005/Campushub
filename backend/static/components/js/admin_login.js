(function () {
  "use strict";

  const REMEMBER_KEY = "campushub_remember";
  const USERNAME_KEY = "campushub_username";

  function initializeLogin() {
    const form = document.getElementById("adminLoginForm");
    if (!form) return;

    const usernameInput = document.getElementById("username");
    const passwordInput = document.getElementById("password");
    const rememberInput = document.getElementById("rememberMe");
    const errorMessage = document.getElementById("errorMessage");
    const loginButton = form.querySelector('button[type="submit"]');
    const passwordButton = document.getElementById("togglePassword");
    const eyeOpen = document.getElementById("eyeOpen");
    const eyeClosed = document.getElementById("eyeClosed");

    if (!usernameInput || !passwordInput) return;

    const loginUrl = form.dataset.loginUrl || "/api/admin_login/";
    const redirectUrl = form.dataset.redirectUrl || "/admin-dashboard/";
    const resolvedLoginUrl = new URL(loginUrl, window.location.href).toString();

    function showError(message) {
      if (!errorMessage) return;
      errorMessage.textContent = message;
      errorMessage.classList.remove("d-none");
    }

    function hideError() {
      if (!errorMessage) return;
      errorMessage.classList.add("d-none");
    }

    function setLoading(isLoading) {
      if (!loginButton) return;
      loginButton.disabled = isLoading;
      loginButton.classList.toggle("loading", isLoading);
    }

    function rememberUsername(username) {
      if (rememberInput?.checked) {
        localStorage.setItem(USERNAME_KEY, username);
        localStorage.setItem(REMEMBER_KEY, "true");
        return;
      }

      localStorage.removeItem(USERNAME_KEY);
      localStorage.removeItem(REMEMBER_KEY);
    }

    function restoreUsername() {
      if (localStorage.getItem(REMEMBER_KEY) !== "true") return;

      const savedUsername = localStorage.getItem(USERNAME_KEY);
      if (!savedUsername) return;

      usernameInput.value = savedUsername;
      if (rememberInput) rememberInput.checked = true;
      passwordInput.focus();
    }

    function togglePassword() {
      if (!passwordButton || !eyeOpen || !eyeClosed) return;

      const showPassword = passwordInput.type === "password";
      passwordInput.type = showPassword ? "text" : "password";
      eyeOpen.classList.toggle("d-none", showPassword);
      eyeClosed.classList.toggle("d-none", !showPassword);
      passwordButton.setAttribute("aria-pressed", String(showPassword));
      passwordButton.setAttribute(
        "aria-label",
        showPassword ? "Hide password" : "Show password"
      );
    }

    async function submitLogin(event) {
      event.preventDefault();
      hideError();

      const username = usernameInput.value.trim();
      const password = passwordInput.value.trim();

      if (!username || !password) {
        showError("Invalid Username or Password");
        return;
      }

      rememberUsername(username);
      setLoading(true);

      try {
        const response = await fetch(resolvedLoginUrl, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          credentials: "same-origin",
          body: JSON.stringify({
            username,
            password,
            remember_me: rememberInput?.checked || false,
          }),
        });
        const data = await response.json().catch(() => ({}));

        if (!response.ok) {
          showError(data.error || "Invalid username or password");
          setLoading(false);
          return;
        }

        if (data.tab_token) {
          window.CampusHubAdminSession?.setTabToken?.(data.tab_token);
        }

        sessionStorage.removeItem("sidebar_collapsed");
        const nextUrl = data.redirect_url || redirectUrl;
        window.location.href =
          window.CampusHubAdminSession?.urlWithToken?.(nextUrl) || nextUrl;
      } catch (error) {
        showError(
          `Cannot connect to login server at ${resolvedLoginUrl}. Start Django and open the login page from the Django URL.`
        );
        setLoading(false);
        console.error("Login error:", error);
      }
    }

    passwordButton?.addEventListener("click", togglePassword);
    form.addEventListener("submit", submitLogin);
    restoreUsername();
  }

  const THEME_KEY = "campushub_admin_theme";

  function initializeThemeToggle() {
    const toggleBtn = document.getElementById("themeToggleBtn");
    const sunIcon = document.getElementById("themeIconSun");
    const moonIcon = document.getElementById("themeIconMoon");
    const brandLogo = document.getElementById("loginBrandLogo");
    const favicon = document.getElementById("pageFavicon");

    function applyTheme(theme) {
      const isDark = theme === "dark";
      document.documentElement.setAttribute("data-theme", isDark ? "dark" : "light");
      localStorage.setItem(THEME_KEY, isDark ? "dark" : "light");

      if (toggleBtn) {
        toggleBtn.setAttribute(
          "title",
          isDark ? "Switch to light mode" : "Switch to dark mode"
        );
        toggleBtn.setAttribute(
          "aria-label",
          isDark ? "Switch to light mode" : "Switch to dark mode"
        );
      }

      if (sunIcon && moonIcon) {
        if (isDark) {
          sunIcon.classList.add("d-none");
          moonIcon.classList.remove("d-none");
        } else {
          moonIcon.classList.add("d-none");
          sunIcon.classList.remove("d-none");
        }
      }

      if (brandLogo) {
        const targetSrc = isDark ? brandLogo.dataset.darkSrc : brandLogo.dataset.lightSrc;
        if (targetSrc) brandLogo.src = targetSrc;
      }

      if (favicon) {
        const targetFavicon = isDark ? favicon.dataset.darkSrc : favicon.dataset.lightSrc;
        if (targetFavicon) favicon.href = targetFavicon;
      }
    }

    const current =
      localStorage.getItem(THEME_KEY) ||
      document.documentElement.getAttribute("data-theme") ||
      "light";
    applyTheme(current);

    toggleBtn?.addEventListener("click", function () {
      const activeTheme =
        document.documentElement.getAttribute("data-theme") || "light";
      const nextTheme = activeTheme === "dark" ? "light" : "dark";
      applyTheme(nextTheme);
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    initializeLogin();
    initializeThemeToggle();
  });
})();
