import os 
import re 
 
def quick_analyze(): 
    php_root = r"C:\xampp\htdocs\roster_php" 
 
    print("="*80) 
    print("ROSTER PHP PROJECT - QUICK ANALYSIS") 
    print("="*80) 
 
    php_files_path = os.path.join(php_root, "php_files.txt") 
 
    if not os.path.exists(php_files_path): 
        print("php_files.txt not found") 
        return 
 
    with open(php_files_path, 'r', encoding='utf-8', errors='ignore') as f: 
        content = f.read() 
 
    lines = content.split('\n') 
    php_files = [] 
 
    for line in lines: 
        if '.php' in line.lower(): 
            parts = line.split() 
            if parts: 
                potential_path = parts[-1] if parts else '' 
                if '.php' in potential_path: 
                    php_files.append(potential_path) 
 
    print(f"\nTotal PHP files: {len(php_files)}") 
 
if __name__ == "__main__": 
    quick_analyze() 
