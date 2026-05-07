# ==============================================
# View Teachers - Complete Python Conversion
# ==============================================

from flask import Blueprint, render_template_string, session, redirect, request
from functools import wraps
import mysql.connector
import math

director_view_teacher = Blueprint('director_view_teacher', __name__, url_prefix='/director')

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect('/login')
        if session.get('user_type') != 'director':
            return redirect('/unauthorized')
        return f(*args, **kwargs)
    return decorated_function

db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'roster'
}

def get_db():
    return mysql.connector.connect(**db_config)

@director_view_teacher.route('/view_teacher')
@login_required
def view_teacher_page():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    page     = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 15, type=int)
    search   = request.args.get('search', '', type=str)
    offset   = (page - 1) * per_page

    where_clause = "1=1"
    params = []
    if search:
        where_clause = "(name LIKE %s OR t_id LIKE %s OR phone LIKE %s)"
        search_param = f"%{search}%"
        params.extend([search_param, search_param, search_param])

    cursor.execute(f"SELECT COUNT(*) as total FROM teacher WHERE {where_clause}", params)
    total_count = cursor.fetchone()['total']
    total_pages = math.ceil(total_count / per_page) if total_count > 0 else 1

    cursor.execute(f"""
        SELECT * FROM teacher
        WHERE {where_clause}
        ORDER BY id DESC
        LIMIT %s OFFSET %s
    """, params + [per_page, offset])
    teachers = cursor.fetchall()

    # Fetch column names so the profile panel can show all available fields
    cursor.execute("SHOW COLUMNS FROM teacher")
    all_columns = [row['Field'] for row in cursor.fetchall()]

    cursor.close()
    conn.close()

    # Pagination window
    max_visible = 5
    half        = max_visible // 2
    start_page  = max(1, page - half)
    end_page    = min(total_pages, start_page + max_visible - 1)
    if end_page - start_page + 1 < max_visible:
        start_page = max(1, end_page - max_visible + 1)
    page_range  = range(start_page, end_page + 1)

    start_show = offset + 1 if total_count > 0 else 0
    end_show   = min(offset + per_page, total_count)

    # Serialise teachers to JSON for the JS profile panel
    import json
    from datetime import date, datetime

    def serialise(v):
        if v is None:
            return None
        if isinstance(v, (date, datetime)):
            return str(v)
        if isinstance(v, bytes):
            # BIT / BLOB columns — decode if text, else drop
            try:
                return v.decode('utf-8')
            except Exception:
                return None
        try:
            import decimal
            if isinstance(v, decimal.Decimal):
                return float(v)
        except Exception:
            pass
        # Anything else that isn't a plain JSON type → stringify
        if not isinstance(v, (int, float, str, bool, list, dict)):
            return str(v)
        return v

    teachers_json = json.dumps([
        {k: serialise(v) for k, v in t.items()} for t in teachers
    ])

    return render_template_string(TEMPLATE,
        teachers=teachers,
        teachers_json=teachers_json,
        all_columns=all_columns,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
        total_count=total_count,
        start_show=start_show,
        end_show=end_show,
        page_range=page_range,
        search=search,
    )


TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Teachers</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600&family=DM+Mono:wght@400;500&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="/static/css/core.css">
    <style>
        :root {
            --primary:       #2563eb;
            --primary-light: #eff6ff;
            --primary-mid:   #bfdbfe;
            --success:       #16a34a;
            --success-bg:    #f0fdf4;
            --danger:        #dc2626;
            --danger-bg:     #fff1f2;
            --danger-border: #fecaca;
            --muted:         #64748b;
            --border:        #e2e8f0;
            --surface:       #ffffff;
            --bg:            #f8fafc;
            --text:          #0f172a;
            --radius:        8px;
        }
        *, *::before, *::after { box-sizing: border-box; }
        body {
            background: var(--bg);
            font-family: 'DM Sans', sans-serif;
            color: var(--text);
            font-size: 14px;
            margin: 0;
        }

        /* ── Page header ── */
        .page-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 20px 0 16px;
            border-bottom: 1px solid var(--border);
            margin-bottom: 20px;
        }
        .page-title {
            font-size: 18px;
            font-weight: 600;
            letter-spacing: -.3px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .page-title i { color: var(--primary); font-size: 16px; }
        .count-pill {
            font-size: 12px; font-weight: 500;
            color: var(--muted);
            background: #f1f5f9;
            padding: 2px 8px;
            border-radius: 20px;
        }

        /* ── Buttons ── */
        .btn-add {
            background: var(--primary); color: #fff;
            border: none; border-radius: var(--radius);
            padding: 7px 16px; font-size: 13px; font-weight: 500;
            text-decoration: none;
            display: inline-flex; align-items: center; gap: 6px;
        }
        .btn-add:hover { background: #1d4ed8; color: #fff; }
        .btn-back {
            background: transparent; border: 1px solid var(--border);
            color: var(--muted); border-radius: var(--radius);
            padding: 7px 14px; font-size: 13px;
            text-decoration: none;
            display: inline-flex; align-items: center; gap: 6px;
        }
        .btn-back:hover { border-color: #94a3b8; color: var(--text); }

        /* ── Search ── */
        .search-row { display: flex; gap: 8px; margin-bottom: 16px; }
        .search-row .form-control {
            max-width: 320px; font-size: 13px;
            border-color: var(--border); border-radius: var(--radius);
            padding: 7px 12px;
        }
        .search-row .form-control:focus {
            border-color: var(--primary);
            box-shadow: 0 0 0 3px rgba(37,99,235,.1);
        }
        .btn-search {
            background: var(--primary); color: #fff;
            border: none; border-radius: var(--radius);
            padding: 7px 16px; font-size: 13px; font-weight: 500;
            cursor: pointer;
            display: inline-flex; align-items: center; gap: 6px;
        }
        .btn-search:hover { background: #1d4ed8; }
        .btn-clear {
            background: transparent; border: 1px solid var(--border);
            border-radius: var(--radius); padding: 7px 14px;
            font-size: 13px; color: var(--muted);
            cursor: pointer; text-decoration: none;
        }
        .btn-clear:hover { border-color: #94a3b8; color: var(--text); }

        /* ── Table card ── */
        .table-card {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 10px;
            overflow: hidden;
        }
        table { width: 100%; border-collapse: collapse; }
        thead th {
            background: #f1f5f9;
            font-size: 11px; font-weight: 600;
            letter-spacing: .6px; text-transform: uppercase;
            color: var(--muted);
            padding: 10px 14px;
            border-bottom: 1px solid var(--border);
            white-space: nowrap;
        }
        tbody tr {
            border-bottom: 1px solid #f1f5f9;
            transition: background .12s;
        }
        tbody tr:last-child { border-bottom: none; }
        tbody tr:hover { background: #fafbff; }
        td { padding: 10px 14px; vertical-align: middle; font-size: 13px; }

        .td-num {
            color: var(--muted);
            font-family: 'DM Mono', monospace;
            font-size: 12px; width: 40px; text-align: center;
        }
        .teacher-name { font-weight: 600; font-size: 13.5px; }
        .teacher-tid {
            font-family: 'DM Mono', monospace;
            font-size: 11px; color: var(--muted); margin-top: 1px;
        }
        .contact-line {
            display: flex; align-items: center; gap: 6px;
            color: var(--muted); font-size: 12.5px; line-height: 1.8;
        }
        .contact-line i { width: 12px; color: #94a3b8; }

        .badge-status {
            display: inline-flex; align-items: center; gap: 4px;
            padding: 3px 9px; border-radius: 20px;
            font-size: 11px; font-weight: 600; letter-spacing: .2px;
        }
        .badge-active   { background: var(--success-bg); color: var(--success); }
        .badge-inactive { background: #f1f5f9; color: var(--muted); }
        .badge-dot { width: 5px; height: 5px; border-radius: 50%; background: currentColor; }

        .btn-view {
            display: inline-flex; align-items: center; gap: 4px;
            padding: 4px 11px; border-radius: 6px;
            font-size: 12px; font-weight: 500;
            border: 1px solid var(--primary-mid);
            background: var(--primary-light); color: var(--primary);
            cursor: pointer; transition: all .15s;
        }
        .btn-view:hover { background: #dbeafe; }
        .btn-edit {
            display: inline-flex; align-items: center; gap: 4px;
            padding: 4px 11px; border-radius: 6px;
            font-size: 12px; font-weight: 500;
            border: 1px solid #fde68a;
            background: #fffbeb; color: #b45309;
            cursor: pointer; text-decoration: none; transition: all .15s;
        }
        .btn-edit:hover { background: #fef3c7; }
        .btn-del {
            display: inline-flex; align-items: center; gap: 4px;
            padding: 4px 11px; border-radius: 6px;
            font-size: 12px; font-weight: 500;
            border: 1px solid var(--danger-border);
            background: var(--danger-bg); color: var(--danger);
            cursor: pointer; text-decoration: none; transition: all .15s;
        }
        .btn-del:hover { background: #fee2e2; }

        /* ── Footer / Pagination ── */
        .table-footer {
            display: flex; align-items: center;
            justify-content: space-between;
            padding: 12px 16px;
            border-top: 1px solid var(--border);
            background: #fafbfc;
            flex-wrap: wrap; gap: 10px;
        }
        .footer-info { font-size: 12.5px; color: var(--muted); }
        .pagination { display: flex; align-items: center; gap: 4px; list-style: none; margin: 0; padding: 0; }
        .page-btn {
            display: inline-flex; align-items: center; justify-content: center;
            min-width: 30px; height: 30px; padding: 0 8px;
            border-radius: 6px; border: 1px solid var(--border);
            background: var(--surface); color: var(--text);
            font-size: 12.5px; font-weight: 500;
            text-decoration: none; transition: all .15s;
        }
        .page-btn:hover:not(.disabled):not(.active) {
            border-color: var(--primary); color: var(--primary);
            background: var(--primary-light);
        }
        .page-btn.active {
            background: var(--primary); border-color: var(--primary);
            color: #fff; pointer-events: none;
        }
        .page-btn.disabled { color: #cbd5e1; pointer-events: none; }
        .page-btn i { font-size: 11px; }

        /* ── Empty state ── */
        .empty-state { text-align: center; padding: 48px 20px; color: var(--muted); }
        .empty-state i { font-size: 32px; margin-bottom: 10px; display: block; color: #cbd5e1; }

        /* ════════════════════════════════════════
           PROFILE DRAWER
        ════════════════════════════════════════ */
        .drawer-overlay {
            position: fixed; inset: 0;
            background: rgba(15,23,42,.35);
            backdrop-filter: blur(2px);
            z-index: 1040;
            opacity: 0; pointer-events: none;
            transition: opacity .25s;
        }
        .drawer-overlay.open { opacity: 1; pointer-events: all; }

        .drawer {
            position: fixed; top: 0; right: 0;
            width: 420px; max-width: 95vw; height: 100vh;
            background: var(--surface);
            box-shadow: -8px 0 32px rgba(0,0,0,.12);
            z-index: 1050;
            display: flex; flex-direction: column;
            transform: translateX(100%);
            transition: transform .28s cubic-bezier(.4,0,.2,1);
        }
        .drawer.open { transform: translateX(0); }

        /* Drawer hero */
        .drawer-hero {
            background: linear-gradient(135deg, #1e3a5f 0%, #2563eb 100%);
            padding: 28px 24px 24px;
            position: relative;
            flex-shrink: 0;
        }
        .drawer-close {
            position: absolute; top: 14px; right: 14px;
            width: 30px; height: 30px;
            background: rgba(255,255,255,.15);
            border: none; border-radius: 50%;
            color: #fff; cursor: pointer; font-size: 13px;
            display: flex; align-items: center; justify-content: center;
            transition: background .15s;
        }
        .drawer-close:hover { background: rgba(255,255,255,.28); }

        .avatar-circle {
            width: 64px; height: 64px; border-radius: 50%;
            background: rgba(255,255,255,.18);
            border: 2px solid rgba(255,255,255,.35);
            display: flex; align-items: center; justify-content: center;
            font-size: 26px; font-weight: 700; color: #fff;
            margin-bottom: 14px;
            font-family: 'DM Sans', sans-serif;
            letter-spacing: -1px;
        }
        .drawer-name {
            font-size: 20px; font-weight: 700;
            color: #fff; letter-spacing: -.4px;
            margin-bottom: 2px;
        }
        .drawer-tid {
            font-family: 'DM Mono', monospace;
            font-size: 12px; color: rgba(255,255,255,.65);
            margin-bottom: 12px;
        }
        .drawer-status {
            display: inline-flex; align-items: center; gap: 5px;
            padding: 3px 10px; border-radius: 20px;
            font-size: 11px; font-weight: 600;
        }
        .drawer-status.active   { background: #dcfce7; color: #15803d; }
        .drawer-status.inactive { background: rgba(255,255,255,.15); color: rgba(255,255,255,.8); }

        /* Drawer body */
        .drawer-body {
            flex: 1; overflow-y: auto;
            padding: 20px 24px;
        }

        .section-label {
            font-size: 10px; font-weight: 700;
            letter-spacing: .9px; text-transform: uppercase;
            color: var(--muted);
            margin: 20px 0 10px;
            padding-bottom: 6px;
            border-bottom: 1px solid var(--border);
        }
        .section-label:first-child { margin-top: 0; }

        .info-row {
            display: flex; align-items: flex-start;
            gap: 12px; padding: 8px 0;
            border-bottom: 1px solid #f8fafc;
        }
        .info-row:last-child { border-bottom: none; }
        .info-icon {
            width: 30px; height: 30px; border-radius: 7px;
            background: var(--primary-light);
            display: flex; align-items: center; justify-content: center;
            color: var(--primary); font-size: 12px;
            flex-shrink: 0; margin-top: 1px;
        }
        .info-label {
            font-size: 11px; color: var(--muted);
            text-transform: uppercase; letter-spacing: .4px;
            margin-bottom: 1px;
        }
        .info-value {
            font-size: 13.5px; font-weight: 500;
            color: var(--text); word-break: break-word;
        }
        .info-value.mono {
            font-family: 'DM Mono', monospace;
            font-size: 12.5px;
        }
        .info-value.empty { color: #94a3b8; font-style: italic; font-weight: 400; }

        /* Drawer footer */
        .drawer-footer {
            padding: 14px 24px;
            border-top: 1px solid var(--border);
            background: #fafbfc;
            display: flex; gap: 8px;
            flex-shrink: 0;
        }
        .drawer-footer a, .drawer-footer button {
            flex: 1; padding: 9px;
            border-radius: var(--radius);
            font-size: 13px; font-weight: 500;
            display: inline-flex; align-items: center;
            justify-content: center; gap: 6px;
            cursor: pointer; text-decoration: none;
            border: none;
        }
        .df-edit { background: #fffbeb; color: #b45309; border: 1px solid #fde68a; }
        .df-edit:hover { background: #fef3c7; }
        .df-del  { background: var(--danger-bg); color: var(--danger); border: 1px solid var(--danger-border); }
        .df-del:hover { background: #fee2e2; }
    </style>
</head>
<body>
<div class="container" style="max-width:900px;">

    <!-- Header -->
    <div class="page-header">
        <div class="page-title">
            <i class="fas fa-chalkboard-teacher"></i>
            Teachers
            {% if total_count %}
                <span class="count-pill">{{ total_count }}</span>
            {% endif %}
        </div>
        <div style="display:flex;gap:8px;">
            <a href="/director/insert_teacher" class="btn-add"><i class="fas fa-plus"></i> Add Teacher</a>
            <a href="/director/director_dashboard" class="btn-back"><i class="fas fa-arrow-left"></i> Back</a>
        </div>
    </div>

    <!-- Search -->
    <form method="GET" class="search-row">
        <input type="text" name="search" class="form-control"
               placeholder="Search name, ID or phone…" value="{{ search }}">
        <input type="hidden" name="per_page" value="{{ per_page }}">
        <button type="submit" class="btn-search"><i class="fas fa-search"></i> Search</button>
        {% if search %}
            <a href="?per_page={{ per_page }}" class="btn-clear">Clear</a>
        {% endif %}
    </form>

    <!-- Table -->
    <div class="table-card">
        <table>
            <thead>
                <tr>
                    <th class="td-num">#</th>
                    <th>Teacher</th>
                    <th>Contact</th>
                    <th>Status</th>
                    <th style="text-align:right;">Actions</th>
                </tr>
            </thead>
            <tbody>
                {% for teacher in teachers %}
                <tr>
                    <td class="td-num">{{ start_show + loop.index0 }}</td>
                    <td>
                        <div class="teacher-name">{{ teacher.name }}</div>
                        <div class="teacher-tid">{{ teacher.t_id }}</div>
                    </td>
                    <td>
                        <div class="contact-line"><i class="fas fa-phone"></i>{{ teacher.phone or '—' }}</div>
                        <div class="contact-line"><i class="fas fa-envelope"></i>{{ teacher.email or '—' }}</div>
                    </td>
                    <td>
                        {% if teacher.status == 'active' %}
                            <span class="badge-status badge-active"><span class="badge-dot"></span>Active</span>
                        {% else %}
                            <span class="badge-status badge-inactive"><span class="badge-dot"></span>{{ (teacher.status or 'Inactive') | capitalize }}</span>
                        {% endif %}
                    </td>
                    <td style="text-align:right;">
                        <div style="display:flex;gap:4px;justify-content:flex-end;">
                            <button class="btn-view" onclick="openProfile({{ loop.index0 }})">
                                <i class="fas fa-id-card"></i> Profile
                            </button>
                            <a href="#" class="btn-edit"><i class="fas fa-pen"></i> Edit</a>
                            <a href="#" class="btn-del"><i class="fas fa-trash"></i></a>
                        </div>
                    </td>
                </tr>
                {% else %}
                <tr>
                    <td colspan="5">
                        <div class="empty-state">
                            <i class="fas fa-user-slash"></i>
                            No teachers found{% if search %} for "<strong>{{ search }}</strong>"{% endif %}
                        </div>
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>

        <!-- Footer -->
        <div class="table-footer">
            <div class="footer-info">
                {% if total_count > 0 %}
                    Showing <strong>{{ start_show }}</strong>–<strong>{{ end_show }}</strong>
                    of <strong>{{ total_count }}</strong> teacher{{ 's' if total_count != 1 else '' }}
                {% else %}
                    No results
                {% endif %}
            </div>
            {% if total_pages > 1 %}
            <ul class="pagination">
                {% if page > 1 %}
                <li><a class="page-btn" href="?page=1&per_page={{ per_page }}&search={{ search }}" title="First"><i class="fas fa-angle-double-left"></i></a></li>
                <li><a class="page-btn" href="?page={{ page-1 }}&per_page={{ per_page }}&search={{ search }}" title="Prev"><i class="fas fa-angle-left"></i></a></li>
                {% else %}
                <li><span class="page-btn disabled"><i class="fas fa-angle-double-left"></i></span></li>
                <li><span class="page-btn disabled"><i class="fas fa-angle-left"></i></span></li>
                {% endif %}

                {% for p in page_range %}
                    {% if p == page %}
                    <li><span class="page-btn active">{{ p }}</span></li>
                    {% else %}
                    <li><a class="page-btn" href="?page={{ p }}&per_page={{ per_page }}&search={{ search }}">{{ p }}</a></li>
                    {% endif %}
                {% endfor %}

                {% if page < total_pages %}
                <li><a class="page-btn" href="?page={{ page+1 }}&per_page={{ per_page }}&search={{ search }}" title="Next"><i class="fas fa-angle-right"></i></a></li>
                <li><a class="page-btn" href="?page={{ total_pages }}&per_page={{ per_page }}&search={{ search }}" title="Last"><i class="fas fa-angle-double-right"></i></a></li>
                {% else %}
                <li><span class="page-btn disabled"><i class="fas fa-angle-right"></i></span></li>
                <li><span class="page-btn disabled"><i class="fas fa-angle-double-right"></i></span></li>
                {% endif %}
            </ul>
            {% endif %}
        </div>
    </div>
</div>

<!-- ═══════════════════════════════════════
     PROFILE DRAWER
════════════════════════════════════════ -->
<div class="drawer-overlay" id="drawerOverlay" onclick="closeProfile()"></div>
<div class="drawer" id="profileDrawer">

    <!-- Hero -->
    <div class="drawer-hero">
        <button class="drawer-close" onclick="closeProfile()"><i class="fas fa-times"></i></button>
        <div class="avatar-circle" id="pAvatar">—</div>
        <div class="drawer-name"  id="pName">—</div>
        <div class="drawer-tid"   id="pTid">—</div>
        <span class="drawer-status" id="pStatus"></span>
    </div>

    <!-- Body -->
    <div class="drawer-body" id="drawerBody"></div>

    <!-- Footer -->
    <div class="drawer-footer">
        <a href="#" id="pEditBtn" class="df-edit"><i class="fas fa-pen"></i> Edit</a>
        <a href="#" id="pDelBtn"  class="df-del" ><i class="fas fa-trash"></i> Delete</a>
    </div>
</div>

<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
<script src="/static/js/core.js"></script>
<script>
const TEACHERS = {{ teachers_json | safe }};

// Field metadata: label, icon, section, type
const FIELD_META = {
    id:               { label:'System ID',      icon:'fa-hashtag',          section:'Identity',   type:'mono' },
    t_id:             { label:'Teacher ID',     icon:'fa-id-badge',         section:'Identity',   type:'mono' },
    name:             { label:'Full Name',      icon:'fa-user',             section:'Identity' },
    status:           { label:'Status',         icon:'fa-circle',           section:'Identity' },
    phone:            { label:'Phone',          icon:'fa-phone',            section:'Contact' },
    email:            { label:'Email',          icon:'fa-envelope',         section:'Contact' },
    address:          { label:'Address',        icon:'fa-map-marker-alt',   section:'Contact' },
    gender:           { label:'Gender',         icon:'fa-venus-mars',       section:'Personal' },
    dob:              { label:'Date of Birth',  icon:'fa-birthday-cake',    section:'Personal' },
    nationality:      { label:'Nationality',    icon:'fa-flag',             section:'Personal' },
    religion:         { label:'Religion',       icon:'fa-place-of-worship', section:'Personal' },
    qualification:    { label:'Qualification',  icon:'fa-graduation-cap',   section:'Professional' },
    specialization:   { label:'Specialization', icon:'fa-book',             section:'Professional' },
    experience:       { label:'Experience',     icon:'fa-briefcase',        section:'Professional' },
    join_date:        { label:'Join Date',      icon:'fa-calendar-check',   section:'Professional' },
    salary:           { label:'Salary',         icon:'fa-money-bill-wave',  section:'Professional' },
    bank_account:     { label:'Bank Account',   icon:'fa-university',       section:'Professional', type:'mono' },
    created_at:       { label:'Created At',     icon:'fa-clock',            section:'System' },
    updated_at:       { label:'Updated At',     icon:'fa-history',          section:'System' },
};

const SKIP_IN_BODY = new Set(['name','t_id','status','id']);

function initials(name) {
    if (!name) return '?';
    const parts = name.trim().split(/\s+/);
    return parts.length >= 2
        ? (parts[0][0] + parts[parts.length-1][0]).toUpperCase()
        : name[0].toUpperCase();
}

function openProfile(idx) {
    const t = TEACHERS[idx];
    if (!t) return;

    // Hero
    document.getElementById('pAvatar').textContent = initials(t.name || '');
    document.getElementById('pName').textContent   = t.name || '—';
    document.getElementById('pTid').textContent    = t.t_id  || '';

    const statusEl = document.getElementById('pStatus');
    const isActive = (t.status || '').toLowerCase() === 'active';
    statusEl.textContent  = isActive ? '● Active' : '● ' + (t.status || 'Inactive');
    statusEl.className    = 'drawer-status ' + (isActive ? 'active' : 'inactive');

    // Body — group fields by section
    const sections = {};
    for (const [key, val] of Object.entries(t)) {
        if (SKIP_IN_BODY.has(key)) continue;
        const meta = FIELD_META[key] || { label: key.replace(/_/g,' '), icon:'fa-info-circle', section:'Other' };
        if (!sections[meta.section]) sections[meta.section] = [];
        sections[meta.section].push({ key, val, meta });
    }

    let html = '';
    for (const [section, fields] of Object.entries(sections)) {
        html += `<div class="section-label">${section}</div>`;
        for (const { val, meta } of fields) {
            const display = (val !== null && val !== '' && val !== undefined)
                ? String(val)
                : null;
            const valueClass = display ? ('info-value' + (meta.type === 'mono' ? ' mono' : '')) : 'info-value empty';
            const valueText  = display || 'Not provided';
            html += `
            <div class="info-row">
                <div class="info-icon"><i class="fas ${meta.icon}"></i></div>
                <div>
                    <div class="info-label">${meta.label}</div>
                    <div class="${valueClass}">${valueText}</div>
                </div>
            </div>`;
        }
    }

    document.getElementById('drawerBody').innerHTML = html;
    document.getElementById('drawerBody').scrollTop = 0;

    // Edit / delete links (update hrefs when you have real routes)
    document.getElementById('pEditBtn').href = '#';
    document.getElementById('pDelBtn').href  = '#';

    // Open
    document.getElementById('drawerOverlay').classList.add('open');
    document.getElementById('profileDrawer').classList.add('open');
    document.body.style.overflow = 'hidden';
}

function closeProfile() {
    document.getElementById('drawerOverlay').classList.remove('open');
    document.getElementById('profileDrawer').classList.remove('open');
    document.body.style.overflow = '';
}

document.addEventListener('keydown', e => { if (e.key === 'Escape') closeProfile(); });
</script>
</body>
</html>
'''