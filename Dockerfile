# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container to the root directory
WORKDIR /

# Copy all the files from the current directory to the container
COPY . .

# Install the required dependencies from requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Expose port 5500 to allow access to the app
EXPOSE 5500

# Define environment variable to avoid Python buffering output
ENV PYTHONUNBUFFERED=1

# Command to run the Flask app
CMD ["python", "app.py"]
