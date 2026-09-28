import asyncio
from pathlib import Path
from typing import AsyncGenerator
import aiosqlite

from src.config import settings

_db_lock = asyncio.Lock()


from contextlib import asynccontextmanager


@asynccontextmanager
async def get_db_connection() -> AsyncGenerator[aiosqlite.Connection, None]:
    settings.setup_directories()
    async with aiosqlite.connect(str(settings.DATABASE_PATH)) as db:
        db.row_factory = aiosqlite.Row
        await db.execute("PRAGMA journal_mode = WAL;")
        await db.execute("PRAGMA foreign_keys = ON;")
        await db.execute("PRAGMA synchronous = NORMAL;")
        yield db


async def init_db() -> None:
    import sys

    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        schema_path = Path(sys._MEIPASS) / "src" / "db" / "schema.sql"
    else:
        schema_path = Path(__file__).parent / "schema.sql"

    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found at {schema_path}")

    schema_sql = schema_path.read_text(encoding="utf-8")

    async with _db_lock:
        async with aiosqlite.connect(str(settings.DATABASE_PATH)) as db:
            await db.execute("PRAGMA foreign_keys = ON;")
            await db.executescript(schema_sql)
            await db.commit()

            # Dynamic migrations for new image columns
            cursor_chars = await db.execute("PRAGMA table_info(characters)")
            char_cols = [r[1] for r in await cursor_chars.fetchall()]
            if "visual_tags" not in char_cols:
                await db.execute("ALTER TABLE characters ADD COLUMN visual_tags TEXT NOT NULL DEFAULT ''")
            if "negative_prompt" not in char_cols:
                await db.execute("ALTER TABLE characters ADD COLUMN negative_prompt TEXT NOT NULL DEFAULT ''")

            cursor_msgs = await db.execute("PRAGMA table_info(messages)")
            msg_cols = [r[1] for r in await cursor_msgs.fetchall()]
            if "image_url" not in msg_cols:
                await db.execute("ALTER TABLE messages ADD COLUMN image_url TEXT NOT NULL DEFAULT ''")

            await db.commit()

            # Ensure a default user persona exists
            cursor = await db.execute("SELECT id FROM user_personas WHERE is_active = 1 LIMIT 1")
            row = await cursor.fetchone()
            if not row:
                cursor_any = await db.execute("SELECT id FROM user_personas LIMIT 1")
                any_row = await cursor_any.fetchone()
                if not any_row:
                    await db.execute(
                        """
                        INSERT INTO user_personas (id, name, pronouns, description, traits, is_active)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (
                            "default_user",
                            "User",
                            "they/them",
                            "A charismatic and curious companion.",
                            "attentive, playful, adventurous",
                            1,
                        ),
                    )
                    await db.commit()
                else:
                    await db.execute(
                        "UPDATE user_personas SET is_active = 1 WHERE id = ?",
                        (any_row[0],),
                    )
                    await db.commit()
