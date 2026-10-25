/**
 * otp_input.js: OTP challenge input, live validation, dispatch, and auto-advance.
 */
(function (window) {
  "use strict";

  const Core = window.Core || {};

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

  document.addEventListener("DOMContentLoaded", function () {
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
      if (valid) {
        if (signupChallenge) signupChallenge.style.display = "block";
        if (signupSendBtn) signupSendBtn.disabled = false;
      } else {
        if (signupChallenge) signupChallenge.style.display = "none";
        if (signupSendBtn) signupSendBtn.disabled = true;
      }
    }

    if (signupPhoneInput) {
      signupPhoneInput.addEventListener("input", checkSignupPhone);
      signupPhoneInput.addEventListener("change", checkSignupPhone);
      checkSignupPhone();
    }

    document.querySelectorAll("[data-action-send-otp]").forEach(function (btn) {
      btn.addEventListener("click", async function (e) {
        e.preventDefault();
        const targetSelector = btn.getAttribute("data-target-input");
        const targetInput = document.querySelector(targetSelector);
        if (!targetInput || !targetInput.value.trim()) {
          if (Core.auth && Core.auth.showToast) {
            Core.auth.showToast("Please enter a valid phone number or email address.");
          }
          return;
        }

        const identifier = targetInput.value.trim();
        const channel = identifier.includes("@") ? "email" : "phone";

        // Resolve purpose from button data-purpose or parent form
        const form = btn.closest("form");
        const purpose =
          btn.getAttribute("data-purpose") ||
          (form && (form.id === "form_otp_signup" || form.getAttribute("data-auth-api") === "otp-signup")
            ? "signup"
            : "login");

        btn.disabled = true;
        btn.textContent = "Sending...";

        try {
          const res = await fetch("/api/users/v1/auth/otp/send/", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              "X-CSRFToken": Core.getCSRFToken ? Core.getCSRFToken() : "",
            },
            body: JSON.stringify({ identifier: identifier, channel: channel, purpose: purpose }),
          });
          const data = await res.json();

          if (res.ok) {
            if (Core.auth && Core.auth.showToast) {
              Core.auth.showToast("Verification code dispatched successfully.", "success");
            }
            targetInput.readOnly = true;
            targetInput.classList.add("form-input-readonly");
            btn.textContent = "Sent";
            btn.disabled = true;

            const form = btn.closest("form");
            const challenge = form
              ? (form.querySelector("#otp_challenge_wrapper") || form.querySelector("#otp_signup_challenge_wrapper"))
              : null;
            if (challenge) {
              challenge.style.display = "block";
              const firstBox = challenge.querySelector("[data-otp-box]");
              if (firstBox) firstBox.focus();
            }
          } else {
            if (Core.auth && Core.auth.showToast) {
              Core.auth.showToast(data.detail || data.identifier || "Failed to dispatch verification code.");
            }
            btn.disabled = false;
            btn.textContent = "Send Code";
          }
        } catch (err) {
          if (Core.auth && Core.auth.showToast) {
            Core.auth.showToast("Network error. Please try again.");
          }
          btn.disabled = false;
          btn.textContent = "Send Code";
        }
      });
    });

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
            } catch (e) {}
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
  });

  window.Core = Core;
})(window);
