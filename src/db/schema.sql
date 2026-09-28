-- Production SQLite Schema for Naughty-AI-Assistant

CREATE TABLE IF NOT EXISTS characters (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    tagline TEXT NOT NULL DEFAULT '',
    avatar TEXT NOT NULL DEFAULT '',
    description TEXT NOT NULL DEFAULT '',
    personality TEXT NOT NULL DEFAULT '',
    scenario TEXT NOT NULL DEFAULT '',
    first_message TEXT NOT NULL DEFAULT '',
    example_dialogue TEXT NOT NULL DEFAULT '',
    system_prompt TEXT NOT NULL DEFAULT '',
    visual_tags TEXT NOT NULL DEFAULT '',
    negative_prompt TEXT NOT NULL DEFAULT '',
    is_builtin INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS user_personas (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    pronouns TEXT NOT NULL DEFAULT '',
    description TEXT NOT NULL DEFAULT '',
    traits TEXT NOT NULL DEFAULT '',
    is_active INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    character_id TEXT NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
    user_persona_id TEXT REFERENCES user_personas(id) ON DELETE SET NULL,
    title TEXT NOT NULL,
    memory_notes TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS messages (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK(role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    swipe_index INTEGER NOT NULL DEFAULT 0,
    alternatives TEXT NOT NULL DEFAULT '[]',
    image_url TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS memory_facts (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    user_persona_id TEXT REFERENCES user_personas(id) ON DELETE SET NULL,
    fact_text TEXT NOT NULL,
    category TEXT NOT NULL DEFAULT 'general',
    confidence REAL NOT NULL DEFAULT 1.0,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS app_settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_sessions_character ON sessions(character_id);
CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id, created_at ASC);
CREATE INDEX IF NOT EXISTS idx_memory_facts_session ON memory_facts(session_id);
CREATE INDEX IF NOT EXISTS idx_memory_facts_persona ON memory_facts(user_persona_id);
