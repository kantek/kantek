DO
$$
    BEGIN
        IF NOT EXISTS(SELECT 1 FROM pg_type WHERE typname = 'character_class') THEN
            CREATE TYPE character_class AS ENUM ('emoji');
        END IF;
        IF NOT EXISTS(SELECT 1 FROM pg_type WHERE typname = 'action') THEN
            CREATE TYPE action AS ENUM ('delete', 'kick', 'ban');
        END IF;
    END
$$;


CREATE TABLE IF NOT EXISTS bundesnachrichtendienst
(
    id              SERIAL NOT NULL PRIMARY KEY,
    chat_id            BIGINT REFERENCES chats (id),
    action          action NOT NULL,
    pattern         TEXT,
    character_class character_class
)
