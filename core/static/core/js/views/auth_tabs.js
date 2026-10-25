/**
 * auth_tabs.js: Auth tab switching, password toggling, and attempt warning banners.
 */
(function (window) {
  "use strict";

  const Core = window.Core || {};
  Core.auth = Core.auth || {};

  Core.auth.setWarning = function (elementId, message) {
    const el = document.getElementById(elementId);
    if (!el) return;
    if (message) {
      const textEl = el.querySelector(".warning-text");
      if (textEl) textEl.textContent = message;
      el.style.display = "flex";
    } else {
      el.style.display = "none";
    }
  };

  Core.auth.switchTab = function (tabKey) {
    document.querySelectorAll("[data-auth-tab]").forEach(function (btn) {
      const isActive = btn.getAttribute("data-auth-tab") === tabKey;
      btn.classList.toggle("active", isActive);
    });
    document.querySelectorAll("[data-auth-tab-content]").forEach(function (content) {
      const isTarget = content.getAttribute("data-auth-tab-content") === tabKey;
      content.style.display = isTarget ? "" : "none";
    });
  };

  Core.auth.switchUsernameTab = function (tabKey) {
    document.querySelectorAll("[data-username-tab]").forEach(function (btn) {
      const isActive = btn.getAttribute("data-username-tab") === tabKey;
      btn.classList.toggle("active", isActive);
    });
    document.querySelectorAll("[data-username-tab-content]").forEach(function (content) {
      const isTarget = content.getAttribute("data-username-tab-content") === tabKey;
      content.style.display = isTarget ? "" : "none";
    });
  };

  Core.auth.switchOTPTab = function (tabKey) {
    document.querySelectorAll("[data-otp-tab]").forEach(function (btn) {
      const isActive = btn.getAttribute("data-otp-tab") === tabKey;
      btn.classList.toggle("active", isActive);
    });
    document.querySelectorAll("[data-otp-tab-content]").forEach(function (content) {
      const isTarget = content.getAttribute("data-otp-tab-content") === tabKey;
      content.style.display = isTarget ? "" : "none";
    });
  };

  Core.auth.switchMethod = function (methodKey) {
    document.querySelectorAll("[data-auth-method]").forEach(function (btn) {
      const isActive = btn.getAttribute("data-auth-method") === methodKey;
      btn.classList.toggle("active", isActive);
    });
    document.querySelectorAll("[data-auth-method-content]").forEach(function (content) {
      const isTarget = content.getAttribute("data-auth-method-content") === methodKey;
      content.style.display = isTarget ? "" : "none";
    });
  };

  Core.auth.togglePassword = function (btn) {
    const targetId = btn.getAttribute("data-password-toggle");
    const input = document.getElementById(targetId);
    if (input) {
      const isPassword = input.type === "password";
      input.type = isPassword ? "text" : "password";
      btn.classList.toggle("active", isPassword);
    }
  };

  document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll("[data-auth-method]").forEach(function (btn) {
      btn.addEventListener("click", function (e) {
        e.preventDefault();
        const method = btn.getAttribute("data-auth-method");
        Core.auth.switchMethod(method);
      });
    });

    document.querySelectorAll("[data-auth-tab]").forEach(function (btn) {
      btn.addEventListener("click", function (e) {
        e.preventDefault();
        const tab = btn.getAttribute("data-auth-tab");
        Core.auth.switchTab(tab);
      });
    });

    document.querySelectorAll("[data-username-tab]").forEach(function (btn) {
      btn.addEventListener("click", function (e) {
        e.preventDefault();
        const tab = btn.getAttribute("data-username-tab");
        Core.auth.switchUsernameTab(tab);
      });
    });

    document.querySelectorAll("[data-otp-tab]").forEach(function (btn) {
      btn.addEventListener("click", function (e) {
        e.preventDefault();
        const tab = btn.getAttribute("data-otp-tab");
        Core.auth.switchOTPTab(tab);
      });
    });

    document.querySelectorAll("[data-password-toggle]").forEach(function (btn) {
      btn.addEventListener("click", function (e) {
        e.preventDefault();
        Core.auth.togglePassword(btn);
      });
    });
  });

  window.Core = Core;
})(window);
