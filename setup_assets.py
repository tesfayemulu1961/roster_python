import os 
 
def create_file_with_content(filepath, content): 
    with open(filepath, 'w', encoding='utf-8') as f: 
        f.write(content) 
    print(f"  Created: {filepath}") 
 
# Create directories 
directories = [ 
    'static/css/core', 
    'static/css/dashboards/director', 
    'static/css/dashboards/room-teacher', 
    'static/js/core', 
    'static/js/dashboards', 
    'templates/director', 
    'templates/room_teacher', 
] 
 
print("Creating directory structure...") 
for dir_path in directories: 
    os.makedirs(dir_path, exist_ok=True) 
    print(f"  Created: {dir_path}") 
 
print("\nû Directory structure created successfully!") 
