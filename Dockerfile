FROM python:3.12-slim
WORKDIR /app
COPY backend ./backend
COPY frontend ./frontend
COPY scripts ./scripts
COPY engine ./engine
COPY package.json package-lock.json ./
RUN npm ci --ignore-scripts
COPY fixtures ./fixtures
ENV PYTHONUNBUFFERED=1 PYTHONPATH=/app/backend ZIWEI_DB=/app/data/ziwei.sqlite3
RUN mkdir -p /app/data
EXPOSE 8000
CMD ["python", "backend/app.py"]
