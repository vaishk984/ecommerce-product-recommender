import pandas as pd
import sqlite3
import json

# --- Configuration ---
CSV_PATH = 'data/products.csv'
DB_PATH = 'data/db.sqlite3'
PRODUCTS_TABLE_NAME = 'products'
INTERACTIONS_TABLE_NAME = 'user_interactions'

# --- Main Seeding Function ---
def seed_database():
    """
    Reads product data from a CSV, cleans it, and populates a SQLite database.
    Also creates a table for user interactions and adds sample data.
    """
    print("Starting database seeding process...")

    # 1. Read and Clean Product Data
    try:
        df = pd.read_csv(CSV_PATH)
        print(f"Successfully loaded {CSV_PATH}")

        # Select and rename columns to match our desired schema
        # Based on your screenshot, these are the best columns to use
        df_selected = df[['uniq_id', 'product_name', 'product_category_tree', 'description']].copy()
        df_selected.rename(columns={
            'uniq_id': 'product_id',
            'product_name': 'name',
            'product_category_tree': 'category',
            'description': 'description'
        }, inplace=True)

        # Clean the 'category' column to get only the main category
        # E.g., "Home & Kitchen >> Kitchen & Dining >> ..." -> "Home & Kitchen"
        def clean_category(raw_cat):
            try:
                # The data is a string representation of a list
                first_item = json.loads(raw_cat)[0]
                return first_item.split('>>')[0].strip()
            except (json.JSONDecodeError, IndexError):
                return "Uncategorized" # Handle malformed or empty data

        df_selected['category'] = df_selected['category'].apply(clean_category)
        
        # Drop rows where essential information might be missing
        df_selected.dropna(subset=['product_id', 'name'], inplace=True)
        print(f"Cleaned and prepared {len(df_selected)} product records.")

    except FileNotFoundError:
        print(f"Error: The file {CSV_PATH} was not found. Make sure it's in the 'data' folder.")
        return
    except KeyError as e:
        print(f"Error: A required column was not found in the CSV: {e}")
        return

    # 2. Connect to SQLite and Create Tables
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    print(f"Connected to SQLite database at {DB_PATH}")

    # Use pandas `to_sql` to create the 'products' table and insert data
    # `if_exists='replace'` will drop the table first if it exists, which is
    # useful if you need to re-run the script.
    df_selected.to_sql(PRODUCTS_TABLE_NAME, conn, if_exists='replace', index=False)
    print(f"Successfully created and populated the '{PRODUCTS_TABLE_NAME}' table.")

    # 3. Create and Populate User Interactions Table
    cursor.execute(f'''
    CREATE TABLE IF NOT EXISTS {INTERACTIONS_TABLE_NAME} (
        interaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        product_id TEXT NOT NULL,
        event_type TEXT NOT NULL,
        FOREIGN KEY (product_id) REFERENCES {PRODUCTS_TABLE_NAME} (product_id)
    );
    ''')
    print(f"Successfully created the '{INTERACTIONS_TABLE_NAME}' table.")

    # Add some sample interaction data so we can test the API
    sample_interactions = [
        ('user123', 'c2d766ca982eca8304150849735ffef9', 'view'), # A "Solid" t-shirt
        ('user123', '7f7036a6d550aaa89d34c77bd39a5e48', 'view'), # A "Printed" t-shirt
        ('user456', 'ce5a6818f7707e2cb61fdcdbba61f5ad', 'purchase') # "AW Bellies" shoes
    ]
    
    # We use `executemany` for efficiency
    cursor.executemany(f'INSERT INTO {INTERACTIONS_TABLE_NAME} (user_id, product_id, event_type) VALUES (?, ?, ?)', sample_interactions)
    conn.commit()
    print(f"Inserted {len(sample_interactions)} sample user interactions.")

    # 4. Close the connection
    conn.close()
    print("Database seeding complete. The file 'data/db.sqlite3' is ready.")


if __name__ == '__main__':
    seed_database()