# Boltz-2 RunPod Serverless Worker
#
# Base image: RunPod PyTorch with CUDA 11.8 (compatible with boltz[cuda])
FROM runpod/pytorch:2.1.0-py3.10-cuda11.8.0-devel-ubuntu22.04

# Prevent interactive prompts during apt installs
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip install --no-cache-dir --upgrade pip

# Install Boltz-2 with CUDA extras and the RunPod serverless SDK
RUN pip install --no-cache-dir \
    "boltz[cuda]" \
    runpod

# (Optional) Pre-download Boltz-2 model weights into the image to speed up
# cold starts. Comment out if you prefer to download on first run instead.
# Weights are cached at /root/.boltz by default (or $BOLTZ_CACHE).
# RUN python -c "from boltz.main import download_weights; download_weights()"

# Copy the handler script
WORKDIR /app
COPY handler.py /app/handler.py

# RunPod serverless entry point
CMD ["python", "-u", "/app/handler.py"]
