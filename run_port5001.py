import sys
import traceback
import os

print("Starting server on port 5001...")
os.chdir(r'C:\xampp\htdocs\roster_python')

try:
    from src.app import create_app
    app = create_app()
    print(f"Routes loaded: {len(app.url_map._rules)} routes")
    print("\nStarting Flask server on http://127.0.0.1:5001")
    app.run(host='127.0.0.1', port=5001, debug=True)
except Exception as e:
    print(f"Error: {e}")
    traceback.print_exc()