"""
Home / Dashboard page.
"""
import streamlit as st

st.set_page_config(
    page_title="Home — Boltz-2 UI",
    page_icon="🏠",
    layout="wide",
)

# Ensure session state keys exist
if "runpod_api_key" not in st.session_state:
    st.session_state.runpod_api_key = ""
if "runpod_endpoint_id" not in st.session_state:
    st.session_state.runpod_endpoint_id = ""
if "jobs" not in st.session_state:
    st.session_state.jobs = {}

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.title("🏠 Home Dashboard")
st.markdown(
    """
    **Boltz-2 Structure Prediction UI** lets you submit biomolecular structure predictions
    via [RunPod](https://runpod.io) serverless GPUs without needing a local GPU.
    Predictions are powered by [Boltz-2](https://github.com/jwohlwend/boltz) —
    a state-of-the-art model for protein, DNA, RNA, and ligand complex structure prediction.
    """
)

# ---------------------------------------------------------------------------
# Status card
# ---------------------------------------------------------------------------
st.subheader("⚙️ Configuration Status")
col1, col2, col3 = st.columns(3)

api_key_ok = bool(st.session_state.runpod_api_key)
endpoint_ok = bool(st.session_state.runpod_endpoint_id)

with col1:
    if api_key_ok:
        st.success("✅ RunPod API Key configured")
    else:
        st.error("❌ RunPod API Key not set")

with col2:
    if endpoint_ok:
        st.success("✅ Endpoint ID configured")
    else:
        st.error("❌ Endpoint ID not set")

with col3:
    job_count = len(st.session_state.jobs)
    completed = sum(
        1
        for j in st.session_state.jobs.values()
        if j.get("status") == "COMPLETED"
    )
    st.info(f"📋 {job_count} job(s) tracked | {completed} completed")

if not api_key_ok or not endpoint_ok:
    st.warning(
        "👉 Go to the **🔬 Predict** page and enter your RunPod API key and endpoint ID "
        "in the sidebar to get started."
    )

# ---------------------------------------------------------------------------
# Budget calculator
# ---------------------------------------------------------------------------
st.divider()
st.subheader("💰 Budget Estimation Calculator")
st.markdown(
    """
    Estimate the RunPod cost for your predictions.
    *Assumptions*: RTX 3090 serverless @ ~$0.00026/sec ($0.94/hr).
    Typical prediction time increases with sequence length.
    """
)

calc_col1, calc_col2, calc_col3 = st.columns(3)
with calc_col1:
    num_predictions = st.number_input(
        "Number of predictions", min_value=1, max_value=10000, value=10, step=1
    )
with calc_col2:
    avg_length = st.number_input(
        "Average total residues per complex",
        min_value=50,
        max_value=5000,
        value=300,
        step=50,
    )
with calc_col3:
    gpu_rate = st.number_input(
        "GPU rate ($/sec)", min_value=0.0001, max_value=0.01, value=0.00026, step=0.00001, format="%.5f"
    )

# Rough estimate: ~2 min base + 0.2 sec per residue for a typical Boltz-2 run
estimated_seconds_each = max(120, avg_length * 0.2)
total_seconds = num_predictions * estimated_seconds_each
total_cost = total_seconds * gpu_rate

est_col1, est_col2, est_col3 = st.columns(3)
with est_col1:
    st.metric("⏱ Est. time/prediction", f"{estimated_seconds_each/60:.1f} min")
with est_col2:
    st.metric("💵 Cost/prediction", f"${estimated_seconds_each * gpu_rate:.3f}")
with est_col3:
    st.metric("💸 Total estimated cost", f"${total_cost:.2f}")

st.caption(
    "These are rough estimates only. Actual times vary with model version, "
    "number of samples, and GPU availability."
)

# ---------------------------------------------------------------------------
# Links
# ---------------------------------------------------------------------------
st.divider()
st.subheader("🔗 Useful Links")
link_col1, link_col2, link_col3 = st.columns(3)
with link_col1:
    st.markdown("📄 [Boltz-2 GitHub](https://github.com/jwohlwend/boltz)")
with link_col2:
    st.markdown("🖥️ [RunPod Serverless](https://www.runpod.io/serverless-gpu)")
with link_col3:
    st.markdown("📚 [ColabFold MSA Server](https://github.com/sokrypton/ColabFold)")
