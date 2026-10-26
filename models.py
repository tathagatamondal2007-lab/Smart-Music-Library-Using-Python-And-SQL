import os
import sqlite3
import json
import base64
from datetime import datetime
from dataclasses import dataclass
import pygame

# Initialize pygame mixer for audio playback
try:
    pygame.mixer.init()
except Exception:
    pass


@dataclass
class Song:
    id: int
    title: str
    artist: str
    album: str
    duration: int
    genre: str
    file_path: str
    play_count: int = 0


def get_database_path():
    """Automatically finds a safe, persistent folder in Windows AppData to store the database."""
    app_data = os.getenv('APPDATA')
    if app_data:
        save_dir = os.path.join(app_data, 'SmartMusicLibrary')
        os.makedirs(save_dir, exist_ok=True)
        return os.path.join(save_dir, 'music_library.db')
    return 'music_library.db'


def get_license_file_path():
    """Finds or creates the local path for the offline license token file."""
    app_data = os.getenv('APPDATA')
    if app_data:
        save_dir = os.path.join(app_data, 'SmartMusicLibrary')
        os.makedirs(save_dir, exist_ok=True)
        return os.path.join(save_dir, 'license.key')
    return 'license.key'


def init_database():
    """Initializes all necessary SQLite database tables, including songs and subscriptions."""
    conn = sqlite3.connect(get_database_path())
    cursor = conn.cursor()

    # 1. Songs table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS songs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            artist TEXT NOT NULL,
            album TEXT,
            duration INTEGER,
            genre TEXT,
            file_path TEXT UNIQUE NOT NULL,
            play_count INTEGER DEFAULT 0
        )
    """)

    # 2. Subscriptions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            license_key TEXT UNIQUE,
            tier TEXT,
            expiry_date TEXT,
            is_active INTEGER
        )
    """)

    conn.commit()
    conn.close()


def generate_local_license(license_key: str, tier: str, expiry_date: str):
    """
    Generates and saves the local license.key file and updates
    the SQLite database with active subscription details automatically.
    """
    license_data = {
        "license_key": license_key,
        "tier": tier,
        "expiry_date": expiry_date,
        "is_active": 1
    }

    file_path = get_license_file_path()
    json_str = json.dumps(license_data)
    encoded_token = base64.b64encode(json_str.encode('utf-8')).decode('utf-8')

    with open(file_path, 'w') as f:
        f.write(encoded_token)

    conn = sqlite3.connect(get_database_path())
    cursor = conn.cursor()
    cursor.execute("DELETE FROM subscriptions;")
    cursor.execute("""
        INSERT INTO subscriptions (license_key, tier, expiry_date, is_active)
        VALUES (?, ?, ?, ?)
    """, (license_key, tier, expiry_date, 1))

    conn.commit()
    conn.close()

    print(f"Success! License file automatically created at: {file_path}")


def read_offline_license_file() -> dict | None:
    """Reads and decodes the local license.key file safely."""
    file_path = get_license_file_path()
    if not os.path.exists(file_path):
        return None

    try:
        with open(file_path, 'r') as f:
            encoded_token = f.read().strip()

        decoded_bytes = base64.b64decode(encoded_token.encode('utf-8'))
        return json.loads(decoded_bytes.decode('utf-8'))
    except Exception:
        return None


def validate_offline_subscription() -> bool:
    """
    Validates the offline subscription by cross-verifying the local license file
    and the SQLite database against the current local system date.
    """
    token_data = read_offline_license_file()
    if not token_data:
        return False

    expiry_str = token_data.get("expiry_date")
    is_active = token_data.get("is_active", 0)

    if not is_active or not expiry_str:
        return False

    try:
        conn = sqlite3.connect(get_database_path())
        cursor = conn.cursor()
        cursor.execute("SELECT expiry_date, is_active FROM subscriptions LIMIT 1;")
        row = cursor.fetchone()
        conn.close()

        if not row or row[1] == 0:
            return False

        db_expiry = row[0]
        if db_expiry != expiry_str:
            return False

    except Exception:
        return False

    try:
        expiry_date = datetime.strptime(expiry_str, "%Y-%m-%d")
        if datetime.now() <= expiry_date:
            return True
    except ValueError:
        return False

    return False


class DatabaseManager:
    """Handles all SQLite database operations for songs and playlists."""
    def __init__(self):
        init_database()

    def get_all_songs(self):
        conn = sqlite3.connect(get_database_path())
        cursor = conn.cursor()
        cursor.execute("SELECT id, title, artist, album, duration, genre, file_path, play_count FROM songs")
        rows = cursor.fetchall()
        conn.close()
        return [Song(*row) for row in rows]

    def add_song(self, song: Song):
        conn = sqlite3.connect(get_database_path())
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR IGNORE INTO songs (title, artist, album, duration, genre, file_path, play_count)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (song.title, song.artist, song.album, song.duration, song.genre, song.file_path, song.play_count))
        conn.commit()
        conn.close()

    def search_songs(self, query: str):
        conn = sqlite3.connect(get_database_path())
        cursor = conn.cursor()
        search_term = f"%{query}%"
        cursor.execute("""
            SELECT id, title, artist, album, duration, genre, file_path, play_count 
            FROM songs 
            WHERE title LIKE ? OR artist LIKE ? OR album LIKE ?
        """, (search_term, search_term, search_term))
        rows = cursor.fetchall()
        conn.close()
        return [Song(*row) for row in rows]

    def update_song_path(self, song_id: int, new_path: str):
        conn = sqlite3.connect(get_database_path())
        cursor = conn.cursor()
        cursor.execute("UPDATE songs SET file_path = ? WHERE id = ?", (new_path, song_id))
        conn.commit()
        conn.close()

    def get_top_played_songs(self, limit=5):
        conn = sqlite3.connect(get_database_path())
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, title, artist, album, duration, genre, file_path, play_count 
            FROM songs 
            ORDER BY play_count DESC LIMIT ?
        """, (limit,))
        rows = cursor.fetchall()
        conn.close()
        return [Song(*row) for row in rows]

    def get_songs_by_attribute(self, attribute: str, value: str):
        conn = sqlite3.connect(get_database_path())
        cursor = conn.cursor()
        search_term = f"%{value}%"
        if attribute not in ("artist", "genre"):
            conn.close()
            return []
        cursor.execute(f"""
            SELECT id, title, artist, album, duration, genre, file_path, play_count 
            FROM songs 
            WHERE {attribute} LIKE ?
        """, (search_term,))
        rows = cursor.fetchall()
        conn.close()
        return [Song(*row) for row in rows]

    def increment_play_count(self, song_id: int):
        conn = sqlite3.connect(get_database_path())
        cursor = conn.cursor()
        cursor.execute("UPDATE songs SET play_count = play_count + 1 WHERE id = ?", (song_id,))
        conn.commit()
        conn.close()


def play_audio(file_path: str) -> bool:
    """Loads and plays an audio file using Pygame mixer."""
    try:
        if not os.path.exists(file_path):
            print(f"❌ Audio file not found at: {file_path}")
            return False
        pygame.mixer.music.load(file_path)
        pygame.mixer.music.play()
        print(f"▶️ Playing audio...")
        return True
    except Exception as e:
        print(f"❌ Error playing audio: {e}")
        return False


class MusicPlayer:
    """Controls playback state (pause, resume, stop, volume)."""
    def pause_song(self):
        try:
            pygame.mixer.music.pause()
            print("⏸️ Music paused.")
        except Exception as e:
            print(f"❌ Error pausing music: {e}")

    def resume_song(self):
        try:
            pygame.mixer.music.unpause()
            print("▶️ Music resumed.")
        except Exception as e:
            print(f"❌ Error resuming music: {e}")

    def stop_song(self):
        try:
            pygame.mixer.music.stop()
            print("⏹️ Music stopped.")
        except Exception as e:
            print(f"❌ Error stopping music: {e}")

    def set_volume(self, volume: float):
        try:
            pygame.mixer.music.set_volume(max(0.0, min(1.0, volume)))
            print(f"🔊 Volume set to {int(volume * 100)}%")
        except Exception as e:
            print(f"❌ Error setting volume: {e}")


if __name__ == "__main__":
    print("Initializing database and generating local license...")
    init_database()

    generate_local_license(
        license_key="SML-OFFLINE-MASTER-KEY",
        tier="Premium",
        expiry_date="2027-12-31"
    )

    is_valid = validate_offline_subscription()
    print(f"Offline Subscription Validation Test Passed? -> {is_valid}")