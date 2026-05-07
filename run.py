import os
import sys

os.chdir(r'C:\xampp\htdocs\roster_python')
sys.path.insert(0, os.getcwd())

print("=" * 50)
print("Starting Roster API Server")
print("=" * 50)

try:
    from src.app import create_app
    from waitress import serve
    
    app = create_app()
    print(f"? Routes loaded: {len(app.url_map._rules)}")
    print(f"? Server starting on http://127.0.0.1:5000")
    print(f"? Press Ctrl+C to stop")
    print("=" * 50 + "\n")
    
    serve(app, host='0.0.0.0', port=5000)
    
except Exception as e:
    print(f"? Error: {e}")
    import traceback
    traceback.print_exc()
    input("\nPress Enter to exit...")
