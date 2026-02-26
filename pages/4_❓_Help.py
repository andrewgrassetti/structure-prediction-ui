"""
Help & Setup Guide page.
"""
import streamlit as st

st.set_page_config(
    page_title="Help — Boltz-2 UI",
    page_icon="❓",
    layout="wide",
)

st.title("❓ Help & Setup Guide")

# ---------------------------------------------------------------------------
tabs = st.tabs(
    [
        "🚀 RunPod Setup",
        "📄 FASTA Format",
        "🧬 Boltz-2 YAML Format",
        "⚙️ Parameters",
        "📊 Understanding Results",
        "💰 Budget Guide",
        "🔧 Troubleshooting",
    ]
)

# ============================================================
# Tab 1: RunPod Setup
# ============================================================
with tabs[0]:
    st.header("Setting Up RunPod Serverless")
    st.markdown(
        """
        ### Step 1 — Create a RunPod account
        1. Go to [runpod.io](https://www.runpod.io/) and sign up.
        2. Verify your email address.

        ### Step 2 — Add funds
        1. Navigate to **Billing** → **Add Credits**.
        2. Add $10–30 to get started. Credits roll over.

        ### Step 3 — Create a Serverless Endpoint
        1. In the RunPod dashboard, go to **Serverless** → **+ New Endpoint**.
        2. Under **Worker Image**, enter the Docker image you built from the
           `worker/Dockerfile` in this repo (e.g. `yourname/boltz2-worker:latest`).
        3. Set **GPU** to *RTX 3090* or *A5000* (24 GB VRAM minimum).
        4. Set **Min Replicas** to `0` (scale to zero when idle to avoid charges).
        5. Set **Max Replicas** to `1` (or more for parallelism).
        6. Click **Deploy**.

        ### Step 4 — Get your API key
        1. Go to **Settings** → **API Keys** → **+ API Key**.
        2. Copy the key and paste it into the sidebar of the **🔬 Predict** page.

        ### Step 5 — Get your Endpoint ID
        1. In **Serverless** → your endpoint, copy the **Endpoint ID** (looks like
           `abc123def456`).
        2. Paste it into the sidebar of the **🔬 Predict** page.

        ### Step 6 — Build and push the Docker worker image
        ```bash
        cd worker/
        docker build -t yourname/boltz2-worker:latest .
        docker push yourname/boltz2-worker:latest
        ```
        Then use `yourname/boltz2-worker:latest` as the worker image in Step 3.
        """
    )

# ============================================================
# Tab 2: FASTA Format
# ============================================================
with tabs[1]:
    st.header("FASTA Input Format")
    st.markdown(
        """
        The app accepts standard FASTA files. Supported header formats:

        #### Extended Boltz format: `>CHAIN_ID|ENTITY_TYPE`
        ```
        >A|protein
        MVTPEGNVSLVDESLLVGVSLEAPLGSTEVNQQIAAFIESRKQFEQLH...
        >B|protein
        EFKEAFSLFDKDGDGTITTKELGTVMRSLGQNPTEAELQDMINEVDAD...
        >C|dna
        ATCGATCGATCG
        >D|rna
        AUGCAUGCAUGC
        ```

        #### With MSA path: `>CHAIN_ID|ENTITY_TYPE|MSA_PATH`
        ```
        >A|protein|/path/to/msa.a3m
        MVTPEGNVSLV...
        ```

        #### Simple format: `>sequence_name` (defaults to protein)
        ```
        >my_protein
        MVTPEGNVSLV...
        ```

        #### Valid entity types
        | Type | Description |
        |------|-------------|
        | `protein` | Amino-acid sequence (default) |
        | `dna` | DNA nucleotide sequence |
        | `rna` | RNA nucleotide sequence |

        > **Note:** Ligands cannot be represented in FASTA format; use the
        > ligand input section on the Predict page instead.
        """
    )

    st.subheader("Example: Single protein")
    st.code(
        """>A|protein
MVTPEGNVSLVDESLLVGVSLEAPLGSTEVNQQIAAFIESRKQFEQLHRDSGQVLLRGNP
QLQHLQDVRNHPDLILDEKEKAHIPNWVDREAGMLFQHAQHVKDQFEYLRNTKKYLEET
""",
        language="text",
    )

    st.subheader("Example: Protein–protein complex")
    st.code(
        """>A|protein
MVTPEGNVSLVDESLLVGVSLEAPLGSTEVNQQIAAFIESRKQFEQLH
>B|protein
EFKEAFSLFDKDGDGTITTKELGTVMRSLGQNPTEAELQDMINEVDAD
""",
        language="text",
    )

# ============================================================
# Tab 3: Boltz-2 YAML Format
# ============================================================
with tabs[2]:
    st.header("Boltz-2 YAML Input Format")
    st.markdown(
        """
        Boltz-2 prefers YAML input. The app converts your FASTA automatically, but you
        can also inspect the generated YAML on the Predict page.

        ```yaml
        version: 1
        sequences:
          - protein:
              id: A
              sequence: MVTPEGNVSLV...
          - protein:
              id: B
              sequence: EFKEAFSLF...
          - ligand:
              id: C
              ccd: SAH         # CCD code (3-letter PDB ligand code)
          - ligand:
              id: D
              smiles: 'CC1=CC=CC=C1'   # SMILES string
          - dna:
              id: E
              sequence: ATCGATCG
          - rna:
              id: F
              sequence: AUGCAUGC
        ```

        #### With pre-computed MSA
        ```yaml
        - protein:
            id: A
            sequence: MVTPEGNVSLV...
            msa: /path/to/alignment.a3m
        ```

        Reference: [jwohlwend/boltz docs/prediction.md](https://github.com/jwohlwend/boltz/blob/main/docs/prediction.md)
        """
    )

# ============================================================
# Tab 4: Parameters
# ============================================================
with tabs[3]:
    st.header("Prediction Parameters")
    params_data = {
        "Parameter": [
            "Model version",
            "Recycling steps",
            "Sampling steps",
            "Diffusion samples",
            "Max parallel samples",
            "Step scale",
            "Output format",
            "Use MSA server",
            "MSA server URL",
            "Use potentials",
            "Override existing",
            "Disable kernels",
        ],
        "Default": [
            "boltz2",
            "3",
            "200",
            "1",
            "5",
            "1.5 (boltz2) / 1.638 (boltz1)",
            "mmcif",
            "True",
            "https://api.colabfold.com",
            "False",
            "False",
            "False",
        ],
        "Description": [
            "Model version: boltz2 (recommended) or boltz1.",
            "Number of trunk recycling iterations. More = better (slower).",
            "Number of diffusion sampling steps (50–500).",
            "Number of structure samples to generate per prediction.",
            "Max samples processed simultaneously (trade-off: memory vs. speed).",
            "Diffusion step scale. Lower values produce more diverse structures.",
            "Output file format: mmCIF (recommended) or PDB.",
            "Automatically generate MSAs via ColabFold server.",
            "URL of the ColabFold MSA server.",
            "Enable auxiliary statistical potentials.",
            "Overwrite existing output files.",
            "Disable cuEquivariance kernels. Use for GPUs with compute capability < 8.0.",
        ],
    }
    import pandas as pd
    st.dataframe(pd.DataFrame(params_data), use_container_width=True, hide_index=True)

# ============================================================
# Tab 5: Understanding Results
# ============================================================
with tabs[4]:
    st.header("Understanding Confidence Metrics")
    st.markdown(
        """
        Boltz-2 outputs several confidence scores:

        | Metric | Range | Meaning |
        |--------|-------|---------|
        | `confidence_score` | 0–1 | Overall quality score: `(4 × complex_pLDDT + iPTM) / 5` |
        | `ptm` | 0–1 | Predicted TM-score for the complex |
        | `iptm` | 0–1 | Interface PTM — confidence at chain interfaces |
        | `ligand_iptm` | 0–1 | Interface PTM for protein–ligand contacts |
        | `protein_iptm` | 0–1 | Interface PTM for protein–protein contacts |
        | `complex_plddt` | 0–100 | Per-residue confidence averaged across the complex |
        | `complex_iplddt` | 0–100 | pLDDT at interface residues |
        | `complex_pde` | Å | Predicted distance error for the complex |
        | `complex_ipde` | Å | Predicted distance error at interfaces |

        #### pLDDT colour scale (3D viewer)
        | Colour | Range | Interpretation |
        |--------|-------|----------------|
        | 🔵 Blue | 90–100 | Very high confidence |
        | 🟢 Cyan | 70–89 | Confident |
        | 🟡 Yellow | 50–69 | Low confidence |
        | 🔴 Red | 0–49 | Very low confidence |

        #### Affinity output
        If the input YAML includes `properties: affinity`, Boltz-2 predicts binding affinity
        as a Gibbs free energy (ΔG, kcal/mol) and returns it in `affinity_*.json`.
        """
    )

# ============================================================
# Tab 6: Budget Guide
# ============================================================
with tabs[5]:
    st.header("Budget Estimation Guide")
    st.markdown(
        """
        ### RunPod Serverless Pricing
        RunPod charges **per second** of GPU time, only while a job is running.

        | GPU | VRAM | Approx. cost/hr |
        |-----|------|----------------|
        | RTX 3090 | 24 GB | ~$0.94/hr (~$0.00026/sec) |
        | A5000 | 24 GB | ~$1.08/hr (~$0.00030/sec) |
        | A100 80GB | 80 GB | ~$2.89/hr (~$0.00080/sec) |

        ### Typical Boltz-2 run times
        | Input size | Est. time | Est. cost (RTX 3090) |
        |------------|-----------|----------------------|
        | Single protein (~200 aa) | 2–3 min | $0.03–$0.05 |
        | Protein complex (~500 aa total) | 4–6 min | $0.06–$0.09 |
        | Large complex (~1000 aa total) | 8–15 min | $0.12–$0.24 |

        ### Budget examples
        | Monthly budget | Est. predictions (300 aa avg) |
        |----------------|-------------------------------|
        | $10 | ~150–300 |
        | $30 | ~450–900 |

        > **Tip:** Use `diffusion_samples=1` (default) to minimize cost. Increase only
        > when you need multiple structure candidates.
        """
    )

# ============================================================
# Tab 7: Troubleshooting
# ============================================================
with tabs[6]:
    st.header("Troubleshooting")
    st.markdown(
        """
        #### Job stuck in "Queued" state
        - RunPod needs to spin up a cold worker. This can take 1–3 minutes.
        - Check your RunPod dashboard for any error messages.
        - Ensure your endpoint has sufficient credit.

        #### Job fails immediately
        - Verify the Docker image is accessible and runs correctly.
        - Check RunPod worker logs in the dashboard.
        - Try running `boltz predict` locally to reproduce the error.

        #### GPU out-of-memory errors
        - Reduce `diffusion_samples` or `max_parallel_samples`.
        - Switch to a larger GPU (A100 80GB).
        - For very large complexes (>1000 residues), consider enabling `--no_kernels`.

        #### "Invalid API key" error
        - Re-generate your API key in the RunPod dashboard.
        - Make sure you copied the full key without trailing spaces.

        #### py3Dmol not showing structures
        - Ensure `py3Dmol` and `stmol` are installed: `pip install py3Dmol stmol`.
        - Some browsers may block the WebGL viewer — try Chrome or Firefox.

        #### ColabFold MSA server errors
        - The free ColabFold server has rate limits. Wait a few minutes and retry.
        - For production use, consider self-hosting ColabFold.

        #### Links
        - [Boltz-2 GitHub Issues](https://github.com/jwohlwend/boltz/issues)
        - [RunPod Documentation](https://docs.runpod.io/)
        - [ColabFold](https://github.com/sokrypton/ColabFold)
        """
    )
