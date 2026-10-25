/**
 * theme.js: Theme Switcher component (Light / Dark / Auto).
 */
(function (window) {
  "use strict";

  const Core = window.Core || {};

  Core.theme = {
    get: function () {
      return (
        document.documentElement.getAttribute("data-theme") ||
        localStorage.getItem("core_theme") ||
        (window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light")
      );
    },
    set: function (themeName) {
      if (themeName === "dark" || themeName === "light") {
        document.documentElement.setAttribute("data-theme", themeName);
        try {
          localStorage.setItem("core_theme", themeName);
        } catch (e) {}
      } else {
        document.documentElement.removeAttribute("data-theme");
        try {
          localStorage.removeItem("core_theme");
        } catch (e) {}
      }
      Core.theme.updateUI();
    },
    toggle: function () {
      const current = Core.theme.get();
      const nextTheme = current === "dark" ? "light" : "dark";
      Core.theme.set(nextTheme);
      return nextTheme;
    },
    updateUI: function () {
      const current = Core.theme.get();
      document.querySelectorAll("[data-theme-toggle]").forEach(function (btn) {
        const darkIcon = btn.querySelector(".theme-icon-dark");
        const lightIcon = btn.querySelector(".theme-icon-light");
        if (darkIcon && lightIcon) {
          if (current === "dark") {
            darkIcon.style.display = "none";
            lightIcon.style.display = "inline-flex";
          } else {
            darkIcon.style.display = "inline-flex";
            lightIcon.style.display = "none";
          }
        }
      });
    },
    init: function () {
      Core.theme.updateUI();
    },
  };

  document.addEventListener("DOMContentLoaded", function () {
    Core.theme.init();

    document.querySelectorAll("[data-theme-toggle]").forEach(function (btn) {
      btn.addEventListener("click", function (e) {
        e.preventDefault();
        Core.theme.toggle();
      });
    });
  });

  window.Core = Core;
})(window);
