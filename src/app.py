import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, jsonify
from flask_cors import CORS
from src.database import init_db, create_tables
from api.auth import auth_bp
from api.roster import roster_bp
from api.teacher import teacher_bp
from api.grades import grade_bp
from api.scores import score_bp
from api.admin import admin_bp
from api.dashboard import dashboard_bp

def create_app():
    app = Flask(__name__)
    
    from src.config import Config
    app.config.from_object(Config)
    
    init_db(app)
    
    CORS(app, supports_credentials=True)
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(roster_bp, url_prefix='/api/roster')
    app.register_blueprint(teacher_bp, url_prefix='/api')
    app.register_blueprint(grade_bp, url_prefix='/api')
    app.register_blueprint(score_bp, url_prefix='/api')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')
    
    @app.route('/api/health')
    def health():
        return jsonify({'status': 'ok'})
    
    @app.route('/')
    def index():
        return jsonify({'message': 'School Management System API', 'version': '1.0'})
    
    create_tables(app)
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)