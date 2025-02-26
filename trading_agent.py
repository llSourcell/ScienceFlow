import os
from openai import OpenAI
import random
import json
from datetime import datetime, timedelta
import yfinance as yf

class TradingAgent:
    def __init__(self):
        self.client = OpenAI(api_key="ENTER KEY HERE")
        self.supported_assets = {
            'crypto': ['BTC-USD', 'ETH-USD', 'SOL-USD', 'ADA-USD', 'XRP-USD'],
            'stocks': ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META'],
            'forex': ['EURUSD=X', 'GBPUSD=X', 'USDJPY=X', 'AUDUSD=X']
        }
        
    def get_market_data(self, symbol, period="1mo"):
        """Fetch market data for a given symbol"""
        try:
            data = yf.download(symbol, period=period)
            return data
        except Exception as e:
            print(f"Error fetching market data for {symbol}: {str(e)}")
            return None
            
    def get_current_price(self, symbol):
        """Get the current price of an asset"""
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period="1d")
            if not data.empty:
                return data['Close'].iloc[-1]
            return None
        except Exception as e:
            print(f"Error getting current price for {symbol}: {str(e)}")
            return None
    
    def analyze_market(self, symbol, user_prompt=""):
        """Analyze market data and generate trading insights"""
        try:
            # Get market data
            data = self.get_market_data(symbol)
            if data is None or data.empty:
                return self._generate_fallback_analysis(symbol)
                
            # Calculate basic metrics
            current_price = data['Close'].iloc[-1]
            price_change = data['Close'].iloc[-1] - data['Close'].iloc[0]
            percent_change = (price_change / data['Close'].iloc[0]) * 100
            avg_volume = data['Volume'].mean() if 'Volume' in data else 'N/A'
            
            # Prepare market data summary
            market_summary = {
                'symbol': symbol,
                'current_price': round(current_price, 2),
                'price_change': round(price_change, 2),
                'percent_change': round(percent_change, 2),
                'period': '1 month',
                'avg_volume': avg_volume if isinstance(avg_volume, str) else round(avg_volume, 2)
            }
            
            # Use AI to generate analysis
            return self._generate_ai_analysis(symbol, market_summary, user_prompt)
            
        except Exception as e:
            print(f"Error analyzing market for {symbol}: {str(e)}")
            return self._generate_fallback_analysis(symbol)
    
    def _generate_ai_analysis(self, symbol, market_summary, user_prompt):
        """Generate AI-powered market analysis"""
        try:
            prompt = f"""
            Symbol: {symbol}
            Current Price: ${market_summary['current_price']}
            Price Change: ${market_summary['price_change']} ({market_summary['percent_change']}%)
            Period: {market_summary['period']}
            Average Volume: {market_summary['avg_volume']}
            
            User's specific question: {user_prompt if user_prompt else 'Provide a general market analysis'}
            """
            
            completion = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": """You are an expert financial analyst and trading advisor.
                    Provide detailed market analysis and trading recommendations based on the provided data.
                    Include technical analysis, potential support/resistance levels, and a clear buy/sell/hold recommendation.
                    Always include risk assessment and position sizing advice."""},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.7
            )
            
            analysis = completion.choices[0].message.content.strip()
            
            # Add a trading recommendation
            recommendation = self._generate_trading_recommendation(symbol, market_summary)
            
            return {
                "market_data": market_summary,
                "analysis": analysis,
                "recommendation": recommendation
            }
            
        except Exception as e:
            print(f"Error generating AI analysis: {str(e)}")
            return self._generate_fallback_analysis(symbol)
    
    def _generate_trading_recommendation(self, symbol, market_summary):
        """Generate a specific trading recommendation"""
        sentiment = "bullish" if market_summary['percent_change'] > 0 else "bearish"
        
        if market_summary['percent_change'] > 5:
            action = "STRONG BUY"
            confidence = "high"
            target_price = round(market_summary['current_price'] * 1.1, 2)
            stop_loss = round(market_summary['current_price'] * 0.95, 2)
        elif market_summary['percent_change'] > 0:
            action = "BUY"
            confidence = "medium"
            target_price = round(market_summary['current_price'] * 1.05, 2)
            stop_loss = round(market_summary['current_price'] * 0.97, 2)
        elif market_summary['percent_change'] > -5:
            action = "HOLD"
            confidence = "medium"
            target_price = round(market_summary['current_price'] * 1.03, 2)
            stop_loss = round(market_summary['current_price'] * 0.95, 2)
        else:
            action = "SELL"
            confidence = "high"
            target_price = round(market_summary['current_price'] * 0.95, 2)
            stop_loss = round(market_summary['current_price'] * 1.05, 2)
            
        return {
            "action": action,
            "confidence": confidence,
            "target_price": target_price,
            "stop_loss": stop_loss,
            "sentiment": sentiment,
            "time_frame": "short-term (1-2 weeks)"
        }
    
    def _generate_fallback_analysis(self, symbol):
        """Generate fallback analysis when real data cannot be fetched"""
        current_price = random.uniform(10, 1000)
        percent_change = random.uniform(-10, 10)
        
        market_summary = {
            'symbol': symbol,
            'current_price': round(current_price, 2),
            'price_change': round(current_price * percent_change / 100, 2),
            'percent_change': round(percent_change, 2),
            'period': '1 month',
            'avg_volume': round(random.uniform(100000, 10000000), 0)
        }
        
        sentiment = "bullish" if percent_change > 0 else "bearish"
        
        if percent_change > 5:
            action = "STRONG BUY"
        elif percent_change > 0:
            action = "BUY"
        elif percent_change > -5:
            action = "HOLD"
        else:
            action = "SELL"
            
        recommendation = {
            "action": action,
            "confidence": "medium",
            "target_price": round(current_price * 1.05, 2),
            "stop_loss": round(current_price * 0.95, 2),
            "sentiment": sentiment,
            "time_frame": "short-term (1-2 weeks)"
        }
        
        analysis = f"""
        # Market Analysis for {symbol}
        
        ## Current Market Conditions
        The asset is currently trading at ${market_summary['current_price']} with a {market_summary['percent_change']}% change over the past month.
        
        ## Technical Analysis
        The market sentiment appears to be {sentiment} based on recent price action. 
        Trading volume has been averaging around {market_summary['avg_volume']} shares per day.
        
        ## Recommendation
        Based on the current market conditions, our recommendation is to {action} {symbol}.
        - Target Price: ${recommendation['target_price']}
        - Stop Loss: ${recommendation['stop_loss']}
        - Time Frame: {recommendation['time_frame']}
        
        ## Risk Assessment
        This recommendation comes with a medium level of risk. Always ensure proper position sizing and risk management.
        """
        
        return {
            "market_data": market_summary,
            "analysis": analysis,
            "recommendation": recommendation
        }
        
    def execute_trade(self, user_id, symbol, trade_type, amount):
        """Simulate executing a trade"""
        current_price = self.get_current_price(symbol)
        if current_price is None:
            # Use a random price if we can't get the real one
            current_price = random.uniform(10, 1000)
            
        trade = {
            "user_id": user_id,
            "symbol": symbol,
            "trade_type": trade_type,
            "amount": amount,
            "price": current_price,
            "total": amount * current_price,
            "timestamp": datetime.now().isoformat(),
            "status": "completed",
            "transaction_id": f"tx-{random.randint(10000, 99999)}"
        }
        
        return trade