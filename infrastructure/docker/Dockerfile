FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 DATA_DIR=/app/data
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && useradd --uid 10001 --create-home market
COPY --chown=market:market . .
RUN mkdir -p data && chown market:market data
USER market
EXPOSE 5050
CMD ["python", "app.py"]
