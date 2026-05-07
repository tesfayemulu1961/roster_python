// Student & Parent Records Page Specific JavaScript

$(document).ready(function() {
    $('#recordsTable').DataTable({
        "paging": false,
        "searching": false,
        "info": false,
        "order": [],
        "columnDefs": [
            { "orderable": false, "targets": [0, 7] }
        ]
    });
});

// Auto-submit form when academic year changes
document.addEventListener('DOMContentLoaded', function() {
    var yearSelect = document.querySelector('.academic-year-select');
    if (yearSelect) {
        yearSelect.addEventListener('change', function() {
            this.form.submit();
        });
    }
});