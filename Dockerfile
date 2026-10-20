FROM node:22-slim AS node-deps
WORKDIR /app
COPY package.json package-lock.json ./
COPY node_modules ./node_modules

FROM python:3.12-slim
WORKDIR /app
COPY --from=node-deps /usr/local/bin/node /usr/local/bin/node
COPY --from=node-deps /app/node_modules ./node_modules
COPY backend ./backend
COPY frontend ./frontend
COPY scripts ./scripts
COPY engine ./engine
COPY fixtures ./fixtures
ENV PYTHONUNBUFFERED=1 PYTHONPATH=/app/backend ZIWEI_DB=/app/data/ziwei.sqlite3
RUN mkdir -p /app/data
EXPOSE 8000
CMD ["python", "backend/app.py"]
