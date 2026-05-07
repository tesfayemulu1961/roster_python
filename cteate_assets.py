import os

# Create directory structure
directories = [
    'static/css/core',
    'static/css/dashboards/director',
    'static/css/dashboards/vice-director',
    'static/css/dashboards/kg-director',
    'static/css/dashboards/room-teacher',
    'static/css/dashboards/subject-teacher',
    'static/css/dashboards/student',
    'static/css/dashboards/parent',
    'static/css/modules',
    'static/js/core',
    'static/js/dashboards',
    'static/js/modules',
    'templates/director',
    'templates/room_teacher',
    'templates/subject_teacher',
    'templates/student',
    'templates/parent'
]

print("Creating directory structure...")
for dir_path in directories:
    os.makedirs(dir_path, exist_ok=True)
    print(f"  Created: {dir_path}")

print("\n✓ Directory structure created successfully!")
print("\nNext steps:")
print("1. Copy the CSS content to each file")
print("2. Copy the JS content to each file")
print("3. Update your Python files to use the external CSS/JS")