from flask_login import UserMixin
from datetime import datetime

class User(UserMixin):
    def __init__(self, email, password, subscription_tier, balance=10000.0):
        self.id = email  # Using email as the user id
        self.email = email
        self.password = password
        self.subscription_tier = subscription_tier
        self.balance = balance  # Default starting balance in USD

class Asset:
    def __init__(self, symbol, name, asset_type, current_price=0.0):
        self.symbol = symbol
        self.name = name
        self.asset_type = asset_type  # crypto, stock, forex, etc.
        self.current_price = current_price
        
class Trade:
    def __init__(self, user_id, asset_symbol, trade_type, amount, price, timestamp=None):
        self.user_id = user_id
        self.asset_symbol = asset_symbol
        self.trade_type = trade_type  # buy or sell
        self.amount = amount  # quantity of the asset
        self.price = price  # price per unit
        self.timestamp = timestamp or datetime.now()
        self.total = amount * price
        
class Portfolio:
    def __init__(self, user_id, holdings=None):
        self.user_id = user_id
        self.holdings = holdings or {}  # Dictionary mapping asset symbols to quantities
        
    def add_holding(self, symbol, amount):
        if symbol in self.holdings:
            self.holdings[symbol] += amount
        else:
            self.holdings[symbol] = amount
            
    def remove_holding(self, symbol, amount):
        if symbol in self.holdings:
            self.holdings[symbol] -= amount
            if self.holdings[symbol] <= 0:
                del self.holdings[symbol]
                
    def get_total_value(self, asset_prices):
        total = 0
        for symbol, amount in self.holdings.items():
            if symbol in asset_prices:
                total += amount * asset_prices[symbol]
        return total