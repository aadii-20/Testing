import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List

import json
import re

from bson import ObjectId
from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.prompts import PromptTemplate
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint

# Load environment variables from .env file
load_dotenv()

# Get the project root directory (parent of backend folder)
# In AI-chatboat/backend/main.py, parent is AI-chatboat
PROJECT_ROOT = Path(__file__).parent.parent

from auth import auth as auth_utils, schemas
from database import get_db, init_db
from rag.pdf_loader import load_pdf_text, chunk_text
from rag.vector_store import VectorStore, embed_query
from rag.advanced_nlp import rewrite_query, generate_answer
from rbac.roles import role_required


app = FastAPI(title="RBAC Educational Chatbot")

# ─── AI Model Setup for Quiz Generation ────────────────────────────────────────
hf_api_key = os.getenv("HUGGINGFACE_API_KEY") or os.getenv("HUGGINGFACEHUB_API_TOKEN")

llm = HuggingFaceEndpoint(
    repo_id="Qwen/Qwen2.5-7B-Instruct", 
    task="text-generation", 
    max_new_tokens=2048, 
    temperature=0.4,
    huggingfacehub_api_token=hf_api_key
)
quiz_model = ChatHuggingFace(llm=llm)

QUIZ_FORMATS = {
    "MCQ": '[{"question": "...", "options": ["A) ..", "B) .."], "answer": "A", "explanation": "..."}]',
    "Fill in blanks": '[{"question": "The ____ is...", "answer": "word", "explanation": "..."}]',
    "Short Answer": '[{"question": "...", "answer": "...", "explanation": "..."}]',
    "Long Answer": '[{"question": "...", "answer": "...", "explanation": "..."}]'
}

LEGACY_SUBJECT_CONFIG = {
    "Science": {"folder": "personalised_learning/Sciences", "files": {f"Chapter {i}": f"sci ({i}).pdf" for i in range(1, 11)}},
    "Math": {"folder": "personalised_learning/Maths", "files": {f"Chapter {i}": f"math{i}.pdf" for i in range(1, 13)}},
    "English": {"folder": "personalised_learning/Englishs", "files": {f"Chapter {i}": f"iebe10{i}.pdf" for i in range(1, 10)}},
    "Hindi": {"folder": "personalised_learning/Hindis", "files": {f"Chapter {i}": f"hin ({i}).pdf" for i in range(1, 14)}},
    "Social Science": {"folder": "personalised_learning/Social science", "files": {f"Chapter {i}": f"iess40{i}.pdf" for i in range(1, 6)}}
}

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
    ],
    # Using regex to allow any localhost port (robust for dev environment where ports change)
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    """Initialize MongoDB indexes on application startup."""
    init_db()


# ─── Dynamic PDF Discovery ───────────────────────────────────────────────────
# Looks for structure: std/{standard}/{Subject}/{Chapter}.pdf
STD_DIR = PROJECT_ROOT / "std"

VECTOR_STORES: Dict[str, Dict[str, VectorStore]] = {}


def get_available_content(standard: str = None) -> Dict[str, Dict[str, str]]:
    """
    Scans the std directory for content.
    If standard is provided, returns subjects/chapters for that standard.
    Returns: { "subject_name": { "chapter_name": "absolute_path_to_pdf" } }
    """
    content_map = {}

    if not STD_DIR.exists():
        return content_map

    if not standard:
        return content_map

    std_path = STD_DIR / standard
    if not std_path.exists():
        return content_map

    for subject_path in std_path.iterdir():
        if subject_path.is_dir():
            subject_name = subject_path.name
            chapters = {}
            for file_path in subject_path.glob("*.pdf"):
                chapter_name = file_path.stem
                chapters[chapter_name] = str(file_path.resolve())
            if chapters:
                content_map[subject_name] = chapters

    return content_map


def get_vector_store(subject: str, chapter: str, standard: str) -> VectorStore:
    store_key = f"{standard}_{subject}_{chapter}".lower()

    if store_key in VECTOR_STORES:
        return VECTOR_STORES[store_key]

    content = get_available_content(standard)

    subject_map = {k.lower(): k for k in content.keys()}
    s_key = subject.lower()

    if s_key not in subject_map:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subject '{subject}' not found for Standard {standard}",
        )

    real_subject_name = subject_map[s_key]
    chapters_map = {k.lower(): k for k in content[real_subject_name].keys()}
    c_key = chapter.lower()

    if c_key not in chapters_map:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chapter '{chapter}' not found in {real_subject_name} (Std {standard})",
        )

    pdf_path = content[real_subject_name][chapters_map[c_key]]

    try:
        raw_text = load_pdf_text(pdf_path)
        chunks = chunk_text(raw_text)
        store = VectorStore(chunks)
        VECTOR_STORES[store_key] = store
        return store
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load PDF: {str(e)}"
        )


# ─── Helper: convert MongoDB doc → Pydantic schema ───────────────────────────

def _session_doc_to_schema(
    session: dict, messages: list = None
) -> schemas.ChatSessionRead:
    """Convert a MongoDB chat_sessions document to ChatSessionRead."""
    msg_list = []
    if messages:
        for m in messages:
            msg_list.append(schemas.ChatMessageRead(
                id=str(m["_id"]),
                session_id=str(m["session_id"]),
                role=m["role"],
                content=m["content"],
                created_at=m["created_at"],
            ))

    return schemas.ChatSessionRead(
        id=str(session["_id"]),
        user_id=str(session["user_id"]),
        title=session.get("title"),
        subject=session["subject"],
        chapter=session["chapter"],
        standard=session.get("standard"),
        language=session.get("language", "English"),
        created_at=session["created_at"],
        messages=msg_list,
    )


# ─── Auth Routes ─────────────────────────────────────────────────────────────

@app.post("/signup", response_model=schemas.Token)
def signup(data: dict):
    """
    Create a new user account. Accepts {"email", "password", "role", "standard"}.
    Role must be "student" or "teacher".
    Standard is required for students.
    """
    email = data.get("email")
    password = data.get("password")
    role = data.get("role", "student")
    standard = data.get("standard")

    if not email or not password:
        raise HTTPException(status_code=400, detail="Email and password required")

    if role not in ["student", "teacher"]:
        raise HTTPException(status_code=400, detail="Role must be 'student' or 'teacher'")

    if role == "student" and not standard:
        raise HTTPException(status_code=400, detail="Standard is required for students")

    db = get_db()

    # Check if user already exists
    if db["users"].find_one({"email": email}):
        raise HTTPException(status_code=400, detail="Email already registered")

    # Insert new user
    hashed_password = auth_utils.get_password_hash(password)
    result = db["users"].insert_one({
        "email": email,
        "hashed_password": hashed_password,
        "role": role,
        "standard": standard,
    })

    # Return JWT immediately after signup
    access_token = auth_utils.create_access_token({
        "sub": email,
        "role": role,
        "standard": standard,
    })
    return schemas.Token(access_token=access_token)


@app.post("/login", response_model=schemas.LoginResponse)
def login(data: dict):
    """
    JSON login accepting {"email", "password"}.
    Returns a JWT embedding the user role and standard.
    """
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        raise HTTPException(status_code=400, detail="Email and password required")

    user = auth_utils.authenticate_user(email=email, password=password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    access_token = auth_utils.create_access_token({
        "sub": user["email"],
        "role": user["role"],
        "standard": user.get("standard"),
    })
    return {"token": access_token, "role": user["role"]}


@app.post("/forgot-password")
def forgot_password(data: dict):
    """
    Resets user password. Accepts {"email", "new_password"}.
    """
    email = data.get("email")
    new_password = data.get("new_password")

    if not email or not new_password:
        raise HTTPException(status_code=400, detail="Email and new password required")

    db = get_db()
    user = db["users"].find_one({"email": email})
    if not user:
        raise HTTPException(status_code=404, detail="User with this email not found")

    hashed_password = auth_utils.get_password_hash(new_password)
    db["users"].update_one(
        {"email": email},
        {"$set": {"hashed_password": hashed_password}}
    )

    return {"message": "Password updated successfully"}


# ─── Subjects Route ───────────────────────────────────────────────────────────

@app.get("/subjects", response_model=List[schemas.Subject])
def list_subjects(
    user: schemas.UserRead = Depends(auth_utils.get_current_user),
    standard: str = None,
):
    """
    Return all available subjects and chapters.
    Students automatically use their own standard.
    Teachers can pass a ?standard= query param.
    """
    target_standard = standard

    if user.role == "student":
        target_standard = user.standard
        if not target_standard:
            return []

    if not target_standard:
        target_standard = "8"

    content = get_available_content(target_standard)

    subjects: List[schemas.Subject] = []
    for subject_name, chapters in content.items():
        subjects.append(schemas.Subject(
            name=subject_name,
            chapters=list(chapters.keys()),
        ))
    return subjects


# ─── Chat Session Routes ──────────────────────────────────────────────────────

@app.post("/sessions", response_model=schemas.ChatSessionRead)
def create_session(
    session_in: schemas.ChatSessionCreate,
    user: schemas.UserRead = Depends(auth_utils.get_current_user),
):
    """Start a new chat session."""
    db = get_db()

    title = session_in.title or f"{session_in.subject} - {session_in.chapter}"

    std = session_in.standard
    if not std and user.role == "student":
        std = user.standard
    if not std:
        std = "8"

    now = datetime.utcnow()
    result = db["chat_sessions"].insert_one({
        "user_id": user.id,          # stored as string (ObjectId str)
        "title": title,
        "subject": session_in.subject,
        "chapter": session_in.chapter,
        "standard": std,
        "language": session_in.language,
        "created_at": now,
    })

    doc = db["chat_sessions"].find_one({"_id": result.inserted_id})
    return _session_doc_to_schema(doc, messages=[])


@app.get("/sessions", response_model=List[schemas.ChatSessionRead])
def list_sessions(
    user: schemas.UserRead = Depends(auth_utils.get_current_user),
):
    """List all chat sessions for the current user, newest first."""
    db = get_db()
    cursor = db["chat_sessions"].find(
        {"user_id": user.id}
    ).sort("created_at", -1)

    sessions = []
    for doc in cursor:
        sessions.append(_session_doc_to_schema(doc, messages=[]))
    return sessions


@app.get("/sessions/{session_id}", response_model=schemas.ChatSessionRead)
def get_session(
    session_id: str,
    user: schemas.UserRead = Depends(auth_utils.get_current_user),
):
    """Get a specific session with its messages."""
    db = get_db()

    try:
        oid = ObjectId(session_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid session ID")

    session = db["chat_sessions"].find_one({"_id": oid, "user_id": user.id})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    messages = list(
        db["chat_messages"]
        .find({"session_id": session_id})
        .sort("created_at", 1)
    )
    return _session_doc_to_schema(session, messages=messages)


@app.post("/sessions/{session_id}/message", response_model=schemas.ChatResponse)
def send_message_to_session(
    session_id: str,
    payload: schemas.ChatMessageCreate,
    user: schemas.UserRead = Depends(auth_utils.get_current_user),
):
    """
    Send a user message to an existing session and get an AI response.
    Saves both user and assistant messages to MongoDB.
    """
    db = get_db()

    try:
        oid = ObjectId(session_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid session ID")

    # 1. Verify session belongs to user
    session = db["chat_sessions"].find_one({"_id": oid, "user_id": user.id})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    now = datetime.utcnow()

    # 2. Save user message
    db["chat_messages"].insert_one({
        "session_id": session_id,
        "role": "user",
        "content": payload.content,
        "created_at": now,
    })

    # 3. Generate AI response
    try:
        store = get_vector_store(session["subject"], session["chapter"], session["standard"])

        rewritten = rewrite_query(payload.content)
        query_emb = embed_query(rewritten)
        results = store.search(query_emb, top_k=5)
        retrieved_chunks: List[str] = [chunk for chunk, _ in results]

        if not retrieved_chunks:
            answer_text = "I could not find any relevant information in the course material for this question."
        else:
            context_text = "\n\n".join(retrieved_chunks)
            answer_text = generate_answer(
                user.role, context_text, payload.content, session.get("language", "English")
            )

        # 4. Save AI message
        db["chat_messages"].insert_one({
            "session_id": session_id,
            "role": "assistant",
            "content": answer_text,
            "created_at": datetime.utcnow(),
        })

        return schemas.ChatResponse(answer=answer_text)

    except Exception as e:
        print(f"Error in chat session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}",
        )


# ─── Legacy Chat Route ────────────────────────────────────────────────────────

@app.post("/chat", response_model=schemas.ChatResponse)
def chat(
    payload: schemas.ChatRequest,
    user: schemas.UserRead = Depends(role_required("student", "teacher")),
):
    """
    Role-aware stateless chat endpoint (legacy).
    Uses Ollama + SentenceTransformers for local AI.
    """
    std = user.standard if hasattr(user, "standard") else None
    if not std:
        raise HTTPException(status_code=400, detail="Standard not found for user")

    try:
        store = get_vector_store(payload.subject, payload.chapter, std)

        print(f"\n=== DEBUG: Chat Request ===")
        print(f"Subject: {payload.subject}, Chapter: {payload.chapter}")
        print(f"Question: {payload.question}")
        print(f"User Role: {user.role}")

        rewritten = rewrite_query(payload.question)
        print(f"Rewritten Query: {rewritten}")

        query_emb = embed_query(rewritten)
        results = store.search(query_emb, top_k=5)
        retrieved_chunks: List[str] = [chunk for chunk, _ in results]

        print(f"\n=== Retrieved {len(retrieved_chunks)} chunks ===")
        for i, (chunk, distance) in enumerate(results):
            print(f"Chunk {i+1} (distance: {distance:.4f}): {chunk[:200]}...")

        if not retrieved_chunks:
            print("WARNING: No chunks retrieved!")
            return schemas.ChatResponse(
                answer="I could not find any relevant information in the course material for this question."
            )

        context_text = "\n\n".join(retrieved_chunks)
        print(f"\n=== Context (Raw Chunks) ===")
        print(f"{context_text[:500]}...")

        answer_text = generate_answer(user.role, context_text, payload.question, payload.language)
        print(f"\n=== Generated Answer ===")
        try:
            print(f"{answer_text[:300]}...")
        except UnicodeEncodeError:
            print(f"{answer_text[:300].encode('utf-8', errors='ignore').decode('ascii', errors='ignore')}... (Unicode chars hidden)")

        return schemas.ChatResponse(answer=answer_text)

    except Exception as e:
        print(f"General Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while processing your request: {str(e)}",
        )


# ─── Student Dashboard Routes ─────────────────────────────────────────────────

@app.post("/student/ask-ai-doubt")
def ask_ai_doubt(
    data: dict,
    user: schemas.UserRead = Depends(auth_utils.get_current_user),
):
    """Answers a quick doubt from the student dashboard using the Qwen LLM."""
    question = data.get("question")
    if not question:
        raise HTTPException(status_code=400, detail="Question is required")
        
    try:
        # Prompt instructing the LLM to act as a helpful AI teacher
        prompt = f"You are a helpful and educational AI teacher for a student in standard {user.standard}. Answer the following doubt clearly and concisely:\n\nStudent: {question}\n\nTeacher:"
        
        response = quiz_model.invoke(prompt)
        # Extract the text from the AIMessage object if it's not a raw string
        answer_text = response.content if hasattr(response, 'content') else str(response)
        
        return {"answer": answer_text}
    except Exception as e:
        print(f"Error generating doubt answer: {e}")
        raise HTTPException(status_code=500, detail="AI Service is currently unavailable")

@app.get("/student/stats")
def get_student_stats(
    user: schemas.UserRead = Depends(auth_utils.get_current_user),
):
    """Returns statistics for the student dashboard."""
    db = get_db()

    # 1. Get chapters count from PDFs
    available_content = get_available_content(user.standard)
    total_chapters = 0
    subjects_data_map = {}

    for sub, chapters in available_content.items():
        count = len(chapters)
        total_chapters += count
        subjects_data_map[sub] = 0

    # 2. Get Student Progress from DB
    stats = db["student_progress"].find_one({"user_id": user.id})
    accuracy = 0
    completed = 0
    recent_activity = []
    
    if stats:
        accuracy = stats.get("accuracy", 0)
        completed = stats.get("chapters_completed", 0)
        mastery_data = stats.get("subject_mastery", {})
        for sub, score in mastery_data.items():
            if sub in subjects_data_map:
                subjects_data_map[sub] = score
        recent_activity = stats.get("recent_activity", [])
        
    subjects_data = [{"name": sub, "progress": score} for sub, score in subjects_data_map.items()]

    if not recent_activity:
        recent_activity.append({"task": "Joined RBAS Chatbot", "date": "Just now"})

    return {
        "student_name": f"Student ({user.email})",
        "accuracy": accuracy,
        "chapters": completed,
        "recommendation": "Keep exploring your chapters!",
        "subjects": subjects_data,
        "recent_activity": recent_activity,
    }

@app.post("/student/submit-quiz")
def submit_quiz_score(
    data: dict,
    user: schemas.UserRead = Depends(auth_utils.get_current_user),
):
    score = data.get("score")
    total = data.get("total")
    subject = data.get("subject", "")
    
    if score is None or total is None or total == 0:
        raise HTTPException(status_code=400, detail="Invalid data")

    db = get_db()
    current_quiz_accuracy = (score / total) * 100
    
    stats = db["student_progress"].find_one({"user_id": user.id})
    
    now_str = datetime.utcnow().strftime("%I:%M %p")
    new_activity = {"task": f"Completed {subject} Quiz ({round(current_quiz_accuracy)}%)", "date": f"Today, {now_str}"}

    if not stats:
        initial_progress = {
            "user_id": user.id,
            "accuracy": current_quiz_accuracy,
            "chapters_completed": 1,
            "subject_mastery": {subject: current_quiz_accuracy} if subject else {},
            "recent_activity": [new_activity]
        }
        db["student_progress"].insert_one(initial_progress)
    else:
        new_accuracy = round((stats.get("accuracy", 0) + current_quiz_accuracy) / 2, 2) if stats.get("chapters_completed", 0) > 0 else current_quiz_accuracy
        new_chapters = stats.get("chapters_completed", 0) + 1
        
        mastery_data = stats.get("subject_mastery", {})
        if subject:
            current_sub_acc = mastery_data.get(subject, 0)
            mastery_data[subject] = round((current_sub_acc + current_quiz_accuracy) / 2 if current_sub_acc > 0 else current_quiz_accuracy, 2)
            
        activity_data = stats.get("recent_activity", [])
        activity_data.insert(0, new_activity)
        if len(activity_data) > 5:
            activity_data.pop()
            
        db["student_progress"].update_one(
            {"user_id": user.id},
            {"$set": {
                "accuracy": new_accuracy,
                "chapters_completed": new_chapters,
                "subject_mastery": mastery_data,
                "recent_activity": activity_data
            }}
        )

    return {"message": "Score updated successfully"}

# ─── Teacher Dashboard Routes ──────────────────────────────────────────────────

@app.get("/teacher/analytics")
def get_teacher_analytics(
    user: schemas.UserRead = Depends(auth_utils.get_current_user),
):
    """Returns aggregated analytics for the teacher dashboard."""
    if user.role != "teacher":
        raise HTTPException(status_code=403, detail="Not authorized")

    db = get_db()
    
    # Get all students
    all_students_cursor = db["users"].find({"role": "student"})
    students_list = []
    
    total_acc = 0
    valid_acc_count = 0
    
    for student_doc in all_students_cursor:
        student_id = str(student_doc["_id"])
        stats = db["student_progress"].find_one({"user_id": student_id})
        
        acc = stats.get("accuracy", 0) if stats else 0
        chapters = stats.get("chapters_completed", 0) if stats else 0
        
        students_list.append({
            "id": student_id,
            "name": student_doc.get("email", "Unknown Student").split("@")[0],
            "email": student_doc.get("email", ""),
            "class": student_doc.get("standard", "8"),
            "accuracy": round(acc, 1),
            "chapters": chapters
        })
        
        if stats and chapters > 0:
            total_acc += acc
            valid_acc_count += 1
            
    avg_acc = round(total_acc / valid_acc_count, 1) if valid_acc_count > 0 else 0

    return {
        "total_students": len(students_list),
        "average_accuracy": avg_acc,
        "students": students_list
    }

# ─── Generative AI Quiz Route ─────────────────────────────────────────────────

@app.post("/generate-quiz")
def generate_quiz(data: dict):
    subj = data.get("subject")
    raw_chap = data.get("chapter") # e.g. "Chapter 1"
    
    if not subj or not raw_chap:
        raise HTTPException(status_code=400, detail="Subject and chapter are required")

    q_type = data.get("type", "MCQ")
    num = data.get("num_questions", 5)
    diff = data.get("difficulty", "Medium")
    standard = data.get("standard", "8") # Fallback to 8 if not provided by UI

    try:
        content_map = get_available_content(standard)
        pdf_path = None
        # Try dynamically first
        subject_key = next((k for k in content_map.keys() if k.lower() == subj.lower()), None)
        if subject_key:
            chapter_key = next((k for k in content_map[subject_key].keys() if raw_chap.lower() in k.lower()), None)
            if chapter_key:
                pdf_path = content_map[subject_key][chapter_key]
        
        # Fallback to legacy structure if not found dynamically
        if not pdf_path:
            legacy_subj = next((k for k in LEGACY_SUBJECT_CONFIG.keys() if k.lower() == subj.lower()), None)
            if legacy_subj:
                cfg = LEGACY_SUBJECT_CONFIG[legacy_subj]
                filename = cfg["files"].get(raw_chap)
                if filename:
                    # Path relative to backend root
                    legacy_path = PROJECT_ROOT / "backend" / cfg["folder"] / filename
                    print(f"Checking legacy path: {legacy_path}")
                    if legacy_path.exists():
                        pdf_path = str(legacy_path)
                    else:
                        print(f"Legacy path does not exist: {legacy_path}")

        if not pdf_path:
            raise KeyError(f"PDF missing for {subj} - {raw_chap}")
            
        # Borrow the pdf text extraction from vector store logic to reuse chunks briefly
        raw_text = load_pdf_text(pdf_path)
        chunks = chunk_text(raw_text)
        context = " ".join([c for c in chunks[:3]]) # use top few chunks as context
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error fetching quiz PDF context: {e}")
        raise HTTPException(status_code=400, detail="Invalid Subject/Chapter or PDF missing")

    if not context:
        raise HTTPException(status_code=404, detail="PDF content not found")

    is_hindi_subj = subj.lower() in ["hindi"] 
    
    language_instruction = ""
    if is_hindi_subj:
        language_instruction = '''
        CRITICAL HINDI INSTRUCTION: 
        1. The generated Output (all questions, options, answers, and explanations) MUST BE 100% IN HINDI (Devanagari script: हिंदी).
        2. DO NOT output any English words, roman letters, or transliterated Hindi (Hinglish) in the generated content.
        3. The JSON keys ("question", "options", "answer", "explanation") MUST be in English.
        4. Provide pure Hindi text. For example, use "कहाँ", "सही", "यह उत्तर है।".
        '''
    else:
        language_instruction = "Generate the content in English."

    type_instruction = ""
    if q_type == "Short Answer":
        type_instruction = "The answers MUST be concise, strictly between 1 to 3 lines max."
    elif q_type == "Long Answer":
        type_instruction = "The answers MUST be detailed, strictly between 4 to 6 lines max."

    prompt = PromptTemplate.from_template(
        '''
        You are a professional teacher. Generate {num} {diff}-level {type} from this text:
        
        Text: {context}
        
        {lang_instr}
        {type_instr}
        
        Return ONLY a JSON list in this format: {hint}
        '''
    )
    
    try:
        res = (prompt | quiz_model).invoke({
            "num": num, 
            "diff": diff, 
            "type": q_type, 
            "context": context, 
            "lang_instr": language_instruction,
            "type_instr": type_instruction,
            "hint": QUIZ_FORMATS.get(q_type, QUIZ_FORMATS["MCQ"])
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error invoking quiz LLM: {e}")
        # Raising a managed exception ensures FastAPI applies the CORS headers properly
        raise HTTPException(
            status_code=500, 
            detail=f"AI service currently unavailable or failed to generate quiz. Details: {str(e)}"
        )
    
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



@app.post("/student/ask-ai-doubt")
def ask_ai_doubt(
    data: dict,
    user: schemas.UserRead = Depends(auth_utils.get_current_user),
):
    question = data.get("question", "")
    if not question:
        return {"answer": "Please ask a question."}

    print(f"Global search for: {question} (Std {user.standard})")

    try:
        content = get_available_content(user.standard)
        all_results = []

        rewritten = rewrite_query(question)
        query_emb = embed_query(rewritten)

        for sub, chapters in content.items():
            for chap in chapters.keys():
                try:
                    store = get_vector_store(sub, chap, user.standard)
                    results = store.search(query_emb, top_k=2)
                    for txt, dist in results:
                        all_results.append((dist, txt))
                except Exception:
                    pass

        all_results.sort(key=lambda x: x[0])
        top_chunks = [txt for dist, txt in all_results[:5]]

        if not top_chunks:
            return {"answer": "I could not find any relevant information in your course materials."}

        context_text = "\n\n".join(top_chunks)
        answer = generate_answer(user.role, context_text, question, "English")
        return {"answer": answer}

    except Exception as e:
        print(f"Global search error: {e}")
        return {"answer": "I encountered an error while searching your books. Please try again."}
