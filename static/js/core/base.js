/* ============================================
   BASE JAVASCRIPT - Shared by ALL Dashboards
   ============================================ */

// Wait for DOM to load
document.addEventListener('DOMContentLoaded', function() {
    initDropdowns();
    initTooltips();
    initLogoutConfirmation();
    initYearFilter();
    initSidebarToggle();
});

// Initialize Bootstrap dropdowns
function initDropdowns() {
    var dropdowns = [].slice.call(document.querySelectorAll('.dropdown-toggle'));
    dropdowns.forEach(function(dropdown) {
        new bootstrap.Dropdown(dropdown);
    });
}

// Initialize tooltips
function initTooltips() {
    var tooltips = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltips.forEach(function(tooltip) {
        new bootstrap.Tooltip(tooltip);
    });
}

// Logout confirmation
function initLogoutConfirmation() {
    var logoutBtns = document.querySelectorAll('.logout-btn, a[href="/logout"]');
    logoutBtns.forEach(function(btn) {
        btn.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to logout?')) {
                e.preventDefault();
            }
        });
    });
}

// Academic year filter
function initYearFilter() {
    var yearSelect = document.getElementById('academicYearSelect');
    if (yearSelect) {
        yearSelect.addEventListener('change', function() {
            window.location.href = '?ec_year=' + this.value;
        });
    }
}

// Sidebar toggle for mobile
function initSidebarToggle() {
    var toggleBtn = document.querySelector('.sidebar-toggle');
    var sidebar = document.querySelector('.sidebar');
    if (toggleBtn && sidebar) {
        toggleBtn.addEventListener('click', function() {
            sidebar.classList.toggle('open');
        });
    }
}

// Show notification
function showNotification(message, type) {
    var notification = document.createElement('div');
    notification.className = `alert alert-${type} notification`;
    notification.innerHTML = message;
    notification.style.cssText = `
        position: fixed;
        top: 80px;
        right: 20px;
        z-index: 9999;
        min-width: 300px;
        animation: slideIn 0.3s ease;
    `;
    document.body.appendChild(notification);
    
    setTimeout(function() {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(function() {
            notification.remove();
        }, 300);
    }, 3000);
}

// Format number with commas
function formatNumber(num) {
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

// Loading spinner
function showLoading(elementId) {
    var element = document.getElementById(elementId);
    if (element) {
        var spinner = document.createElement('div');
        spinner.className = 'spinner-border text-primary';
        spinner.setAttribute('role', 'status');
        element.style.opacity = '0.5';
        element.appendChild(spinner);
    }
}

function hideLoading(elementId) {
    var element = document.getElementById(elementId);
    if (element) {
        element.style.opacity = '1';
        var spinner = element.querySelector('.spinner-border');
        if (spinner) spinner.remove();
    }
}