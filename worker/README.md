# Boltz-2 RunPod Serverless Worker

This directory contains the Docker worker image for running Boltz-2 predictions
on RunPod serverless GPU infrastructure.

## Contents

| File | Description |
|------|-------------|
| `handler.py` | RunPod serverless handler — receives jobs, runs `boltz predict`, returns results |
| `Dockerfile` | Docker image definition |

## Building and Pushing

```bash
# Build the image
docker build -t <your-dockerhub-username>/boltz2-worker:latest .

# Push to Docker Hub (or any container registry RunPod can access)
docker push <your-dockerhub-username>/boltz2-worker:latest
```

## RunPod Endpoint Setup

1. Log in to [RunPod](https://www.runpod.io/).
2. Go to **Serverless** → **+ New Endpoint**.
3. Set **Container Image** to `<your-dockerhub-username>/boltz2-worker:latest`.
4. Set **GPU** to *RTX 3090* or *A5000* (minimum 24 GB VRAM).
5. Set **Min Workers** to `0` (scale-to-zero to avoid idle charges).
6. Set **Max Workers** to `1` (increase for parallel jobs).
7. Click **Deploy** and copy the **Endpoint ID**.

## Handler Input Format

The handler expects an ``input`` payload with these fields (all optional except
``yaml_content``):

```json
{
  "yaml_content": "<Boltz-2 YAML string>",
  "job_name": "my_prediction",
  "model": "boltz2",
  "recycling_steps": 3,
  "sampling_steps": 200,
  "diffusion_samples": 1,
  "max_parallel_samples": 5,
  "step_scale": 1.5,
  "output_format": "mmcif",
  "use_msa_server": true,
  "msa_server_url": "https://api.colabfold.com",
  "use_potentials": false,
  "override": false,
  "no_kernels": false
}
```

## Handler Output Format

On **success**:
```json
{
  "structure_b64": "<base64-encoded CIF/PDB>",
  "structure_filename": "prediction_model_0.cif",
  "confidence_json_b64": "<base64-encoded confidence JSON>",
  "affinity_json_b64": "<base64-encoded affinity JSON (if applicable)>"
}
```

On **failure**:
```json
{
  "error": "Human-readable error message",
  "stderr": "Last 4000 chars of stderr",
  "stdout": "Last 4000 chars of stdout"
}
```

## Model Weights

Boltz-2 model weights are downloaded automatically on first run to `/root/.boltz`
(or the path set by the `BOLTZ_CACHE` environment variable).

To pre-bake weights into the image (faster cold starts, larger image size),
uncomment the `RUN python -c ...` line in the Dockerfile.

## Notes

- Minimum GPU VRAM: 24 GB (RTX 3090 / A5000).
- For older GPUs (compute capability < 8.0), set `no_kernels: true` in the input.
- The ColabFold MSA server is free but rate-limited; for high-throughput use,
  consider self-hosting ColabFold.
