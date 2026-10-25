/**
 * modal.js: Modal dialog open, close, and backdrop dismissal component.
 */
(function (window) {
  "use strict";

  const Core = window.Core || {};

  Core.modal = {
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
  };

  document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll("[data-modal-target]").forEach(function (btn) {
      btn.addEventListener("click", function (e) {
        e.preventDefault();
        const targetId = btn.getAttribute("data-modal-target");
        Core.modal.open(targetId);
      });
    });

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
