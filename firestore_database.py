import os
from google.cloud import firestore
from datetime import datetime

class FirestoreDB:
    def __init__(self):
        # Ensure that GOOGLE_APPLICATION_CREDENTIALS is set to your service account JSON
        self.db = firestore.Client()

    def create_user(self, email, password_hash, subscription_tier):
        doc_ref = self.db.collection('users').document(email)
        doc_ref.set({
            'email': email,
            'password': password_hash,
            'subscription_tier': subscription_tier,
            'balance': 10000.0,  # Default starting balance
            'created_at': datetime.now()
        })

    def get_user_by_email(self, email):
        doc = self.db.collection('users').document(email).get()
        if doc.exists:
            return doc.to_dict()
        return None

    def update_user_balance(self, user_id, new_balance):
        """Update a user's balance"""
        doc_ref = self.db.collection('users').document(user_id)
        doc_ref.update({'balance': new_balance})

    def get_portfolio(self, user_id):
        """Get a user's portfolio"""
        doc = self.db.collection('portfolios').document(user_id).get()
        if doc.exists:
            return doc.to_dict()
        return {}

    def add_to_portfolio(self, user_id, symbol, amount):
        """Add an asset to a user's portfolio"""
        doc_ref = self.db.collection('portfolios').document(user_id)
        doc = doc_ref.get()
        
        if doc.exists:
            portfolio = doc.to_dict()
            if symbol in portfolio:
                portfolio[symbol] += amount
            else:
                portfolio[symbol] = amount
            doc_ref.update(portfolio)
        else:
            doc_ref.set({symbol: amount})

    def remove_from_portfolio(self, user_id, symbol, amount):
        """Remove an asset from a user's portfolio"""
        doc_ref = self.db.collection('portfolios').document(user_id)
        doc = doc_ref.get()
        
        if doc.exists:
            portfolio = doc.to_dict()
            if symbol in portfolio:
                portfolio[symbol] -= amount
                if portfolio[symbol] <= 0:
                    portfolio.pop(symbol)
                doc_ref.update(portfolio)

    def save_trade(self, trade_data):
        """Save a trade to the database"""
        doc_ref = self.db.collection('trades').document()
        trade_data['id'] = doc_ref.id
        doc_ref.set(trade_data)
        return doc_ref.id

    def get_user_trades(self, user_id, limit=None):
        """Get a user's trades, optionally limited to a certain number"""
        query = self.db.collection('trades').where('user_id', '==', user_id).order_by('timestamp', direction=firestore.Query.DESCENDING)
        
        if limit:
            query = query.limit(limit)
            
        trades = []
        for doc in query.stream():
            trade = doc.to_dict()
            trade['id'] = doc.id
            trades.append(trade)
            
        return trades

    def get_market_data(self, symbol):
        """Get historical market data for a symbol"""
        doc = self.db.collection('market_data').document(symbol).get()
        if doc.exists:
            return doc.to_dict()
        return None

    def save_market_data(self, symbol, data):
        """Save market data for a symbol"""
        doc_ref = self.db.collection('market_data').document(symbol)
        doc_ref.set(data)

    # Legacy methods kept for backward compatibility
    def create_research_project(self, user_email, prompt, pipeline_result):
        doc_ref = self.db.collection('research_projects').document()
        doc_ref.set({
            'user_email': user_email,
            'prompt': prompt,
            'pipeline_result': pipeline_result,
            'published_paper': None,
            'verification_report': None,
            'peer_review_report': None
        })
        return doc_ref.id

    def get_projects_for_user(self, user_email):
        docs = self.db.collection('research_projects').where('user_email', '==', user_email).stream()
        projects = []
        for d in docs:
            p = d.to_dict()
            p['id'] = d.id
            projects.append(p)
        return projects

    def update_project_field(self, project_id, field_name, value):
        doc_ref = self.db.collection('research_projects').document(project_id)
        doc_ref.update({field_name: value})

    def publish_paper(self, project_id):
        doc_ref = self.db.collection('research_projects').document(project_id)
        doc = doc_ref.get()
        if doc.exists:
            data = doc.to_dict()
            prompt = data.get('prompt', '')
            pipeline_result = data.get('pipeline_result', '')
            published_text = f"**Paper Title:** Automated Discovery from Prompt: '{prompt}'\n\n{pipeline_result}\n\n**Status:** Published to arXiv (Mock)"
            doc_ref.update({'published_paper': published_text})
            return True
        return False