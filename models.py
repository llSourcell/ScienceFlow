from flask_login import UserMixin

class User(UserMixin):
    def __init__(self, email, password, subscription_tier):
        self.id = email  # Using email as the user id
        self.email = email
        self.password = password
        self.subscription_tier = subscription_tier