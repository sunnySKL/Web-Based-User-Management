-- Add current_approver column to academic_requests table if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'academic_requests' 
        AND column_name = 'current_approver'
    ) THEN
        ALTER TABLE academic_requests ADD COLUMN current_approver VARCHAR(50) DEFAULT 'department_counselor';
    END IF;
END $$; 