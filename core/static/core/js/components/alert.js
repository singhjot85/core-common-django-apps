/**
 * alert.js: Alert notification dismissal component.
 */
(function (window) {
  "use strict";

  const Core = window.Core || {};

  Core.alert = {
    dismiss: function (element) {
      const alertEl = element.closest(".alert");
      if (alertEl) {
        alertEl.remove();
      }
    },
  };

  document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll("[data-alert-dismiss]").forEach(function (btn) {
      btn.addEventListener("click", function (e) {
        e.preventDefault();
        Core.alert.dismiss(btn);
      });
    });
  });

  window.Core = Core;
})(window);
