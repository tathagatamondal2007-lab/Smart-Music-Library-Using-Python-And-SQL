import sys
from models import DatabaseManager, Song, play_audio, MusicPlayer

def display_menu():
    print("\n=== 🎵 SMART MUSIC LIBRARY (ADVANCED) 🎵 ===")
    print("1. View All Songs")
    print("2. Add a New Song")
    print("3. Search & Play Song")
    print("4. Edit Song File Path")
    print("5. View Top Played Songs")
    print("6. Filter Songs (by Artist or Genre)")
    print("7. Playback Controls (Pause / Resume / Volume)")
    print("0. Stop Current Audio")
    print("8. Exit")

def main():
    db = DatabaseManager()
    player = MusicPlayer()

    while True:
        display_menu()
        choice = input("\nEnter choice (0-8): ").strip()

        if choice == "1":
            songs = db.get_all_songs()
            if not songs:
                print("\n📂 No songs in the library.")
            else:
                print("\n--- 🎶 All Songs ---")
                for s in songs:
                    print(f"ID: {s.id} | Title: {s.title} | Artist: {s.artist} | Plays: {s.play_count}")

        elif choice == "2":
            print("\n--- ➕ Add a New Song ---")
            title = input("Enter Title: ").strip()
            artist = input("Enter Artist: ").strip()
            album = input("Enter Album: ").strip()
            duration_str = input("Enter Duration (in seconds): ").strip()
            duration = int(duration_str) if duration_str.isdigit() else 0
            genre = input("Enter Genre: ").strip()
            file_path = input("Enter Audio File Path: ").strip()

            new_song = Song(0, title, artist, album, duration, genre, file_path, 0)
            db.add_song(new_song)
            print(f"✅ '{title}' added successfully!")

        elif choice == "3":
            query = input("\nEnter search query (title/artist/album): ").strip()
            results = db.search_songs(query)

            if not results:
                print("❌ No matching songs found.")
            else:
                print("\n--- 🔍 Search Results ---")
                for i, s in enumerate(results, 1):
                    print(f"{i}. {s.title} by {s.artist} (Plays: {s.play_count})")

                song_choice = input("\nEnter number to play (or press Enter to skip): ").strip()
                if song_choice.isdigit():
                    idx = int(song_choice) - 1
                    if 0 <= idx < len(results):
                        target_song = results[idx]
                        if play_audio(target_song.file_path):
                            db.increment_play_count(target_song.id)

        elif choice == "4":
            query = input("\nEnter search term for the song to update: ").strip()
            results = db.search_songs(query)

            if not results:
                print("❌ No matching song found.")
            else:
                print("\nMatching Songs:")
                for i, s in enumerate(results, 1):
                    print(f"{i}. {s.title} by {s.artist}")

                song_choice = input("\nEnter song number to update: ").strip()
                if song_choice.isdigit():
                    idx = int(song_choice) - 1
                    if 0 <= idx < len(results):
                        target_song = results[idx]
                        new_path = input(f"Enter new file path for '{target_song.title}': ").strip()
                        db.update_song_path(target_song.id, new_path)
                        print(f"✅ Successfully updated path!")

        elif choice == "5":
            print("\n--- 🔥 Top Played Songs ---")
            top_songs = db.get_top_played_songs(limit=5)
            if not top_songs:
                print("📂 No play history available yet.")
            else:
                for i, s in enumerate(top_songs, 1):
                    print(f"{i}. {s.title} by {s.artist} — 🔥 {s.play_count} plays")

        elif choice == "6":
            print("\n--- 🔎 Filter Songs ---")
            filter_type = input("Filter by (1) Artist or (2) Genre? Enter 1 or 2: ").strip()
            if filter_type == "1":
                val = input("Enter artist name: ").strip()
                results = db.get_songs_by_attribute("artist", val)
            elif filter_type == "2":
                val = input("Enter genre name: ").strip()
                results = db.get_songs_by_attribute("genre", val)
            else:
                print("❌ Invalid selection.")
                continue

            if not results:
                print("❌ No songs found matching that filter.")
            else:
                print("\nFiltered Results:")
                for s in results:
                    print(f"• {s.title} by {s.artist} [Genre: {s.genre}] (Plays: {s.play_count})")

        elif choice == "7":
            print("\n--- 🎛️ Playback Controls ---")
            print("1. Pause Music")
            print("2. Resume Music")
            print("3. Set Volume (0 to 100)")
            sub_choice = input("Select control option: ").strip()

            if sub_choice == "1":
                player.pause_song()
            elif sub_choice == "2":
                player.resume_song()
            elif sub_choice == "3":
                vol_input = input("Enter volume level (0 - 100): ").strip()
                if vol_input.isdigit():
                    player.set_volume(int(vol_input) / 100.0)
                else:
                    print("❌ Please enter a valid number.")
            else:
                print("❌ Invalid control option.")

        elif choice == "0":
            player.stop_song()

        elif choice == "8":
            print("\n👋 Exiting Music Library. Goodbye!")
            sys.exit()

        else:
            print("❌ Invalid option. Please enter a number between 0 and 8.")

if __name__ == "__main__":
    main1 = main()
    