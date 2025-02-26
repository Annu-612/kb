import os
import logging
from flask import Flask, request, jsonify
from pymongo import MongoClient
import bcrypt
from flask_cors import CORS
import re

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MongoDB connection
MONGO_URI = os.environ.get("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["mydatabase"]  # Replace with your actual database name
users_collection = db["users"]

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    logger.info("Received registration data: %s", data)

    # Validate data
    errors = {}
    if not data.get('name'):
        errors['name'] = 'Name is required'
    if not data.get('email'):
        errors['email'] = 'Email is required'
    elif not re.match(r'\S+@\S+\.\S+', data['email']):
        errors['email'] = 'Please enter a valid email'
    if data.get('phone') and not re.match(r'^\d{10}$', data['phone']):
        errors['phone'] = 'Please enter a valid 10-digit phone number'
    if not data.get('password'):
        errors['password'] = 'Password is required'
    elif len(data['password']) < 8:
        errors['password'] = 'Password must be at least 8 characters'
    if not data.get('pincode') or not re.match(r'^\d{6}$', data['pincode']):
        errors['pincode'] = 'Please enter a valid 6-digit pincode'
    if not data.get('address'):
        errors['address'] = 'Address is required'
    if data['role'] == 'customer' and not data.get('krishiBhavanId'):
        errors['krishiBhavanId'] = 'Krishi-Bhavan ID is required'
    if data['role'] == 'seller' and not data.get('krishiBhavan'):
        errors['krishiBhavan'] = 'Please select a Krishi-Bhavan'

    if errors:
        logger.error("Validation errors: %s", errors)
        return jsonify({'errors': errors}), 400

    # Hash the password
    hashed_password = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt())

    # Store data in MongoDB
    user = {
        'name': data['name'],
        'email': data['email'],
        'phone': data.get('phone'),
        'address': data['address'],
        'pincode': data['pincode'],
        'password': hashed_password,
        'role': data['role'],
        'krishiBhavanId': data.get('krishiBhavanId') if data['role'] == 'customer' else None,
        'krishiBhavan': data.get('krishiBhavan') if data['role'] == 'seller' else None
    }
    users_collection.insert_one(user)
    logger.info("User registered successfully: %s", user)

    return jsonify({'message': 'User registered successfully', 'id': str(user['_id'])}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    logger.info("Received login data: %s", data)

    # Validate data
    if not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Email and password are required'}), 400

    # Find user in MongoDB
    user = users_collection.find_one({'email': data['email']})
    if not user:
        return jsonify({'error': 'Invalid credentials'}), 401

    # Check password
    if not bcrypt.checkpw(data['password'].encode('utf-8'), user['password']):
        return jsonify({'error': 'Invalid credentials'}), 401

    # Return user data
    user_data = {
        'id': str(user['_id']),
        'email': user['email'],
        'name': user['name'],
        'phone': user['phone'],
        'address': user['address'],
        'pincode': user['pincode'],
        'role': user['role'],
        'krishiBhavanId': user.get('krishiBhavanId'),
        'krishiBhavan': user.get('krishiBhavan')
    }
    logger.info("User logged in successfully: %s", user_data)
    return jsonify(user_data), 200

if __name__ == '__main__':
    app.run(debug=True)
