from flask import Blueprint, request, jsonify
from pymongo import MongoClient
from bson.objectid import ObjectId
import os
from dotenv import load_dotenv
from datetime import datetime


load_dotenv()

seeds_bp = Blueprint('seeds', __name__, url_prefix='/seeds')

MONGODB_URI = os.getenv('MONGODB_URI')
mongo_client = MongoClient(MONGODB_URI)
db = mongo_client['agrishare']
seeds_collection = db['seed_posts']

# ===== POST A NEW SEED =====
@seeds_bp.route('/', methods=['POST'])
def create_seed():
    """
    POST /seeds
    Body: {
        "user_id": "507f1f77bcf86cd799439011",
        "type": "have",  // "have" or "need"
        "crop_name": "Wheat",
        "quantity": 50,
        "unit": "kg",
        "price": 500,
        "notes": "Best in rainy season",
        "village": "Nagar",
        "district": "Belgaum"
    }
    """
    try:
        data = request.get_json()
        
        # Validate
        if not all(k in data for k in ['user_id', 'type', 'crop_name', 'quantity']):
            return jsonify({'message': 'Missing required fields', 'status': 'error'}), 400
        
        seed = {
            'user_id': ObjectId(data['user_id']),
            'type': data['type'],  # 'have' or 'need'
            'crop_name': data['crop_name'],
            'quantity': data['quantity'],
            'unit': data.get('unit', 'kg'),
            'price': data.get('price', None),
            'notes': data.get('notes', ''),
            'village': data.get('village', ''),
            'district': data.get('district', ''),
            'created_at': datetime.utcnow()
        }
        
        result = seeds_collection.insert_one(seed)
        
        return jsonify({
            'message': 'Seed post created',
            'status': 'success',
            'seed_id': str(result.inserted_id)
        }), 201
    
    except Exception as e:
        return jsonify({'message': str(e), 'status': 'error'}), 500

# ===== GET ALL SEEDS (with filters) =====
@seeds_bp.route('/', methods=['GET'])
def get_seeds():
    """
    GET /seeds?type=have&crop_name=Wheat&district=Belgaum
    """
    try:
        # Build filter
        filter_query = {}
        
        if request.args.get('type'):
            filter_query['type'] = request.args.get('type')
        if request.args.get('crop_name'):
            filter_query['crop_name'] = {'$regex': request.args.get('crop_name'), '$options': 'i'}
        if request.args.get('district'):
            filter_query['district'] = request.args.get('district')
        
        # Get seeds
        seeds = list(seeds_collection.find(filter_query).sort('created_at', -1).limit(50))
        
        # Convert ObjectId to string
        for seed in seeds:
            seed['_id'] = str(seed['_id'])
            seed['user_id'] = str(seed['user_id'])
        
        return jsonify({
            'message': 'Seeds retrieved',
            'status': 'success',
            'count': len(seeds),
            'seeds': seeds
        }), 200
    
    except Exception as e:
        return jsonify({'message': str(e), 'status': 'error'}), 500

# ===== GET SINGLE SEED BY ID =====
@seeds_bp.route('/<seed_id>', methods=['GET'])
def get_seed(seed_id):
    """
    GET /seeds/507f1f77bcf86cd799439011
    """
    try:
        seed = seeds_collection.find_one({'_id': ObjectId(seed_id)})
        
        if not seed:
            return jsonify({'message': 'Seed not found', 'status': 'error'}), 404
        
        seed['_id'] = str(seed['_id'])
        seed['user_id'] = str(seed['user_id'])
        
        return jsonify({
            'message': 'Seed retrieved',
            'status': 'success',
            'seed': seed
        }), 200
    
    except Exception as e:
        return jsonify({'message': str(e), 'status': 'error'}), 500

# ===== UPDATE SEED =====
@seeds_bp.route('/<seed_id>', methods=['PUT'])
def update_seed(seed_id):
    """
    PUT /seeds/507f1f77bcf86cd799439011
    Body: { "price": 600, "notes": "Updated notes" }
    """
    try:
        data = request.get_json()
        
        result = seeds_collection.update_one(
            {'_id': ObjectId(seed_id)},
            {'$set': data}
        )
        
        if result.matched_count == 0:
            return jsonify({'message': 'Seed not found', 'status': 'error'}), 404
        
        return jsonify({
            'message': 'Seed updated',
            'status': 'success'
        }), 200
    
    except Exception as e:
        return jsonify({'message': str(e), 'status': 'error'}), 500

# ===== DELETE SEED =====
@seeds_bp.route('/<seed_id>', methods=['DELETE'])
def delete_seed(seed_id):
    """
    DELETE /seeds/507f1f77bcf86cd799439011
    """
    try:
        result = seeds_collection.delete_one({'_id': ObjectId(seed_id)})
        
        if result.deleted_count == 0:
            return jsonify({'message': 'Seed not found', 'status': 'error'}), 404
        
        return jsonify({
            'message': 'Seed deleted',
            'status': 'success'
        }), 200
    
    except Exception as e:
        return jsonify({'message': str(e), 'status': 'error'}), 500
