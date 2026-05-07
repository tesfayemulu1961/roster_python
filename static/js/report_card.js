/* ==============================================
   Report Card JavaScript
   ============================================== */

$(document).ready(function() {
    // Auto-submit on dropdown change (optional)
    $('select[name="student_id"]').change(function() {
        if ($(this).val()) {
            $(this).closest('form').submit();
        }
    });
    
    // Print functionality
    $('.print-btn').click(function() {
        window.print();
    });
});