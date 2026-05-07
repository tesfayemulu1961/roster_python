from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

db = SQLAlchemy()

class Base(DeclarativeBase):
    pass

def init_db(app):
    db_uri = (
        f"mysql+pymysql://{app.config['DB_USER']}:{app.config['DB_PASS']}"
        f"@{app.config['DB_HOST']}/{app.config['DB_NAME']}?charset={app.config.get('DB_CHARSET', 'utf8mb4')}"
    )
    app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)

def create_tables(app):
    with app.app_context():
        db.create_all()

def get_session():
    return db.session
