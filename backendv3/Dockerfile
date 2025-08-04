# Use the official Python 3.12 slim image as the base image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies (if any)
# RUN apt-get update && apt-get install -y build-essential

# Copy the requirements file into the container
COPY requirements.txt .

# Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code into the container
COPY app ./app
# COPY EmbeddingBaseDf_w_not_education.csv .\app\core\InjectionChatBot\initial_documents\EmbeddingBaseDf_w_not_education.csv
# COPY .env /app/.env


# Expose the port that the app runs on
EXPOSE 8000
# EXPOSE 8001

# Set environment variables (optional)
# ENV APP_ENV=production
ENV PYTHONUNBUFFERED=1


# Add HEALTHCHECK to monitor the health of the application
# HEALTHCHECK --interval=30s --timeout=10s --start-period=5s CMD curl -f http://localhost:8000/health || exit 1

# Command to run the application using Uvicorn with hot-reload and multiple workers
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--workers", "4"]
