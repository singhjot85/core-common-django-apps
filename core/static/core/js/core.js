/**
 * Core JavaScript Utilities
 */

(function (window) {
  "use strict";

  const Core = {
    /**
     * Retrieve CSRF token from cookie or hidden input
     */
    getCSRFToken: function () {
      const input = document.querySelector('input[name="csrfmiddlewaretoken"]');
      if (input && input.value) {
        return input.value;
      }
      const match = document.cookie.match(/csrftoken=([\w-]+)/);
      return match ? match[1] : "";
    },

    /**
     * Modal Helper
     */
    modal: {
      open: function (modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
          modal.classList.add("open");
          document.body.style.overflow = "hidden";
        }
      },
      close: function (modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
          modal.classList.remove("open");
          document.body.style.overflow = "";
        }
      },
    },

    /**
     * Fetch wrapper with auto-injected CSRF and JSON handling
     */
    api: {
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
    },
  };

  // Initialize interactive event listeners
  document.addEventListener("DOMContentLoaded", function () {
    // Modal open buttons
    document.querySelectorAll("[data-modal-target]").forEach(function (btn) {
      btn.addEventListener("click", function (e) {
        e.preventDefault();
        const targetId = btn.getAttribute("data-modal-target");
        Core.modal.open(targetId);
      });
    });

    // Modal close buttons
    document.querySelectorAll("[data-modal-close]").forEach(function (btn) {
      btn.addEventListener("click", function (e) {
        e.preventDefault();
        const targetId = btn.getAttribute("data-modal-close");
        if (targetId) {
          Core.modal.close(targetId);
        } else {
          const parentModal = btn.closest(".modal-backdrop");
          if (parentModal) {
            parentModal.classList.remove("open");
            document.body.style.overflow = "";
          }
        }
      });
    });

    // Close modal on clicking backdrop
    document.querySelectorAll(".modal-backdrop").forEach(function (backdrop) {
      backdrop.addEventListener("click", function (e) {
        if (e.target === backdrop) {
          backdrop.classList.remove("open");
          document.body.style.overflow = "";
        }
      });
    });
  });

  window.Core = Core;
})(window);
