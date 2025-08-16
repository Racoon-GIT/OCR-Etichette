FROM python:3.11-slim

# System deps for Tesseract, ZBar (barcodes) and OpenCV runtime
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr libtesseract-dev \
    libzbar0 \
    libgl1 libglib2.0-0 \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Expose port for Render
ENV PORT=10000
EXPOSE 10000

# Start the web service (Flask via Gunicorn)
CMD ["gunicorn", "-b", "0.0.0.0:10000", "app:app"]
