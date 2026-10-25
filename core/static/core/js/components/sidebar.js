/**
 * sidebar.js: Sidebar collapse, expand, and mobile navigation component.
 */
(function (window) {
  "use strict";

  const Core = window.Core || {};

  Core.sidebar = {
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
  };

  document.addEventListener("DOMContentLoaded", function () {
    Core.sidebar.init();

    document.querySelectorAll("[data-sidebar-toggle], #sidebar_collapse_toggle").forEach(function (btn) {
      btn.addEventListener("click", function (e) {
        e.preventDefault();
        Core.sidebar.toggle();
      });
    });

    document.querySelectorAll("[data-sidebar-mobile-toggle], .mobile-menu-toggle").forEach(function (btn) {
      btn.addEventListener("click", function (e) {
        e.preventDefault();
        Core.sidebar.toggleMobile();
      });
    });
  });

  window.Core = Core;
})(window);
