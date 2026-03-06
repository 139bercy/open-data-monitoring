psql -h localhost -U postgres -d odm -c "CREATE TABLE IF NOT EXISTS applied_patches (patch_name TEXT PRIMARY KEY, applied_at TIMESTAMPTZ DEFAULT NOW());" > /dev/null
for f in db/patchs/*.sql; do
    patch_name=$(basename $f)
    is_applied=$(psql -h localhost -U postgres -d odm -tAc "SELECT 1 FROM applied_patches WHERE patch_name='$patch_name'")

    if [ "$is_applied" != "1" ]; then
        echo "  🚀 Applying $patch_name..."
        psql -h localhost -U postgres -d odm -f $f && \
        psql -h localhost -U postgres -d odm -c "INSERT INTO applied_patches (patch_name) VALUES ('$patch_name')"
    else
        echo "  ✅ $patch_name already applied."
    fi
done
