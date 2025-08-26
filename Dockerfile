# Use Python 3.10 as base image
FROM python:3.11-slim

# Add useful command line tools and gosu for step-down from root
RUN apt-get update && \
    apt-get install -y libxml2-dev libxslt1-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY server.py .
COPY config.py .

# Set environment variables
ENV HOST=0.0.0.0
ENV PORT=8000
# Default UID/GID (can be overridden at runtime)
ENV UID=1000
ENV GID=1000

# Expose port
EXPOSE 8000

# Set entrypoint
ENTRYPOINT ["python", "server.py"]
