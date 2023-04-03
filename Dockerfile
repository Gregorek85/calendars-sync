# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory to /app
WORKDIR /app

# Install cron and other required packages
RUN apt-get update && apt-get -y install cron

# Create a log file to save cron job logs
RUN touch /var/log/cron.log
# Copy the crontab file to the cron directory
COPY crontab /etc/cron.d/cron-job
# Give execution rights on the cron job
RUN chmod 0644 /etc/cron.d/cron-job
# Apply the cron job
RUN crontab /etc/cron.d/cron-job

# Copy the requirements.txt and install requirements.
COPY requirements.txt /app
RUN pip install --trusted-host pypi.python.org -r requirements.txt
# Copy the rest of the project files into the container at /app
COPY . /app

# Run cron service when the container launches
ENTRYPOINT ["sh", "-c", "cron -f"]
