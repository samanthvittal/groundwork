/**
 * Groundwork App JavaScript
 * Handles theme toggle, dropdowns, sidebar, and HTMX configuration
 */

// Theme Management
const ThemeManager = {
  init() {
    const saved = localStorage.getItem('theme') || 'system';
    this.apply(saved);
    this.bindToggle();
  },

  apply(theme) {
    const root = document.documentElement;
    if (theme === 'system') {
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      root.setAttribute('data-theme', prefersDark ? 'dark' : 'light');
    } else {
      root.setAttribute('data-theme', theme);
    }
    localStorage.setItem('theme', theme);
    this.updateIcon(theme);
  },

  updateIcon(theme) {
    const icon = document.querySelector('[data-theme-icon]');
    if (!icon) return;
    const isDark = theme === 'dark' ||
      (theme === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches);
    icon.innerHTML = isDark ? '☀️' : '🌙';
  },

  bindToggle() {
    document.addEventListener('click', (e) => {
      const toggle = e.target.closest('[data-theme-toggle]');
      if (!toggle) return;
      const current = localStorage.getItem('theme') || 'system';
      const next = current === 'light' ? 'dark' : current === 'dark' ? 'system' : 'light';
      this.apply(next);
    });
  }
};

// Dropdown Management
const DropdownManager = {
  init() {
    document.addEventListener('click', (e) => {
      const trigger = e.target.closest('[data-dropdown-trigger]');
      if (trigger) {
        e.preventDefault();
        const dropdown = trigger.closest('[data-dropdown]');
        this.toggle(dropdown);
        return;
      }
      // Close all dropdowns when clicking outside
      if (!e.target.closest('[data-dropdown]')) {
        this.closeAll();
      }
    });

    // Close on escape
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') this.closeAll();
    });
  },

  toggle(dropdown) {
    const isOpen = dropdown.classList.contains('open');
    this.closeAll();
    if (!isOpen) dropdown.classList.add('open');
  },

  closeAll() {
    document.querySelectorAll('[data-dropdown].open').forEach(d => d.classList.remove('open'));
  }
};

// Sidebar Management
const SidebarManager = {
  init() {
    document.addEventListener('click', (e) => {
      const toggle = e.target.closest('[data-sidebar-toggle]');
      if (toggle) {
        document.body.classList.toggle('sidebar-collapsed');
        localStorage.setItem('sidebar-collapsed', document.body.classList.contains('sidebar-collapsed'));
      }

      // Mobile overlay click closes sidebar
      if (e.target.closest('.sidebar-overlay')) {
        document.body.classList.remove('sidebar-open');
      }

      // Mobile menu toggle
      const mobileToggle = e.target.closest('[data-mobile-menu-toggle]');
      if (mobileToggle) {
        document.body.classList.toggle('sidebar-open');
      }
    });

    // Restore sidebar state
    if (localStorage.getItem('sidebar-collapsed') === 'true') {
      document.body.classList.add('sidebar-collapsed');
    }

    // Close mobile sidebar on escape
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        document.body.classList.remove('sidebar-open');
      }
    });
  }
};

// Toast Notifications
const ToastManager = {
  container: null,

  init() {
    this.container = document.getElementById('toast-container');
    if (!this.container) {
      this.container = document.createElement('div');
      this.container.id = 'toast-container';
      this.container.className = 'toast-container';
      document.body.appendChild(this.container);
    }
  },

  show(message, type = 'info', duration = 5000) {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
      <span class="toast-message">${message}</span>
      <button class="toast-close" onclick="this.parentElement.remove()">×</button>
    `;
    this.container.appendChild(toast);

    // Auto dismiss (except errors)
    if (type !== 'error' && duration > 0) {
      setTimeout(() => toast.remove(), duration);
    }

    return toast;
  }
};

// Flash Message Handler (for HTMX responses)
const FlashHandler = {
  init() {
    document.body.addEventListener('htmx:afterSwap', (e) => {
      // Check for flash messages in response headers
      const flash = e.detail.xhr.getResponseHeader('X-Flash-Message');
      const flashType = e.detail.xhr.getResponseHeader('X-Flash-Type') || 'info';
      if (flash) {
        ToastManager.show(decodeURIComponent(flash), flashType);
      }
    });
  }
};

// Password Visibility Toggle
const PasswordToggle = {
  init() {
    document.addEventListener('click', (e) => {
      const toggle = e.target.closest('[data-password-toggle]');
      if (!toggle) return;
      const input = toggle.closest('.input-group').querySelector('input');
      const isPassword = input.type === 'password';
      input.type = isPassword ? 'text' : 'password';
      toggle.textContent = isPassword ? '🙈' : '👁️';
    });
  }
};

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
  ThemeManager.init();
  DropdownManager.init();
  SidebarManager.init();
  ToastManager.init();
  FlashHandler.init();
  PasswordToggle.init();
});

// HTMX Configuration
document.body.addEventListener('htmx:configRequest', (e) => {
  // Add CSRF token to all requests
  const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;
  if (csrfToken) {
    e.detail.headers['X-CSRF-Token'] = csrfToken;
  }
});

// Expose ToastManager globally for use in templates
window.Toast = ToastManager;
