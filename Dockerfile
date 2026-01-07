FROM python:3.11-alpine

RUN apk add --no-cache \
    sqlite \
    curl \
    && rm -rf /var/cache/apk/*

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY *.py ./

ENV DATA_DIR=/data
ENV LOGS_DIR=/logs

VOLUME /data

EXPOSE 8765

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8765/about || exit 1

CMD ["python", "renshuu_connect.py"]

