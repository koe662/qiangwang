FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN chmod +x /app/entrypoint.sh

ENV HOST=0.0.0.0
ENV PORT=5000
ENV FLAG_PATH=/var/ctf/flag.txt

CMD ["/app/entrypoint.sh"]
