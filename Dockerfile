# Adobe Hackathon Challenge 1B - BERT Implementation
# Docker image for advanced BERT-based document ranking
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV TRANSFORMERS_CACHE=/app/.cache/transformers
ENV HF_HOME=/app/.cache/huggingface

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Download RoBERTa-Base model during build to avoid runtime download
RUN python -c "from transformers import RobertaTokenizer, RobertaModel; \
    tokenizer = RobertaTokenizer.from_pretrained('roberta-base'); \
    model = RobertaModel.from_pretrained('roberta-base'); \
    print('✅ RoBERTa-Base model cached successfully')"

# Copy application files
COPY utils/ ./utils/
COPY run_collection.py .
COPY README.md .

# Create necessary directories
RUN mkdir -p /app/collections /app/output

# Set permissions
RUN chmod +x run_collection.py

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import torch, transformers; print('✅ BERT system healthy')" || exit 1

# Default command - hackathon compliance
CMD ["python", "hackathon_main.py"]

# Labels for metadata
LABEL maintainer="Adobe Hackathon Team"
LABEL version="1.0"
LABEL description="BERT-based document ranking system for Challenge 1B"
LABEL constraint.compliance="<1GB model size"
LABEL model.type="RoBERTa-Base"
LABEL model.size="~500MB"
