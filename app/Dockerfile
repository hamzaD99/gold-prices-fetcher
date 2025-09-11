FROM python:latest

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN playwright install-deps
RUN playwright install

COPY . .

CMD ["celery", "-A", "tasks", "worker", "--loglevel=info"]
