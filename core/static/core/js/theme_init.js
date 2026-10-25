/**
 * theme_init.js: Theme preference initializer for FOUC prevention.
 */
(function () {
    "use strict";
    try {
        var theme = localStorage.getItem("core_theme") ||
            (window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
        if (theme) document.documentElement.setAttribute("data-theme", theme);
    } catch (e) {}
})();
