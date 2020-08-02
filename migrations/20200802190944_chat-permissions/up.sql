ALTER TABLE chats ADD COLUMN permissions jsonb;
ALTER TABLE chats ADD COLUMN locked bool DEFAULT FALSE;
