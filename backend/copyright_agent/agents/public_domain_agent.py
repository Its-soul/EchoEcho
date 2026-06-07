from ..services.preprocessing import PreprocessedLyrics, preprocess_lyrics


PUBLIC_DOMAIN_SONGS = [
    "Happy Birthday to You",
    "Jingle Bells",
    "Silent Night",
    "Twinkle Twinkle Little Star",
    "Old MacDonald Had a Farm",
    "Mary Had a Little Lamb",
]


class PublicDomainAgent:
    def __init__(self, songs: list[str] | None = None) -> None:
        self.songs = songs or PUBLIC_DOMAIN_SONGS
        self.normalized_songs = {
            preprocess_lyrics(song).cleaned: song for song in self.songs
        }

    def run(self, lyrics: str | PreprocessedLyrics) -> dict:
        preprocessed = (
            lyrics if isinstance(lyrics, PreprocessedLyrics) else preprocess_lyrics(lyrics)
        )
        for normalized_song, song_name in self.normalized_songs.items():
            if normalized_song and normalized_song in preprocessed.cleaned:
                return {"is_public_domain": True, "song_name": song_name}
        return {"is_public_domain": False, "song_name": ""}
