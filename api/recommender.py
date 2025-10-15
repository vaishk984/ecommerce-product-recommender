import pandas as pd
import sqlite3
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import os
import inflect  # For handling pluralization
from .llm_handler import client as groq_client # Import the Groq client directly

# --- Configuration ---
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'db.sqlite3')
PRODUCTS_TABLE_NAME = 'products'
p = inflect.engine() # Initialize the pluralization engine

class Recommender:
    def __init__(self):
        print("Initializing hybrid recommender...")
        self.df = self._load_product_data()
        self._prepare_data()
        self.tfidf_vectorizer, self.tfidf_matrix = self._compute_tfidf()
        self.cosine_sim = self._compute_similarity_matrix()
        self.indices = pd.Series(self.df.index, index=self.df['product_id']).drop_duplicates()
        print("Recommender initialized successfully.")

    def _load_product_data(self):
        try:
            conn = sqlite3.connect(DB_PATH)
            query = f"SELECT * FROM {PRODUCTS_TABLE_NAME};"
            df = pd.read_sql_query(query, conn)
            conn.close()
            print(f"Successfully loaded {len(df)} products from the database.")
            return df
        except Exception as e:
            print(f"Error loading data from database: {e}")
            return pd.DataFrame(columns=['product_id', 'name', 'category', 'description'])

    def _prepare_data(self):
        self.df['description'] = self.df['description'].fillna('')
        self.df['category'] = self.df['category'].fillna('')
        self.df['name'] = self.df['name'].fillna('')
        self.df['soup'] = self.df['name'] + ' ' + self.df['category'] + ' ' + self.df['description']
        print("Created 'soup' column for text analysis.")
        
    def _compute_tfidf(self):
        tfidf = TfidfVectorizer(stop_words='english')
        tfidf_matrix = tfidf.fit_transform(self.df['soup'])
        return tfidf, tfidf_matrix

    def _compute_similarity_matrix(self):
        # This is now only used as a fallback
        return cosine_similarity(self.tfidf_matrix, self.tfidf_matrix)

    def _get_llm_search_terms(self, product_name):
        """
        "Head" Strategy: Use LLM to brainstorm complementary products.
        """
        print(f"Using LLM to get complementary search terms for '{product_name}'...")
        prompt = f"""
You are a task-oriented AI that generates related product search terms.
The input product is: "{product_name}"

Your task is to generate a list of 5 to 6 related product search terms by following these strict rules:

1.  **Analyze the product name to determine the target gender** (e.g., "women's", "men's", or "unisex"). All suggestions MUST be appropriate for that gender.
2.  The first 3-4 terms must be **strongly related products** (e.g., other clothing or items in the same category).
3.  The last 2 terms must be **complementary but useful accessories or equipment** (weak links).
4.  The output MUST be a **single, comma-separated list**.
5.  Each term MUST be a **single, singular, lowercase noun** (e.g., "helmet", not "Helmets").
6.  Do NOT include any introduction, explanation, newlines, or extra text. Only the list itself.

---
Here are some perfect examples:

Input: "Alisha Solid Women's Cycling Shorts"
Output: jersey,legging,bra,helmet,bottle

Input: "Men's Leather Wallet"
Output: belt,watch,shoe,briefcase,keychain

Input: "Living Room Sofa"
Output: cushion,rug,lamp,table,ottoman
---
"""
        try:
            chat_completion = groq_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.1-8b-instant",
                temperature=0.2, # Low temperature for factual, predictable output
            )
            terms = chat_completion.choices[0].message.content.strip().lower().split(',')
            print(f"LLM suggested terms: {terms}")
            return [term.strip() for term in terms]
        except Exception as e:
            print(f"LLM query expansion failed: {e}")
            return []
        
        # Add source_category as an argument
    def _find_products_by_keyword(self, keyword, exclude_ids, source_category):
        """
        Search for products containing a keyword in their name or description.
        """
        # Convert keyword to singular to broaden the search
        singular_keyword = p.singular_noun(keyword) or keyword
        
        # --- THIS IS THE LINE THAT WAS MISSING ---
        search_regex = r'\b({}|{})\b'.format(singular_keyword, keyword)
        
        # Search in the 'soup' column for efficiency
        matches = self.df[
            self.df['soup'].str.contains(search_regex, case=False, na=False) &
            ~self.df['product_id'].isin(exclude_ids)
        ]
        
        # Prioritize matches from the same category
        same_category_matches = matches[matches['category'] == source_category]
        if not same_category_matches.empty:
            return same_category_matches.head(2)
            
        return matches.head(2) # Fallback to any category
        
        

    def get_recommendations(self, product_id: str, num_recs: int = 5):
        """
        Hybrid recommendation function.
        """
        if product_id not in self.indices:
            return []

        # --- 1. "Head" Strategy: LLM-powered complementary recommendations ---
        source_product = self.df.iloc[self.indices[product_id]]
        product_name = source_product['name']
        
        complementary_recs_df = pd.DataFrame()
        suggested_terms = self._get_llm_search_terms(product_name)
        
        recommended_ids = {product_id} # Set to keep track of already recommended IDs
        
        if suggested_terms:
            for term in suggested_terms:
                if len(complementary_recs_df) >= num_recs:
                    break
                # + NEW CODE (Correct)
                found_products = self._find_products_by_keyword(term, recommended_ids, source_product['category'])
                if not found_products.empty:
                    complementary_recs_df = pd.concat([complementary_recs_df, found_products])
                    recommended_ids.update(found_products['product_id'].tolist())

        # --- 2. "Tail" Strategy: Improved content-based recommendations ---
        # Get a larger list of similar items first
        idx = self.indices[product_id]
        sim_scores = list(enumerate(self.cosine_sim[idx]))
        sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
        
        similar_recs_df = pd.DataFrame()
        # Iterate through similar items and add them if they are not duplicates
        for i, score in sim_scores[1:]: # Skip the first item (itself)
            if len(similar_recs_df) + len(complementary_recs_df) >= num_recs:
                break
            
            rec_product = self.df.iloc[i]
            # CRITICAL FIX: Check if the name is too similar to the source product
            # and if the ID hasn't already been recommended
            if rec_product['name'] != product_name and rec_product['product_id'] not in recommended_ids:
                # Need to convert the Series to a DataFrame to concat
                similar_recs_df = pd.concat([similar_recs_df, rec_product.to_frame().T])
                recommended_ids.add(rec_product['product_id'])

        # --- 3. Combine and Return ---
        final_recs_df = pd.concat([complementary_recs_df, similar_recs_df]).head(num_recs)
        
        print(f"Generated {len(final_recs_df)} recommendations.")
        return final_recs_df['product_id'].tolist()