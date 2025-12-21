from flask import Flask, jsonify
from flask_cors import CORS
from pymongo import MongoClient
import os
from dotenv import load_dotenv
from auth import auth_bp

load_dotenv()

app = Flask(__name__)
CORS(app)

# ===== MONGODB CONNECTION =====
MONGODB_URI = os.getenv("MONGODB_URI")

try:
    mongo_client = MongoClient(MONGODB_URI)
    db = mongo_client["agrishare"]

    # Test connection
    mongo_client.admin.command("ping")
    print("✅ Connected to MongoDB")

except Exception as e:
    print("❌ MongoDB error:", e)

# ===== CREATE COLLECTIONS (if they don't exist) =====
def init_collections():
    required_collections = ['users', 'seed_posts', 'animal_posts', 'prices']
    existing_collections = db.list_collection_names()

    for collection in required_collections:
        if collection not in existing_collections:
            db.create_collection(collection)
            print(f"✅ Created collection: {collection}")
        else:
            print(f"⏭️ Collection already exists: {collection}")

# Call this once when app starts
init_collections()

# ===== ROUTES =====
@app.route("/ping")
def ping():
    return jsonify({
        "message": "Backend running",
        "status": "success"
    })

@app.route("/db-status")
def db_status():
    try:
        collections = db.list_collection_names()
        return jsonify({
            "message": "Database connected",
            "status": "success",
            "collections": collections
        })
    except Exception as e:
        return jsonify({
            "message": str(e),
            "status": "error"
        }), 500

@app.errorhandler(404)
def not_found(e):
    return jsonify({
        "message": "Route not found",
        "status": "error"
    }), 404

if __name__ == "__main__":
    app.run(debug=True, port=5000)
