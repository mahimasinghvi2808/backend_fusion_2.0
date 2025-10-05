from flask import Flask, jsonify, request
from flask_jwt_extended import (
    JWTManager, create_access_token,
    jwt_required, get_jwt_identity
)
from flasgger import Swagger
from dotenv import load_dotenv
from weaviate_client import (
    add_market_news, search_market_news,
    add_conversation, get_conversation_history,
    add_recommendation, search_recommendations
)
import os
import datetime
import json

load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['JWT_SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

swagger = Swagger(app)

from database import db
db.init_app(app)
from models import User, Portfolio, Transaction, MarketData, Recommendation, RiskAnalysis

jwt = JWTManager(app)

# Test route
@app.route('/ping', methods=['GET'])
def ping():
    """
    Health check endpoint
    ---
    responses:
      200:
        description: Server is running
    """
    return jsonify({"status": "ok"}), 200

# Authentication routes
@app.route('/register', methods=['POST'])
def register():
    """
    Register a new user
    ---
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            username:
              type: string
            email:
              type: string
            password:
              type: string
    responses:
      201:
        description: User created successfully
    """
    data = request.get_json()
    user = User(
        username=data['username'],
        email=data['email'],
        password_hash=data['password']
    )
    db.session.add(user)
    db.session.commit()
    return jsonify({"message": "User created successfully"}), 201

@app.route('/login', methods=['POST'])
def login():
    """
    Login and get access token
    ---
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            username:
              type: string
            password:
              type: string
    responses:
      200:
        description: Login successful
      401:
        description: Invalid credentials
    """
    data = request.get_json()
    user = User.query.filter_by(username=data['username']).first()
    if user and user.password_hash == data['password']:
        access_token = create_access_token(identity=user.id)
        return jsonify({"access_token": access_token}), 200
    return jsonify({"message": "Invalid credentials"}), 401

# Portfolio routes
@app.route('/portfolios', methods=['GET', 'POST'])
@jwt_required()
def portfolios():
    """
    Get all portfolios or create a new portfolio
    ---
    security:
      - Bearer: []
    responses:
      200:
        description: List of portfolios
      201:
        description: Portfolio created
    """
    user_id = get_jwt_identity()
    if request.method == 'GET':
        portfolios = Portfolio.query.filter_by(user_id=user_id).all()
        return jsonify([p.to_dict() for p in portfolios]), 200
    
    data = request.get_json()
    portfolio = Portfolio(
        user_id=user_id,
        stock_symbol=data['stock_symbol'],
        quantity=data['quantity'],
        avg_buy_price=data['avg_buy_price']
    )
    db.session.add(portfolio)
    db.session.commit()
    return jsonify(portfolio.to_dict()), 201

@app.route('/portfolios/<int:id>', methods=['PUT', 'DELETE'])
@jwt_required()
def portfolio(id):
    """
    Update or delete a portfolio
    ---
    security:
      - Bearer: []
    parameters:
      - name: id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Portfolio updated or deleted
      403:
        description: Unauthorized
      404:
        description: Portfolio not found
    """
    user_id = get_jwt_identity()
    portfolio = Portfolio.query.get_or_404(id)
    if portfolio.user_id != user_id:
        return jsonify({"message": "Unauthorized"}), 403
    
    if request.method == 'PUT':
        data = request.get_json()
        portfolio.quantity = data.get('quantity', portfolio.quantity)
        portfolio.avg_buy_price = data.get('avg_buy_price', portfolio.avg_buy_price)
        db.session.commit()
        return jsonify(portfolio.to_dict()), 200
    
    if request.method == 'DELETE':
        db.session.delete(portfolio)
        db.session.commit()
        return jsonify({"message": "Portfolio deleted"}), 200

# Transaction routes
@app.route('/transactions', methods=['GET', 'POST'])
@jwt_required()
def transactions():
    """
    Get all transactions or create a new transaction
    ---
    security:
      - Bearer: []
    responses:
      200:
        description: List of transactions
      201:
        description: Transaction created
    """
    user_id = get_jwt_identity()
    if request.method == 'GET':
        transactions = Transaction.query.filter_by(user_id=user_id).all()
        return jsonify([t.to_dict() for t in transactions]), 200
    
    data = request.get_json()
    transaction = Transaction(
        user_id=user_id,
        stock_symbol=data['stock_symbol'],
        action=data['action'],
        quantity=data['quantity'],
        price=data['price']
    )
    db.session.add(transaction)
    db.session.commit()
    return jsonify(transaction.to_dict()), 201

# Market data routes
@app.route('/market-data', methods=['POST', 'GET'])
@jwt_required()
def market_data():
    """
    Add or get market data
    ---
    security:
      - Bearer: []
    responses:
      200:
        description: Market data retrieved
      201:
        description: Market data added
    """
    if request.method == 'POST':
        data = request.get_json()
        market_data = MarketData(
            symbol=data['symbol'],
            price=data['price']
        )
        db.session.add(market_data)
        db.session.commit()
        return jsonify(market_data.to_dict()), 201
    
    if request.method == 'GET':
        data = request.get_json()
        market_data = MarketData.query.filter_by(symbol=data['symbol']).order_by(MarketData.timestamp.desc()).first()
        if market_data:
            return jsonify(market_data.to_dict()), 200
        return jsonify({"message": "No data found"}), 404

# Recommendation routes
@app.route('/recommendations', methods=['POST', 'GET'])
@jwt_required()
def recommendations():
    """
    Get all recommendations or create a new recommendation
    ---
    security:
      - Bearer: []
    responses:
      200:
        description: List of recommendations
      201:
        description: Recommendation created
    """
    user_id = get_jwt_identity()
    if request.method == 'POST':
        data = request.get_json()
        recommendation = Recommendation(
            user_id=user_id,
            text=data['text']
        )
        db.session.add(recommendation)
        db.session.commit()
        return jsonify(recommendation.to_dict()), 201
    
    if request.method == 'GET':
        recommendations = Recommendation.query.filter_by(user_id=user_id).all()
        return jsonify([r.to_dict() for r in recommendations]), 200

# Risk analysis routes
@app.route('/risk-analyses', methods=['POST', 'GET'])
@jwt_required()
def risk_analyses():
    """
    Get all risk analyses or create a new risk analysis
    ---
    security:
      - Bearer: []
    responses:
      200:
        description: List of risk analyses
      201:
        description: Risk analysis created
    """
    user_id = get_jwt_identity()
    if request.method == 'POST':
        data = request.get_json()
        risk_analysis = RiskAnalysis(
            user_id=user_id,
            risk_score=data['risk_score'],
            explanation=data['explanation']
        )
        db.session.add(risk_analysis)
        db.session.commit()
        return jsonify(risk_analysis.to_dict()), 201
    
    if request.method == 'GET':
        analyses = RiskAnalysis.query.filter_by(user_id=user_id).all()
        return jsonify([a.to_dict() for a in analyses]), 200

# Vector database routes
@app.route('/vector/news', methods=['POST', 'GET'])
@jwt_required()
def vector_news():
    """
    Add or search market news in vector database
    ---
    security:
      - Bearer: []
    responses:
      200:
        description: News retrieved
      201:
        description: News added
    """
    if request.method == 'POST':
        data = request.get_json()
        add_market_news(
            title=data['title'],
            content=data['content'],
            timestamp=datetime.datetime.now().isoformat(),
            vector=data['vector']
        )
        return jsonify({"message": "News added"}), 201
    
    if request.method == 'GET':
        query_vector = request.args.get('vector')
        if query_vector:
            results = search_market_news(json.loads(query_vector))
            return jsonify({"results": results}), 200
        return jsonify({"message": "No vector query provided"}), 400

@app.route('/vector/conversations', methods=['POST', 'GET'])
@jwt_required()
def vector_conversations():
    """
    Add or get conversation history from vector database
    ---
    security:
      - Bearer: []
    responses:
      200:
        description: Conversation history retrieved
      201:
        description: Conversation saved
    """
    user_id = get_jwt_identity()
    if request.method == 'POST':
        data = request.get_json()
        add_conversation(
            user_id=user_id,
            message=data['message'],
            timestamp=datetime.datetime.now().isoformat(),
            vector=data['vector']
        )
        return jsonify({"message": "Conversation saved"}), 201
    
    if request.method == 'GET':
        history = get_conversation_history(user_id)
        return jsonify({"history": history}), 200

@app.route('/vector/recommendations', methods=['POST', 'GET'])
@jwt_required()
def vector_recommendations():
    """
    Add or search recommendations in vector database
    ---
    security:
      - Bearer: []
    responses:
      200:
        description: Recommendations retrieved
      201:
        description: Recommendation saved
    """
    user_id = get_jwt_identity()
    if request.method == 'POST':
        data = request.get_json()
        add_recommendation(
            user_id=user_id,
            text=data['text'],
            timestamp=datetime.datetime.now().isoformat(),
            vector=data['vector']
        )
        return jsonify({"message": "Recommendation saved"}), 201
    
    if request.method == 'GET':
        query_vector = request.args.get('vector')
        if query_vector:
            results = search_recommendations(json.loads(query_vector), user_id)
            return jsonify({"results": results}), 200
        return jsonify({"message": "No vector query provided"}), 400

if __name__ == '__main__':
    app.run(debug=True)
