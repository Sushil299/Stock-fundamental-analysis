# -*- coding: utf-8 -*-
"""user_app

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1-870mHldiZ9svkczmIvpy1jMZH4KKxJk
"""

import streamlit as st
import requests

# Backend URL
BACKEND_URL = "https://ai-equity-analyst.onrender.com"

# Set Streamlit Page Layout
st.set_page_config(page_title="AI Equity Analyst", layout="wide")

# Title Section
st.title("AI Equity Analyst")
st.markdown("###Get AI-powered fundamental analysis of listed companies.")

# Fetch Available Companies for Dropdown
st.sidebar.header("Select a Company")

companies_response = requests.get(f"{BACKEND_URL}/companies")  # New API to list companies
if companies_response.status_code == 200:
    company_list = companies_response.json().get("companies", [])
else:
    company_list = []

if not company_list:
    st.sidebar.warning("⚠️ No companies available. Try uploading data.")
else:
    company_name = st.sidebar.selectbox("Choose a Company", company_list)

    # Fetch Analysis on Button Click
    if st.sidebar.button("Get Analysis"):
        response = requests.get(f"{BACKEND_URL}/summary/{company_name}")
        if response.status_code == 200:
            summaries = response.json().get("Summaries", [])
            if summaries:
                st.markdown("## 🔍 AI-Generated Summary")
                for summary in summaries:
                    st.write(summary["Summary"])  # Directly show the summary
                    st.markdown("---")
            else:
                st.warning("⚠️ No summaries found for this company.")
        else:
            st.error("❌ Failed to fetch summaries.")

