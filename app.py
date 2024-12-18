import os
from openai import OpenAI
from flask import Flask, render_template, request, jsonify, send_file
from flask_login import LoginManager, current_user, login_user, login_required, logout_user
from flask_bcrypt import Bcrypt
from models import User
from firestore_database import FirestoreDB
from sciflow_agent import ScienceFlowAgent
from verifier import Verifier
from reviewer_agents import ReviewerAgents
from weasyprint import HTML, CSS
from jinja2 import Template
import tempfile
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'a-very-secret-key'

bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"



db = FirestoreDB()
agent = ScienceFlowAgent()
verifier = Verifier()
reviewer = ReviewerAgents()

@login_manager.user_loader
def load_user(user_id):
    user_data = db.get_user_by_email(user_id)
    if user_data:
        return User(
            email=user_data['email'],
            password=user_data['password'],
            subscription_tier=user_data.get('subscription_tier', 'free')
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
    return "Register endpoint. Send a POST request to register."

@app.route("/login", methods=["POST"])
def login():
    email = request.form.get("email")
    password = request.form.get("password")

    user_data = db.get_user_by_email(email)
    if user_data and bcrypt.check_password_hash(user_data['password'], password):
        user_obj = User(
            email=user_data['email'],
            password=user_data['password'],
            subscription_tier=user_data.get('subscription_tier', 'free')
        )
        login_user(user_obj)
        return "Login successful.", 200
    else:
        return "Invalid credentials.", 401

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return "Logged out."

@app.route("/discovery")
def discovery_page():
    return render_template("discovery_pipeline.html", is_authenticated=current_user.is_authenticated)

def generate_paper_title(pipeline_result: str, client: OpenAI) -> str:
    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an expert mathematics paper title generator. Generate a formal, academic title that accurately reflects the mathematical content and is styled like a research paper title."},
                {"role": "user", "content": f"""Based on this mathematical research:

{pipeline_result}

Generate a formal mathematics paper title that:
1. Accurately reflects the specific conjecture or finding
2. Uses proper mathematical terminology
3. Is styled like a research paper title
4. Is concise but descriptive
5. Captures the novelty of the work

Return only the title, nothing else."""}
            ],
            max_tokens=100,
            temperature=0.7
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error generating title: {str(e)}")
        return "A Novel Conjecture in Number Theory"

@app.route("/run_pipeline", methods=["POST"])
def run_pipeline():
    prompt = request.json.get("prompt")
    if not prompt:
        return jsonify({"error": "No prompt provided"}), 400

    client = OpenAI(api_key="ENTER KEY")
    
    pipeline_result = agent.generate_pipeline(prompt)
    verification_result = verifier.verify(pipeline_result)
    peer_review = reviewer.get_peer_review(pipeline_result, verification_result)
    
    # Generate title using GPT
    paper_title = generate_paper_title(pipeline_result, client)

    return jsonify({
        "pipeline_result": pipeline_result,
        "verification_report": verification_result,
        "peer_review_report": peer_review,
        "paper_title": paper_title
    })

def format_paper_html(title, content, verification, review):
    # LaTeX-style template for the paper
    template = Template("""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body { font-family: "Times New Roman", Times, serif; line-height: 1.5; margin: 60px; }
            .title { font-size: 24px; font-weight: bold; text-align: center; margin-bottom: 20px; }
            .date { text-align: center; margin-bottom: 40px; }
            .abstract { margin: 20px 40px; }
            .section { margin-top: 30px; }
            .section-title { font-size: 18px; font-weight: bold; margin-bottom: 15px; }
            .math { font-style: italic; }
            @page { margin: 60px; size: letter; }
            .verification { background-color: #f8f9fa; padding: 20px; margin: 20px 0; }
            .peer-review { background-color: #f8f9fa; padding: 20px; margin: 20px 0; }
        </style>
    </head>
    <body>
        <div class="title">{{ title }}</div>
        <div class="date">{{ date }}</div>
        
        <div class="section">
            <div class="section-title">Abstract</div>
            <div class="abstract">
                This paper presents a novel mathematical conjecture generated through an AI-assisted 
                mathematical discovery pipeline. The conjecture and its implications are formally stated,
                verified, and peer-reviewed through a systematic process.
            </div>
        </div>

        <div class="section">
            <div class="section-title">Main Content</div>
            {{ content | replace('\n', '<br>') | safe }}
        </div>

        <div class="section">
            <div class="section-title">Verification Results</div>
            <div class="verification">
                {{ verification | replace('\n', '<br>') | safe }}
            </div>
        </div>

        <div class="section">
            <div class="section-title">Peer Review</div>
            <div class="peer-review">
                {{ review | replace('\n', '<br>') | safe }}
            </div>
        </div>
    </body>
    </html>
    """)
    
    return template.render(
        title=title,
        content=content,
        verification=verification,
        review=review,
        date=datetime.now().strftime("%B %d, %Y")
    )

@app.route('/generate_pdf', methods=['POST'])
def generate_pdf():
    try:
        data = request.json
        html_content = format_paper_html(
            data['title'],
            data['content'],
            data['verification'],
            data['review']
        )
        
        # Create temporary files for the PDF generation
        with tempfile.NamedTemporaryFile(suffix='.html') as html_file, \
             tempfile.NamedTemporaryFile(suffix='.pdf') as pdf_file:
            
            # Write HTML content to temporary file
            html_file.write(html_content.encode('utf-8'))
            html_file.flush()
            
            # Generate PDF
            HTML(filename=html_file.name).write_pdf(
                pdf_file.name,
                stylesheets=[CSS(string='@page { size: letter; margin: 1in; }')])
            
            # Return the PDF file
            return send_file(
                pdf_file.name,
                mimetype='application/pdf',
                as_attachment=True,
                download_name=f"paper_{datetime.now().strftime('%Y%m%d')}.pdf"
            )
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    # Before running:
    # export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service_account.json
    # export OPENAI_API_KEY=your_openai_key
    # pip install -r requirements.txt
    # flask run --host=0.0.0.0 --port=8080
    app.run(host="0.0.0.0", port=8080, debug=True)