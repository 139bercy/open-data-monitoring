### Dockerfile Nginx (multi-stage)
# Build the frontend with Node and serve the produced `dist` with Nginx

FROM node:18-alpine AS builder

WORKDIR /app
COPY front/package.json front/package-lock.json* ./
# Use npm install to be tolerant when package-lock.json is missing in the repo
RUN npm install --no-audit --no-fund
COPY front/ ./
RUN npm run build

FROM nginx:1.25-alpine

# Copy built frontend
COPY --from=builder /app/dist /usr/share/nginx/html

# Use our custom nginx config
COPY deploy/nginx/nginx.conf /etc/nginx/nginx.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
