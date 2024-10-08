FROM nvidia/opengl:1.2-glvnd-runtime-ubuntu22.04

# Switch to root user for installations
USER root

# Set the working directory in the container
WORKDIR /app

# Install system dependencies and build dependencies
RUN apt-get update && apt-get install -y \
    python3 python3-pip python-is-python3 \
    tar gzip xz-utils wget\
    libgl1-mesa-glx libglib2.0-0 \
    libsm6 libxext6 libxrender-dev \
    gcc g++ mesa-utils xvfb \
    libegl1-mesa libegl1-mesa-dev libgles2-mesa-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Clone your Git repository and copy necessary files to /app
COPY ./main.py /app/main.py
COPY ./symlink_patch.py /app/symlink_patch.py
COPY ./requirements.txt /app/requirements.txt

# Create site-packages directory
RUN mkdir -p /app/site-packages

# Install Python dependencies in /app
RUN pip install --upgrade pip && \
    pip install \
    --target=/app/site-packages \
    --upgrade \
    -r /app/requirements.txt && \
    pip install \
    --upgrade \
    torch==2.4.1  \
    --index-url https://download.pytorch.org/whl/cu121 && \
    pip install fastapi uvicorn

# Download and install FFmpeg in /app
RUN wget https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linux64-gpl.tar.xz && \
    tar xJf ffmpeg-master-latest-linux64-gpl.tar.xz && \
    mv ffmpeg-master-latest-linux64-gpl/bin/ffmpeg /app/ffmpeg && \
    mv ffmpeg-master-latest-linux64-gpl/bin/ffprobe /app/ffprobe && \
    rm -rf ffmpeg-master-latest-linux64-gpl*

# Copy contents of /usr to /app/usr
RUN mkdir -p /app/usr/lib64 && \
    cp -r /usr/lib64/* /app/usr/lib64/

# Remove unnecessary files
RUN find /app -type d -name '__pycache__' -exec rm -rf {} + && \
    find /app -type f -name '*.pyc' -delete && \
    find /app -type f -name '*.pyo' -delete && \
    find /app -type d -name 'tests' -exec rm -rf {} +

# Copy the FastAPI app
COPY main.py /app/main.py

ENV NVIDIA_DRIVER_CAPABILITIES="all" \
    NVIDIA_VISIBLE_DEVICES="all" \
    WINDOW_BACKEND="headless" \
    WORKSPACE='/tmp' \
    HOST=0.0.0.0 \
    PATH="/app:/app/site-packages:/usr/local/bin:${PATH}" \
    PYTHONPATH="/app/site-packages" \
    LD_LIBRARY_PATH="/usr/lib/x86_64-linux-gnu"

# Expose port 8080
EXPOSE 8080

# Set the entrypoint to run the FastAPI app
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080", "--reload"]