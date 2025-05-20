import streamlit as st
from app_main import run_app

if __name__ == "__main__":
    st.set_page_config(
        page_title="Synopsis Scorer",
        page_icon="📝",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    
    run_app()