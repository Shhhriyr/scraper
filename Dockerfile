# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container at /app
COPY . .

# Create a volume for data persistence (optional but good practice)
VOLUME /app/data

# Define the command to run the scraper
# -u forces stdout and stderr to be unbuffered. This option has no effect on stdin.
ENTRYPOINT ["python", "-u", "scraper.py"]
CMD ["--help"]
