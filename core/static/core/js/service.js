/**
 * Core Data & API Service Layer
 * Provides data handling and REST API integration for server-rendered components.
 */

(function (window) {
  "use strict";

  const listeners = {};

  const EventBus = {
    on: function (event, callback) {
      if (!listeners[event]) {
        listeners[event] = [];
      }
      listeners[event].push(callback);
    },
    off: function (event, callback) {
      if (!listeners[event]) return;
      listeners[event] = listeners[event].filter(cb => cb !== callback);
    },
    emit: function (event, data) {
      if (!listeners[event]) return;
      listeners[event].forEach(cb => {
        try {
          cb(data);
        } catch (e) {
          console.error("Event error:", e);
        }
      });
    },
  };

  const DataService = {
    events: EventBus,

    /**
     * Initial application configuration (sidebar, tenant, permissions)
     */
    config: {
      getInitialConfig: async function () {
        try {
          return await window.Core.api.get("/api/config/");
        } catch (e) {
          console.warn("Using fallback client configuration", e);
          return {
            sidebar_links: [
              { title: "Home", href: "/", icon: "home", is_active: true },
              { title: "Customers", href: "/crm/", icon: "groups" },
              { title: "Organizations", href: "/tenants/", icon: "domain" },
              { title: "Invoices", href: "/invoices/", icon: "receipt_long" },
            ],
            unread_notifications: 0,
          };
        }
      },
    },

    /**
     * CRM Customers Data Operations
     */
    crm: {
      listCustomers: async function (params = {}) {
        const query = new URLSearchParams(params).toString();
        const url = `/api/crm/customers/${query ? "?" + query : ""}`;
        return await window.Core.api.get(url);
      },
      getCustomer: async function (id) {
        return await window.Core.api.get(`/api/crm/customers/${id}/`);
      },
      createCustomer: async function (data) {
        const res = await window.Core.api.post("/api/crm/customers/", data);
        EventBus.emit("customer:created", res);
        return res;
      },
      updateCustomer: async function (id, data) {
        const res = await window.Core.api.patch(`/api/crm/customers/${id}/`, data);
        EventBus.emit("customer:updated", res);
        return res;
      },
      deleteCustomer: async function (id) {
        const res = await window.Core.api.delete(`/api/crm/customers/${id}/`);
        EventBus.emit("customer:deleted", { id });
        return res;
      },
    },

    /**
     * Tenant / Organization Operations
     */
    tenants: {
      listTenants: async function (params = {}) {
        const query = new URLSearchParams(params).toString();
        const url = `/api/tenants/${query ? "?" + query : ""}`;
        return await window.Core.api.get(url);
      },
      getTenant: async function (id) {
        return await window.Core.api.get(`/api/tenants/${id}/`);
      },
      createTenant: async function (data) {
        const res = await window.Core.api.post("/api/tenants/", data);
        EventBus.emit("tenant:created", res);
        return res;
      },
    },

    /**
     * Invoices Operations
     */
    invoices: {
      listInvoices: async function (params = {}) {
        const query = new URLSearchParams(params).toString();
        const url = `/api/invoices/${query ? "?" + query : ""}`;
        return await window.Core.api.get(url);
      },
      getInvoice: async function (id) {
        return await window.Core.api.get(`/api/invoices/${id}/`);
      },
    },
  };

  window.DataService = DataService;
})(window);
