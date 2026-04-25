# SpendLog

SpendLog is a modern, AI-powered personal finance and expense tracking application. It features a stunning, futuristic "cyber-glass" user interface and leverages AI to provide an intelligent, frictionless expense tracking experience.

## ✨ Key Features

- **🧠 Smart Entry (AI)**: Log your transactions naturally. Just type *"Spent $25 on groceries yesterday"* and the AI will automatically parse the date, category, and amount to log it for you.
- **🤖 AI Financial Advisor**: A built-in chat assistant that analyzes your recent spending habits and answers your personal financial questions in real-time.
- **📊 Advanced Data Visualization**: Beautiful, interactive charts powered by Chart.js. Features grouped bar charts with logarithmic scaling to perfectly balance massive outliers with small daily expenses.
- **📱 Fully Responsive UI**: A meticulously designed glassmorphism interface that looks and functions perfectly on desktops, tablets, and mobile devices.
- **🔒 Secure Authentication**: Built-in user registration and login system with cryptographic password hashing to keep your financial data private.
- **☁️ Cloud Ready**: Pre-configured to support seamless deployment to Render with PostgreSQL database support.

## 🛠️ Technology Stack

- **Backend**: Python, Flask, Flask-SQLAlchemy, Flask-Login
- **Frontend**: HTML5, Vanilla CSS (Glassmorphism UI), JavaScript
- **Database**: MySQL (Local Development) -> PostgreSQL (Production)
- **Data Visualization**: Chart.js (with `chartjs-plugin-datalabels`)

## 🚀 Local Setup & Installation

Follow these steps to run SpendLog on your local machine:

### 1. Clone the repository
```bash
git clone https://github.com/vishwa-panchal10/SpendLog.git
cd SpendLog
```

### 2. Create a Virtual Environment
```bash
python -m venv venv
# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Setup Environment Variables
Create a `.env` file in the root directory of the project and add your Google Gemini API key:
```env
SECRET_KEY=your_flask_secret_key_here
```
*(You can get a free API key from [Google AI Studio](https://aistudio.google.com/))*

### 5. Run the Application
```bash
python app.py
```
The application will be running at `http://localhost:5000`.

## ☁️ Deployment (Render)

This project is configured for easy deployment on [Render](https://render.com/).

1. Connect your GitHub repository to Render as a **Web Service**.
2. **Build Command**: `pip install -r requirements.txt`
3. **Start Command**: `gunicorn app:app`
4. Add your **Environment Variables** in the Render dashboard:
   - `GEMINI_API_KEY`
   - `SECRET_KEY`
   - `DATABASE_URL` (If attaching a Render PostgreSQL database)

---
*Developed with a focus on modern design and intelligent automation.*
