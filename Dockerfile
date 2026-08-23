# Use official Playwright image with all dependencies
FROM mcr.microsoft.com/playwright/python:v1.45.0-jammy

# Set working directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy bot code
COPY bot/ ./bot/

# Create directories for data and logs
RUN mkdir -p /app/data /app/logs

# Command to run the bot
CMD ["python", "-m", "bot.main"]