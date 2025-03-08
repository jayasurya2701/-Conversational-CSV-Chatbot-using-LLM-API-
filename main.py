import streamlit as st
import pandas as pd
import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
LLM_API_KEY = os.getenv("LLM_API_KEY")
LLM_API_URL = os.getenv("LLM_API_URL")
LLM_MODEL_NAME = os.getenv("LLM_MODEL_NAME")

# Validate API credentials
if not all([LLM_API_KEY, LLM_API_URL, LLM_MODEL_NAME]):
    st.error("Missing LLM API credentials. Check your .env file.")

# UI Enhancements
st.set_page_config(page_title="Conversational CSV Chatbot", page_icon="🤖", layout="wide")

# Sidebar settings
st.sidebar.title("⚙️ Settings")
temp = st.sidebar.slider("Response Creativity (Temperature)", 0.0, 1.0, 0.7, 0.1)
theme = st.sidebar.radio("Select Theme", ["Default", "Light", "Dark"])

# Apply theme dynamically
if theme == "Dark":
    theme_css = """
    <style>
        [data-testid="stAppViewContainer"] {
            background-color: #121212;
            color: white;
        }
        [data-testid="stChatMessage"] {
            background-color: #1e1e1e;
            color: white;
            border-radius: 10px;
        }
        [data-testid="stSidebar"] {
            background-color: #1e1e1e;
            color: white;
        }
        .stTextInput, .stTextArea, .stMarkdown, .stButton, .stTitle, .stHeader, .stSubheader {
            color: white !important;
        }
    </style>
    """
elif theme == "Light":
    theme_css = """
    <style>
        [data-testid="stAppViewContainer"] {
            background-color: #ffffff;
            color: black;
        }
        [data-testid="stChatMessage"] {
            background-color: #f0f0f0;
            color: black;
            border-radius: 10px;
        }
    </style>
    """
else:
    theme_css = ""  # Default style

st.markdown(theme_css, unsafe_allow_html=True)

# Function to Load CSV
@st.cache_data
def load_csv(file):
    try:
        return pd.read_csv(file)
    except Exception as e:
        st.error(f"Error loading CSV: {e}")
        return None

# Function to Query LLM API
def query_llm(prompt):
    headers = {"Authorization": f"Bearer {LLM_API_KEY}", "Content-Type": "application/json"}
    payload = {"model": LLM_MODEL_NAME, "messages": [{"role": "user", "content": prompt}], "temperature": temp}
    try:
        response = requests.post(LLM_API_URL, json=payload, headers=headers)
        if response.status_code == 200:
            return response.json().get("choices", [{}])[0].get("message", {}).get("content", "No response from LLM.")
        else:
            st.error(f"API Error {response.status_code}: {response.text}")
            return "Error querying LLM."
    except requests.exceptions.RequestException as e:
        st.error(f"Request failed: {e}")
        return "Error connecting to LLM API."

# Chatbot UI
st.title("🤖 Conversational CSV Chatbot")
uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"])

if uploaded_file is not None:
    df = load_csv(uploaded_file)
    if df is not None:
        text_data = df.astype(str).apply(lambda x: ' '.join(x), axis=1).tolist()
        st.session_state["chat_history"] = st.session_state.get("chat_history", [])

        st.chat_message("assistant").write("Hello! I have analyzed your dataset. Ask me anything about it!")

        user_query = st.chat_input("Ask a question about your data:")
        if user_query:
            prompt = f"Dataset Analysis:\n{text_data[:50]}\nUser Query: {user_query}\nAnswer:"
            response = query_llm(prompt)

            # Store conversation history
            st.session_state["chat_history"].append((user_query, response))

            # Display chat history
            for user_msg, bot_reply in st.session_state["chat_history"]:
                st.chat_message("user").write(user_msg)
                st.chat_message("assistant").write(bot_reply)
