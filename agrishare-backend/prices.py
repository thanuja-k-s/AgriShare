from flask import Blueprint, request, jsonify
from pymongo import MongoClient
from bson.objectid import ObjectId
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

prices_bp = Blueprint('prices', __name__, url_prefix='/prices')

MONGODB_URI = os.getenv('MONGODB_URI')
mongo_client = MongoClient(MONGODB_URI)
db = mongo_client['agrishare']
prices_collection = db['prices']

# ===== ADD PRICE DATA (for admin) =====
@prices_bp.route('/', methods=['POST'])
def add_price():
    """
    POST /prices
    Body: {
        "crop_name": "Wheat",
        "mandi": "Indore",
        "min_price": 35,
        "max_price": 42,
        "modal_price": 40,
        "unit": "per kg",
        "date": "2024-01-20"
    }
    """
    try:
        data = request.get_json()
        
        if not all(k in data for k in ['crop_name', 'mandi', 'min_price', 'max_price', 'modal_price']):
            return jsonify({'message': 'Missing required fields', 'status': 'error'}), 400
        
        price = {
            'crop_name': data['crop_name'],
            'mandi': data['mandi'],
            'min_price': data['min_price'],
            'max_price': data['max_price'],
            'modal_price': data['modal_price'],
            'unit': data.get('unit', 'per kg'),
            'date': data.get('date', str(datetime.utcnow().date())),
            'created_at': datetime.utcnow()
        }
        
        result = prices_collection.insert_one(price)
        
        return jsonify({
            'message': 'Price added',
            'status': 'success',
            'price_id': str(result.inserted_id)
        }), 201
    
    except Exception as e:
        return jsonify({'message': str(e), 'status': 'error'}), 500

# ===== GET PRICES (with filters) =====
@prices_bp.route('/', methods=['GET'])
def get_prices():
    """
    GET /prices?crop_name=Wheat&date=2024-01-20&mandi=Indore
    """
    try:
        filter_query = {}
        
        if request.args.get('crop_name'):
            filter_query['crop_name'] = {'$regex': request.args.get('crop_name'), '$options': 'i'}
        if request.args.get('mandi'):
            filter_query['mandi'] = request.args.get('mandi')
        if request.args.get('date'):
            filter_query['date'] = request.args.get('date')
        
        prices = list(prices_collection.find(filter_query).sort('created_at', -1).limit(100))
        
        for price in prices:
            price['_id'] = str(price['_id'])
        
        return jsonify({
            'message': 'Prices retrieved',
            'status': 'success',
            'count': len(prices),
            'prices': prices
        }), 200
    
    except Exception as e:
        return jsonify({'message': str(e), 'status': 'error'}), 500

# ===== GET TODAY'S PRICES =====
@prices_bp.route('/today', methods=['GET'])
def get_today_prices():
    """
    GET /prices/today?crop_name=Wheat
    """
    try:
        today = str(datetime.utcnow().date())
        
        filter_query = {'date': today}
        
        if request.args.get('crop_name'):
            filter_query['crop_name'] = {'$regex': request.args.get('crop_name'), '$options': 'i'}
        
        prices = list(prices_collection.find(filter_query))
        
        for price in prices:
            price['_id'] = str(price['_id'])
        
        return jsonify({
            'message': "Today's prices retrieved",
            'status': 'success',
            'date': today,
            'count': len(prices),
            'prices': prices
        }), 200
    
    except Exception as e:
        return jsonify({'message': str(e), 'status': 'error'}), 500
