# E-commerce Product Recommender 

This project is a complete, full-stack application that provides intelligent, personalized product recommendations. It features a Streamlit web interface, a FastAPI backend, a hybrid recommendation engine, and leverages a Large Language Model (LLM) for generating dynamic, human-like explanations and product summaries.

---

## Key Features

* **Interactive Web Interface:** A user-friendly frontend built with Streamlit to visualize recommendations.
* **Hybrid Recommendation Engine:** Combines two strategies for smart suggestions:
    * **LLM-Powered Query Expansion:** Uses an LLM to brainstorm complementary product categories (e.g., "helmet" for "cycling shorts").
    * **Content-Based Filtering:** Uses TF-IDF and Cosine Similarity to find similar products while filtering out exact duplicates.
* **AI-Powered Explanations & Summaries:** Leverages the Llama 3.1 model via the Groq API to:
    * Generate a unique, friendly explanation for each recommendation.
    * Summarize long product descriptions into concise, appealing blurbs.
* **Decoupled Architecture:** A robust backend API built with FastAPI serves the data, allowing the frontend to remain lightweight and responsive.

---

## Video Link
https://youtu.be/iEnZjNh3F2o?si=HTh-eJE8Mb0gm19z

---

## Technology Stack

| Component | Technology/Library |
| :--- | :--- |
| **Frontend** | Streamlit |
| **Backend API** | Python, FastAPI, Uvicorn |
| **Recommendation Engine** | Pandas, Scikit-learn, Inflect |
| **LLM Integration** | Groq API (Llama 3.1) |
| **Database** | SQLite |

---

## Workflow

User → Streamlit UI → FastAPI → Recommender (TF-IDF + Cosine Similarity) → Groq LLM → Response

---

## Screenshots

<img width="1919" height="902" alt="Screenshot 2025-10-17 113518" src="https://github.com/user-attachments/assets/08dd51f7-f3d9-4a86-ac11-949c4e2bcac3" />

<img width="1919" height="785" alt="Screenshot 2025-10-17 114147" src="https://github.com/user-attachments/assets/d2442e69-1d5c-417d-bf2e-745c7ffc6606" />

<img width="1919" height="881" alt="Screenshot 2025-10-17 114155" src="https://github.com/user-attachments/assets/b96fd5aa-ccc2-4dc8-8ff5-3dae6eaf5a8c" />



## Setup & Run

**1. Clone the repository:**
```bash
git clone <your-repository-url>
cd product-recommender
```

**2  Create and activate a virtual environment:**
```bash
python -m venv venv
# On Windows
.\venv\Scripts\Activate.ps1
# On macOS/Linux
source venv/bin/activate
```

**3. Install dependencies:**
```bash
pip install -r requirements.txt
```

**4. Add API Key:**
```bash
Get an API key from Groq.
Paste the key into the API_KEY variable inside api/llm_handler.py
```
**5. Seed the database:**
```bash
python seed_database.py
```
**6. Run the Application:**

Terminal 1 (Backend):
```bash
python -m uvicorn api.main:app --reload
```

Terminal 2 (Frontend):
```bash
streamlit run app.py
```
