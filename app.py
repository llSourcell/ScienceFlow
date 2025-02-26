import os
from openai import OpenAI
from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for
from flask_login import LoginManager, current_user, login_user, login_required, logout_user
from flask_bcrypt import Bcrypt
from models import User, Asset, Trade, Portfolio
from firestore_database import FirestoreDB
from trading_agent import TradingAgent
import tempfile
from datetime import datetime
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'a-very-secret-key'

bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"

db = FirestoreDB()
trading_agent = TradingAgent()

@login_manager.user_loader
def load_user(user_id):
    user_data = db.get_user_by_email(user_id)
    if user_data:
        return User(
            email=user_data['email'],
            password=user_data['password'],
            subscription_tier=user_data.get('subscription_tier', 'free'),
            balance=user_data.get('balance', 10000.0)
        )
    return None

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        subscription_tier = request.form.get("subscription_tier", "free")

        existing_user = db.get_user_by_email(email)
        if existing_user:
            return "Email already registered.", 400

        hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')
        db.create_user(email, hashed_pw, subscription_tier)
        return "Registration successful.", 200
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user_data = db.get_user_by_email(email)
        if user_data and bcrypt.check_password_hash(user_data['password'], password):
            user_obj = User(
                email=user_data['email'],
                password=user_data['password'],
                subscription_tier=user_data.get('subscription_tier', 'free'),
                balance=user_data.get('balance', 10000.0)
            )
            login_user(user_obj)
            return redirect(url_for('dashboard'))
        else:
            return "Invalid credentials.", 401
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route("/")
def index():
    return render_template("trading_dashboard.html", is_authenticated=current_user.is_authenticated)

@app.route("/dashboard")
@login_required
def dashboard():
    # Get user's portfolio
    portfolio_data = db.get_portfolio(current_user.id)
    
    # Get recent trades
    recent_trades = db.get_user_trades(current_user.id, limit=5)
    
    return render_template(
        "trading_dashboard.html", 
        user=current_user,
        portfolio=portfolio_data,
        recent_trades=recent_trades,
        is_authenticated=True
    )

@app.route("/market")
def market():
    # Get list of available assets
    assets = {
        'crypto': trading_agent.supported_assets['crypto'],
        'stocks': trading_agent.supported_assets['stocks'],
        'forex': trading_agent.supported_assets['forex']
    }
    
    return render_template(
        "market.html", 
        assets=assets,
        is_authenticated=current_user.is_authenticated
    )

@app.route("/analyze_market", methods=["POST"])
def analyze_market():
    symbol = request.json.get("symbol")
    user_prompt = request.json.get("prompt", "")
    
    if not symbol:
        return jsonify({"error": "No symbol provided"}), 400
    
    analysis_result = trading_agent.analyze_market(symbol, user_prompt)
    
    return jsonify(analysis_result)

@app.route("/execute_trade", methods=["POST"])
@login_required
def execute_trade():
    symbol = request.json.get("symbol")
    trade_type = request.json.get("trade_type")  # buy or sell
    amount = float(request.json.get("amount", 0))
    
    if not symbol or not trade_type or amount <= 0:
        return jsonify({"error": "Invalid trade parameters"}), 400
    
    # Get current price
    current_price = trading_agent.get_current_price(symbol)
    if current_price is None:
        return jsonify({"error": f"Could not get current price for {symbol}"}), 400
    
    total_cost = amount * current_price
    
    # Check if user has enough balance for buy
    if trade_type.lower() == "buy":
        if current_user.balance < total_cost:
            return jsonify({"error": "Insufficient balance"}), 400
    
    # Check if user has enough assets for sell
    if trade_type.lower() == "sell":
        portfolio = db.get_portfolio(current_user.id)
        if symbol not in portfolio or portfolio[symbol] < amount:
            return jsonify({"error": f"Insufficient {symbol} in portfolio"}), 400
    
    # Execute the trade
    trade_result = trading_agent.execute_trade(current_user.id, symbol, trade_type, amount)
    
    # Update user's balance and portfolio
    if trade_type.lower() == "buy":
        db.update_user_balance(current_user.id, current_user.balance - total_cost)
        db.add_to_portfolio(current_user.id, symbol, amount)
    else:  # sell
        db.update_user_balance(current_user.id, current_user.balance + total_cost)
        db.remove_from_portfolio(current_user.id, symbol, amount)
    
    # Save the trade
    db.save_trade(trade_result)
    
    return jsonify({
        "success": True,
        "trade": trade_result,
        "new_balance": current_user.balance - total_cost if trade_type.lower() == "buy" else current_user.balance + total_cost
    })

@app.route("/portfolio")
@login_required
def portfolio():
    # Get user's portfolio
    portfolio_data = db.get_portfolio(current_user.id)
    
    # Get current prices for all assets in portfolio
    portfolio_with_prices = {}
    total_value = 0
    
    for symbol, amount in portfolio_data.items():
        price = trading_agent.get_current_price(symbol)
        if price is None:
            price = 0
        
        value = amount * price
        total_value += value
        
        portfolio_with_prices[symbol] = {
            "amount": amount,
            "price": price,
            "value": value
        }
    
    return render_template(
        "portfolio.html",
        portfolio=portfolio_with_prices,
        total_value=total_value,
        balance=current_user.balance,
        is_authenticated=True
    )

@app.route("/trade_history")
@login_required
def trade_history():
    # Get all user's trades
    trades = db.get_user_trades(current_user.id)
    
    return render_template(
        "trade_history.html",
        trades=trades,
        is_authenticated=True
    )

@app.route("/get_price", methods=["GET"])
def get_price():
    symbol = request.args.get("symbol")
    
    if not symbol:
        return jsonify({"error": "No symbol provided"}), 400
    
    price = trading_agent.get_current_price(symbol)
    
    if price is None:
        return jsonify({"error": f"Could not get price for {symbol}"}), 400
    
    return jsonify({"symbol": symbol, "price": price})

if __name__ == "__main__":
    # Before running:
    # export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service_account.json
    # export OPENAI_API_KEY=your_openai_key
    # pip install -r requirements.txt
    # flask run --host=0.0.0.0 --port=8080
    app.run(host="0.0.0.0", port=8080, debug=True)