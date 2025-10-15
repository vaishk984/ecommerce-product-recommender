import os
import dotenv
dotenv.load_dotenv()  # Load environment variables from .env file
from groq import Groq

# --- Configuration ---
# PASTE YOUR GROQ API KEY HERE
API_KEY = os.getenv("API_KEY")

# --- Initialization ---
client = None
if not API_KEY or API_KEY == "YOUR-GROQ-API-KEY":
    print("!!! FATAL ERROR: Groq API key is missing.")
else:
    try:
        client = Groq(api_key=API_KEY)
        print("✅ Groq LLM handler configured successfully.")
    except Exception as e:
        print(f"!!! CRITICAL: Failed to configure Groq client. Error: {e}")


def generate_explanation(source_product: dict, recommended_product: dict) -> str:
    if not client:
        return "Groq LLM was not initialized. Check server startup logs."

    prompt = f"""
    You are an expert e-commerce assistant.
    A user recently viewed '{source_product['name']}'.
    We are recommending '{recommended_product['name']}'.
    Explain why this is a good recommendation in one short, friendly sentence. Start with "Because you viewed...".
    """
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            # This is the correct model name for Llama 3 8B on Groq
            model="llama-3.1-8b-instant",
        )
        return chat_completion.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error during Groq LLM call: {e}")
        return "We think you'll like this product based on your recent activity."
    
    # Add this new function to the bottom of your llm_handler.py file

def summarize_description_with_llm(product_name: str, description: str) -> str:
    """
    Uses the LLM to create a short, punchy summary of a product description.
    """
    if not client:
        return description[:150] # Fallback to a simple truncation

    prompt = f"""
    You are an expert e-commerce copywriter. Your task is to summarize a long, messy product description into a concise and appealing blurb for a customer.

    **Rules:**
    - The summary MUST be a maximum of 25 words.
    - It MUST include the primary material and the product type.
    - It should be a single, engaging sentence.

    **Product Name:** "{product_name}"
    **Long Description:** "{description}"

    **Summary:**
    """
    try:
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.1-8b-instant",
            temperature=0.5, # A bit of creativity is good for marketing copy
        )
        return chat_completion.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error during description summarization: {e}")
        return description[:150] # Fallback on error