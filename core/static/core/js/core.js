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
     * Theme Switcher Helper (Light / Dark / Auto)
     */
    theme: {
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

    /**
     * Session & Token Lifecycle Management
     */
    authSession: {
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
    },

    /**
     * Auth Page & Form Utilities
     */
    auth: {
      showToast: function (message, type) {
        const container = document.getElementById("auth_toast_container");
        if (!container) return;
        const toast = document.createElement("div");
        toast.className = "auth-toast auth-toast-" + (type || "danger");
        toast.innerHTML = "<span>" + message + "</span>";
        container.appendChild(toast);
        setTimeout(function () {
          toast.remove();
        }, 6000);
      },
      setWarning: function (elementId, message) {
        const el = document.getElementById(elementId);
        if (!el) return;
        if (message) {
          const textEl = el.querySelector(".warning-text");
          if (textEl) textEl.textContent = message;
          el.style.display = "flex";
        } else {
          el.style.display = "none";
        }
      },
      switchTab: function (tabKey) {
        document.querySelectorAll("[data-auth-tab]").forEach(function (btn) {
          const isActive = btn.getAttribute("data-auth-tab") === tabKey;
          btn.classList.toggle("active", isActive);
        });
        document.querySelectorAll("[data-auth-tab-content]").forEach(function (content) {
          const isTarget = content.getAttribute("data-auth-tab-content") === tabKey;
          content.style.display = isTarget ? "" : "none";
        });
      },
      switchUsernameTab: function (tabKey) {
        document.querySelectorAll("[data-username-tab]").forEach(function (btn) {
          const isActive = btn.getAttribute("data-username-tab") === tabKey;
          btn.classList.toggle("active", isActive);
        });
        document.querySelectorAll("[data-username-tab-content]").forEach(function (content) {
          const isTarget = content.getAttribute("data-username-tab-content") === tabKey;
          content.style.display = isTarget ? "" : "none";
        });
      },
      switchOTPTab: function (tabKey) {
        document.querySelectorAll("[data-otp-tab]").forEach(function (btn) {
          const isActive = btn.getAttribute("data-otp-tab") === tabKey;
          btn.classList.toggle("active", isActive);
        });
        document.querySelectorAll("[data-otp-tab-content]").forEach(function (content) {
          const isTarget = content.getAttribute("data-otp-tab-content") === tabKey;
          content.style.display = isTarget ? "" : "none";
        });
      },
      switchMethod: function (methodKey) {
        document.querySelectorAll("[data-auth-method]").forEach(function (btn) {
          const isActive = btn.getAttribute("data-auth-method") === methodKey;
          btn.classList.toggle("active", isActive);
        });
        document.querySelectorAll("[data-auth-method-content]").forEach(function (content) {
          const isTarget = content.getAttribute("data-auth-method-content") === methodKey;
          content.style.display = isTarget ? "" : "none";
        });
      },
      togglePassword: function (btn) {
        const targetId = btn.getAttribute("data-password-toggle");
        const input = document.getElementById(targetId);
        if (input) {
          const isPassword = input.type === "password";
          input.type = isPassword ? "text" : "password";
          btn.classList.toggle("active", isPassword);
        }
      },
    },
  };

  // Initialize interactive event listeners
  document.addEventListener("DOMContentLoaded", function () {
    // Restore sidebar state & theme UI
    Core.sidebar.init();
    Core.theme.init();
    Core.authSession.initWatcher();

    // Theme toggle button
    document.querySelectorAll("[data-theme-toggle]").forEach(function (btn) {
      btn.addEventListener("click", function (e) {
        e.preventDefault();
        Core.theme.toggle();
      });
    });

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

    // Auth Method Switcher (Password vs OTP)
    document.querySelectorAll("[data-auth-method]").forEach(function (btn) {
      btn.addEventListener("click", function (e) {
        e.preventDefault();
        const method = btn.getAttribute("data-auth-method");
        Core.auth.switchMethod(method);
      });
    });

    // Legacy Auth Tab Switcher
    document.querySelectorAll("[data-auth-tab]").forEach(function (btn) {
      btn.addEventListener("click", function (e) {
        e.preventDefault();
        const tab = btn.getAttribute("data-auth-tab");
        Core.auth.switchTab(tab);
      });
    });

    // Username Card Tab Switcher
    document.querySelectorAll("[data-username-tab]").forEach(function (btn) {
      btn.addEventListener("click", function (e) {
        e.preventDefault();
        const tab = btn.getAttribute("data-username-tab");
        Core.auth.switchUsernameTab(tab);
      });
    });

    // OTP Card Tab Switcher
    document.querySelectorAll("[data-otp-tab]").forEach(function (btn) {
      btn.addEventListener("click", function (e) {
        e.preventDefault();
        const tab = btn.getAttribute("data-otp-tab");
        Core.auth.switchOTPTab(tab);
      });
    });

    // Password Visibility Toggle
    document.querySelectorAll("[data-password-toggle]").forEach(function (btn) {
      btn.addEventListener("click", function (e) {
        e.preventDefault();
        Core.auth.togglePassword(btn);
      });
    });

    // Validation Helpers
    function isValidPhone(value) {
      const digits = (value || "").replace(/\D/g, "");
      return digits.length >= 10;
    }

    function isValidEmail(value) {
      return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test((value || "").trim());
    }

    function isValidIdentifier(value, allowEmail) {
      const trimmed = (value || "").trim();
      if (allowEmail && trimmed.includes("@")) {
        return isValidEmail(trimmed);
      }
      return isValidPhone(trimmed);
    }

    // Keep OTP challenge hidden until valid 10-digit phone or valid email is entered
    const loginIdentifierInput = document.getElementById("otp_login_identifier");
    const loginSendBtn = document.getElementById("btn_send_login_otp");
    const loginChallenge = document.getElementById("otp_challenge_wrapper");

    function checkLoginIdentifier() {
      if (!loginIdentifierInput || loginIdentifierInput.readOnly) return;
      const valid = isValidIdentifier(loginIdentifierInput.value, true);
      if (valid) {
        if (loginChallenge) loginChallenge.style.display = "block";
        if (loginSendBtn) loginSendBtn.disabled = false;
      } else {
        if (loginChallenge) loginChallenge.style.display = "none";
        if (loginSendBtn) loginSendBtn.disabled = true;
      }
    }

    if (loginIdentifierInput) {
      loginIdentifierInput.addEventListener("input", checkLoginIdentifier);
      loginIdentifierInput.addEventListener("change", checkLoginIdentifier);
      checkLoginIdentifier();
    }

    const signupPhoneInput = document.getElementById("otp_signup_phone");
    const signupSendBtn = document.getElementById("btn_send_signup_otp");
    const signupChallenge = document.getElementById("otp_signup_challenge_wrapper");

    function checkSignupPhone() {
      if (!signupPhoneInput || signupPhoneInput.readOnly) return;
      const valid = isValidPhone(signupPhoneInput.value);
      if (signupSendBtn) signupSendBtn.disabled = !valid;
    }

    if (signupPhoneInput) {
      signupPhoneInput.addEventListener("input", checkSignupPhone);
      signupPhoneInput.addEventListener("change", checkSignupPhone);
      checkSignupPhone();
    }

    // Send OTP Buttons
    document.querySelectorAll("[data-action-send-otp]").forEach(function (btn) {
      btn.addEventListener("click", async function (e) {
        e.preventDefault();
        const targetSelector = btn.getAttribute("data-target-input");
        const targetInput = document.querySelector(targetSelector);
        if (!targetInput || !targetInput.value.trim()) {
          Core.auth.showToast("Please enter a valid phone number or email address.");
          return;
        }

        const identifier = targetInput.value.trim();
        const channel = identifier.includes("@") ? "email" : "phone";
        const form = btn.closest("form");
        const isSignup = form && form.id === "form_otp_signup";
        const purpose = isSignup ? "signup" : "login";

        btn.disabled = true;
        btn.textContent = "Sending...";

        try {
          const res = await fetch("/api/users/v1/auth/otp/send/", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              "X-CSRFToken": Core.getCSRFToken(),
            },
            body: JSON.stringify({ identifier: identifier, channel: channel, purpose: purpose }),
          });
          const data = await res.json();

          if (res.ok) {
            Core.auth.showToast("Verification code dispatched successfully.", "success");
            targetInput.readOnly = true;
            targetInput.classList.add("form-input-readonly");
            btn.textContent = "Sent";
            btn.disabled = true;

            // Ensure challenge section for this form is visible and focused
            const challenge = form
              ? (form.querySelector("#otp_challenge_wrapper") || form.querySelector("#otp_signup_challenge_wrapper"))
              : null;
            if (challenge) {
              challenge.style.display = "block";
              const firstBox = challenge.querySelector("[data-otp-box]");
              if (firstBox) firstBox.focus();
            }
          } else {
            Core.auth.showToast(data.detail || data.identifier || "Failed to dispatch verification code.");
            btn.disabled = false;
            btn.textContent = "Send Code";
          }
        } catch (err) {
          Core.auth.showToast("Network error. Please try again.");
          btn.disabled = false;
          btn.textContent = "Send Code";
        }
      });
    });

    // OTP Box auto-advance, backspace navigation, clipboard paste, and submit enablement
    document.querySelectorAll("[data-otp-group]").forEach(function (group) {
      const boxes = Array.from(group.querySelectorAll("[data-otp-box]"));
      const hiddenInput = group.querySelector('input[type="hidden"]');
      const submitBtn = document.getElementById("btn_otp_submit") ||
                        document.getElementById("btn_otp_signup_submit");

      function syncOTP() {
        const val = boxes.map(function (b) { return b.value; }).join("");
        if (hiddenInput) {
          hiddenInput.value = val;
        }
        if (submitBtn) {
          submitBtn.disabled = val.length < boxes.length;
        }
      }

      // Clipboard suggestion on clicking first OTP box
      if (boxes.length > 0) {
        boxes[0].addEventListener("click", async function () {
          if (!boxes[0].value && navigator.clipboard && navigator.clipboard.readText) {
            try {
              const clipText = await navigator.clipboard.readText();
              const clean = clipText.trim().replace(/\D/g, "");
              if (clean.length === boxes.length) {
                clean.split("").forEach(function (char, i) {
                  boxes[i].value = char;
                });
                syncOTP();
                boxes[boxes.length - 1].focus();
              }
            } catch (e) {
              // Clipboard permission denied or unsupported
            }
          }
        });
      }

      boxes.forEach(function (box, idx) {
        box.addEventListener("input", function () {
          if (box.value.length >= 1 && idx < boxes.length - 1) {
            boxes[idx + 1].focus();
            boxes[idx + 1].select();
          }
          syncOTP();
        });

        box.addEventListener("keydown", function (e) {
          if (e.key === "Backspace" && !box.value && idx > 0) {
            boxes[idx - 1].focus();
            boxes[idx - 1].select();
          }
        });
      });
    });

    // Form submission handlers for Username and OTP forms
    const usernameForm = document.getElementById("form_username_login");
    if (usernameForm) {
      usernameForm.addEventListener("submit", async function (e) {
        e.preventDefault();
        const submitBtn = document.getElementById("btn_username_submit");
        if (submitBtn) submitBtn.disabled = true;

        const formData = new FormData(usernameForm);
        const payload = Object.fromEntries(formData.entries());

        try {
          const res = await fetch(usernameForm.action, {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              "X-CSRFToken": Core.getCSRFToken(),
            },
            body: JSON.stringify(payload),
          });
          const data = await res.json();

          if (res.ok) {
            if (data.access) {
              Core.authSession.setCookie("access_token", data.access, data.access_expires_in || 3600);
            }
            if (data.refresh) {
              Core.authSession.setCookie("refresh_token", data.refresh, 86400 * 7);
            }
            window.location.href = data.redirect_url || usernameForm.dataset.redirectUrl || "/";
          } else {
            Core.auth.showToast(data.detail || "Authentication failed.");
            if (typeof data.remaining_attempts !== "undefined") {
              if (data.is_locked) {
                Core.auth.setWarning("username_login_attempts_warning", "Account locked. An unlock link has been emailed to you.");
                if (submitBtn) submitBtn.disabled = true;
                return;
              } else {
                Core.auth.setWarning(
                  "username_login_attempts_warning",
                  "Warning: " + data.remaining_attempts + " remaining attempts before account lockout."
                );
              }
            }
            if (submitBtn) submitBtn.disabled = false;
          }
        } catch (err) {
          Core.auth.showToast("Network error during login. Please try again.");
          if (submitBtn) submitBtn.disabled = false;
        }
      });
    }

    const otpForm = document.getElementById("form_otp_login");
    if (otpForm) {
      otpForm.addEventListener("submit", async function (e) {
        e.preventDefault();
        const submitBtn = document.getElementById("btn_otp_submit");
        if (submitBtn) submitBtn.disabled = true;

        const identifierInput = document.getElementById("otp_login_identifier");
        const hiddenOtp = otpForm.querySelector('input[name="otp_code"]');
        const identifier = identifierInput ? identifierInput.value.trim() : "";
        const code = hiddenOtp ? hiddenOtp.value.trim() : "";
        const isEmail = identifier.includes("@");

        const phoneAction = otpForm.dataset.phoneAction || "/api/users/v1/auth/otp/phone-login/";
        const emailAction = otpForm.dataset.emailAction || "/api/users/v1/auth/otp/email-login/";
        const endpoint = isEmail ? emailAction : phoneAction;
        const payload = isEmail
          ? { email: identifier, otp_code: code }
          : { phone_number: identifier, otp_code: code };

        try {
          const res = await fetch(endpoint, {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              "X-CSRFToken": Core.getCSRFToken(),
            },
            body: JSON.stringify(payload),
          });
          const data = await res.json();

          if (res.ok) {
            if (data.access) {
              Core.authSession.setCookie("access_token", data.access, data.access_expires_in || 3600);
            }
            if (data.refresh) {
              Core.authSession.setCookie("refresh_token", data.refresh, 86400 * 7);
            }
            window.location.href = data.redirect_url || otpForm.dataset.redirectUrl || "/";
          } else {
            Core.auth.showToast(data.detail || data.otp_code || data.email || data.phone_number || "Verification failed.");
            if (typeof data.remaining_attempts !== "undefined") {
              if (data.is_locked) {
                Core.auth.setWarning("otp_login_attempts_warning", "Account locked. An unlock link has been emailed to you.");
                if (submitBtn) submitBtn.disabled = true;
                return;
              } else {
                Core.auth.setWarning(
                  "otp_login_attempts_warning",
                  "Warning: " + data.remaining_attempts + " remaining attempts before account lockout."
                );
              }
            }
            if (submitBtn) submitBtn.disabled = false;
          }
        } catch (err) {
          Core.auth.showToast("Network error during OTP verification.");
          if (submitBtn) submitBtn.disabled = false;
        }
      });
    }

    const otpSignupForm = document.getElementById("form_otp_signup");
    if (otpSignupForm) {
      otpSignupForm.addEventListener("submit", async function (e) {
        e.preventDefault();
        const submitBtn = document.getElementById("btn_otp_signup_submit");
        if (submitBtn) submitBtn.disabled = true;

        const phoneInput = document.getElementById("otp_signup_phone");
        const hiddenOtp =
          otpSignupForm.querySelector('input[name="otp_code"]') ||
          otpSignupForm.querySelector('input[name="signup_otp_code"]');
        const firstNameInput = otpSignupForm.querySelector('input[name="first_name"]');
        const lastNameInput = otpSignupForm.querySelector('input[name="last_name"]');
        const emailInput = otpSignupForm.querySelector('input[name="email"]');

        const phoneNumber = phoneInput ? phoneInput.value.trim() : "";
        const code = hiddenOtp ? hiddenOtp.value.trim() : "";
        const firstName = firstNameInput ? firstNameInput.value.trim() : "";
        const lastName = lastNameInput ? lastNameInput.value.trim() : "";
        const email = emailInput ? emailInput.value.trim() : "";

        if (!phoneNumber || !code) {
          Core.auth.showToast("Please enter phone number and 6-digit verification code.");
          if (submitBtn) submitBtn.disabled = false;
          return;
        }

        const payload = {
          first_name: firstName,
          last_name: lastName,
          phone_number: phoneNumber,
          otp_code: code,
        };
        if (email) {
          payload.email = email;
        }

        try {
          const endpoint = otpSignupForm.action || "/api/users/v1/auth/otp/phone-signup/";

          const res = await fetch(endpoint, {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              "X-CSRFToken": Core.getCSRFToken(),
            },
            body: JSON.stringify(payload),
          });
          const data = await res.json();

          if (res.ok) {
            if (data.access) {
              Core.authSession.setCookie("access_token", data.access, data.access_expires_in || 3600);
            }
            if (data.refresh) {
              Core.authSession.setCookie("refresh_token", data.refresh, 86400 * 7);
            }
            window.location.href = data.redirect_url || otpSignupForm.dataset.redirectUrl || "/";
          } else {
            const errorMsg = data.detail || data.otp_code || data.phone_number || data.email || "Signup failed.";
            Core.auth.showToast(errorMsg);
            if (submitBtn) submitBtn.disabled = false;
          }
        } catch (err) {
          Core.auth.showToast("Network error during verification. Please try again.");
          if (submitBtn) submitBtn.disabled = false;
        }
      });
    }
  });

  window.Core = Core;
})(window);
