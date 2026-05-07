/* ============================================
   COMMON JAVASCRIPT FOR ALL DASHBOARDS
   ============================================ */

// Wait for DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    
    // Initialize Bootstrap dropdowns
    initializeDropdowns();
    
    // Initialize tooltips if any
    initializeTooltips();
    
    // Add logout confirmation
    initializeLogoutConfirmation();
    
    // Initialize academic year filter if exists
    initializeAcademicYearFilter();
});

// Initialize all Bootstrap dropdowns
function initializeDropdowns() {
    var dropdownElementList = [].slice.call(document.querySelectorAll('.dropdown-toggle'));
    var dropdownList = dropdownElementList.map(function(dropdownToggleEl) {
        return new bootstrap.Dropdown(dropdownToggleEl);
    });
}

// Initialize tooltips
function initializeTooltips() {
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Add logout confirmation dialog
function initializeLogoutConfirmation() {
    var logoutLinks = document.querySelectorAll('a[href="/logout"], button[onclick*="logout"]');
    logoutLinks.forEach(function(link) {
        link.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to logout?')) {
                e.preventDefault();
            }
        });
    });
}

// Initialize academic year filter
function initializeAcademicYearFilter() {
    var yearSelect = document.getElementById('academicYearSelect');
    if (yearSelect) {
        yearSelect.addEventListener('change', function() {
            window.location.href = '?ec_year=' + this.value;
        });
    }
}

// Show notification message
function showNotification(message, type) {
    var notification = document.createElement('div');
    notification.className = 'alert alert-' + type;
    notification.innerHTML = message;
    notification.style.position = 'fixed';
    notification.style.top = '80px';
    notification.style.right = '20px';
    notification.style.zIndex = '9999';
    notification.style.minWidth = '300px';
    document.body.appendChild(notification);
    
    setTimeout(function() {
        notification.style.opacity = '0';
        setTimeout(function() {
            notification.remove();
        }, 500);
    }, 3000);
}

// Format number with commas
function formatNumber(num) {
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}