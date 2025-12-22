from flask import Blueprint, request, jsonify
from pymongo import MongoClient
from bson.objectid import ObjectId
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

animals_bp = Blueprint('animals', __name__, url_prefix='/animals')

MONGODB_URI = os.getenv('MONGODB_URI')
mongo_client = MongoClient(MONGODB_URI)
db = mongo_client['agrishare']
animals_collection = db['animal_posts']

# ===== POST A NEW ANIMAL =====
@animals_bp.route('/', methods=['POST'])
def create_animal():
    """
    POST /animals
    Body: {
        "user_id": "507f1f77bcf86cd799439011",
        "animal_type": "buffalo",  // cow, buffalo, goat, hen, sheep
        "quantity": 1,
        "age_years": 3,
        "age_months": 0,
        "gender": "female",
        "health_status": "very good",
        "price": 80000,
        "description": "Healthy buffalo",
        "village": "Nagar",
        "district": "Belgaum"
    }
    """
    try:
        data = request.get_json()
        
        if not all(k in data for k in ['user_id', 'animal_type', 'quantity', 'price']):
            return jsonify({'message': 'Missing required fields', 'status': 'error'}), 400
        
        animal = {
            'user_id': ObjectId(data['user_id']),
            'animal_type': data['animal_type'],
            'quantity': data['quantity'],
            'age_years': data.get('age_years', 0),
            'age_months': data.get('age_months', 0),
            'gender': data.get('gender', 'not specified'),
            'health_status': data.get('health_status', 'good'),
            'price': data['price'],
            'description': data.get('description', ''),
            'village': data.get('village', ''),
            'district': data.get('district', ''),
            'created_at': datetime.utcnow()
        }
        
        result = animals_collection.insert_one(animal)
        
        return jsonify({
            'message': 'Animal post created',
            'status': 'success',
            'animal_id': str(result.inserted_id)
        }), 201
    
    except Exception as e:
        return jsonify({'message': str(e), 'status': 'error'}), 500

# ===== GET ALL ANIMALS (with filters) =====
@animals_bp.route('/', methods=['GET'])
def get_animals():
    """
    GET /animals?animal_type=buffalo&district=Belgaum&min_price=50000&max_price=100000
    """
    try:
        filter_query = {}
        
        if request.args.get('animal_type'):
            filter_query['animal_type'] = request.args.get('animal_type')
        if request.args.get('district'):
            filter_query['district'] = request.args.get('district')
        
        # Price filters
        if request.args.get('min_price') or request.args.get('max_price'):
            price_query = {}
            if request.args.get('min_price'):
                price_query['$gte'] = float(request.args.get('min_price'))
            if request.args.get('max_price'):
                price_query['$lte'] = float(request.args.get('max_price'))
            filter_query['price'] = price_query
        
        animals = list(animals_collection.find(filter_query).sort('created_at', -1).limit(50))
        
        for animal in animals:
            animal['_id'] = str(animal['_id'])
            animal['user_id'] = str(animal['user_id'])
        
        return jsonify({
            'message': 'Animals retrieved',
            'status': 'success',
            'count': len(animals),
            'animals': animals
        }), 200
    
    except Exception as e:
        return jsonify({'message': str(e), 'status': 'error'}), 500

# ===== GET SINGLE ANIMAL BY ID =====
@animals_bp.route('/<animal_id>', methods=['GET'])
def get_animal(animal_id):
    try:
        animal = animals_collection.find_one({'_id': ObjectId(animal_id)})
        
        if not animal:
            return jsonify({'message': 'Animal not found', 'status': 'error'}), 404
        
        animal['_id'] = str(animal['_id'])
        animal['user_id'] = str(animal['user_id'])
        
        return jsonify({
            'message': 'Animal retrieved',
            'status': 'success',
            'animal': animal
        }), 200
    
    except Exception as e:
        return jsonify({'message': str(e), 'status': 'error'}), 500

# ===== UPDATE ANIMAL =====
@animals_bp.route('/<animal_id>', methods=['PUT'])
def update_animal(animal_id):
    try:
        data = request.get_json()
        
        result = animals_collection.update_one(
            {'_id': ObjectId(animal_id)},
            {'$set': data}
        )
        
        if result.matched_count == 0:
            return jsonify({'message': 'Animal not found', 'status': 'error'}), 404
        
        return jsonify({
            'message': 'Animal updated',
            'status': 'success'
        }), 200
    
    except Exception as e:
        return jsonify({'message': str(e), 'status': 'error'}), 500

# ===== DELETE ANIMAL =====
@animals_bp.route('/<animal_id>', methods=['DELETE'])
def delete_animal(animal_id):
    try:
        result = animals_collection.delete_one({'_id': ObjectId(animal_id)})
        
        if result.deleted_count == 0:
            return jsonify({'message': 'Animal not found', 'status': 'error'}), 404
        
        return jsonify({
            'message': 'Animal deleted',
            'status': 'success'
        }), 200
    
    except Exception as e:
        return jsonify({'message': str(e), 'status': 'error'}), 500
