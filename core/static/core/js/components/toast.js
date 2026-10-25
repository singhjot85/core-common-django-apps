/**
 * toast.js: Dynamic toast notification banner component.
 */
(function (window) {
  "use strict";

  const Core = window.Core || {};

  Core.toast = {
    show: function (message, type) {
      const container = document.getElementById("auth_toast_container") || document.body;
      const toast = document.createElement("div");
      toast.className = "auth-toast auth-toast-" + (type || "danger");
      toast.innerHTML = "<span>" + message + "</span>";
      container.appendChild(toast);
      setTimeout(function () {
        toast.remove();
      }, 6000);
    },
  };

  // Backwards compatibility alias for Core.auth.showToast
  Core.auth = Core.auth || {};
  Core.auth.showToast = Core.toast.show;

  window.Core = Core;
})(window);
