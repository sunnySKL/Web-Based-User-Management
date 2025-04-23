-- Create approval_workflows table if it doesn't exist
CREATE TABLE IF NOT EXISTS approval_workflows (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create workflow_steps table if it doesn't exist
CREATE TABLE IF NOT EXISTS workflow_steps (
    id SERIAL PRIMARY KEY,
    workflow_id INTEGER NOT NULL REFERENCES approval_workflows(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL,
    step_order INTEGER NOT NULL,
    can_skip BOOLEAN DEFAULT FALSE,
    is_required BOOLEAN DEFAULT TRUE
);

-- Insert default workflow if it doesn't exist
INSERT INTO approval_workflows (name, description)
SELECT 'Default Approval Workflow', 'Standard three-step approval process'
WHERE NOT EXISTS (SELECT 1 FROM approval_workflows WHERE name = 'Default Approval Workflow');

-- Get the ID of the default workflow
DO $$
DECLARE
    default_workflow_id INTEGER;
BEGIN
    SELECT id INTO default_workflow_id FROM approval_workflows WHERE name = 'Default Approval Workflow';
    
    -- Insert default steps if they don't exist
    IF NOT EXISTS (SELECT 1 FROM workflow_steps WHERE workflow_id = default_workflow_id) THEN
        -- Department Counselor (step 1)
        INSERT INTO workflow_steps (workflow_id, role, step_order, can_skip, is_required)
        VALUES (default_workflow_id, 'Department Counselor', 1, TRUE, TRUE);
        
        -- Academic Director (step 2)
        INSERT INTO workflow_steps (workflow_id, role, step_order, can_skip, is_required)
        VALUES (default_workflow_id, 'Academic Director', 2, TRUE, TRUE);
        
        -- College Supervisor (step 3)
        INSERT INTO workflow_steps (workflow_id, role, step_order, can_skip, is_required)
        VALUES (default_workflow_id, 'College Supervisor', 3, FALSE, TRUE);
    END IF;
END $$; 