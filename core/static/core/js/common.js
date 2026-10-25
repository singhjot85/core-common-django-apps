/**
 * common.js: Core common utilities (CSRF, REST API client, session management).
 */
(function (window) {
  "use strict";

  const Core = window.Core || {};

  /**
   * Retrieve CSRF token from cookie or hidden input
   */
  Core.getCSRFToken = function () {
    const input = document.querySelector('input[name="csrfmiddlewaretoken"]');
    if (input && input.value) {
      return input.value;
    }
    const match = document.cookie.match(/csrftoken=([\w-]+)/);
    return match ? match[1] : "";
  };

  /**
   * Fetch wrapper with auto-injected CSRF and JSON handling
   */
  Core.api = {
    request: async function (url, options = {}) {
      const headers = {
        "Content-Type": "application/json",
        "X-CSRFToken": Core.getCSRFToken(),
        ...(options.headers || {}),
      };

      const config = {
        ...options,
        headers: headers,
      };

      if (config.body && typeof config.body === "object") {
        config.body = JSON.stringify(config.body);
      }

      const response = await fetch(url, config);
      if (!response.ok) {
        let errorData = {};
        try {
          errorData = await response.json();
        } catch (e) {
          errorData = { detail: response.statusText };
        }
        throw { status: response.status, data: errorData };
      }

      if (response.status === 204) {
        return null;
      }

      return await response.json();
    },

    get: function (url, options = {}) {
      return Core.api.request(url, { ...options, method: "GET" });
    },

    post: function (url, data, options = {}) {
      return Core.api.request(url, { ...options, method: "POST", body: data });
    },

    patch: function (url, data, options = {}) {
      return Core.api.request(url, { ...options, method: "PATCH", body: data });
    },

    delete: function (url, options = {}) {
      return Core.api.request(url, { ...options, method: "DELETE" });
    },
  };

  /**
   * Session & Token Lifecycle Management
   */
  Core.authSession = {
    getCookie: function (name) {
      const match = document.cookie.match(new RegExp("(^|;\\s*)(" + name + ")=([^;]*)"));
      return match ? decodeURIComponent(match[3]) : null;
    },
    setCookie: function (name, value, seconds) {
      let expires = "";
      if (seconds) {
        const d = new Date();
        d.setTime(d.getTime() + seconds * 1000);
        expires = "; expires=" + d.toUTCString();
      }
      document.cookie = name + "=" + encodeURIComponent(value) + expires + "; path=/; SameSite=Lax";
    },
    deleteCookie: function (name) {
      document.cookie = name + "=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/; SameSite=Lax";
    },
    getToken: function () {
      return Core.authSession.getCookie("access_token");
    },
    parseJWT: function (token) {
      try {
        const base64Url = token.split(".")[1];
        const base64 = base64Url.replace(/-/g, "+").replace(/_/g, "/");
        const jsonPayload = decodeURIComponent(
          atob(base64)
            .split("")
            .map(function (c) {
              return "%" + ("00" + c.charCodeAt(0).toString(16)).slice(-2);
            })
            .join("")
        );
        return JSON.parse(jsonPayload);
      } catch (e) {
        return null;
      }
    },
    showTimeoutModal: function () {
      const overlay = document.getElementById("session_timeout_overlay");
      if (overlay) {
        overlay.style.display = "flex";
        document.body.style.overflow = "hidden";
      }
    },
    initWatcher: function () {
      const token = Core.authSession.getToken();
      if (!token) return;

      const payload = Core.authSession.parseJWT(token);
      if (payload && payload.exp) {
        const expiresAtMs = payload.exp * 1000;
        const remainingMs = expiresAtMs - Date.now();
        if (remainingMs <= 0) {
          Core.authSession.showTimeoutModal();
        } else {
          setTimeout(function () {
            Core.authSession.showTimeoutModal();
          }, remainingMs);
        }
      }
    },
  };

  document.addEventListener("DOMContentLoaded", function () {
    Core.authSession.initWatcher();
  });

  window.Core = Core;
})(window);
