FROM python:3.12

# Switch to root user for installations
USER root

# Set the working directory in the container
WORKDIR /app

# Install system dependencies and build dependencies
RUN apt-get update && apt-get install -y \
    tar gzip xz-utils\
    libgl1-mesa-glx libglib2.0-0 \
    libsm6 libxext6 libxrender-dev \
    gcc g++ && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Clone your Git repository and copy necessary files to /app
COPY ./main.py /app/main.py
COPY ./symlink_patch.py /app/symlink_patch.py
COPY ./requirements.txt /app/requirements.txt

# Create site-packages directory
RUN mkdir -p /app/site-packages

# Install Python dependencies in /app
RUN python -m pip install --upgrade pip && \
    python -m pip install \
    --no-cache-dir \
    --target=/app/site-packages \
    --upgrade \
    -r /app/requirements.txt

# Download and install FFmpeg in /app
RUN wget https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linux64-gpl.tar.xz && \
    tar xJf ffmpeg-master-latest-linux64-gpl.tar.xz && \
    mv ffmpeg-master-latest-linux64-gpl/bin/ffmpeg /app/ffmpeg && \
    mv ffmpeg-master-latest-linux64-gpl/bin/ffprobe /app/ffprobe && \
    rm -rf ffmpeg-master-latest-linux64-gpl*

# Ensure FFmpeg is in the PATH
ENV PATH="/app:/usr/local/bin:${PATH}"

# Copy contents of /usr to /app/usr
RUN mkdir -p /app/usr/lib64 && \
    cp -r /usr/lib64/* /app/usr/lib64/

# Remove unnecessary files
RUN find /app -type d -name '__pycache__' -exec rm -rf {} + && \
    find /app -type f -name '*.pyc' -delete && \
    find /app -type f -name '*.pyo' -delete && \
    find /app -type d -name 'tests' -exec rm -rf {} +

# Install FastAPI and Uvicorn
RUN pip install fastapi uvicorn

# Copy the FastAPI app
COPY main.py /app/main.py

# Expose port 8080
EXPOSE 8080

# Define an environment variable
# This variable will be used by Uvicorn as the binding address
ENV HOST 0.0.0.0

# Set the entrypoint to run the FastAPI app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080", "--reload"]