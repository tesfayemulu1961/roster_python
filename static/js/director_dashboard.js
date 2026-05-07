// Initialize all dropdowns
var dropdownElementList = [].slice.call(document.querySelectorAll('.dropdown-toggle'))
var dropdownList = dropdownElementList.map(function (dropdownToggleEl) {
    return new bootstrap.Dropdown(dropdownToggleEl)
});

// Handle submenu visibility on hover
document.querySelectorAll('.dropdown-submenu').forEach(function(submenu) {
    submenu.addEventListener('mouseenter', function(e) {
        var dropdown = this.querySelector('.dropdown-menu');
        if (dropdown) {
            dropdown.classList.add('show');
        }
    });
    
    submenu.addEventListener('mouseleave', function(e) {
        var dropdown = this.querySelector('.dropdown-menu');
        if (dropdown) {
            dropdown.classList.remove('show');
        }
    });
});

// Ensure parent dropdowns stay open when hovering over submenus
document.querySelectorAll('.dropdown-menu').forEach(function(menu) {
    menu.addEventListener('mouseenter', function(e) {
        this.classList.add('show');
    });
    menu.addEventListener('mouseleave', function(e) {
        this.classList.remove('show');
    });
});