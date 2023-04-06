# Use an official Python runtime as a parent image
FROM python:3.11

# Set environment variables
ENV TZ=Europe/Warsaw

# Install required packages
RUN apt-get update && apt-get install -y \
    cron \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

# Set the timezone
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Create a log file to save cron job logs
RUN touch /var/log/cron.log

# Copy the crontab file to the cron directory
COPY crontab /etc/cron.d/cron-job
# Give execution rights on the cron job
RUN chmod 0644 /etc/cron.d/cron-job
# Apply the cron job
RUN crontab /etc/cron.d/cron-job

# Set the working directory to /app
WORKDIR /app

# Copy the requirements.txt and install requirements.
COPY requirements.txt /app
RUN pip install --trusted-host pypi.python.org -r requirements.txt
# Copy the rest of the project files into the container at /app
COPY . /app

# Convert line endings from CRLF to LF
RUN sed -i 's/\r$//' /app/calendar_sync/credentials/outlook_token.txt
RUN sed -i 's/\r$//' /app/calendar_sync/credentials/google_token.json
# Give execution rights on the entrypoint.sh script
RUN chmod +x /app/entrypoint.sh

# Use the entrypoint.sh script as the entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]
