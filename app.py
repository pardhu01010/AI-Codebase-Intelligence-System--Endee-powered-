import streamlit as st
import requests

from config import API_BASE_URL

API_URL = API_BASE_URL.rstrip("/")

st.set_page_config(page_title="AI Codebase Intelligence System", layout="wide")

st.title("AI Codebase Intelligence System")
st.markdown(
    "Understand your codebase structurally + semantically. Powered by **Endee**, **Inngest**, & **Groq**."
)

st.sidebar.header("1. Ingest Repository")
repo_url = st.sidebar.text_input(
    "GitHub Repo URL", placeholder="https://github.com/user/repo"
)
if st.sidebar.button("Ingest Repo"):
    if repo_url:
        try:
            with st.spinner("Ingesting repository... Please wait (this can take 1-3 minutes)."):
                response = requests.post(f"{API_URL}/ingest", json={"repo_url": repo_url})
                if response.status_code == 200:
                    import time
                    while True:
                        status_res = requests.get(f"{API_URL}/ingest/status")
                        if status_res.status_code == 200:
                            status = status_res.json().get("status")
                            if status == "completed":
                                st.sidebar.success("Successfully completed! Now you can ask your questions.")
                                break
                            elif status == "error":
                                st.sidebar.error("Ingestion failed! Please check the Inngest Dev Server logs.")
                                break
                        else:
                            st.sidebar.error("Failed to check ingestion status.")
                            break
                        time.sleep(2)
                else:
                    st.sidebar.error(f"Error: {response.text}")
        except Exception as e:
            st.sidebar.error(f"Failed to connect to API: {e}")
    else:
        st.sidebar.warning("Please enter a URL")

st.header("2. Ask Questions")
top_k = st.number_input("Number of context chunks to retrieve", min_value=1, max_value=50, value=5)
query = st.text_input(
    "What do you want to know about the codebase?",
    placeholder="e.g. Where is the dataset loading handled?",
)
if st.button("Search & Reason"):
    if query:
        with st.spinner(f"Retrieving top {top_k} chunks from Endee and reasoning with Groq..."):
            try:
                response = requests.post(f"{API_URL}/query", json={"query": query, "top_k": top_k})
                if response.status_code == 200:
                    data = response.json()
                    st.markdown("### Answer")
                    st.write(data.get("answer", ""))
                    st.markdown("### Sources")
                    sources = data.get("sources", [])
                    if sources:
                        for s in sources:
                            st.markdown(f"- `{s}`")
                    else:
                        st.write("No specific sources found.")
                else:
                    st.error(f"API Error: {response.text}")
            except Exception as e:
                st.error(f"Failed to connect to API: {e}")
    else:
        st.warning("Please enter a query.")
