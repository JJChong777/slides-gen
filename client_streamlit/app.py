import streamlit as st
import requests
from modules import API_URL_EDIT, API_URL_GEN

st.set_page_config(layout="wide")

def main():
    pages = [
        st.Page("slides.py", title="Slide Deck AI", icon="📊")
    ]

    selected_page = st.navigation(pages)
    selected_page.run()

if __name__ == "__main__":
    main()