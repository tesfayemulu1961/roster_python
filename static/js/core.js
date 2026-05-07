// Core JavaScript for School Management System 
 
document.addEventListener('DOMContentLoaded', function() { 
    var logoutBtns = document.querySelectorAll('.logout-btn, a[href="/logout"]'); 
    logoutBtns.forEach(function(btn) { 
        btn.addEventListener('click', function(e) { 
            if (!confirm('Are you sure you want to logout?')) { 
                e.preventDefault(); 
            } 
        }); 
    }); 
 
    var yearSelect = document.getElementById('academicYearSelect'); 
    if (yearSelect) { 
        yearSelect.addEventListener('change', function() { 
            window.location.href = '?ec_year=' + this.value; 
        }); 
    } 
}); 
 
function showNotification(message, type) { 
    var notification = document.createElement('div'); 
    notification.className = 'alert alert-' + type; 
    notification.innerHTML = message; 
    notification.style.cssText = 'position:fixed;top:80px;right:20px;z-index:9999;min-width:300px;'; 
    document.body.appendChild(notification); 
    setTimeout(function() { 
        notification.remove(); 
    }, 3000); 
} 
