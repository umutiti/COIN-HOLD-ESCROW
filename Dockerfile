# Use Python 3.10 slim (compatible wheels for aiohttp & frozenlist)
FROM python:3.10-slim

# Set work directory inside the container
WORKDIR /app

# Install system build dependencies (just in case some packages need them)
RUN apt-get update && apt-get install -y build-essential python3-dev && rm -rf /var/lib/apt/lists/*

# Copy only requirements first to install dependencies (better layer caching)
COPY requirements.txt .

# Upgrade pip and install project dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy all project files into the container
COPY . .

# Expose the port your bot might use (not strictly needed for Telegram, but good practice)
EXPOSE 8080

# Run your bot
CMD ["python", "bot.py"]
