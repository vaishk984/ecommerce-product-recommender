from fastapi import FastAPI, HTTPException
import sqlite3
import os

# Import our custom modules
from .recommender import Recommender
from .llm_handler import generate_explanation, summarize_description_with_llm

# --- Configuration ---
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'db.sqlite3')

# --- FastAPI App Initialization ---
app = FastAPI(
    title="E-commerce Product Recommender API",
    description="An API that provides product recommendations with LLM-powered explanations.",
    version="1.0.0"
)

# --- Load the Recommender Model ---
# This is a global variable that will hold our recommender engine.
# It's loaded once when the application starts up.
recommender_engine = None

@app.on_event("startup")
def load_recommender():
    """
    Load the recommender model into memory when the API server starts.
    """
    global recommender_engine
    print("API starting up. Loading recommender model...")
    recommender_engine = Recommender()
    print("Recommender model loaded.")

# --- Helper Functions ---
def get_db_connection():
    """Establishes a connection to the SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row # This allows us to access columns by name
    return conn

def get_product_details(product_id: str):
    """Fetches product details from the database by product_id."""
    conn = get_db_connection()
    product = conn.execute('SELECT * FROM products WHERE product_id = ?', (product_id,)).fetchone()
    conn.close()
    if product is None:
        return None
    return dict(product) # Convert the Row object to a dictionary

def get_last_user_interaction(user_id: str):
    """Fetches the last product a user interacted with."""
    conn = get_db_connection()
    # For simplicity, we just grab the latest interaction.
    interaction = conn.execute(
        'SELECT product_id FROM user_interactions WHERE user_id = ? ORDER BY interaction_id DESC LIMIT 1',
        (user_id,)
    ).fetchone()
    conn.close()
    if interaction is None:
        return None
    return interaction['product_id']

# --- API Endpoint ---
@app.get("/recommendations/{user_id}")
def get_recommendations_for_user(user_id: str):
    """
    Generates product recommendations for a given user ID.
    """
    print(f"Received request for user_id: {user_id}")

    # 1. Find the source product from the user's behavior
    last_viewed_product_id = get_last_user_interaction(user_id)
    if not last_viewed_product_id:
        raise HTTPException(status_code=404, detail=f"User with ID '{user_id}' not found or has no interactions.")

    source_product_details = get_product_details(last_viewed_product_id)
    if not source_product_details:
         raise HTTPException(status_code=404, detail=f"Source product with ID '{last_viewed_product_id}' not found.")

    print(f"User's last interaction was with product: {source_product_details['name']}")

    # --- NEW: Summarize the source product's description ---
    source_product_details['description'] = summarize_description_with_llm(
        source_product_details['name'],
        source_product_details['description']
    )

    # 2. Get recommendations from the recommender engine
    recommended_ids = recommender_engine.get_recommendations(product_id=last_viewed_product_id, num_recs=5)
    if not recommended_ids:
        raise HTTPException(status_code=404, detail="Could not generate recommendations for this product.")

    # 3. For each recommendation, fetch details, summarize, and generate an explanation
    recommendations_with_explanations = []
    for rec_id in recommended_ids:
        rec_details = get_product_details(rec_id)
        if rec_details:
            # --- NEW: Summarize the recommended product's description ---
            rec_details['description'] = summarize_description_with_llm(
                rec_details['name'],
                rec_details['description']
            )

            explanation = generate_explanation(
                source_product=source_product_details,
                recommended_product=rec_details
            )
            recommendations_with_explanations.append({
                "recommended_product": rec_details,
                "explanation": explanation
            })

    return {
        "user_id": user_id,
        "source_product": source_product_details,
        "recommendations": recommendations_with_explanations
    }