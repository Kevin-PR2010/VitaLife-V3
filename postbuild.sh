#!/bin/bash
# Retry model download with exponential backoff
max_retries=5
retry_delay=5

for i in $(seq 1 $max_retries); do
    echo "Attempt $i/$max_retries: Downloading spaCy model..."
    python -m spacy download en_core_web_sm && break || sleep $retry_delay
    retry_delay=$((retry_delay * 2))
done
