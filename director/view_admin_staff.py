from flask import Blueprint, render_template_string, session, redirect, url_for
import base64

# Create blueprint
view_admin_staff_bp = Blueprint('view_admin_staff', __name__)

@view_admin_staff_bp.route('/director/view_admin_staff')
def view_admin_staff():
    """View all admin staff members"""
    
    # Check if user is logged in as director
    if not session.get('logged_in') or session.get('user_type') != 'director':
        return redirect(url_for('unauthorized'))
    
    # Get success message from session if exists
    success = session.pop('success', '')
    
    # Get database connection
    from app import get_db
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    staff_members = []
    
    try:
        # Fetch all admin staff ordered by role and full_name
        cursor.execute("""
            SELECT ID, full_name, gender, age, role, phone, photo
            FROM admin_staff 
            ORDER BY role, full_name
        """)
        
        staff_rows = cursor.fetchall()
        print(f"Found {len(staff_rows)} staff members")  # Debug print
        
        # Process images for display
        for staff in staff_rows:
            staff_dict = {
                'id': staff['ID'],
                'full_name': staff['full_name'],
                'gender': staff['gender'],
                'age': staff['age'],
                'role': staff['role'],
                'phone': staff['phone'],
                'photo_base64': None
            }
            
            # Convert photo to base64 if exists
            if staff['photo'] and len(staff['photo']) > 0:
                try:
                    photo_base64 = base64.b64encode(staff['photo']).decode('utf-8')
                    staff_dict['photo_base64'] = photo_base64
                except Exception as img_error:
                    print(f"Error converting image: {img_error}")
            
            staff_members.append(staff_dict)
        
        print(f"Processed {len(staff_members)} staff members")  # Debug print
        
    except Exception as e:
        print(f"Error fetching admin staff: {e}")
        staff_members = []
    finally:
        cursor.close()
        conn.close()
    
    # HTML Template
    html_template = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>View Admin Staff - School Roster System</title>
        <style>
            :root {
                --primary-color: #3498db;
                --success-color: #2ecc71;
                --danger-color: #e74c3c;
                --light-gray: #f5f5f5;
                --border-color: #ddd;
            }
            
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.6;
                margin: 0;
                padding: 20px;
                color: #333;
                background-color: #f9f9f9;
            }
            
            .container {
                max-width: 1200px;
                margin: 0 auto;
                background: white;
                padding: 30px;
                border-radius: 8px;
                box-shadow: 0 0 20px rgba(0,0,0,0.1);
            }
            
            h1 {
                color: var(--primary-color);
                margin-top: 0;
                border-bottom: 2px solid var(--light-gray);
                padding-bottom: 10px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            
            .alert {
                padding: 15px;
                margin-bottom: 20px;
                border-radius: 4px;
            }
            
            .alert-success {
                background-color: #d4edda;
                color: #155724;
                border: 1px solid #c3e6cb;
            }
            
            .staff-grid {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
                gap: 20px;
                margin-top: 20px;
            }
            
            .staff-card {
                border: 1px solid var(--border-color);
                border-radius: 8px;
                padding: 20px;
                transition: transform 0.3s, box-shadow 0.3s;
                background: white;
            }
            
            .staff-card:hover {
                transform: translateY(-5px);
                box-shadow: 0 10px 20px rgba(0,0,0,0.1);
            }
            
            .photo-container {
                height: 150px;
                display: flex;
                align-items: center;
                justify-content: center;
                margin-bottom: 15px;
                overflow: hidden;
                background-color: #f5f5f5;
                border-radius: 4px;
            }
            
            .staff-photo {
                max-height: 100%;
                max-width: 100%;
                object-fit: contain;
            }
            
            .no-photo {
                text-align: center;
                color: #999;
                font-size: 14px;
                padding: 20px;
            }
            
            .staff-details h3 {
                margin-top: 0;
                color: var(--primary-color);
            }
            
            .staff-details p {
                margin: 8px 0;
            }
            
            .staff-role {
                display: inline-block;
                padding: 3px 8px;
                background-color: var(--primary-color);
                color: white;
                border-radius: 4px;
                font-size: 0.8em;
                margin-bottom: 10px;
            }
            
            .action-buttons {
                display: flex;
                gap: 10px;
                margin-top: 15px;
            }
            
            .btn {
                display: inline-block;
                padding: 8px 15px;
                text-decoration: none;
                border-radius: 4px;
                font-size: 14px;
                transition: background-color 0.3s;
                border: none;
                cursor: pointer;
            }
            
            .btn-edit {
                background-color: var(--primary-color);
                color: white;
            }
            
            .btn-delete {
                background-color: var(--danger-color);
                color: white;
            }
            
            .btn-add {
                background-color: var(--success-color);
                color: white;
                padding: 10px 20px;
            }
            
            .btn:hover {
                opacity: 0.9;
            }
            
            @media (max-width: 768px) {
                .staff-grid {
                    grid-template-columns: 1fr;
                }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>
                Admin Staff
                <a href="/director/insert_admin_staff" class="btn btn-add">+ Add New Staff</a>
            </h1>
            
            {% if success %}
                <div class="alert alert-success">{{ success }}</div>
            {% endif %}
            
            {% if staff_members %}
                <div class="staff-grid">
                    {% for staff in staff_members %}
                        <div class="staff-card">
                            <div class="photo-container">
                                {% if staff.photo_base64 %}
                                    <img src="data:image/jpeg;base64,{{ staff.photo_base64 }}" 
                                         alt="Staff Photo" 
                                         class="staff-photo">
                                {% else %}
                                    <div class="no-photo">📷 No Photo</div>
                                {% endif %}
                            </div>
                            
                            <div class="staff-details">
                                <span class="staff-role">{{ staff.role|title }}</span>
                                <h3>{{ staff.full_name }}</h3>
                                <p><strong>Gender:</strong> {{ 'Male' if staff.gender == 'M' else 'Female' }}</p>
                                <p><strong>Age:</strong> {{ staff.age }}</p>
                                <p><strong>Phone:</strong> {{ staff.phone }}</p>
                                
                                <div class="action-buttons">
                                    <a href="/director/edit_admin_staff/{{ staff.id }}" class="btn btn-edit">Edit</a>
                                    <a href="/director/delete_admin_staff/{{ staff.id }}" class="btn btn-delete" onclick="return confirm('Are you sure you want to delete this staff member?')">Delete</a>
                                </div>
                            </div>
                        </div>
                    {% endfor %}
                </div>
            {% else %}
                <p style="text-align: center; color: #666; padding: 40px;">
                    No admin staff members found in the database.
                </p>
            {% endif %}
        </div>
    </body>
    </html>
    """
    
    return render_template_string(html_template, success=success, staff_members=staff_members)


@view_admin_staff_bp.route('/director/edit_admin_staff/<int:id>', methods=['GET', 'POST'])
def edit_admin_staff(id):
    """Edit admin staff member"""
    
    if not session.get('logged_in') or session.get('user_type') != 'director':
        return redirect(url_for('unauthorized'))
    
    from app import get_db
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    if request.method == 'POST':
        try:
            full_name = request.form.get('full_name', '').strip()
            gender = request.form.get('gender', 'M')
            age = request.form.get('age', '')
            role = request.form.get('role', 'director')
            phone = request.form.get('phone', '').strip()
            
            cursor.execute("""
                UPDATE admin_staff 
                SET full_name=%s, gender=%s, age=%s, role=%s, phone=%s
                WHERE ID=%s
            """, (full_name, gender, age, role, phone, id))
            
            conn.commit()
            session['success'] = "Staff member updated successfully!"
            return redirect(url_for('view_admin_staff.view_admin_staff'))
            
        except Exception as e:
            error = str(e)
            cursor.execute("SELECT * FROM admin_staff WHERE ID=%s", (id,))
            staff = cursor.fetchone()
            cursor.close()
            conn.close()
            
            edit_form = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Edit Admin Staff</title>
                <style>
                    body { font-family: Arial; padding: 20px; background: #f5f5f5; }
                    .container { max-width: 500px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; }
                    input, select { width: 100%; padding: 8px; margin: 5px 0 15px; border: 1px solid #ddd; border-radius: 4px; }
                    button { background: #3498db; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
                    .error { color: red; background: #ffebee; padding: 10px; margin-bottom: 15px; border-radius: 4px; }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>Edit Admin Staff</h1>
                    {% if error %}<div class="error">{{ error }}</div>{% endif %}
                    <form method="POST">
                        <label>Full Name:</label>
                        <input type="text" name="full_name" value="{{ staff.full_name }}" required>
                        
                        <label>Gender:</label>
                        <select name="gender">
                            <option value="M" {{ 'selected' if staff.gender == 'M' else '' }}>Male</option>
                            <option value="F" {{ 'selected' if staff.gender == 'F' else '' }}>Female</option>
                        </select>
                        
                        <label>Age:</label>
                        <input type="number" name="age" value="{{ staff.age }}" required>
                        
                        <label>Role:</label>
                        <select name="role">
                            <option value="director" {{ 'selected' if staff.role == 'director' else '' }}>Director</option>
                            <option value="vice director" {{ 'selected' if staff.role == 'vice director' else '' }}>Vice Director</option>
                            <option value="supervisor" {{ 'selected' if staff.role == 'supervisor' else '' }}>Supervisor</option>
                            <option value="KG director" {{ 'selected' if staff.role == 'KG director' else '' }}>KG Director</option>
                        </select>
                        
                        <label>Phone:</label>
                        <input type="text" name="phone" value="{{ staff.phone }}" required>
                        
                        <button type="submit">Update</button>
                        <a href="/director/view_admin_staff">Cancel</a>
                    </form>
                </div>
            </body>
            </html>
            """
            return render_template_string(edit_form, staff=staff, error=error)
    
    cursor.execute("SELECT * FROM admin_staff WHERE ID=%s", (id,))
    staff = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if not staff:
        return "Staff not found", 404
    
    edit_form = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Edit Admin Staff</title>
        <style>
            body { font-family: Arial; padding: 20px; background: #f5f5f5; }
            .container { max-width: 500px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; }
            input, select { width: 100%; padding: 8px; margin: 5px 0 15px; border: 1px solid #ddd; border-radius: 4px; }
            button { background: #3498db; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Edit Admin Staff</h1>
            <form method="POST">
                <label>Full Name:</label>
                <input type="text" name="full_name" value="{{ staff.full_name }}" required>
                
                <label>Gender:</label>
                <select name="gender">
                    <option value="M" {{ 'selected' if staff.gender == 'M' else '' }}>Male</option>
                    <option value="F" {{ 'selected' if staff.gender == 'F' else '' }}>Female</option>
                </select>
                
                <label>Age:</label>
                <input type="number" name="age" value="{{ staff.age }}" required>
                
                <label>Role:</label>
                <select name="role">
                    <option value="director" {{ 'selected' if staff.role == 'director' else '' }}>Director</option>
                    <option value="vice director" {{ 'selected' if staff.role == 'vice director' else '' }}>Vice Director</option>
                    <option value="supervisor" {{ 'selected' if staff.role == 'supervisor' else '' }}>Supervisor</option>
                    <option value="KG director" {{ 'selected' if staff.role == 'KG director' else '' }}>KG Director</option>
                </select>
                
                <label>Phone:</label>
                <input type="text" name="phone" value="{{ staff.phone }}" required>
                
                <button type="submit">Update</button>
                <a href="/director/view_admin_staff">Cancel</a>
            </form>
        </div>
    </body>
    </html>
    """
    
    return render_template_string(edit_form, staff=staff, error=None)


@view_admin_staff_bp.route('/director/delete_admin_staff/<int:id>')
def delete_admin_staff(id):
    """Delete admin staff member"""
    
    if not session.get('logged_in') or session.get('user_type') != 'director':
        return redirect(url_for('unauthorized'))
    
    from app import get_db
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Delete from users table first (foreign key constraint)
        cursor.execute("DELETE FROM users WHERE user_type='admin_staff' AND reference_id=%s", (id,))
        # Delete from admin_staff
        cursor.execute("DELETE FROM admin_staff WHERE ID=%s", (id,))
        conn.commit()
        session['success'] = "Staff member deleted successfully!"
    except Exception as e:
        print(f"Error: {e}")
        session['success'] = f"Error: {str(e)}"
        conn.rollback()
    finally:
        cursor.close()
        conn.close()
    
    return redirect(url_for('view_admin_staff.view_admin_staff'))

print("✅ view_admin_staff.py loaded - Ready to display existing data")