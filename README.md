# ⚡ Information Chaos Engine (PS-01)
> **Autonomous Multi-Modal Information Extraction, Entity Resolution & Conflict Radar System**  
> *Built for FlipHack '26 / FlipNotes × AKTU Hackathon*

---

## 📌 Problem Statement Overview
In university environments, critical notices, exam dates, and task deadlines are scattered across heterogeneous channels (PDF circulars, WhatsApp groups, manual memos). Re-scheduling often results in silent overwrites, contradictory deadlines, and student confusion.

**Information Chaos Engine** processes raw inputs, autonomously extracts structured tasks, detects duplicate records, isolates ambiguous phrasing, and triggers an interactive **Conflict Radar** requiring explicit human verification.

---

## 🚀 Key Features

- **Multi-Modal Ingestion:** Supports raw text, official university PDF uploads, manual form registration, and live WhatsApp webhook broadcasts.
- **Autonomous Conflict Radar:** Flags contradictory deadlines across notices and offers side-by-side Matrix Diff view.
- **Ambiguity Detection Engine:** Flags vague temporal expressions (`"next week"`, `"soon"`, `"tentative"`) with custom integrity badges.
- **Authenticity & Trust Scoring:** Heuristic verification of official circular numbers vs unverified forwards.
- **Student Copilot AI:** Context-aware local RAG retrieval assistant to answer student queries in natural language.
- **1-Click Calendar Sync:** Dynamic RFC 5545 iCalendar (`.ics`) generation for Google Calendar / Apple Calendar.
- **Multi-Tenant Architecture:** Secure user signup, phone/email OTP verification, and isolated student workspaces.
- **3D WebGL Interface:** Built with Three.js particle dynamics, Web Speech voice AI, and synthesized Web Audio alerts.

---

## 🛠️ Tech Stack

- **Backend:** Python 3, FastAPI, pypdf, Difflib (Levenshtein & SequenceMatcher heuristics)
- **Frontend:** Modern HTML5, Tailwind CSS, Three.js (WebGL), Web Speech API, Web Audio API
- **Desktop Packaging:** pywebview

---

## ⚡ How to Run Locally

### 1. Clone the repository
```bash
git clone https://github.com/<YOUR-USERNAME>/information-chaos-engine.git
cd information-chaos-engine