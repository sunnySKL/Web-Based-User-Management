-- Add uh_id column to users table if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'users' 
        AND column_name = 'uh_id'
    ) THEN
        ALTER TABLE users ADD COLUMN uh_id INTEGER;
        ALTER TABLE users ADD CONSTRAINT users_uh_id_key UNIQUE (uh_id);
    END IF;
END $$; 