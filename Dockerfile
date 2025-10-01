# Use Python 3.12 slim image as base
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    TZ=UTC

# Set work directory
WORKDIR /app

# Install system dependencies including cron
RUN apt-get update && apt-get install -y \
    gcc \
    cron \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the entire project
COPY . .

# Create output directory
RUN mkdir -p output

# Create log directory for cron
RUN mkdir -p /var/log

# Copy cron configuration
RUN echo "0 18 * * * root cd /app && scrapy crawl euraxess_scraper >> /var/log/cron.log 2>&1" > /etc/cron.d/euraxess-cron && \
    chmod 0644 /etc/cron.d/euraxess-cron && \
    crontab /etc/cron.d/euraxess-cron

# Expose Streamlit port
EXPOSE 8501

# Create a startup script to handle different services
RUN echo '#!/bin/bash\n\
if [ "$1" = "scrape" ]; then\n\
    exec scrapy crawl euraxess_scraper\n\
elif [ "$1" = "streamlit" ]; then\n\
    echo "Starting Streamlit application..."\n\
    echo "Access the app at: http://localhost:8501"\n\
    echo "Press Ctrl+C to stop the application"\n\
    exec streamlit run app.py --server.address=0.0.0.0 --server.port=8501\n\
elif [ "$1" = "scheduler" ]; then\n\
    echo "Starting cron scheduler..."\n\
    echo "Scraper will run daily at 18:00 UTC (6 PM World Time)"\n\
    echo "Current UTC time: $(date -u)"\n\
    touch /var/log/cron.log\n\
    service cron start\n\
    echo "Cron service started successfully"\n\
    echo "Monitoring cron logs..."\n\
    tail -f /var/log/cron.log &\n\
    while true; do sleep 30; done\n\
elif [ "$1" = "full" ]; then\n\
    echo "Starting integrated service (Scheduler + Streamlit)..."\n\
    echo "🕕 Scheduler: Daily at 18:00 UTC (6 PM World Time)"\n\
    echo "🌐 Streamlit: http://localhost:8501"\n\
    echo "Current UTC time: $(date -u)"\n\
    \n\
    # Start cron service\n\
    touch /var/log/cron.log\n\
    service cron start\n\
    echo "✅ Cron scheduler started"\n\
    \n\
    # Start streamlit in background\n\
    streamlit run app.py --server.address=0.0.0.0 --server.port=8501 &\n\
    STREAMLIT_PID=$!\n\
    echo "✅ Streamlit started (PID: $STREAMLIT_PID)"\n\
    \n\
    # Monitor both services\n\
    echo "📊 Both services are running. Access web app at http://localhost:8501"\n\
    echo "📝 Monitoring logs (Ctrl+C to stop all services):"\n\
    \n\
    # Function to cleanup on exit\n\
    cleanup() {\n\
        echo "Stopping services..."\n\
        kill $STREAMLIT_PID 2>/dev/null\n\
        service cron stop\n\
        exit 0\n\
    }\n\
    trap cleanup SIGTERM SIGINT\n\
    \n\
    # Keep container running and show logs\n\
    tail -f /var/log/cron.log &\n\
    wait $STREAMLIT_PID\n\
elif [ "$1" = "bash" ]; then\n\
    exec /bin/bash\n\
else\n\
    echo "Usage: docker run [OPTIONS] IMAGE [scrape|streamlit|scheduler|full|bash]"\n\
    echo "  scrape     - Run the Scrapy spider once"\n\
    echo "  streamlit  - Run only the Streamlit web application"\n\
    echo "  scheduler  - Run only the cron scheduler (daily at 18:00 UTC)"\n\
    echo "  full       - Run both scheduler and streamlit (recommended)"\n\
    echo "  bash       - Start an interactive bash shell"\n\
    echo ""\n\
    echo "Recommended: docker run -p 8501:8501 -v ./output:/app/output IMAGE full"\n\
    exit 1\n\
fi' > /app/entrypoint.sh && chmod +x /app/entrypoint.sh

# Set the entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]

# Default command - run both scheduler and streamlit
CMD ["full"]