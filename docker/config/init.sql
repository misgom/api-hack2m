CREATE TABLE users (
    uuid UUID DEFAULT gen_random_uuid(),
    name TEXT,
    email TEXT UNIQUE,
    session_id TEXT UNIQUE,
    password TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP,
    PRIMARY KEY (uuid)
);

CREATE TABLE challenges (
    uuid UUID DEFAULT gen_random_uuid(),
    key TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    system_prompt TEXT NOT NULL,
    flag TEXT NOT NULL,
    points INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP,
    PRIMARY KEY (uuid)
);

CREATE TABLE scores (
    uuid UUID DEFAULT gen_random_uuid(),
    user_id UUID,
    session_id TEXT,
    challenge_id UUID NOT NULL,
    score INT NOT NULL,
    is_final BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP,
    PRIMARY KEY (uuid),
    FOREIGN KEY (user_id) REFERENCES users(uuid) ON DELETE CASCADE,
    FOREIGN KEY (session_id) REFERENCES users(session_id) ON DELETE CASCADE,
    FOREIGN KEY (challenge_id) REFERENCES challenges(uuid) ON DELETE CASCADE
);

CREATE TABLE history (
    uuid UUID DEFAULT gen_random_uuid(),
    user_id UUID,
    session_id TEXT,
    challenge_id UUID NOT NULL,
    input TEXT NOT NULL,
    output TEXT NOT NULL,
    full_prompt TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP,
    PRIMARY KEY (uuid),
    FOREIGN KEY (user_id) REFERENCES users(uuid) ON DELETE CASCADE,
    FOREIGN KEY (session_id) REFERENCES users(session_id) ON DELETE CASCADE,
    FOREIGN KEY (challenge_id) REFERENCES challenges(uuid) ON DELETE CASCADE
)
