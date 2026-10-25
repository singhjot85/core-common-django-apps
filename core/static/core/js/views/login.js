/**
 * login.js: Form submission handlers for username and OTP login/signup.
 */
(function (window) {
  "use strict";

  const Core = window.Core || {};

  document.addEventListener("DOMContentLoaded", function () {
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
              "X-CSRFToken": Core.getCSRFToken ? Core.getCSRFToken() : "",
            },
            body: JSON.stringify(payload),
          });
          const data = await res.json();

          if (res.ok) {
            if (data.access && Core.authSession) {
              Core.authSession.setCookie("access_token", data.access, data.access_expires_in || 3600);
            }
            if (data.refresh && Core.authSession) {
              Core.authSession.setCookie("refresh_token", data.refresh, 86400 * 7);
            }
            window.location.href = data.redirect_url || usernameForm.dataset.redirectUrl || "/";
          } else {
            if (Core.auth && Core.auth.showToast) {
              Core.auth.showToast(data.detail || "Authentication failed.");
            }
            if (typeof data.remaining_attempts !== "undefined" && Core.auth && Core.auth.setWarning) {
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
          if (Core.auth && Core.auth.showToast) {
            Core.auth.showToast("Network error during login. Please try again.");
          }
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
        const channel = identifier.includes("@") ? "email" : "phone";

        try {
          const res = await fetch(otpForm.action, {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              "X-CSRFToken": Core.getCSRFToken ? Core.getCSRFToken() : "",
            },
            body: JSON.stringify({ identifier: identifier, code: code, channel: channel }),
          });
          const data = await res.json();

          if (res.ok) {
            if (data.access && Core.authSession) {
              Core.authSession.setCookie("access_token", data.access, data.access_expires_in || 3600);
            }
            if (data.refresh && Core.authSession) {
              Core.authSession.setCookie("refresh_token", data.refresh, 86400 * 7);
            }
            window.location.href = data.redirect_url || otpForm.dataset.redirectUrl || "/";
          } else {
            if (Core.auth && Core.auth.showToast) {
              Core.auth.showToast(data.detail || data.code || "Verification failed.");
            }
            if (typeof data.remaining_attempts !== "undefined" && Core.auth && Core.auth.setWarning) {
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
          if (Core.auth && Core.auth.showToast) {
            Core.auth.showToast("Network error during OTP verification.");
          }
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
          otpSignupForm.querySelector('input[name="signup_otp_code"]') ||
          otpSignupForm.querySelector('input[name="otp_code"]');
        const identifier = phoneInput ? phoneInput.value.trim() : "";
        const code = hiddenOtp ? hiddenOtp.value.trim() : "";
        const channel = identifier.includes("@") ? "email" : "phone";

        if (!identifier || !code) {
          if (Core.auth && Core.auth.showToast) {
            Core.auth.showToast("Please enter phone number and 6-digit verification code.");
          }
          if (submitBtn) submitBtn.disabled = false;
          return;
        }

        try {
          const actionAttr = otpSignupForm.getAttribute("action");
          const endpoint =
            actionAttr && !actionAttr.endsWith("/auth/signup/")
              ? actionAttr
              : "/api/users/v1/auth/otp/verify/";

          const res = await fetch(endpoint, {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              "X-CSRFToken": Core.getCSRFToken ? Core.getCSRFToken() : "",
            },
            body: JSON.stringify({ identifier: identifier, code: code, channel: channel }),
          });
          const data = await res.json();

          if (res.ok) {
            if (data.access && Core.authSession) {
              Core.authSession.setCookie("access_token", data.access, data.access_expires_in || 3600);
            }
            if (data.refresh && Core.authSession) {
              Core.authSession.setCookie("refresh_token", data.refresh, 86400 * 7);
            }
            window.location.href = data.redirect_url || otpSignupForm.dataset.redirectUrl || "/";
          } else {
            if (Core.auth && Core.auth.showToast) {
              Core.auth.showToast(data.detail || data.code || "Verification failed.");
            }
            if (submitBtn) submitBtn.disabled = false;
          }
        } catch (err) {
          if (Core.auth && Core.auth.showToast) {
            Core.auth.showToast("Network error during verification. Please try again.");
          }
          if (submitBtn) submitBtn.disabled = false;
        }
      });
    }
  });

  window.Core = Core;
})(window);
