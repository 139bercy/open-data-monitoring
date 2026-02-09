ALTER TABLE platforms ADD COLUMN IF NOT EXISTS last_sync_status varchar(50) CHECK ( last_sync_status IN ('pending', 'success', 'failed')) DEFAULT 'pending';
ALTER TABLE datasets ADD COLUMN IF NOT EXISTS last_sync_status varchar(50) CHECK ( last_sync_status IN ('pending', 'success', 'failed')) DEFAULT 'pending';
