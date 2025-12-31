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

# ===== POST SEED =====
@seeds_bp.route('/', methods=['POST', 'OPTIONS'])
def create_seed():
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        data = request.get_json()
        print(f"POST /seeds data: {data}")  # DEBUG
        
        if not all(k in data for k in ['user_id', 'type', 'crop_name', 'quantity']):
            return jsonify({'message': 'Missing required fields', 'status': 'error'}), 400
        
        seed = {
            'user_id': ObjectId(data['user_id']),
            'type': data['type'],
            'crop_name': data['crop_name'],
            'quantity': data['quantity'],
            'unit': data.get('unit', 'kg'),
            'price': data.get('price'),
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
        print(f"Seed error: {e}")
        return jsonify({'message': str(e), 'status': 'error'}), 500

# ===== GET SEEDS =====
@seeds_bp.route('/', methods=['GET', 'OPTIONS'])
def get_seeds():
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        print(f"GET /seeds params: {request.args}")  # DEBUG
        
        filter_query = {}
        if request.args.get('type'):
            filter_query['type'] = request.args.get('type')
        if request.args.get('crop_name'):
            filter_query['crop_name'] = {'$regex': request.args.get('crop_name'), '$options': 'i'}
        if request.args.get('district'):
            filter_query['district'] = request.args.get('district')
        
        seeds = list(seeds_collection.find(filter_query).sort('created_at', -1).limit(50))
        
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
        print(f"Seeds GET error: {e}")
        return jsonify({'message': str(e), 'status': 'error'}), 500
