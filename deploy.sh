#!/bin/bash
set -e

REMOTE_PATH=""
SSH_HOST=""
UPDATE_DB=false

# Argument parsing
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --update-db) UPDATE_DB=true ;;
        *)
            if [ -z "$REMOTE_PATH" ]; then REMOTE_PATH="$1";
            elif [ -z "$SSH_HOST" ]; then SSH_HOST="$1";
            fi
            ;;
    esac
    shift
done

if [ -z "$REMOTE_PATH" ] || [ -z "$SSH_HOST" ]; then
    echo "Usage: $0 [--update-db] <REMOTE_PATH> <SSH_HOST>"
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
    ssh $SSH_HOST "cd $REMOTE_PATH &&
    psql -h localhost -U postgres -d odm -c 'CREATE TABLE IF NOT EXISTS applied_patches (patch_name TEXT PRIMARY KEY, applied_at TIMESTAMPTZ DEFAULT NOW());' > /dev/null
    for f in db/patchs/*.sql; do
        patch_name=\$(basename \$f)
        is_applied=\$(psql -h localhost -U postgres -d odm -tAc \"SELECT 1 FROM applied_patches WHERE patch_name='\$patch_name'\")

        if [ \"\$is_applied\" != \"1\" ]; then
            echo \"  🚀 Applying \$patch_name...\"
            psql -h localhost -U postgres -d odm -f \$f && \
            psql -h localhost -U postgres -d odm -c \"INSERT INTO applied_patches (patch_name) VALUES ('\$patch_name')\"
        else
            echo \"  ✅ \$patch_name already applied.\"
        fi
    done"
else
    echo "⏭️ Skipping database migrations (use --update-db to enable)."
fi

# 5. Restart Service
echo "🔄 Restarting API service..."
ssh $SSH_HOST "systemctl --user restart odm-api"

echo "✅ Deployment successful!"
