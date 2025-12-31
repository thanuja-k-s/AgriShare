from flask import Flask, jsonify, request
from flask_cors import CORS
from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# ====================================
# NUCLEAR CORS + HTTPS FIX (DEVELOPMENT)
# ====================================
app.config.update({
    'SECRET_KEY': 'dev-secret-key',
    'TESTING': True,
    'DEBUG': True,
    'WTF_CSRF_ENABLED': False,
    'SESSION_COOKIE_SECURE': False,
    'SESSION_COOKIE_SAMESITE': 'None',
    'PERMANENT_SESSION_LIFETIME': 3600
})

# BULLETPROOF CORS - Handle ALL methods + origins
CORS(app, 
     origins=["http://localhost:3000", "http://127.0.0.1:3000", "*"],
     methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
     allow_headers=['Content-Type', 'Authorization'],
     expose_headers=['Authorization'],
     supports_credentials=True)

print("🚀 CORS configured for localhost:3000")

# ====================================
# MONGODB
# ====================================
MONGODB_URI = os.getenv('MONGODB_URI')
try:
    mongo_client = MongoClient(MONGODB_URI)
    db = mongo_client['agrishare']
    mongo_client.admin.command('ping')
    print("✅ Connected to MongoDB!")
except Exception as e:
    print(f"❌ MongoDB connection failed: {e}")

def init_collections():
    required_collections = ['users', 'seed_posts', 'animal_posts', 'prices']
    existing_collections = db.list_collection_names()
    for collection in required_collections:
        if collection not in existing_collections:
            db.create_collection(collection)
            print(f"✅ Created collection: {collection}")

init_collections()

# ====================================
# MANUAL OPTIONS HANDLER (Kills 308)
# ====================================
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

@app.route('/options/<path:path>', methods=['OPTIONS'])
@app.route('/', defaults={'path': ''}, methods=['OPTIONS'])
@app.route('/<path:path>', methods=['OPTIONS'])
def options(path):
    return '', 200

# ====================================
# REGISTER BLUEPRINTS
# ====================================
try:
    from auth import auth_bp
    from seeds import seeds_bp
    from animals import animals_bp
    from prices import prices_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(seeds_bp)
    app.register_blueprint(animals_bp)
    app.register_blueprint(prices_bp)
    print("✅ All blueprints registered")
except ImportError as e:
    print(f"⚠️ Missing blueprint: {e}")

# ====================================
# PING + HEALTH
# ====================================
@app.route('/ping', methods=['GET', 'OPTIONS'])
def ping():
    return jsonify({'message': 'Backend is running! CORS OK!', 'status': 'success'}), 200

@app.route('/db-status', methods=['GET', 'OPTIONS'])
def db_status():
    try:
        collections = db.list_collection_names()
        return jsonify({
            'message': 'Database OK',
            'status': 'success',
            'collections': collections
        }), 200
    except Exception as e:
        return jsonify({'message': str(e), 'status': 'error'}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({'message': 'Route not found', 'status': 'error'}), 404

if __name__ == '__main__':
    print("🚀 Starting Flask on http://0.0.0.0:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)  # ← NO ssl_context
