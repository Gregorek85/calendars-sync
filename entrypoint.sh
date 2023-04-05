#!/bin/sh

# Ensure the cron service is running
service cron start

#run job now
python /app/main.py

# Keep the container running
tail -f /var/log/cron.log