# 🧬 Boltz-2 Structure Prediction UI

A comprehensive Streamlit web interface for running
[Boltz-2](https://github.com/jwohlwend/boltz) biomolecular structure predictions
on [RunPod](https://runpod.io) serverless GPU infrastructure — no local GPU required.

> **Screenshot placeholder** — add a screenshot of the app here after deployment.

---

## Architecture

```
Streamlit App (local or Streamlit Cloud)
    ├── Sidebar: RunPod API key login (stored in st.session_state only)
    ├── Page 1: 🏠 Home / Dashboard
    ├── Page 2: 🔬 Structure Prediction
    ├── Page 3: 📊 Results Viewer
    └── Page 4: ❓ Help & Setup Guide
            │
            ▼  (REST API calls)
    RunPod Serverless Endpoint
    ├── Custom Docker image with boltz[cuda] installed
    ├── GPU: RTX 3090 / A5000 (24 GB VRAM)
    └── Runs `boltz predict` on uploaded inputs, returns results
```

---

## Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/andrewgrassetti/structure-prediction-ui.git
cd structure-prediction-ui

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Run the Streamlit app
streamlit run app.py
```

Open `http://localhost:8501` in your browser.

---

## Cloud GPU Setup Guide (RunPod)

### 1. Create a RunPod account
Sign up at [runpod.io](https://www.runpod.io/) and verify your email.

### 2. Add funds
Go to **Billing** → **Add Credits**. Add $10–30 to get started (credits roll over).

### 3. Build and push the worker Docker image

```bash
cd worker/
docker build -t <yourname>/boltz2-worker:latest .
docker push <yourname>/boltz2-worker:latest
```

### 4. Create a Serverless Endpoint
1. **Serverless** → **+ New Endpoint**
2. Worker Image: `<yourname>/boltz2-worker:latest`
3. GPU: RTX 3090 or A5000 (24 GB VRAM minimum)
4. Min Replicas: `0` (scale-to-zero — avoids idle charges)
5. Max Replicas: `1` (or more for parallelism)
6. Click **Deploy** and copy the **Endpoint ID**

### 5. Get your API key
**Settings** → **API Keys** → **+ API Key** → copy the key.

### 6. Enter credentials in the app
On the **🔬 Predict** page sidebar, enter your API key and endpoint ID.
They are stored only in `st.session_state` — never written to disk.

---

## FASTA Input Guide

### Extended Boltz format (recommended)
```
>A|protein
MVTPEGNVSLV...
>B|protein
EFKEAFSLF...
>C|dna
ATCGATCG
```

### Simple format (defaults to protein)
```
>my_protein
MVTPEGNVSLV...
```

### Header format
`>CHAIN_ID|ENTITY_TYPE` or `>CHAIN_ID|ENTITY_TYPE|MSA_PATH`

Valid entity types: `protein`, `dna`, `rna`

See `examples/` for sample files.

---

## Boltz-2 Parameter Reference

| Parameter | Default | Range | Description |
|-----------|---------|-------|-------------|
| Model | `boltz2` | boltz2 / boltz1 | Model version |
| Recycling steps | `3` | 1–10 | Trunk recycling iterations |
| Sampling steps | `200` | 50–500 | Diffusion sampling steps |
| Diffusion samples | `1` | 1–10 | Structure samples per run |
| Max parallel samples | `5` | 1–20 | Parallelism (memory vs. speed) |
| Step scale | `1.5` | 1.0–2.0 | Diffusion step scale |
| Output format | `mmcif` | mmcif / pdb | Output file format |
| Use MSA server | `True` | — | Auto-generate MSAs via ColabFold |
| Use potentials | `False` | — | Enable auxiliary potentials |

---

## Output Interpretation Guide

| Metric | Range | Description |
|--------|-------|-------------|
| `confidence_score` | 0–1 | Overall quality: `(4×pLDDT + iPTM) / 5` |
| `ptm` | 0–1 | Predicted TM-score |
| `iptm` | 0–1 | Interface PTM — confidence at chain interfaces |
| `complex_plddt` | 0–100 | Average per-residue confidence |
| `complex_pde` | Å | Predicted distance error |

### pLDDT colour scale
- 🔵 **90–100**: Very high confidence
- 🟢 **70–89**: Confident
- 🟡 **50–69**: Low confidence
- 🔴 **0–49**: Very low confidence

---

## Budget Guide

RunPod charges per second of GPU time (scale-to-zero = no idle charges).

| GPU | ~Cost/hr | Typical prediction (300 aa) | Cost/prediction |
|-----|----------|-----------------------------|----------------|
| RTX 3090 | $0.94 | 3–5 min | $0.05–$0.08 |
| A5000 | $1.08 | 3–5 min | $0.05–$0.09 |

**$30/month ≈ 300–600 predictions** at typical sequence lengths.

---

## Troubleshooting

- **Job stuck in "Queued"**: RunPod is spinning up a cold worker (1–3 min). Check your dashboard.
- **Job fails**: Check worker logs in RunPod dashboard. Try running `boltz predict` locally.
- **OOM errors**: Reduce `diffusion_samples` / `max_parallel_samples`, or use a larger GPU.
- **py3Dmol not showing**: Install with `pip install py3Dmol stmol` and use Chrome/Firefox.
- **ColabFold errors**: Server is rate-limited; wait a few minutes and retry.

---

## Project Structure

```
structure-prediction-ui/
├── app.py                      # Main Streamlit entry point
├── pages/
│   ├── 1_🏠_Home.py           # Home dashboard
│   ├── 2_🔬_Predict.py        # Prediction submission
│   ├── 3_📊_Results.py        # Results viewer
│   └── 4_❓_Help.py           # Help & setup guide
├── utils/
│   ├── __init__.py
│   ├── runpod_client.py        # RunPod REST API client
│   ├── fasta_parser.py         # FASTA parsing & validation
│   ├── yaml_builder.py         # Boltz-2 YAML builder
│   └── visualization.py        # py3Dmol 3D viewer helpers
├── worker/
│   ├── handler.py              # RunPod serverless handler
│   ├── Dockerfile              # Worker Docker image
│   └── README.md               # Worker build & deploy guide
├── examples/
│   ├── example_single.fasta    # Single protein example
│   ├── example_multi.fasta     # Multi-chain example
│   └── example_complex.yaml    # Full Boltz-2 YAML example
├── requirements.txt
└── .streamlit/config.toml      # Streamlit theme
```

---

## Links

- 📄 [Boltz-2 GitHub](https://github.com/jwohlwend/boltz)
- 🖥️ [RunPod Serverless](https://www.runpod.io/serverless-gpu)
- 📚 [ColabFold](https://github.com/sokrypton/ColabFold)
