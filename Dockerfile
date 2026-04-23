FROM nvidia/cuda:12.1.0-cudnn8-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y \
    python3 python3-pip git wget curl ffmpeg \
    libgl1 libglib2.0-0 libsm6 libxrender1 libxext6 \
    && rm -rf /var/lib/apt/lists/*

# ComfyUI
WORKDIR /app
RUN git clone https://github.com/comfyanonymous/ComfyUI.git
WORKDIR /app/ComfyUI
RUN pip3 install -r requirements.txt

# LTX-2 ComfyUI Node
RUN git clone https://github.com/Lightricks/ComfyUI-LTXVideo.git \
    custom_nodes/ComfyUI-LTXVideo
RUN pip3 install -r custom_nodes/ComfyUI-LTXVideo/requirements.txt

# RunPod SDK
WORKDIR /app
COPY requirements.txt .
RUN pip3 install -r requirements.txt

COPY handler.py .
COPY start.sh .
COPY extra_model_paths.yaml .

RUN chmod +x start.sh

CMD ["python3", "handler.py"]
