import os
import re

def fix_python_files():
    """Automatically add external CSS/JS links to all Python files"""
    
    base_dir = r"C:\xampp\htdocs\roster_python"
    
    # Files to process
    directories = ['director', 'room_teacher']
    
    css_link = '<link rel="stylesheet" href="/static/css/core.css">'
    js_link = '<script src="/static/js/core.js"></script>'
    
    files_modified = 0
    
    for directory in directories:
        dir_path = os.path.join(base_dir, directory)
        if not os.path.exists(dir_path):
            continue
            
        for root, dirs, files in os.walk(dir_path):
            for file in files:
                if file.endswith('.py') and file not in ['__init__.py', 'fix_external_links.py']:
                    filepath = os.path.join(root, file)
                    
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        modified = False
                        
                        # Check if file has HTML content
                        if '<head>' in content or '<html>' in content:
                            
                            # Add CSS link if missing
                            if css_link not in content and 'core.css' not in content:
                                # Add after <head> tag
                                content = content.replace('<head>', f'<head>\n    {css_link}')
                                modified = True
                                print(f"  Added CSS to: {file}")
                            
                            # Add JS link if missing
                            if js_link not in content and 'core.js' not in content:
                                # Add before </body>
                                if '</body>' in content:
                                    content = content.replace('</body>', f'    {js_link}\n</body>')
                                else:
                                    content = content + f'\n    {js_link}'
                                modified = True
                                print(f"  Added JS to: {file}")
                            
                            # Remove large internal style blocks (optional)
                            # Remove style tags with more than 500 characters
                            style_pattern = r'<style>\s*?(?:[^<]|<[^/]){500,}?\s*?</style>'
                            if re.search(style_pattern, content, re.DOTALL):
                                content = re.sub(style_pattern, '', content, flags=re.DOTALL)
                                modified = True
                                print(f"  Removed large style block from: {file}")
                            
                            # Remove large script blocks (optional)
                            script_pattern = r'<script>\s*?(?:[^<]|<[^/]){500,}?\s*?</script>'
                            if re.search(script_pattern, content, re.DOTALL):
                                content = re.sub(script_pattern, '', content, flags=re.DOTALL)
                                modified = True
                                print(f"  Removed large script block from: {file}")
                        
                        if modified:
                            with open(filepath, 'w', encoding='utf-8') as f:
                                f.write(content)
                            files_modified += 1
                            
                    except Exception as e:
                        print(f"Error processing {file}: {e}")
    
    print(f"\n✅ Modified {files_modified} files")

if __name__ == "__main__":
    print("="*60)
    print("Fixing External CSS/JS Links")
    print("="*60)
    fix_python_files()
    print("\nDone!")