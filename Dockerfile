# Use an official, lightweight Python image
FROM python:3.11-slim

# Set the working directory inside the Google server
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your entire backend folder into the server
COPY . .

# Expose port 8080 (Google's default port)
EXPOSE 8080

# Command to wake up the server when traffic hits
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8080"]
