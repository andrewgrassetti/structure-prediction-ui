"""
Results viewer page — lists jobs, displays confidence metrics, and shows
3D structure previews.
"""
import base64
import json
import time

import streamlit as st

from utils.runpod_client import RunPodClient
from utils.visualization import PY3DMOL_AVAILABLE, show_structure_in_streamlit

st.set_page_config(
    page_title="Results — Boltz-2 UI",
    page_icon="📊",
    layout="wide",
)

# Ensure session state
for _key, _default in [
    ("runpod_api_key", ""),
    ("runpod_endpoint_id", ""),
    ("jobs", {}),
]:
    if _key not in st.session_state:
        st.session_state[_key] = _default

st.title("📊 Results Viewer")

if not st.session_state.jobs:
    st.info(
        "No jobs tracked yet. Submit a prediction on the **🔬 Predict** page first."
    )
    st.stop()

# ---------------------------------------------------------------------------
# Auto-refresh controls
# ---------------------------------------------------------------------------
refresh_col1, refresh_col2 = st.columns([3, 1])
with refresh_col1:
    st.markdown(f"**{len(st.session_state.jobs)}** job(s) tracked.")
with refresh_col2:
    if st.button("🔄 Refresh All Statuses"):
        if st.session_state.runpod_api_key and st.session_state.runpod_endpoint_id:
            client = RunPodClient(
                api_key=st.session_state.runpod_api_key,
                endpoint_id=st.session_state.runpod_endpoint_id,
            )
            refreshed = 0
            for job_id, job in st.session_state.jobs.items():
                if job["status"] not in ("COMPLETED", "FAILED", "CANCELLED"):
                    try:
                        status_data = client.get_job_status(job_id)
                        job["status"] = status_data.get("status", job["status"])
                        if job["status"] == "COMPLETED":
                            job["result"] = status_data.get("output")
                        refreshed += 1
                    except Exception as exc:
                        st.warning(f"Could not refresh {job_id}: {exc}")
            st.success(f"Refreshed {refreshed} in-progress job(s).")
        else:
            st.warning("Configure RunPod credentials to refresh statuses.")

# ---------------------------------------------------------------------------
# Job list
# ---------------------------------------------------------------------------
for job_id, job in st.session_state.jobs.items():
    status = job.get("status", "unknown")
    status_label = RunPodClient.format_status(status)
    submitted_ts = job.get("submitted_at", 0)
    submitted_str = (
        time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(submitted_ts))
        if submitted_ts
        else "—"
    )

    with st.expander(
        f"{status_label}  |  **{job.get('job_name', job_id)}**  —  `{job_id}`  "
        f"({submitted_str})",
        expanded=(status == "COMPLETED"),
    ):
        info_col1, info_col2 = st.columns(2)
        with info_col1:
            st.write(f"**Job ID:** `{job_id}`")
            st.write(f"**Status:** {status_label}")
        with info_col2:
            st.write(f"**Submitted:** {submitted_str}")
            st.write(f"**Job name:** {job.get('job_name', '—')}")

        # Refresh individual job
        if status not in ("COMPLETED", "FAILED", "CANCELLED"):
            if st.button(f"🔄 Refresh status", key=f"refresh_{job_id}"):
                if st.session_state.runpod_api_key and st.session_state.runpod_endpoint_id:
                    try:
                        client = RunPodClient(
                            api_key=st.session_state.runpod_api_key,
                            endpoint_id=st.session_state.runpod_endpoint_id,
                        )
                        status_data = client.get_job_status(job_id)
                        job["status"] = status_data.get("status", job["status"])
                        if job["status"] == "COMPLETED":
                            job["result"] = status_data.get("output")
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Refresh failed: {exc}")
                else:
                    st.warning("Configure RunPod credentials in the sidebar.")

        # Show results when completed
        if status == "COMPLETED" and job.get("result"):
            result = job["result"]
            st.divider()

            # ------------------------------------------------------------------
            # Confidence metrics
            # ------------------------------------------------------------------
            confidence_json_b64 = result.get("confidence_json_b64")
            if confidence_json_b64:
                try:
                    conf_text = base64.b64decode(confidence_json_b64).decode("utf-8")
                    conf_data = json.loads(conf_text)

                    st.subheader("📈 Confidence Metrics")
                    metric_cols = st.columns(4)
                    metrics_map = {
                        "Confidence score": conf_data.get("confidence_score"),
                        "PTM": conf_data.get("ptm"),
                        "iPTM": conf_data.get("iptm"),
                        "Ligand iPTM": conf_data.get("ligand_iptm"),
                        "Protein iPTM": conf_data.get("protein_iptm"),
                        "Complex pLDDT": conf_data.get("complex_plddt"),
                        "Complex ipLDDT": conf_data.get("complex_iplddt"),
                        "Complex PDE": conf_data.get("complex_pde"),
                    }
                    for i, (label, value) in enumerate(metrics_map.items()):
                        if value is not None:
                            metric_cols[i % 4].metric(
                                label, f"{float(value):.3f}"
                            )

                    with st.expander("Raw confidence JSON"):
                        st.json(conf_data)
                except Exception as exc:
                    st.warning(f"Could not parse confidence JSON: {exc}")

            # ------------------------------------------------------------------
            # Affinity results
            # ------------------------------------------------------------------
            affinity_json_b64 = result.get("affinity_json_b64")
            if affinity_json_b64:
                try:
                    aff_text = base64.b64decode(affinity_json_b64).decode("utf-8")
                    aff_data = json.loads(aff_text)
                    st.subheader("🔗 Affinity Results")
                    with st.expander("Affinity JSON"):
                        st.json(aff_data)
                except Exception as exc:
                    st.warning(f"Could not parse affinity JSON: {exc}")

            # ------------------------------------------------------------------
            # Structure download
            # ------------------------------------------------------------------
            structure_b64 = result.get("structure_b64")
            structure_filename = result.get("structure_filename", "structure.cif")
            if structure_b64:
                structure_bytes = base64.b64decode(structure_b64)
                st.download_button(
                    label=f"⬇️ Download {structure_filename}",
                    data=structure_bytes,
                    file_name=structure_filename,
                    mime="chemical/x-mmcif"
                    if structure_filename.endswith(".cif")
                    else "chemical/x-pdb",
                    key=f"dl_struct_{job_id}",
                )

                # ------------------------------------------------------------------
                # 3D viewer
                # ------------------------------------------------------------------
                st.subheader("🧬 3D Structure Preview")
                if PY3DMOL_AVAILABLE:
                    fmt = (
                        "mmcif" if structure_filename.endswith(".cif") else "pdb"
                    )
                    structure_text = structure_bytes.decode(
                        "utf-8", errors="replace"
                    )
                    style_option = st.selectbox(
                        "Colouring style",
                        options=["plddt", "cartoon", "stick", "sphere"],
                        key=f"style_{job_id}",
                    )
                    spin_option = st.checkbox(
                        "Auto-rotate", key=f"spin_{job_id}", value=False
                    )
                    show_structure_in_streamlit(
                        structure_data=structure_text,
                        fmt=fmt,
                        style=style_option,
                        spin=spin_option,
                    )
                else:
                    st.info(
                        "Install py3Dmol (`pip install py3Dmol`) to enable 3D "
                        "structure preview."
                    )

        elif status == "FAILED":
            st.error(
                f"Job failed. Error: {job.get('result', {}).get('error', 'unknown')}"
                if isinstance(job.get("result"), dict)
                else "Job failed. No error details available."
            )

        # Delete job from tracker
        if st.button("🗑️ Remove from list", key=f"del_{job_id}"):
            del st.session_state.jobs[job_id]
            st.rerun()
