ALTER TABLE users
ADD COLUMN IF NOT EXISTS clerk_user_id TEXT;

CREATE UNIQUE INDEX IF NOT EXISTS ux_users_clerk_user_id
ON users (clerk_user_id)
WHERE clerk_user_id IS NOT NULL;
