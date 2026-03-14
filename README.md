# CORE AI - Intelligence Coaching & Personalized Learning

CORE AI is a state-of-the-art AI-powered educational platform designed to provide students with an immersive, personalized learning experience. By leveraging Retrieval-Augmented Generation (RAG) and modern AI models, the platform transforms static textbooks into interactive learning materials. 

## 🚀 Key Features

- **AI-Powered Quiz Generation:** Automatically generates chapter-wise quizzes (MCQs, Fill-in-the-blanks, Short/Long Answers) directly from PDF textbooks.
- **Dynamic Subject Mastery:** Track your progress across multiple subjects including Science, Math, English, Hindi, and Social Science.
- **Instant Doubt Solving:** An AI tutor available 24/7 to answer chapter-specific queries.
- **Multilingual Support:** Specialized support for the Hindi subject with pure Devanagari script output.
- **Unique Question Variety:** Every quiz generation uses randomized extraction to ensure you never get the same questions twice.
- **Secure Authentication & Access:** Built-in Role-Based Access Control (RBAC) and secure user authentication.
- **Performance Analytics:** Visual dashboard tracking accuracy, chapters completed, and recent learning activity.

## 🛠️ Tech Stack

### Frontend
- **React (Vite)**
- **React Router DOM**
- **Axios** (API communication)
- **Vanilla CSS** (Custom Dark-themed UI)

### Backend & Database
- **FastAPI** (High-performance Python API)
- **MongoDB** (Primary NoSQL Database for scalable data storage)
- **SQLAlchemy / SQLite** (Legacy/Secondary relational data mapping)
- **LangChain & HuggingFace** (AI Engine)
- **pdfplumber** (PDF content extraction)

## 📂 Project Structure

```text
AI-CHATBOAT_WORKING/
├── backend/
│   ├── auth/                       # User authentication and JWT models
│   │   ├── auth.py
│   │   ├── models.py
│   │   └── schemas.py
│   ├── personalised_learning/      # Core logic and subject-wise textbook storage
│   │   ├── Englishs/
│   │   ├── Hindis/
│   │   ├── Maths/
│   │   ├── Sciences/
│   │   ├── Social science/
│   │   └── ... (routes, schemas, and local DBs)
│   ├── rag/                        # Retrieval-Augmented Generation module
│   │   ├── advanced_nlp.py
│   │   ├── krutidev_converter.py
│   │   ├── pdf_loader.py
│   │   └── vector_store.py
│   ├── rbac/                       # Role-Based Access Control
│   │   └── roles.py
│   ├── .env                        # Environment variables (API keys, Mongo URI)
│   ├── database.py                 # Database connection logic
│   ├── main.py                     # FastAPI application entry point
│   ├── requirements.txt            # Python dependencies
│   └── test_mongo_connection.py    # MongoDB connection test script
├── frontend/                       # Vite React Application
│   ├── public/
│   ├── src/
│   ├── package.json
│   └── vite.config.js
├── std 9/                          # Standard 9 curriculum materials
├── run_ai_chatbot.bat              # Batch script to boot up both frontend and backend
└── README.md


⚙️ Setup Instructions
Prerequisites
Python 3.8+

Node.js & npm

MongoDB instance (Local or Atlas)

Backend Setup
1. Navigate to the backend directory:
cd backend
2. Create a .env file (you can use .env.example as a template) and add your environment variables:

HUGGINGFACEHUB_API_TOKEN=your_token_here
MONGODB_URI=your_mongodb_connection_string

3. Install dependencies:

pip install -r requirements.txt
(Optional) 

4. Test your MongoDB connection:

python test_mongo_connection.py

5. Start the server:

uvicorn main:app --reload

Frontend Setup

1. Navigate to the frontend directory:

cd frontend

2. Install dependencies:

npm install

3. Run the development server:

npm run dev



© 2026 CORE AI - Advanced Agentic Coding Project.