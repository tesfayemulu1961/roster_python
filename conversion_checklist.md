# PHP to Python Conversion Checklist

## For Each Converted File, Verify:

### Structure ✓
- [ ] Imports Flask Blueprint
- [ ] Creates blueprint with proper url_prefix
- [ ] Has login_required decorator
- [ ] Uses @blueprint.route (not @app.route)

### Database ✓
- [ ] Uses cursor.execute() for queries
- [ ] Uses parameterized queries (%s placeholders)
- [ ] Closes cursor and connection properly
- [ ] Handles exceptions with try/except

### HTML/CSS/JS ✓
- [ ] No large internal CSS blocks
- [ ] Links to /static/css/core.css
- [ ] Links to /static/js/core.js
- [ ] Uses Bootstrap classes
- [ ] Responsive design

### Functionality ✓
- [ ] GET requests show forms/data
- [ ] POST requests process data
- [ ] Shows success/error messages
- [ ] Redirects properly after actions
- [ ] Session validation works

### Director Module Check List
- [ ] director_dashboard.py
- [ ] student_statistics.py
- [ ] teacher_category.py
- [ ] active_sections.py
- [ ] insert_grade.py
- [ ] view_grade.py
- [ ] insert_section.py
- [ ] view_section.py
- [ ] insert_student_parent.py
- [ ] view_student_parent_paginated.py
- [ ] insert_teacher.py
- [ ] view_teacher.py
- [ ] insert_teacher_assignment.py
- [ ] view_teacher_assignment.py
- [ ] insert_users.py
- [ ] view_users.py
- [ ] excel_import.py
- [ ] report_card.py

### Room Teacher Modules
- [ ] grade_1A_rt_dashboard.py
- [ ] grade_1B_rt_dashboard.py
- [ ] grade_2A_rt_dashboard.py
- [ ] grade_2B_rt_dashboard.py
- [ ] grade_3A_rt_dashboard.py
- [ ] grade_3B_rt_dashboard.py
- [ ] grade_4A_rt_dashboard.py
- [ ] grade_4B_rt_dashboard.py
- [ ] grade_5A_rt_dashboard.py
- [ ] grade_5B_rt_dashboard.py
- [ ] grade_6A_rt_dashboard.py
- [ ] grade_6B_rt_dashboard.py
- [ ] grade_7A_rt_dashboard.py
- [ ] grade_7B_rt_dashboard.py
- [ ] grade_8A_rt_dashboard.py
- [ ] grade_8B_rt_dashboard.py