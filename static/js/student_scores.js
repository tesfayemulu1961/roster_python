/* ==============================================
   Student Scores Management JavaScript
   ============================================== */

$(document).ready(function() {
    // Initialize DataTable
    $('#resultsTable').DataTable({
        dom: 'Blfrtip',
        buttons: [
            'copy', 'csv', 'excel', 'print',
            {
                extend: 'pdf',
                text: 'PDF',
                title: 'Student Scores Report',
                exportOptions: {
                    columns: ':visible'
                }
            }
        ],
        scrollX: true,
        pageLength: 10,
        lengthMenu: [
            [10, 25, 50, 100, -1],
            [10, 25, 50, 100, "All"]
        ],
        language: {
            lengthMenu: "Show _MENU_ entries per page",
            search: "Search:",
            paginate: {
                first: "First",
                last: "Last",
                next: "Next",
                previous: "Previous"
            },
            info: "Showing _START_ to _END_ of _TOTAL_ entries",
            infoEmpty: "Showing 0 to 0 of 0 entries",
            infoFiltered: "(filtered from _MAX_ total entries)"
        },
        columnDefs: [
            { targets: [0], orderable: false },
            { targets: '_all', className: 'dt-center' }
        ],
        initComplete: function() {
            // Customize length menu
            $('.dataTables_length').addClass('bs-select');
            $('.dataTables_length label').contents().filter(function() {
                return this.nodeType === 3;
            }).remove();
            $('.dataTables_length label').prepend('Show entries: ');
        }
    });
    
    // Auto-submit when grade changes
    $('select[name="grade"]').change(function() {
        $(this).closest('form').submit();
    });
    
    // Auto-submit when year changes
    $('select[name="year"]').change(function() {
        $(this).closest('form').submit();
    });
    
    // Auto-submit when section changes
    $('select[name="section"]').change(function() {
        $(this).closest('form').submit();
    });
    
    // Refresh button functionality
    $('.refresh-btn').click(function() {
        window.location.reload();
    });
    
    // Confirm delete
    $('.delete-btn').click(function(e) {
        if (!confirm('Are you sure you want to delete this student score?')) {
            e.preventDefault();
        }
    });
});