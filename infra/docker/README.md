# Docker Infrastructure

This directory contains Docker configuration for running the tax-assistant application.

## Usage

From the root directory:

```bash
# Build and run all services
docker-compose -f infra/docker/docker-compose.yml up --build

# Run in detached mode
docker-compose -f infra/docker/docker-compose.yml up -d --build

# Stop services
docker-compose -f infra/docker/docker-compose.yml down
```

## Services

- **api-gateway**: FastAPI backend service (port 8000)
- **web**: React frontend service (port 5173)