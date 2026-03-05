FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all frontend files to the container
COPY . .

# Expose the default gradio port
EXPOSE 7860

# Command to run the frontend app
CMD ["python", "app.py"]