# Frontend Dockerfile
FROM node:20-alpine

WORKDIR /app

# Install dependencies (using legacy-peer-deps for Svelte Flow compatibility)
COPY package*.json ./
RUN npm install --legacy-peer-deps

# Copy application code
COPY . .

# Expose port
EXPOSE 5173

# Default command (overridden in docker-compose)
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
