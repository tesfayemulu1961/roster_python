/* ==============================================
   Student Average Scores Management JavaScript
   ============================================== */

$(document).ready(function() {
    // Initialize DataTable with proper styling
    if ($('#studentTable').length) {
        $('#studentTable').DataTable({
            dom: 'Bfrtip',
            buttons: [
                'copy', 'csv', 'excel', 'print',
                {
                    extend: 'pdf',
                    text: 'PDF',
                    title: 'Student Average Report',
                    exportOptions: {
                        columns: ':visible'
                    }
                }
            ],
            paging: false,
            searching: false,
            info: false,
            responsive: false,  // Changed to false to prevent automatic column hiding
            scrollX: true,       // Enable horizontal scroll instead
            autoWidth: false,    // Prevent automatic width adjustment
            columnDefs: [
                { targets: 2, width: '200px' },  // Name column width
                { targets: '_all', className: 'dt-center' }
            ],
            language: {
                search: "Search:",
                lengthMenu: "Show _MENU_ entries",
                info: "Showing _START_ to _END_ of _TOTAL_ entries",
                infoEmpty: "Showing 0 to 0 of 0 entries",
                infoFiltered: "(filtered from _MAX_ total entries)",
                paginate: {
                    first: "First",
                    last: "Last",
                    next: "Next",
                    previous: "Previous"
                }
            }
        });
        
        // Add custom styling for DataTable buttons
        $('.dt-buttons').addClass('mb-3');
        $('.buttons-copy, .buttons-csv, .buttons-excel, .buttons-print, .buttons-pdf').addClass('btn btn-sm btn-primary me-1');
    }
    
    // Auto-submit when grade changes
    $('select[name="grade"]').change(function() {
        $(this).closest('form').submit();
    });
    
    // Auto-submit when year changes
    $('select[name="year"]').change(function() {
        $(this).closest('form').submit();
    });
    
    // Search functionality
    $('.search-btn').click(function() {
        $(this).closest('form').submit();
    });
    
    // Clear search
    $('.clear-search').click(function() {
        $(this).closest('form').find('input[name="search"]').val('');
        $(this).closest('form').submit();
    });
    
    // Refresh page
    $('.refresh-btn').click(function() {
        window.location.reload();
    });
    
    // Export to CSV
    $('.export-csv').click(function(e) {
        e.preventDefault();
        window.location.href = $(this).attr('href');
    });
    
    // Style null values and low scores
    $('.null-value').css({
        'color': '#dc3545',
        'font-style': 'italic'
    });
    
    $('.low-score').css({
        'color': '#dc3545',
        'font-weight': 'bold'
    });
});