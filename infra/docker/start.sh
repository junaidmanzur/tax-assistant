#!/bin/bash

# Start FastAPI backend on port 8001
cd /app
uvicorn services.api_gateway.main:app --host 127.0.0.1 --port 8001 &

# Start nginx on port 8000 (serves frontend + proxies API)
nginx -g "daemon off;"