#!/bin/bash
set -e

REMOTE_PATH=""
SSH_HOST=""
UPDATE_DB=false
UPDATE_VIEW=false

# Argument parsing
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --update-db) UPDATE_DB=true ;;
        --update-view) UPDATE_VIEW=true ;;
        -*) echo "Unknown option: $1"; exit 1 ;;
        *)
            if [ -z "$REMOTE_PATH" ]; then REMOTE_PATH="$1";
            elif [ -z "$SSH_HOST" ]; then SSH_HOST="$1";
            else echo "Too many arguments: $1"; exit 1;
            fi
            ;;
    esac
    shift
done

if [ -z "$REMOTE_PATH" ] || [ -z "$SSH_HOST" ]; then
    echo "Usage: $0 [--update-db] [--update-view] <REMOTE_PATH> <SSH_HOST>"
    echo "Example: $0 /home/paul/open-data-monitoring my-server"
    exit 1
fi

# Basic validation for SSH_HOST
if [[ "$SSH_HOST" == /* ]]; then
    echo "❌ Error: SSH_HOST ('$SSH_HOST') looks like a path. Check your arguments."
    echo "Usage: $0 [--update-db] [--update-view] <REMOTE_PATH> <SSH_HOST>"
    exit 1
fi

# Configuration
BACKUP_PATH="$REMOTE_PATH/backups"
LOCAL_FRONT_DIST="front/dist"

echo "🚀 Starting deployment to $SSH_HOST..."

# 0. Backup database (Optional)
if [ "$UPDATE_DB" = true ]; then
    echo "🗄️ Backing up database on server..."
    ssh $SSH_HOST "mkdir -p $BACKUP_PATH && pg_dump -h localhost -U postgres -d odm -Fc > $BACKUP_PATH/pre_deploy_\$(date +%Y%m%d_%H%M%S).dump"
else
    echo "⏭️ Skipping database backup (use --update-db to enable)."
fi

# 1. Update code
echo "📥 Updating code on server..."
ssh $SSH_HOST "cd $REMOTE_PATH && git pull"

# 1.5 Update backend dependencies
echo "📦 Updating backend dependencies..."
ssh $SSH_HOST "cd $REMOTE_PATH && ./venv/bin/pip install -r requirements.txt && ./venv/bin/pip install -e ."

# 2. Build Frontend locally
echo "🏗️ Building frontend locally..."
cd front
npm install
npm run build
cd ..

# 3. Send Frontend to server
echo "📤 Sending frontend to server..."
rsync -avz --delete $LOCAL_FRONT_DIST/ $SSH_HOST:$REMOTE_PATH/front/dist/

# 4. Run Migrations (Optional)
if [ "$UPDATE_DB" = true ]; then
    echo "🗄️ Running migrations..."
    ssh $SSH_HOST "cd $REMOTE_PATH && ./utils/migrate.sh"
else
    echo "⏭️ Skipping database migrations (use --update-db to enable)."
fi

# 4.5 Update Views (Optional)
if [ "$UPDATE_VIEW" = true ]; then
    echo "📊 Updating database views..."
    ssh $SSH_HOST "cd $REMOTE_PATH && psql -h localhost -U postgres -d odm -f db/views.sql"
else
    echo "⏭️ Skipping database views update (use --update-view to enable)."
fi

# 5. Restart Service
echo "🔄 Restarting API service..."
ssh $SSH_HOST "systemctl --user restart odm-api"

echo "✅ Deployment successful!"
