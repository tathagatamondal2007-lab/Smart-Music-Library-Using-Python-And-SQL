import os
import sqlite3
from dataclasses import dataclass
import pygame


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
        # Creates a dedicated folder: C:\Users\Username\AppData\Roaming\SmartMusicLibrary
        save_dir = os.path.join(app_data, 'SmartMusicLibrary')
    else:
        # Fallback to user home directory if AppData isn't available
        save_dir = os.path.expanduser('~')

    os.makedirs(save_dir, exist_ok=True)
    return os.path.join(save_dir, 'music_library.db')


class DatabaseManager:
    def __init__(self, db_name=None):
        # Use the safe persistent path automatically
        self.db_name = db_name if db_name else get_database_path()
        print(f"📁 Database Location: {self.db_name}")  # Helpful for locating your persistent file
        self.create_table()

    def get_connection(self):
        return sqlite3.connect(self.db_name)

    def create_table(self):
        with self.get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS songs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    artist TEXT NOT NULL,
                    album TEXT NOT NULL,
                    duration INTEGER,
                    genre TEXT,
                    file_path TEXT NOT NULL,
                    play_count INTEGER DEFAULT 0
                )
            """)
            conn.commit()

            cursor = conn.execute("PRAGMA table_info(songs)")
            columns = [column[1] for column in cursor.fetchall()]
            if "play_count" not in columns:
                conn.execute("ALTER TABLE songs ADD COLUMN play_count INTEGER DEFAULT 0")
            conn.commit()

    def add_song(self, song: Song):
        with self.get_connection() as conn:
            conn.execute("""
                INSERT INTO songs (title, artist, album, duration, genre, file_path, play_count)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (song.title, song.artist, song.album, song.duration, song.genre, song.file_path, song.play_count))
            conn.commit()

    def get_all_songs(self):
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT id, title, artist, album, duration, genre, file_path, play_count FROM songs")
            return [Song(*row) for row in cursor.fetchall()]

    def search_songs(self, query: str):
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT id, title, artist, album, duration, genre, file_path, play_count 
                FROM songs 
                WHERE title LIKE ? OR artist LIKE ? OR album LIKE ?
            """, (f"%{query}%", f"%{query}%", f"%{query}%"))
            return [Song(*row) for row in cursor.fetchall()]

    def get_songs_by_attribute(self, attribute: str, value: str):
        with self.get_connection() as conn:
            query = f"SELECT id, title, artist, album, duration, genre, file_path, play_count FROM songs WHERE {attribute} LIKE ?"
            cursor = conn.execute(query, (f"%{value}%",))
            return [Song(*row) for row in cursor.fetchall()]

    def get_top_played_songs(self, limit: int = 5):
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT id, title, artist, album, duration, genre, file_path, play_count 
                FROM songs 
                ORDER BY play_count DESC 
                LIMIT ?
            """, (limit,))
            return [Song(*row) for row in cursor.fetchall()]

    def update_song_path(self, song_id: int, new_path: str) -> None:
        with self.get_connection() as conn:
            conn.execute("UPDATE songs SET file_path = ? WHERE id = ?", (new_path, song_id))
            conn.commit()

    def increment_play_count(self, song_id: int) -> None:
        with self.get_connection() as conn:
            conn.execute("UPDATE songs SET play_count = play_count + 1 WHERE id = ?", (song_id,))
            conn.commit()


class MusicPlayer:
    def __init__(self):
        pygame.mixer.init()

    def play_song(self, file_path: str):
        if not os.path.exists(file_path):
            print(f"⚠️ File not found at path: {file_path}")
            return False
        try:
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.play()
            print(f"▶️ Now playing: {os.path.basename(file_path)}")
            return True
        except Exception as e:
            print(f"❌ Error playing audio: {e}")
            return False

    def pause_song(self):
        pygame.mixer.music.pause()
        print("⏸️ Music paused.")

    def resume_song(self):
        pygame.mixer.music.unpause()
        print("▶️ Music resumed.")

    def set_volume(self, volume: float):
        vol = max(0.0, min(1.0, volume))
        pygame.mixer.music.set_volume(vol)
        print(f"🔊 Volume set to {int(vol * 100)}%")

    def stop_song(self):
        pygame.mixer.music.stop()
        print("⏹️ Audio stopped.")


_player = MusicPlayer()


def play_audio(file_path: str):
    song = _player.play_song(file_path)
    return song