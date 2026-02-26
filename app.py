"""
Boltz-2 Structure Prediction UI
Main Streamlit application entry point.
"""
import streamlit as st

st.set_page_config(
    page_title="Boltz-2 Structure Prediction",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize session state defaults
if "runpod_api_key" not in st.session_state:
    st.session_state.runpod_api_key = ""
if "runpod_endpoint_id" not in st.session_state:
    st.session_state.runpod_endpoint_id = ""
if "jobs" not in st.session_state:
    st.session_state.jobs = {}

st.title("🧬 Boltz-2 Structure Prediction")
st.markdown(
    """
    Welcome to the **Boltz-2 Structure Prediction UI** — a Streamlit interface for running
    biomolecular structure predictions powered by [Boltz-2](https://github.com/jwohlwend/boltz)
    on [RunPod](https://runpod.io) serverless GPU infrastructure.

    ### Navigation
    Use the sidebar to navigate between pages:

    | Page | Description |
    |------|-------------|
    | 🏠 Home | Dashboard and status overview |
    | 🔬 Predict | Submit new structure prediction jobs |
    | 📊 Results | View and download prediction results |
    | ❓ Help | Setup guide and documentation |

    ### Quick Start
    1. Visit the **❓ Help** page for setup instructions.
    2. Enter your RunPod API key and endpoint ID in the sidebar on the **🔬 Predict** page.
    3. Upload your FASTA file or paste sequences, configure parameters, and submit.
    4. Monitor job progress and download results from the **📊 Results** page.
    """
)
