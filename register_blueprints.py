import os
import importlib

def register_all_blueprints(app):
    """Automatically discover and register all dashboard blueprints"""
    
    # List of all dashboard files to look for
    dashboard_files = [
        'director_dashboard',
        'vice_director_dashboard', 
        'supervisor_dashboard',
        'kg_director_dashboard',
        'room_teacher_dashboard',
        'subject_teacher_dashboard',
        'student_dashboard',
        'parent_dashboard'
    ]
    
    registered = []
    failed = []
    
    for dashboard in dashboard_files:
        try:
            # Try to import the blueprint
            module = importlib.import_module(dashboard)
            
            # Look for blueprint variable (usually ends with _bp)
            blueprint_name = f"{dashboard}_bp"
            if hasattr(module, blueprint_name):
                blueprint = getattr(module, blueprint_name)
                app.register_blueprint(blueprint)
                registered.append(dashboard)
                print(f"✓ Registered: {dashboard}")
            else:
                failed.append(f"{dashboard} (no blueprint found)")
                
        except ImportError as e:
            failed.append(f"{dashboard} ({str(e)})")
    
    return registered, failed