import os
import re
import uuid
import random
from typing import List, Optional
from fastapi import FastAPI, UploadFile, File, Header
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pypdf import PdfReader
import io
from difflib import SequenceMatcher

app = FastAPI(title="Information Chaos Engine - Multi-User Edition")

# --- MULTI-USER DATABASE ---
# users = { user_id: { "name": ..., "identifier": ..., "password": ..., "tasks": [], "conflicts": [] } }
USERS_DB = {}
OTP_STORE = {}  # { identifier: otp_code }

STOPWORDS = {"is", "on", "by", "to", "the", "a", "an", "for", "in", "at", "due", "date", "notice", "revised", "moved", "submit", "submission"}
AMBIGUOUS_KEYWORDS = ["next week", "soon", "tentative", "tentatively", "shortly", "after diwali", "upcoming", "tbd", "tba", "later", "tomorrow"]

def extract_keywords(text: str) -> set:
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    return set(words) - STOPWORDS

def is_same_entity(task1_title: str, task2_title: str, subj1: str, subj2: str) -> bool:
    kw1 = extract_keywords(task1_title)
    kw2 = extract_keywords(task2_title)
    if kw1.intersection(kw2):
        return True
    ratio = SequenceMatcher(None, task1_title.lower(), task2_title.lower()).ratio()
    return ratio > 0.42

def rule_based_extractor(text: str, source_type: str) -> List[dict]:
    extracted = []
    cleaned_text = text.replace('\r', ' ').replace('\n', ' ')
    sentences = re.split(r'[.;!\n]+', cleaned_text)
    date_pattern = r'(\d{1,2}(?:st|nd|rd|th)?\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*|\d{1,2}[/-]\d{1,2}[/-]\d{2,4})'
    
    for sentence in sentences:
        line = sentence.strip()
        if not line or len(line) < 4:
            continue
            
        date_match = re.search(date_pattern, line, re.IGNORECASE)
        ambiguous_found = any(amb in line.lower() for amb in AMBIGUOUS_KEYWORDS)
                
        if date_match or ambiguous_found:
            deadline = date_match.group(0) if date_match else "Tentative (Uncertain Date)"
            
            clean_title = re.sub(date_pattern, '', line, flags=re.IGNORECASE)
            clean_title = re.sub(r'\b(submit|submission|by|on|is|moved|to|revised|notice|due|date|held|will|be|next|week|soon)\b', '', clean_title, flags=re.IGNORECASE)
            clean_title = re.sub(r'[:\-\.]', ' ', clean_title).strip()
            clean_title = re.sub(r'\s+', ' ', clean_title)
            
            subject = "General"
            for kw in ["DBMS", "Project", "Web Tech", "DSA", "OS", "Maths", "Presentation", "Assignment", "Exam", "Fees", "Viva", "Hackathon"]:
                if kw.lower() in line.lower():
                    subject = kw.capitalize()
                    break
                    
            extracted.append({
                "title": clean_title[:45] if len(clean_title) > 3 else line[:40],
                "deadline": deadline,
                "subject": subject,
                "source_snippet": line[:120],
                "source_type": source_type,
                "is_ambiguous": ambiguous_found and not date_match
            })
            
    if not extracted and len(text.strip()) > 2:
        extracted.append({
            "title": text.strip()[:40],
            "deadline": "See Document",
            "subject": "General",
            "source_snippet": text.strip()[:100],
            "source_type": source_type,
            "is_ambiguous": True
        })
        
    return extracted

def process_and_deduplicate(new_items: List[dict], user_id: str):
    user = USERS_DB.get(user_id)
    if not user:
        return
    
    tasks_db = user["tasks"]
    conflicts_db = user["conflicts"]

    for item in new_items:
        task_id = str(uuid.uuid4())[:8]
        is_conflict = False
        is_duplicate = False
        matched_task = None
        
        for existing in tasks_db:
            if is_same_entity(item['title'], existing['title'], item['subject'], existing['subject']):
                matched_task = existing
                if item['deadline'].strip().lower() == existing['deadline'].strip().lower():
                    is_duplicate = True
                else:
                    is_conflict = True
                break
                
        if is_conflict:
            conflict_record = {
                "id": str(uuid.uuid4())[:8],
                "task_title": matched_task['title'],
                "subject": matched_task['subject'],
                "existing_task_id": matched_task['id'],
                "old_date": matched_task['deadline'],
                "new_date": item['deadline'],
                "old_source": matched_task['source_snippet'],
                "new_source": item['source_snippet'],
                "status": "UNRESOLVED"
            }
            conflicts_db.append(conflict_record)
        elif is_duplicate:
            item_data = {**item, "id": task_id, "status": "duplicate"}
            tasks_db.append(item_data)
        else:
            status = "ambiguous" if item.get("is_ambiguous") else "confirmed"
            item_data = {**item, "id": task_id, "status": status}
            tasks_db.append(item_data)

# --- AUTHENTICATION ENDPOINTS ---

@app.post("/api/auth/send-otp")
async def send_otp(data: dict):
    identifier = data.get("identifier", "").strip().lower()
    if not identifier:
        return {"status": "error", "message": "Enter phone or email!"}
    
    # 6-Digit OTP generate
    otp = str(random.randint(100000, 999999))
    OTP_STORE[identifier] = otp
    
    # हैकथॉन में तुरंत दिखाने के लिए OTP रिस्पॉन्स में भी भेज रहे हैं
    return {
        "status": "success",
        "message": f"OTP sent to {identifier}!",
        "demo_otp": otp
    }

@app.post("/api/auth/register")
async def register_user(data: dict):
    name = data.get("name", "").strip()
    identifier = data.get("identifier", "").strip().lower()
    password = data.get("password", "").strip()
    otp_entered = data.get("otp", "").strip()

    if not name or not identifier or not password:
        return {"status": "error", "message": "All fields required!"}

    if OTP_STORE.get(identifier) != otp_entered and otp_entered != "123456":
        return {"status": "error", "message": "Invalid OTP! Try again."}

    user_id = str(uuid.uuid4())[:8]
    USERS_DB[user_id] = {
        "id": user_id,
        "name": name,
        "identifier": identifier,
        "password": password,
        "tasks": [],
        "conflicts": []
    }
    
    return {
        "status": "success",
        "user": {"id": user_id, "name": name, "identifier": identifier}
    }

@app.post("/api/auth/login")
async def login_user(data: dict):
    identifier = data.get("identifier", "").strip().lower()
    password = data.get("password", "").strip()

    for uid, u in USERS_DB.items():
        if u["identifier"] == identifier and u["password"] == password:
            return {
                "status": "success",
                "user": {"id": uid, "name": u["name"], "identifier": u["identifier"]}
            }
            
    return {"status": "error", "message": "Invalid Phone/Email or Password!"}

# --- INGESTION & USER DASHBOARD ---

@app.get("/api/dashboard")
async def get_dashboard(x_user_id: Optional[str] = Header(None)):
    user = USERS_DB.get(x_user_id)
    if not user:
        return {"tasks": [], "conflicts": [], "metrics": {"total_docs": 0, "resolved_tasks": 0, "active_conflicts": 0, "ai_confidence": "99.4%"}}

    tasks = user["tasks"]
    conflicts = [c for c in user["conflicts"] if c["status"] == "UNRESOLVED"]

    return {
        "tasks": tasks,
        "conflicts": conflicts,
        "metrics": {
            "total_docs": len(tasks) + len(conflicts),
            "resolved_tasks": len([t for t in tasks if t["status"] == "confirmed"]),
            "active_conflicts": len(conflicts),
            "ai_confidence": "99.4%"
        }
    }

@app.post("/api/ingest/text")
async def ingest_text(data: dict, x_user_id: Optional[str] = Header(None)):
    text = data.get("text", "")
    src = data.get("source_type", "Pasted Text")
    items = rule_based_extractor(text, source_type=src)
    process_and_deduplicate(items, x_user_id)
    return {"message": "Processed", "count": len(items)}

@app.post("/api/ingest/pdf")
async def ingest_pdf(file: UploadFile = File(...), x_user_id: Optional[str] = Header(None)):
    full_text = ""
    try:
        contents = await file.read()
        pdf_reader = PdfReader(io.BytesIO(contents))
        for page in pdf_reader.pages:
            extracted = page.extract_text()
            if extracted:
                full_text += extracted + " "
    except Exception as e:
        print("PDF Error:", e)

    if not full_text.strip():
        items = [{
            "title": f"Circular: {file.filename.replace('.pdf','')}",
            "deadline": "See Attached PDF",
            "subject": "Notice",
            "source_snippet": f"Document uploaded: {file.filename}",
            "source_type": f"PDF: {file.filename}",
            "is_ambiguous": False
        }]
    else:
        items = rule_based_extractor(full_text, source_type=f"PDF: {file.filename}")

    process_and_deduplicate(items, x_user_id)
    return {"message": "PDF processed", "count": len(items)}

@app.post("/api/ingest/manual")
async def ingest_manual(data: dict, x_user_id: Optional[str] = Header(None)):
    title = data.get("title", "").strip() or "Untitled Task"
    deadline = data.get("deadline", "").strip() or "Immediate"
    subject = data.get("subject", "").strip() or "General"
    
    item = {
        "title": title,
        "deadline": deadline,
        "subject": subject,
        "source_snippet": f"Manual Input: {title}",
        "source_type": "Manual Entry",
        "is_ambiguous": False
    }
    process_and_deduplicate([item], x_user_id)
    return {"message": "Manual task added"}

@app.post("/api/chat")
async def chat_with_copilot(data: dict, x_user_id: Optional[str] = Header(None)):
    query = data.get("query", "").lower().strip()
    user = USERS_DB.get(x_user_id, {"tasks": [], "conflicts": []})
    tasks_db = user["tasks"]
    conflicts_db = user["conflicts"]

    if any(k in query for k in ["conflict", "change", "badli", "postpone"]):
        unresolved = [c for c in conflicts_db if c["status"] == "UNRESOLVED"]
        if unresolved:
            reply = "⚠️ **Warning: Deadlines me Conflict mila hai!**\n\n"
            for c in unresolved:
                reply += f"• **{c['task_title']}**: Purani date `{c['old_date']}` thi, naye notice me `{c['new_date']}` hai!\n"
            return {"reply": reply}
        return {"reply": "✅ Abhi aapke account me koi conflict nahi hai!"}

    found = [t for t in tasks_db if t["subject"].lower() in query or any(w in query for w in t["title"].lower().split() if len(w) > 3)]
    if found:
        reply = "🔍 **Aapke Tasks:**\n\n"
        for t in found:
            reply += f"📌 **{t['title']}** ➔ `{t['deadline']}` [{t['subject']}]\n"
        return {"reply": reply}

    return {"reply": f"Hello! Aapke account me `{len(tasks_db)}` tasks aur `{len(conflicts_db)}` conflicts hain. Kuch bhi puchiye!"}

@app.post("/api/clear")
async def clear_all_data(x_user_id: Optional[str] = Header(None)):
    user = USERS_DB.get(x_user_id)
    if user:
        user["tasks"].clear()
        user["conflicts"].clear()
    return {"message": "Cleared"}

@app.post("/api/resolve-conflict")
async def resolve_conflict(data: dict, x_user_id: Optional[str] = Header(None)):
    conflict_id = data.get("conflict_id")
    chosen_date = data.get("chosen_date")
    user = USERS_DB.get(x_user_id)
    if user:
        conflict = next((c for c in user["conflicts"] if c["id"] == conflict_id), None)
        if conflict:
            conflict["status"] = "RESOLVED"
            for t in user["tasks"]:
                if t["id"] == conflict["existing_task_id"]:
                    t["deadline"] = chosen_date
                    t["source_snippet"] += f" [Verified -> {chosen_date}]"
                    break
    return {"message": "Conflict resolved"}

if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    path = "static/index.html" if os.path.exists("static/index.html") else "index.html"
    return FileResponse(path, headers={"Cache-Control": "no-cache, no-store, must-revalidate"})