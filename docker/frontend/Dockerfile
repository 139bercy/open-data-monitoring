### Dockerfile Frontend (multi-stage)
# Étape 1 : Construction de l'application Vite
FROM node:18-alpine AS builder

WORKDIR /app
COPY front/package.json front/package-lock.json* ./
RUN npm install --no-audit --no-fund
COPY front/ ./
RUN npm run build

# Étape 2 : Image finale avec Node pour servir l'application
FROM node:18-alpine

WORKDIR /app/server
COPY front/server/ ./
RUN npm install --production --no-audit --no-fund

WORKDIR /app
COPY --from=builder /app/dist ./dist

ENV PORT=3401
EXPOSE 3401

WORKDIR /app/server
CMD ["node", "index.mjs"]
