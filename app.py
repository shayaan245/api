# app.py
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from sqlalchemy import func
import re

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
app.config['SECRET_KEY'] = 'your_secret_key_here'
db = SQLAlchemy(app)

c
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)


class Company(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    employees = db.Column(db.Integer)
    users = relationship("User", backref="company")


class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)


class ClientUser(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False)
    updated_at = db.Column(db.DateTime, nullable=True)
    deleted_at = db.Column(db.DateTime, nullable=True)
    active = db.Column(db.Boolean, default=True)


# Define API endpoints
@app.route('/users', methods=['GET'])
def list_users():
    username_filter = request.args.get('username')
    if username_filter:
        users = User.query.filter(User.username.ilike(f'%{username_filter}%')).all()
    else:
        users = User.query.all()
    return jsonify([user.username for user in users])


@app.route('/users', methods=['PUT'])
def update_user():
    # Assuming JSON payload with user data
    data = request.json
    user_id = data.get('id')
    if user_id:
        user = User.query.get(user_id)
        if user:
            user.username = data.get('username', user.username)
            db.session.commit()
            return jsonify({'message': 'User updated successfully'})
    return jsonify({'error': 'User not found'}), 404


@app.route('/clients', methods=['POST'])
def create_client():
    if request.headers.get('X-Role') != 'ROLE_ADMIN':
        return jsonify({'error': 'Unauthorized access'}), 403

    data = request.json
    company_id = data.get('company_id')
    if company_id:
        existing_client = Client.query.filter_by(company_id=company_id).first()
        if existing_client:
            return jsonify({'error': 'Company already has a client'}), 400
        else:
            new_client = Client(
                name=data['name'],
                user_id=data['user_id'],
                company_id=company_id,
                email=data['email'],
                phone=data['phone']
            )
            db.session.add(new_client)
            db.session.commit()
            return jsonify({'message': 'Client created successfully'})
    return jsonify({'error': 'Invalid data provided'}), 400


@app.route('/clients/<int:client_id>', methods=['PATCH'])
def update_client(client_id):
    data = request.json
    client = Client.query.get(client_id)
    if client:
        for key, value in data.items():
            setattr(client, key, value)
        db.session.commit()
        return jsonify({'message': 'Client updated successfully'})
    return jsonify({'error': 'Client not found'}), 404



def search_companies_by_employees(min_employees, max_employees):
    return Company.query.filter(Company.employees.between(min_employees, max_employees)).all()


def search_clients_by_user(user_id):
    return Client.query.filter_by(user_id=user_id).all()


def search_clients_by_name(company_name):
    return Client.query.join(Company).filter(Company.name.ilike(f'%{company_name}%')).all()


def validate_email(email):
    pattern = r'^\S+@\S+\.\S+$'
    return bool(re.match(pattern, email))

import pytest


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client


def test_list_users(client):
    response = client.get('/users')
    assert response.status_code == 200


def test_update_user(client):
    user = User(username='test_user')
    db.session.add(user)
    db.session.commit()

    updated_username = 'updated_user'
    response = client.put('/users', json={'id': user.id, 'username': updated_username})
    assert response.status_code == 200

    updated_user = User.query.get(user.id)
    assert updated_user.username == updated_username

if __name__ == '__main__':
    app.run(debug=True)
