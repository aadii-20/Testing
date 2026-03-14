from typing import List, Dict, Any
import os
import ollama
from groq import Groq
from huggingface_hub import InferenceClient

OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
HF_MODEL = "Qwen/Qwen2.5-7B-Instruct"

groq_client = None
if GROQ_API_KEY:
    try:
        groq_client = Groq(api_key=GROQ_API_KEY)
        print("INFO: Groq client initialized. Using Cloud AI as primary.")
    except Exception as e:
        print(f"WARNING: Groq initialization failed: {e}. Defaulting to Local AI.")

hf_client = None
if HUGGINGFACE_API_KEY:
    try:
        hf_client = InferenceClient(api_key=HUGGINGFACE_API_KEY)
        print("INFO: Hugging Face client initialized.")
    except Exception as e:
        print(f"WARNING: Hugging Face initialization failed: {e}")

def get_system_prompt(language: str = "English") -> str:
    base_prompt = """
You are an expert educational assistant for school students in India.
Your answers must be based ONLY on the provided context from the PDF course material.
Do NOT guess, hallucinate, or add information not present in the context.
If the context does not contain the answer, say: "This information is not available in the selected chapter."

ANSWER QUALITY RULES:
- Always give a COMPLETE, well-structured answer. Never cut off mid-sentence.
- Use clear headings, bullet points, and numbered lists where appropriate.
- For poems/literature: name the poem, name the poet, then explain the theme/content.
- For concepts: define first, then explain with examples from the context.
- Keep answers concise but comprehensive — 3 to 8 sentences or bullet points as needed.

MATH FORMATTING RULES:
- For mathematical expressions, ALWAYS use LaTeX notation.
- Use $...$ for inline math (e.g., $x^2 + y^2 = r^2$).
- Use $$...$$ for block/display math (e.g., $$\\frac{-b \pm \sqrt{b^2-4ac}}{2a}$$).
- Never write math expressions in plain text — always wrap them in $ or $$ delimiters.
"""
    
    if language.lower() == "hindi":
        lang_rule = """
CRITICAL LANGUAGE RULE:
- You MUST write your entire response ONLY in Hindi (Devanagari script - देवनागरी लिपि).
- Do NOT use Roman/English transliteration (e.g., do not write "woh bola", write "वह बोला").
- Do NOT transliterate technical Hindi terms into English chars (e.g., write "प्रकाश संश्लेषण" not "Prakash Sanshleshan").
- Technical and scientific terms with no common Hindi equivalent may stay in English. All explanations MUST be in Devanagari.
"""
    else:
        lang_rule = f"""
CRITICAL LANGUAGE RULE:
- You MUST write your entire response ONLY in {language}.
- Do NOT use Hindi or any other language, even if the context contains it.
- If the context is in another language, translate the relevant information into {language} for your answer.
"""
    return base_prompt.strip() + "\n\n" + lang_rule.strip()

def generate_completion(messages: List[Dict[str, str]]) -> str:
    """
    Hybrid generation: Try Groq (Cloud) first, fallback to Ollama (Local).
    """
    
    if groq_client:
        try:
            # Try the more capable 70b model first for better knowledge base and reasoning
            completion = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                temperature=0.1,
            )
            return completion.choices[0].message.content
        except Exception as e_70b:
            print(f"INFO: Groq 70b failed ({e_70b}), trying 8b...")
            try:
                # Fallback to faster 8b
                completion = groq_client.chat.completions.create(
                    model="llama3-8b-8192",
                    messages=messages,
                    temperature=0.1,
                )
                return completion.choices[0].message.content
            except Exception as e:
                print(f"WARNING: Groq Cloud failed ({e}). Falling back to next available...")

    # Fallback 1: Hugging Face (Cloud)
    if hf_client:
        try:
            # Using chat completion API from huggingface_hub
            completion = hf_client.chat_completion(
                model=HF_MODEL,
                messages=messages,
                max_tokens=1024
            )
            return completion.choices[0].message.content
        except Exception as e:
            print(f"WARNING: Hugging Face Cloud failed ({e}). Falling back to Local AI...")
    
    try:
        response = ollama.chat(model=OLLAMA_MODEL, messages=messages)
        return response['message']['content']
    except Exception as e:
        print(f"ERROR: Local AI failed: {e}")
        return "I apologize, but I'm currently unable to generate a response due to technical issues (AI Service Unavailable)."

def rewrite_query(query: str) -> str:
    """
    Rewrite the user query for better retrieval quality.
    """
    prompt = (
        f"Rewrite the following learner question to be clear, concise, and retrieval-friendly.\n"
        f"Keep the meaning the same. Output ONLY the rewritten question.\n\nQuestion: {query}"
    )
    messages = [{'role': 'user', 'content': prompt}]
    return generate_completion(messages).strip()

def role_prompt(role: str) -> str:
    if role == "student":
        return (
            "You are helping a student. "
            "Explain the concepts directly to the student using simple, engaging language. "
            "If the context contains lesson plans or teaching instructions, rephrase them as learning activities for the student. "
            "Do NOT talk *about* the student or the lesson; talk *to* the student. "
            "Use concrete examples and step-by-step explanations."
        )
    return (
        "You are helping a teacher. "
        "Provide deep explanations, pedagogical insights, and possible ways to teach or assess the topic. "
        "You may suggest questions or summaries."
    )

def generate_answer(role: str, context: str, question: str, language: str = "English") -> str:
    """
    Generate final answer with system, role, and context prompts.
    """
    if language.lower() == "hindi":
        lang_instruction = (
            "TARGET LANGUAGE: Hindi\n"
            "SCRIPT: Write ENTIRELY in Devanagari script (हिंदी में देवनागरी लिपि में लिखें).\n"
            "Do NOT use Roman transliteration. Write real Hindi: 'वह बोला', 'प्रकाश संश्लेषण'.\n"
        )
    else:
        lang_instruction = f"TARGET LANGUAGE: {language}\n"

    final_user_message = (
        f"ROLE:\n{role_prompt(role)}\n\n"
        f"CONTEXT (from PDF chapter):\n{context}\n\n"
        f"USER QUESTION:\n{question}\n\n"
        f"{lang_instruction}\n"
        "INSTRUCTIONS FOR YOUR ANSWER:\n"
        "1. Answer ONLY from the context above — do not add outside knowledge.\n"
        "2. Structure your answer clearly: use a heading, then bullet points or short paragraphs.\n"
        "3. If the question is about a poem: state the poem name, poet name, and describe its theme/content.\n"
        "4. If the question is about a concept: define it first, then explain with context details.\n"
        "5. Give a COMPLETE answer — never stop mid-sentence.\n"
        f"6. Write in the specified target language ({language}) and specified script ONLY.\n"
    )

    messages = [
        {'role': 'system', 'content': get_system_prompt(language)},
        {'role': 'user', 'content': final_user_message}
    ]

    return generate_completion(messages)
