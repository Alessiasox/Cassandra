# .devcontainer/Dockerfile
FROM python:3.10-slim

# For non-interactive apt installs
ENV DEBIAN_FRONTEND=noninteractive

# Install any system packages you might need (e.g. build-essential, git)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create a user (optional, but recommended for dev containers)
# RUN useradd -ms /bin/bash devuser
# USER devuser

WORKDIR /app

# Copy and install your Python dependencies
COPY requirements.txt /app
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your source code
COPY . /app

# By default, just drop into a shell.
CMD [ "bash" ]