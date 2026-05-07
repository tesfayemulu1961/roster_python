import os
import sys

# Change to project directory
os.chdir(r'C:\xampp\htdocs\roster_python')

# Add current directory to path
sys.path.insert(0, os.getcwd())

print("=" * 50)
print("Starting Roster API Server")
print("=" * 50)

try:
    from src.app import create_app
    from waitress import serve
    
    app = create_app()
    print(f"✅ Routes loaded: {len(app.url_map._rules)}")
    print(f"✅ Server starting on http://127.0.0.1:8080")
    print(f"✅ Press Ctrl+C to stop")
    print("=" * 50 + "\n")
    
    # Use waitress instead of Flask's dev server
    serve(app, host='127.0.0.1', port=8080)
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    input("\nPress Enter to exit...")