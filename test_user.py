from src.app import create_app 
from src.database import db 
from src.models import User 
app = create_app() 
with app.app_context(): 
    user = db.session.query(User).filter_by(username='director001').first() 
    if user: 
        print(f"User found: {user.username}") 
        print(f"User ID: {user.user_id}") 
        print(f"User dict: {user.to_dict()}") 
    else: 
        print("User not found") 
