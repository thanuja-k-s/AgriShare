from flask import Blueprint, request, jsonify
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
import bcrypt
import jwt
import os
from dotenv import load_dotenv


load_dotenv()

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# MongoDB connection
MONGODB_URI = os.getenv('MONGODB_URI')
mongo_client = MongoClient(MONGODB_URI)
db = mongo_client['agrishare']
users_collection = db['users']

# Create unique index on email to prevent duplicates
try:
    users_collection.create_index('email', unique=True)
except Exception as e:
    print("Index already exists or DB not ready:", e)


# Secret key for JWT tokens
SECRET_KEY = os.getenv('SECRET_KEY', 'your_secret_key_here_change_in_production')

# ===== REGISTER ROUTE =====
@auth_bp.route('/register', methods=['POST'])
def register():
    try:
        users_collection.create_index('email', unique=True)
    except:
        pass

    """
    POST /auth/register
    Body: {
        "name": "Ramesh Kumar",
        "email": "ramesh@example.com",
        "phone": "9876543210",
        "village": "Nagar",
        "district": "Belgaum",
        "password": "securepass123"
    }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'email', 'phone', 'village', 'district', 'password']
        if not all(field in data for field in required_fields):
            return jsonify({'message': 'Missing required fields', 'status': 'error'}), 400
        
        # Check if user already exists
        if users_collection.find_one({'email': data['email']}):
            return jsonify({'message': 'Email already registered', 'status': 'error'}), 400
        
        # Hash password
        hashed_password = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt())
        
        # Create user document
        user = {
            'name': data['name'],
            'email': data['email'],
            'phone': data['phone'],
            'village': data['village'],
            'district': data['district'],
            'password': hashed_password,
            'role': data.get('role', 'farmer'),  # Default role is farmer
            'created_at': __import__('datetime').datetime.utcnow()
        }
        
        # Insert into database
        result = users_collection.insert_one(user)
        
        return jsonify({
            'message': 'Registration successful',
            'status': 'success',
            'user_id': str(result.inserted_id)
        }), 201
    
    except DuplicateKeyError:
        return jsonify({'message': 'Email already exists', 'status': 'error'}), 400
    except Exception as e:
        return jsonify({'message': str(e), 'status': 'error'}), 500

# ===== LOGIN ROUTE =====
@auth_bp.route('/login', methods=['POST'])
def login():
    """
    POST /auth/login
    Body: {
        "email": "ramesh@example.com",
        "password": "securepass123"
    }
    """
    try:
        data = request.get_json()
        
        # Validate input
        if not data.get('email') or not data.get('password'):
            return jsonify({'message': 'Email and password required', 'status': 'error'}), 400
        
        # Find user
        user = users_collection.find_one({'email': data['email']})
        if not user:
            return jsonify({'message': 'Invalid email or password', 'status': 'error'}), 401
        
        # Check password
        if not bcrypt.checkpw(data['password'].encode('utf-8'), user['password']):
            return jsonify({'message': 'Invalid email or password', 'status': 'error'}), 401
        
        # Create JWT token (valid for 7 days)
        token = jwt.encode({
            'user_id': str(user['_id']),
            'email': user['email'],
            'exp': __import__('datetime').datetime.utcnow() + __import__('datetime').timedelta(days=7)
        }, SECRET_KEY, algorithm='HS256')
        
        return jsonify({
            'message': 'Login successful',
            'status': 'success',
            'token': token,
            'user': {
                'id': str(user['_id']),
                'name': user['name'],
                'email': user['email'],
                'village': user['village'],
                'district': user['district']
            }
        }), 200
    
    except Exception as e:
        return jsonify({'message': str(e), 'status': 'error'}), 500
