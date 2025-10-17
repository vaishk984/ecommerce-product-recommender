import streamlit as st
import requests
import pandas as pd

# --- Page Configuration ---
st.set_page_config(
    page_title="E-commerce Product Recommender",
    page_icon="🛍️",
    layout="wide"
)

# --- API Configuration ---
API_URL = "http://127.0.0.1:8000/recommendations/{user_id}"

# --- UI Components ---
st.title("🛍️ E-commerce Product Recommender")
st.markdown(
    "This interactive app demonstrates a product recommender system. "
    "Select a user ID from the sidebar to see personalized recommendations "
    "and the AI-powered explanation for each suggestion."
)

# --- Sidebar for User Input ---
st.sidebar.header("User Selection")
user_id = st.sidebar.selectbox(
    "Choose a sample user ID:",
    ("user123", "user456")
)

if st.sidebar.button("Get Recommendations"):
    # --- API Call ---
    try:
        response = requests.get(API_URL.format(user_id=user_id))
        response.raise_for_status()
        data = response.json()

        # --- Display Results ---
        st.header(f"Recommendations for User: `{data['user_id']}`")

        # --- Source Product ---
        st.subheader("Based on your recent activity on:")
        source_product = data['source_product']

        # FIXED: `st.container()` needs parentheses
        with st.container():
            st.markdown(f"**{source_product['name']}**")
            st.markdown(f"**Category:** {source_product['category']}")
            st.info(f"*{source_product['description'][:200]}...*")

        st.divider()

        # --- Recommendations Section ---
        st.subheader("Here are some products you might like:")
        recommendations = data['recommendations']

        # Create 3 columns for layout
        cols = st.columns(3)

        for i, rec in enumerate(recommendations[:3]):
            with cols[i]:
                product = rec['recommended_product']
                st.markdown(f"**{product['name']}**")
                st.success(f"**Why you'll like it:** {rec['explanation']}")
                with st.expander("See product details"):
                    st.write(f"**Category:** {product['category']}")
                    st.write(product['description'])

    except requests.exceptions.RequestException as e:
        st.error(f"Could not connect to the API. Please ensure the FastAPI server is running.\n\nError: {e}")
    except KeyError:
        st.error("Received an unexpected data format from the API.")
