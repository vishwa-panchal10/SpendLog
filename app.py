from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date, timedelta
import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
if os.environ.get("GEMINI_API_KEY"):
    genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-2.5-flash')

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'my_super_secret_key_expense_tracker_123')

# Database configuration (supports Render PostgreSQL or local MySQL fallback)
db_url = os.environ.get('DATABASE_URL', 'mysql+pymysql://root:@localhost:3306/expense_tracker')
if db_url.startswith('postgres://'):
    db_url = db_url.replace('postgres://', 'postgresql://', 1)
    
app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    category = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            if user.is_admin:
                 return redirect(url_for('admin'))
            return redirect(url_for('dashboard'))
        else:
            flash('Login failed. Check your email and password.', 'danger')
            
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'danger')
            return redirect(url_for('register'))
            
        new_user = User(
            name=name, 
            email=email, 
            password_hash=generate_password_hash(password, method='pbkdf2:sha256')
        )
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('login'))
        
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/admin')
@login_required
def admin():
    if not current_user.is_admin:
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard'))
    
    all_users = User.query.all()
    user_count = len(all_users)
    total_expenses = db.session.query(db.func.sum(Expense.amount)).scalar() or 0
    return render_template('admin.html', user_count=user_count, total_expenses=total_expenses, users=all_users)

@app.route('/add_expense', methods=['POST'])
@login_required
def add_expense():
    date_str = request.form.get('date')
    category = request.form.get('category')
    amount = float(request.form.get('amount') or 0)
    action = request.form.get('action') # 'submit' or 'add_another'
    
    expense_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    
    new_expense = Expense(user_id=current_user.id, date=expense_date, category=category, amount=amount)
    db.session.add(new_expense)
    db.session.commit()
    
    flash('Expense added successfully!', 'success')
    
    if action == 'add_another':
        return render_template('dashboard.html', add_more=True)
    return redirect(url_for('dashboard'))

# API endpoint for visualizing data
@app.route('/api/expenses')
@login_required
def api_expenses():
    user_filter = request.args.get('user_id', None)
    
    if current_user.is_admin and user_filter:
        if user_filter == 'all':
            expenses = Expense.query.all()
        else:
             expenses = Expense.query.filter_by(user_id=int(user_filter)).all()
    else:
        expenses = Expense.query.filter_by(user_id=current_user.id).all()
        
    data = []
    for e in expenses:
        data.append({
            'date': e.date.strftime('%Y-%m-%d'),
            'category': e.category,
            'amount': e.amount
        })
    return jsonify(data)

# API endpoint for smart text entry
@app.route('/api/smart_add', methods=['POST'])
@login_required
def api_smart_add():
    data = request.get_json()
    text = data.get('text', '')
    
    if not text:
        return jsonify({'status': 'error', 'message': 'No text provided'}), 400
        
    try:
        today_str = date.today().strftime('%Y-%m-%d')
        prompt = f"""
        Extract expense details from the following text. 
        Assume today's date is {today_str}.
        Return ONLY a JSON object with the following keys, no markdown formatting or other text:
        - date (format: YYYY-MM-DD)
        - category (string, e.g., Food, Transport, Utilities, Entertainment, Shopping)
        - amount (number)
        
        Text: "{text}"
        """
        response = model.generate_content(prompt)
        result_text = response.text.strip()
        
        # Remove markdown if the model includes it despite instructions
        if result_text.startswith("```json"):
            result_text = result_text[7:-3].strip()
        elif result_text.startswith("```"):
            result_text = result_text[3:-3].strip()
            
        parsed_data = json.loads(result_text)
        
        expense_date = datetime.strptime(parsed_data['date'], '%Y-%m-%d').date()
        category = parsed_data['category']
        amount = float(parsed_data['amount'])
        
        new_expense = Expense(user_id=current_user.id, date=expense_date, category=category, amount=amount)
        db.session.add(new_expense)
        db.session.commit()
        
        return jsonify({
            'status': 'success', 
            'message': f"Added ${amount:.2f} for {category} on {expense_date}",
            'data': parsed_data
        })
    except Exception as e:
        print("Smart add error:", str(e))
        return jsonify({'status': 'error', 'message': 'Failed to process text. Please try again.'}), 500

# API endpoint for chat advisor
@app.route('/api/chat', methods=['POST'])
@login_required
def api_chat():
    data = request.get_json()
    message = data.get('message', '')
    
    if not message:
        return jsonify({'reply': "I didn't catch that. How can I help with your finances?"})
        
    try:
        # Get recent expenses for context (limit to last 50 to avoid huge prompts)
        expenses = Expense.query.filter_by(user_id=current_user.id).order_by(Expense.date.desc()).limit(50).all()
        
        expense_str = "Recent Expenses:\\n"
        total = 0
        for e in expenses:
            expense_str += f"- {e.date}: ${e.amount:.2f} ({e.category})\\n"
            total += e.amount
        
        expense_str += f"\\nTotal of recent expenses: ${total:.2f}"
            
        prompt = f"""
        You are ExpenceIQ, a helpful and concise AI financial advisor. 
        Answer the user's question based on their recent expense data below. 
        Keep your answer brief, friendly, and formatted as plain text (or simple markdown).
        
        {expense_str}
        
        User: "{message}"
        ExpenceIQ:
        """
        
        response = model.generate_content(prompt)
        return jsonify({'reply': response.text})
    except Exception as e:
        print("Chat error:", str(e))
        return jsonify({'reply': "Sorry, I'm having trouble analyzing your data right now. Please try again later."})


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Create default admin if not exists
        if not User.query.filter_by(email='admin@tracker.com').first():
            admin = User(name='Admin', email='admin@tracker.com', password_hash=generate_password_hash('admin', method='pbkdf2:sha256'), is_admin=True)
            db.session.add(admin)
            db.session.commit()
    app.run(debug=True, port=5000)
