/**
 * session_sync.js: Client-side session and JWT synchronization for core framework.
 */
(function () {
    "use strict";

    function syncJWTSession() {
        try {
            var body = document.body;
            var isAuthenticated = body && body.dataset.authenticated === "true";

            if (!isAuthenticated) {
                var match = document.cookie.match(/(?:^|;\s*)access_token=([^;]*)/);
                if (match && match[1]) {
                    if (!sessionStorage.getItem("jwt_auth_synced")) {
                        sessionStorage.setItem("jwt_auth_synced", "1");
                        window.location.reload();
                    }
                } else {
                    sessionStorage.removeItem("jwt_auth_synced");
                }
            } else {
                sessionStorage.removeItem("jwt_auth_synced");
            }
        } catch (e) {}
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", syncJWTSession);
    } else {
        syncJWTSession();
    }
})();
