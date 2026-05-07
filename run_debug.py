import sys
import traceback
import os

print("=" * 50)
print("Starting debug wrapper")
print("=" * 50)

try:
    # Change to the correct directory
    os.chdir(r'C:\xampp\htdocs\roster_python')
    
    print("Importing src.app...")
    from src.app import create_app
    
    print("Creating app...")
    app = create_app()
    
    print("App created successfully!")
    print(f"Routes: {[rule.rule for rule in app.url_map.iter_rules()]}")
    
    print("\nStarting server...")
    print("=" * 50)
    
    # Run without debug mode to see real errors
    app.run(host='127.0.0.1', port=5001, debug=False, use_reloader=False)
    
except Exception as e:
    print("\n" + "=" * 50)
    print("ERROR CAUGHT:")
    print("=" * 50)
    print(f"Error type: {type(e).__name__}")
    print(f"Error message: {str(e)}")
    print("\nFull traceback:")
    traceback.print_exc()
    
    input("\nPress Enter to exit...")
