"""
Structure Prediction submission page.
"""
import json
import time
import uuid

import pandas as pd
import streamlit as st

from utils.fasta_parser import parse_fasta, validate_chain_ids
from utils.yaml_builder import LigandEntry, build_boltz_yaml, build_prediction_payload

st.set_page_config(
    page_title="Predict — Boltz-2 UI",
    page_icon="🔬",
    layout="wide",
)

# Ensure session state keys exist
for _key, _default in [
    ("runpod_api_key", ""),
    ("runpod_endpoint_id", ""),
    ("jobs", {}),
    ("parsed_sequences", []),
    ("ligands", []),
]:
    if _key not in st.session_state:
        st.session_state[_key] = _default

# ---------------------------------------------------------------------------
# Sidebar — credentials
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("🔑 RunPod Credentials")
    api_key = st.text_input(
        "RunPod API Key",
        type="password",
        value=st.session_state.runpod_api_key,
        key="_api_key_input",
        help="Your RunPod API key. Never stored to disk.",
    )
    st.session_state.runpod_api_key = api_key

    endpoint_id = st.text_input(
        "RunPod Endpoint ID",
        value=st.session_state.runpod_endpoint_id,
        key="_endpoint_id_input",
        help="The serverless endpoint ID from your RunPod dashboard.",
    )
    st.session_state.runpod_endpoint_id = endpoint_id

    st.divider()
    if api_key and endpoint_id:
        st.success("✅ Credentials configured")
    else:
        st.warning("Enter credentials to enable job submission.")

# ---------------------------------------------------------------------------
# Main content
# ---------------------------------------------------------------------------
st.title("🔬 Structure Prediction")

# ---------------------------------------------------------------------------
# Section 1: Sequence input
# ---------------------------------------------------------------------------
st.subheader("1. Input Sequences")
input_tab1, input_tab2 = st.tabs(["📁 Upload FASTA file(s)", "✏️ Paste FASTA text"])

raw_fasta_text = ""

with input_tab1:
    uploaded_files = st.file_uploader(
        "Upload FASTA file(s)",
        type=["fasta", "fa", "fna", "faa"],
        accept_multiple_files=True,
        help="Accepts .fasta, .fa, .fna, .faa files.",
    )
    if uploaded_files:
        combined = []
        for uf in uploaded_files:
            combined.append(uf.read().decode("utf-8", errors="replace"))
        raw_fasta_text = "\n".join(combined)

with input_tab2:
    pasted_text = st.text_area(
        "Paste FASTA-formatted sequences",
        height=200,
        placeholder=(
            ">A|protein\nMVTIEGNVSLV...\n>B|protein\nEFKEAFSLF..."
        ),
    )
    if pasted_text.strip():
        raw_fasta_text = pasted_text

# Parse sequences
if raw_fasta_text.strip():
    sequences, parse_errors = parse_fasta(raw_fasta_text)
    id_warnings = validate_chain_ids(sequences)

    if parse_errors:
        for err in parse_errors:
            st.error(f"Parse error: {err}")

    if id_warnings:
        for w in id_warnings:
            st.warning(w)

    if sequences:
        st.session_state.parsed_sequences = sequences
        st.success(f"✅ Parsed {len(sequences)} sequence(s).")

        # Sequence preview table
        st.subheader("Sequence Preview")
        rows = [
            {
                "Chain ID": s.chain_id,
                "Type": s.entity_type,
                "Length": s.length,
                "Sequence (first 50)": s.preview,
                "Warnings": "; ".join(s.warnings) if s.warnings else "—",
            }
            for s in sequences
        ]
        st.dataframe(pd.DataFrame(rows), use_container_width=True)

        for seq in sequences:
            if seq.warnings:
                for w in seq.warnings:
                    st.warning(f"Chain {seq.chain_id}: {w}")
else:
    st.session_state.parsed_sequences = []

# ---------------------------------------------------------------------------
# Section 2: Optional ligands
# ---------------------------------------------------------------------------
st.divider()
st.subheader("2. Ligands (Optional)")
st.markdown("Add small-molecule ligands by SMILES string or CCD code.")

lig_col1, lig_col2, lig_col3, lig_col4 = st.columns([1, 3, 3, 1])
with lig_col1:
    lig_chain = st.text_input("Chain ID", value="L", key="lig_chain")
with lig_col2:
    lig_smiles = st.text_input("SMILES (optional)", key="lig_smiles")
with lig_col3:
    lig_ccd = st.text_input("CCD code (optional)", key="lig_ccd")
with lig_col4:
    st.write("")
    st.write("")
    if st.button("➕ Add Ligand"):
        if not lig_smiles and not lig_ccd:
            st.error("Provide either SMILES or CCD code.")
        elif not lig_chain:
            st.error("Provide a chain ID for the ligand.")
        else:
            entry = LigandEntry(
                chain_id=lig_chain,
                smiles=lig_smiles or None,
                ccd=lig_ccd or None,
            )
            st.session_state.ligands.append(entry)
            st.success(f"Ligand '{lig_chain}' added.")

if st.session_state.ligands:
    lig_rows = [
        {
            "Chain ID": l.chain_id,
            "SMILES": l.smiles or "",
            "CCD": l.ccd or "",
        }
        for l in st.session_state.ligands
    ]
    st.dataframe(pd.DataFrame(lig_rows), use_container_width=True)
    if st.button("🗑️ Clear All Ligands"):
        st.session_state.ligands = []
        st.rerun()

# ---------------------------------------------------------------------------
# Section 3: Prediction parameters
# ---------------------------------------------------------------------------
st.divider()
st.subheader("3. Prediction Parameters")

param_col1, param_col2 = st.columns(2)

with param_col1:
    model_version = st.selectbox(
        "Model version",
        options=["boltz2", "boltz1"],
        index=0,
        help="boltz2 is recommended for most use cases.",
    )
    recycling_steps = st.slider(
        "Recycling steps", min_value=1, max_value=10, value=3,
        help="Number of recycling iterations. More = slower but potentially better.",
    )
    sampling_steps = st.slider(
        "Sampling steps", min_value=50, max_value=500, value=200, step=10,
        help="Diffusion sampling steps.",
    )
    diffusion_samples = st.slider(
        "Diffusion samples", min_value=1, max_value=10, value=1,
        help="Number of structure samples generated.",
    )
    max_parallel = st.number_input(
        "Max parallel samples", min_value=1, max_value=20, value=5,
        help="Maximum samples processed in parallel (memory vs. speed trade-off).",
    )

with param_col2:
    default_step_scale = 1.5 if model_version == "boltz2" else 1.638
    step_scale = st.slider(
        "Step scale", min_value=1.0, max_value=2.0, value=default_step_scale, step=0.01,
        help="Diffusion step scale factor.",
    )
    output_format = st.selectbox(
        "Output format",
        options=["mmcif", "pdb"],
        index=0,
        help="mmCIF is recommended; PDB has chain limitations.",
    )
    use_msa_server = st.checkbox(
        "Use MSA server",
        value=True,
        help="Automatically generate MSAs via the free ColabFold server.",
    )
    msa_server_url = st.text_input(
        "MSA server URL",
        value="https://api.colabfold.com",
        disabled=not use_msa_server,
    )
    use_potentials = st.checkbox(
        "Use potentials",
        value=False,
        help="Enable auxiliary potentials.",
    )
    override = st.checkbox(
        "Override existing results",
        value=False,
    )
    no_kernels = st.checkbox(
        "Disable cuEquivariance kernels",
        value=False,
        help="Use for older GPUs (compute capability < 8.0).",
    )

job_name = st.text_input(
    "Job name",
    value=f"prediction_{int(time.time())}",
    help="A short identifier for your prediction job.",
)

# ---------------------------------------------------------------------------
# YAML preview
# ---------------------------------------------------------------------------
st.divider()
st.subheader("4. YAML Preview")

if st.session_state.parsed_sequences:
    yaml_content = build_boltz_yaml(
        st.session_state.parsed_sequences,
        ligands=st.session_state.ligands or None,
    )
    with st.expander("Show generated Boltz-2 YAML", expanded=False):
        st.code(yaml_content, language="yaml")
else:
    yaml_content = ""
    st.info("Add sequences above to preview the YAML input.")

# ---------------------------------------------------------------------------
# Submit
# ---------------------------------------------------------------------------
st.divider()
st.subheader("5. Submit Job")

credentials_ok = bool(
    st.session_state.runpod_api_key and st.session_state.runpod_endpoint_id
)
sequences_ok = bool(st.session_state.parsed_sequences)

if not credentials_ok:
    st.warning("⚠️ Configure RunPod credentials in the sidebar first.")
if not sequences_ok:
    st.warning("⚠️ Add at least one sequence before submitting.")

submit_disabled = not (credentials_ok and sequences_ok)

if st.button("🚀 Submit Prediction", disabled=submit_disabled, type="primary"):
    payload = build_prediction_payload(
        yaml_content=yaml_content,
        job_name=job_name,
        model=model_version,
        recycling_steps=recycling_steps,
        sampling_steps=sampling_steps,
        diffusion_samples=diffusion_samples,
        max_parallel_samples=int(max_parallel),
        step_scale=step_scale,
        output_format=output_format,
        use_msa_server=use_msa_server,
        msa_server_url=msa_server_url,
        use_potentials=use_potentials,
        override=override,
        no_kernels=no_kernels,
    )

    with st.status("Submitting job to RunPod…", expanded=True) as status_box:
        try:
            from utils.runpod_client import RunPodClient

            client = RunPodClient(
                api_key=st.session_state.runpod_api_key,
                endpoint_id=st.session_state.runpod_endpoint_id,
            )
            result = client.submit_job(payload)
            job_id = result.get("id", str(uuid.uuid4()))
            initial_status = result.get("status", "IN_QUEUE")

            st.session_state.jobs[job_id] = {
                "job_id": job_id,
                "job_name": job_name,
                "status": initial_status,
                "submitted_at": time.time(),
                "payload": payload,
                "result": None,
            }

            status_box.update(
                label=f"✅ Job submitted! ID: {job_id}", state="complete"
            )
            st.success(
                f"Job **{job_id}** submitted successfully. "
                "Monitor progress on the **📊 Results** page."
            )

        except Exception as exc:
            status_box.update(label="❌ Submission failed", state="error")
            st.error(f"Failed to submit job: {exc}")
