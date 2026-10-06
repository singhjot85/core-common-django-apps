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
     * Sidebar Collapse / Expand / Mobile Navigation Helper
     */
    sidebar: {
      toggle: function () {
        const shell = document.querySelector(".app-shell");
        if (shell) {
          const isCollapsed = shell.classList.toggle("sidebar-collapsed");
          try {
            localStorage.setItem("core_sidebar_collapsed", isCollapsed ? "true" : "false");
          } catch (e) {}
        }
      },
      collapse: function () {
        const shell = document.querySelector(".app-shell");
        if (shell) {
          shell.classList.add("sidebar-collapsed");
          try {
            localStorage.setItem("core_sidebar_collapsed", "true");
          } catch (e) {}
        }
      },
      expand: function () {
        const shell = document.querySelector(".app-shell");
        if (shell) {
          shell.classList.remove("sidebar-collapsed");
          try {
            localStorage.setItem("core_sidebar_collapsed", "false");
          } catch (e) {}
        }
      },
      toggleMobile: function () {
        const sidebar = document.querySelector(".app-sidebar");
        if (sidebar) {
          sidebar.classList.toggle("open");
        }
      },
      openMobile: function () {
        const sidebar = document.querySelector(".app-sidebar");
        if (sidebar) {
          sidebar.classList.add("open");
        }
      },
      closeMobile: function () {
        const sidebar = document.querySelector(".app-sidebar");
        if (sidebar) {
          sidebar.classList.remove("open");
        }
      },
      init: function () {
        try {
          const stored = localStorage.getItem("core_sidebar_collapsed");
          if (stored === "true") {
            const shell = document.querySelector(".app-shell");
            if (shell) shell.classList.add("sidebar-collapsed");
          }
        } catch (e) {}
      },
    },

    /**
     * Alert Helper
     */
    alert: {
      dismiss: function (element) {
        const alertEl = element.closest(".alert");
        if (alertEl) {
          alertEl.remove();
        }
      },
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
    // Restore sidebar state
    Core.sidebar.init();

    // Sidebar collapse toggle button (Desktop)
    document.querySelectorAll("[data-sidebar-toggle], #sidebar_collapse_toggle").forEach(function (btn) {
      btn.addEventListener("click", function (e) {
        e.preventDefault();
        Core.sidebar.toggle();
      });
    });

    // Mobile sidebar toggle button
    document.querySelectorAll("[data-sidebar-mobile-toggle], .mobile-menu-toggle").forEach(function (btn) {
      btn.addEventListener("click", function (e) {
        e.preventDefault();
        Core.sidebar.toggleMobile();
      });
    });

    // Alert dismiss buttons
    document.querySelectorAll("[data-alert-dismiss]").forEach(function (btn) {
      btn.addEventListener("click", function (e) {
        e.preventDefault();
        Core.alert.dismiss(btn);
      });
    });

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
