import os
import pdfplumber
import json
import re
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from dotenv import load_dotenv

# LangChain & AI Imports
from langchain_core.prompts import PromptTemplate
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Local Imports
import models, auth, database

# Load environment variables
load_dotenv()

app = FastAPI()

# Database Setup
models.Base.metadata.create_all(bind=database.engine)

# CORS Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# DB Dependency
def get_db():
    db = database.SessionLocal()
    try: 
        yield db
    finally: 
        db.close()

# ---------------- AI CONFIGURATION ----------------
# ---------------- AI CONFIGURATION UPDATE ----------------
SUBJECT_CONFIG = {
    "Science": {"folder": "Sciences", "files": {f"Chapter {i}": f"sci{(i)}.pdf" for i in range(1, 13)}},
    "Math": {"folder": "Maths", "files": {f"Chapter {i}": f"math{i}.pdf" for i in range(1, 13)}},
    "English": {"folder": "Englishs", "files": {f"Chapter {i}": f"iebe10{i}.pdf" for i in range(1, 10)}},
    
    # Naye Subjects yahan add karein
    "Hindi": {
        "folder": "Hindis", 
        "files": {f"Chapter {i}": f"hin ({i}).pdf" for i in range(1, 14)} # adjust file names as per your PDFs
    },
    "Social Science": {
        "folder": "Social science", 
        "files": {f"Chapter {i}": f"iess40{i}.pdf" for i in range(1, 6)}
    }
}
FORMATS = {
    "MCQ": '[{"question": "...", "options": ["A) ..", "B) .."], "answer": "A", "explanation": "..."}]',
    "Fill in blanks": '[{"question": "The ____ is...", "answer": "word", "explanation": "..."}]',
    "Short Answer": '[{"question": "...", "answer": "...", "explanation": "..."}]',
    "Long Answer": '[{"question": "...", "answer": "...", "explanation": "..."}]'
}

# AI Model Setup
llm = HuggingFaceEndpoint(
    repo_id="EssentialAI/rnj-1-instruct", 
    task="text-generation", 
    max_new_tokens=2048, 
    temperature=0.4
)
model = ChatHuggingFace(llm=llm)

# Helper: Extract PDF Text
def extract_pdf_text(path):
    if not os.path.exists(path):
        return None
    text = ""
    try:
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text: text += page_text + "\n"
        splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
        return " ".join(splitter.split_text(text)[:3])
    except Exception:
        return None

# ---------------- AUTH ROUTES ----------------

@app.post("/register")
def register(user_data: dict, db: Session = Depends(get_db)):
    existing_user = db.query(models.User).filter(models.User.email == user_data.get("email")).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = models.User(
        name=user_data.get("name"),
        email=user_data.get("email"),
        password=user_data.get("password"),
        role=user_data.get("role"),
        class_level=user_data.get("class") if user_data.get("role") == "student" else None
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    if new_user.role == "student":
        initial_progress = models.Progress(student_id=new_user.id, accuracy=0, chapters_completed=0)
        db.add(initial_progress)
        db.commit()

    return {"message": "User created successfully"}

@app.post("/login")
def login(user_data: dict, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == user_data.get("email")).first()
    if not user or user.password != user_data.get("password"):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = auth.create_access_token(data={"sub": user.email, "id": user.id, "role": user.role})
    return {"token": token, "role": user.role}

# ---------------- STUDENT ROUTES ----------------

@app.get("/student/stats")
def get_student_stats(token: str, db: Session = Depends(get_db)):
    payload = auth.decode_token(token)
    user_id = payload.get("id")
    user = db.query(models.User).filter(models.User.id == user_id).first()
    stats = db.query(models.Progress).filter(models.Progress.student_id == user_id).first()
    subject_mastery_data = json.loads(stats.subject_mastery) if stats and stats.subject_mastery else {"Math": 0, "Science": 0, "English": 0, "Hindi": 0, "Social Science": 0}
    recent_activity_data = json.loads(stats.recent_activity) if stats and stats.recent_activity else [{"task": "Started AI Journey", "date": "Today"}]
    
    return {
        "student_name": user.name if user else "Student",
        "accuracy": stats.accuracy if stats else 0,
        "chapters": stats.chapters_completed if stats else 0,
        "subjects": [
            {"name": "Mathematics", "progress": subject_mastery_data.get("Math", 0)},
            {"name": "Science", "progress": subject_mastery_data.get("Science", 0)},
            {"name": "English", "progress": subject_mastery_data.get("English", 0)},
            {"name": "Hindi", "progress": subject_mastery_data.get("Hindi", 0)},
            {"name": "Social Science", "progress": subject_mastery_data.get("Social Science", 0)}
        ],
        "recent_activity": recent_activity_data
    }

@app.post("/student/submit-quiz")
def submit_quiz_score(data: dict, db: Session = Depends(get_db)):
    token = data.get("token")
    score = data.get("score")
    total = data.get("total")
    subject = data.get("subject", "")
    
    if token is None or score is None or total is None or total == 0:
        raise HTTPException(status_code=400, detail="Invalid data")

    try:
        payload = auth.decode_token(token)
        user_id = payload.get("id")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid Token")

    stats = db.query(models.Progress).filter(models.Progress.student_id == user_id).first()
    if stats:
        current_quiz_accuracy = (score / total) * 100
        # Simple rolling average to update overall accuracy
        if stats.chapters_completed == 0:
            stats.accuracy = current_quiz_accuracy
        else:
            stats.accuracy = round((stats.accuracy + current_quiz_accuracy) / 2, 2)
        
        stats.chapters_completed += 1
        
        # --- Update Subject Mastery ---
        if subject:
            mastery_data = json.loads(stats.subject_mastery) if stats.subject_mastery else {"Math": 0, "Science": 0, "English": 0, "Hindi": 0, "Social Science": 0}
            subject_key = subject
            if subject_key and subject_key in mastery_data:
                current_sub_acc = mastery_data[subject_key]
                mastery_data[subject_key] = round((current_sub_acc + current_quiz_accuracy) / 2 if current_sub_acc > 0 else current_quiz_accuracy, 2)
                stats.subject_mastery = json.dumps(mastery_data)
        
        # --- Update Recent Activity ---
        import datetime
        activity_data = json.loads(stats.recent_activity) if stats.recent_activity else []
        date_str = datetime.datetime.now().strftime("%I:%M %p")
        activity_data.insert(0, {"task": f"Completed {subject} Quiz ({round(current_quiz_accuracy)}%)", "date": f"Today, {date_str}"})
        if len(activity_data) > 5:
            activity_data.pop()
        stats.recent_activity = json.dumps(activity_data)

        db.commit()
    
    return {"message": "Score updated successfully"}

@app.post("/student/ask-ai-doubt")
def ask_ai_doubt(data: dict):
    # Basic logic for doubt clearing
    question = data.get("question", "").lower()
    return {"answer": f"Thinking about '{question}'... Please refer to Chapter 1 for detailed context."}

# ---------------- AI QUIZ ROUTE ----------------






import os, pdfplumber, json, re
from fastapi import FastAPI, Depends, HTTPException
from langchain_core.prompts import PromptTemplate
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint

# ... (purane imports same rahenge) ...

@app.post("/generate-quiz")
async def generate_quiz(data: dict):
    subj = data.get("subject")
    chap = data.get("chapter")
    q_type = data.get("type", "MCQ")
    num = data.get("num_questions", 5)
    diff = data.get("difficulty", "Medium")

    try:
        filename = SUBJECT_CONFIG[subj]["files"][chap]
        path = os.path.join(SUBJECT_CONFIG[subj]["folder"], filename)
        context = extract_pdf_text(path)
    except KeyError:
        raise HTTPException(status_code=400, detail="Invalid Subject/Chapter")

    if not context:
        raise HTTPException(status_code=404, detail="PDF content not found")

    # --- HINDI SPECIFIC LOGIC ---
    # Agar subject Hindi hai, toh hum AI ko force karenge Hindi script use karne ke liye
    is_hindi_subj = subj in ["Hindi"] # Add subjects that need Hindi output
    
    language_instruction = ""
    if is_hindi_subj:
        language_instruction = """
        CRITICAL HINDI INSTRUCTION: 
        1. The generated Output (all questions, options, answers, and explanations) MUST BE 100% IN HINDI (Devanagari script: हिंदी).
        2. DO NOT output any English words, roman letters, or transliterated Hindi (Hinglish) in the generated content.
        3. The JSON keys ("question", "options", "answer", "explanation") MUST be in English.
        4. Provide pure Hindi text. For example, use "कहाँ", "सही", "यह उत्तर है।".
        """
    else:
        language_instruction = "Generate the content in English."

    type_instruction = ""
    if q_type == "Short Answer":
        type_instruction = "The answers MUST be concise, strictly between 1 to 3 lines max."
    elif q_type == "Long Answer":
        type_instruction = "The answers MUST be detailed, strictly between 4 to 6 lines max."

    prompt = PromptTemplate.from_template(
        """
        You are a professional teacher. Generate {num} {diff}-level {type} from this text:
        
        Text: {context}
        
        {lang_instr}
        {type_instr}
        
        Return ONLY a JSON list in this format: {hint}
        """
    )
    
    # AI invocation
    res = (prompt | model).invoke({
        "num": num, 
        "diff": diff, 
        "type": q_type, 
        "context": context, 
        "lang_instr": language_instruction,
        "type_instr": type_instruction,
        "hint": FORMATS.get(q_type, FORMATS["MCQ"])
    })
    
    # JSON clean up
    try:
        match = re.search(r"\[.*\]", res.content, re.DOTALL)
        if match:
            json_str = match.group()
            return json.loads(json_str)
        return []
    except Exception as e:
        print("JSON Parsing Error:", e)
        print("Raw Content:", res.content)
        return []


    # # Clean output to get JSON
    # match = re.search(r"\[.*\]", res.content, re.DOTALL)
    # if match:
    #     return json.loads(match.group())
    # return []

# ---------------- TEACHER ROUTES ----------------

@app.get("/teacher/analytics")
def get_teacher_analytics(token: str, db: Session = Depends(get_db)):
    payload = auth.decode_token(token)
    if payload.get("role") != "teacher":
        raise HTTPException(status_code=403, detail="Unauthorized")

    results = db.query(models.User, models.Progress).outerjoin(
        models.Progress, models.User.id == models.Progress.student_id
    ).filter(models.User.role == "student").all()

    student_list = [{
        "id": u.id, "name": u.name, "email": u.email,
        "accuracy": p.accuracy if p else 0,
        "chapters": p.chapters_completed if p else 0
    } for u, p in results]

    return {"total_students": len(student_list), "students": student_list}

@app.post("/forgot-password")
def forgot_password(data: dict, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == data.get("email")).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.password = data.get("new_password")
    db.commit()
    return {"message": "Password updated successfully"}
