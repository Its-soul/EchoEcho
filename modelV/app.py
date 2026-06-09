import time
from pathlib import Path

import numpy as np
import soundfile as sf
import streamlit as st
import torch
from transformers import AutoProcessor, MusicgenForConditionalGeneration


APP_TITLE = "EchoEcho"
MODEL_ID = "facebook/musicgen-small"
OUTPUT_FILE = Path("echoecho_music.wav")
SAMPLE_RATE = 32_000
TARGET_SECONDS = 30
TOKENS_PER_SECOND = 50
MAX_NEW_TOKENS = TARGET_SECONDS * TOKENS_PER_SECOND


MOODS = [
    "Happy",
    "Hopeful",
    "Dreamy",
    "Melancholic",
    "Dark",
    "Energetic",
    "Romantic",
    "Nostalgic",
    "Epic",
    "Relaxed",
]

GENRES = [
    "Lo-fi",
    "Jazz",
    "Neo Soul",
    "Pop",
    "Rock",
    "Ambient",
    "EDM",
    "Classical",
    "Cinematic",
    "Indie Folk",
]

THEMES = [
    "Sunset",
    "Space",
    "Rainy Day",
    "Fantasy",
    "Cyberpunk",
    "Adventure",
    "Love",
    "Memories",
    "Nature",
    "City Night",
]

INSTRUMENTS = [
    "Piano",
    "Acoustic Guitar",
    "Electric Guitar",
    "Violin",
    "Strings",
    "Bass",
    "Drums",
    "Synth",
    "Saxophone",
    "Flute",
    "Choir Pads",
]

COMPLEXITIES = ["Simple", "Moderate", "Rich"]


def format_list(values: list[str]) -> str:
    """Format selected sidebar values into natural prompt text."""
    if not values:
        return ""
    if len(values) == 1:
        return values[0]
    return f"{', '.join(values[:-1])} and {values[-1]}"


def build_prompt(
    moods: list[str],
    genres: list[str],
    themes: list[str],
    instruments: list[str],
    tempo: int,
    complexity: str,
    energy_level: int,
    additional_prompt: str,
) -> str:
    """Create a detailed MusicGen prompt from the user's creative choices."""
    prompt_parts = ["30-second instrumental inspiration sketch."]

    if moods:
        prompt_parts.append(f"{format_list(moods)} mood.")
    if genres:
        prompt_parts.append(f"{format_list(genres)} style.")
    if themes:
        prompt_parts.append(f"Theme is {format_list([theme.lower() for theme in themes])}.")
    if instruments:
        prompt_parts.append(
            f"Instruments include {format_list([item.lower() for item in instruments])}."
        )

    prompt_parts.extend(
        [
            f"Tempo {tempo} BPM.",
            f"{complexity} complexity.",
            f"Energy level {energy_level}.",
        ]
    )

    cleaned_extra = additional_prompt.strip()
    if cleaned_extra:
        prompt_parts.append(cleaned_extra)

    prompt_parts.extend(
        [
            "Instrumental only.",
            "No lyrics.",
            "Creative sketch.",
            "Memorable melody.",
            "Suitable for inspiring songwriters.",
        ]
    )

    return " ".join(prompt_parts)


@st.cache_resource(show_spinner=False)
def load_model() -> tuple[AutoProcessor, MusicgenForConditionalGeneration, torch.device]:
    """Load MusicGen once and reuse it across Streamlit reruns."""
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    processor = AutoProcessor.from_pretrained(MODEL_ID)
    model = MusicgenForConditionalGeneration.from_pretrained(MODEL_ID)
    model.to(device)
    model.eval()
    return processor, model, device


def generate_music(prompt: str) -> np.ndarray:
    """Run MusicGen and return a mono or stereo waveform ready to write as WAV."""
    processor, model, device = load_model()
    inputs = processor(text=[prompt], padding=True, return_tensors="pt")
    inputs = {name: value.to(device) for name, value in inputs.items()}

    with torch.inference_mode():
        audio_values = model.generate(
            **inputs,
            do_sample=True,
            guidance_scale=3.0,
            max_new_tokens=MAX_NEW_TOKENS,
        )

    audio = audio_values[0].detach().cpu().float().numpy()

    # soundfile expects shape (samples,) for mono or (samples, channels) for stereo.
    if audio.ndim == 2:
        audio = np.transpose(audio)

    return np.clip(audio, -1.0, 1.0)


def save_wav(audio: np.ndarray, output_path: Path) -> None:
    """Write generated audio to disk at MusicGen's native 32 kHz sample rate."""
    sf.write(output_path, audio, SAMPLE_RATE, format="WAV")


def render_sidebar() -> dict:
    """Collect all creative controls in the sidebar."""
    with st.sidebar:
        st.header("Creative Controls")

        moods = st.multiselect("Mood", MOODS, default=["Hopeful", "Dreamy"])
        genres = st.multiselect("Genre", GENRES, default=["Lo-fi"])
        themes = st.multiselect("Theme", THEMES, default=["Memories"])

        st.caption("Instruments")
        instruments = [
            instrument
            for instrument in INSTRUMENTS
            if st.checkbox(instrument, value=instrument in {"Piano", "Bass", "Drums"})
        ]

        tempo = st.slider("Tempo", min_value=60, max_value=160, value=85, step=1)
        complexity = st.selectbox("Complexity", COMPLEXITIES, index=1)
        energy_level = st.slider("Energy Level", min_value=1, max_value=10, value=4, step=1)
        additional_prompt = st.text_area(
            "Additional Prompt",
            placeholder="Add arrangement, texture, rhythm, or vibe notes...",
            height=120,
        )

    return {
        "moods": moods,
        "genres": genres,
        "themes": themes,
        "instruments": instruments,
        "tempo": tempo,
        "complexity": complexity,
        "energy_level": energy_level,
        "additional_prompt": additional_prompt,
    }


def main() -> None:
    st.set_page_config(page_title=APP_TITLE, page_icon="♪", layout="centered")

    st.title("EchoEcho")
    st.caption("Generate short musical ideas to beat writer's block.")

    selections = render_sidebar()
    prompt = build_prompt(**selections)

    with st.expander("Generated Prompt", expanded=False):
        st.write(prompt)

    if st.button("Generate Inspiration", type="primary", use_container_width=True):
        start_time = time.perf_counter()

        try:
            with st.spinner("Generating a 30-second instrumental sketch..."):
                audio = generate_music(prompt)
                save_wav(audio, OUTPUT_FILE)

            elapsed = time.perf_counter() - start_time
            st.success(f"Generated in {elapsed:.1f} seconds.")

            st.audio(str(OUTPUT_FILE), format="audio/wav")
            st.download_button(
                label="Download echoecho_music.wav",
                data=OUTPUT_FILE.read_bytes(),
                file_name=OUTPUT_FILE.name,
                mime="audio/wav",
                use_container_width=True,
            )

        except RuntimeError as error:
            if "out of memory" in str(error).lower():
                st.error(
                    "MusicGen ran out of memory while generating audio. "
                    "Close other GPU-heavy apps or run on a machine with more VRAM."
                )
            else:
                st.error(f"Generation failed: {error}")
        except Exception as error:
            st.error(f"Something went wrong while generating music: {error}")


if __name__ == "__main__":
    main()
