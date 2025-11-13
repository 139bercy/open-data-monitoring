### Dockerfile Backend (multi-stage)
# Construction des wheels dans une étape de build pour accélérer l'installation et réduire la taille finale de l'image
FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /wheels

# Copier uniquement requirements.txt pour profiter du cache docker
COPY requirements.txt /wheels/requirements.txt

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential gcc libpq-dev \
    && pip install --upgrade pip wheel setuptools \
    && pip wheel --wheel-dir=/wheels -r /wheels/requirements.txt \
    && apt-get remove -y build-essential gcc \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Création d'un utilisateur non-root pour la sécurité
RUN addgroup --system app && adduser --system --ingroup app app

WORKDIR /app

# Copier les wheels construits et installer depuis ceux-ci
COPY --from=builder /wheels /wheels
COPY requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-index --find-links=/wheels -r /app/requirements.txt

# Copier le reste du projet
COPY . /app

# Installer le package en mode développement
RUN pip install -e .

# S'assurer des bonnes permissions
RUN chown -R app:app /app

USER app

ENV API_PORT=3402
EXPOSE 3402

# Démarrer directement l'API; on utilise une commande shell pour respecter API_PORT
CMD ["sh", "-c", "uvicorn interfaces.api.main:api_app --host 0.0.0.0 --port ${API_PORT:-3402}"]
