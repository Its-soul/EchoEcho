# Echo Echo 🎵

Echo Echo is a multi-agent AI music generation system designed to simulate the workflow of a real music production team. Instead of relying on a single end-to-end music generation model, the system breaks the music creation process into multiple specialized agents that collaborate to produce synchronized lyrics, melody, harmony, and vocals.

The project focuses on orchestration, synchronization, and iterative improvement of generated music through agent collaboration and feedback loops.

---

## Overview

Creating a complete song involves multiple creative tasks such as understanding mood, composing harmony, generating melodies, writing lyrics, synchronizing vocals, and evaluating quality.

Echo Echo approaches this challenge using a collection of independent AI agents managed by a central coordinator called the **Lead Producer**.

Each agent is responsible for a specific task:

* Mood Analysis
* Chord Progression Generation
* Melody Generation
* Lyrics Generation
* Lyrics-Melody Synchronization
* Quality Evaluation
* Singing Voice Synthesis

This architecture provides greater transparency, controllability, and extensibility compared to traditional black-box music generation systems.

---

## Key Features

* Multi-agent architecture for music creation
* Automatic mood and genre analysis
* Chord progression generation
* MIDI melody generation
* AI-generated lyrics
* Syllable-to-note synchronization
* Quality assessment using a Judge Agent
* Iterative refinement through feedback loops
* Singing voice synthesis support
* Fully based on open-source tools and models

---

## System Architecture

```text
User Prompt
      │
      ▼
Mood Agent
      │
      ▼
Chord Agent
      │
      ▼
Melody Agent
      │
      ▼
Lyrics Agent
      │
      ▼
Sync Agent
      │
      ▼
Judge Agent
      │
      ▼
Voice Agent
      │
      ▼
Final Song Output
```

The Lead Producer coordinates communication between all agents and handles revision cycles whenever the Judge Agent identifies quality issues.

---

## Project Structure

```text
echo-echo/
│
├── app/
│   ├── main.py
│   ├── config.py
│   │
│   ├── agents/
│   │   ├── mood_agent.py
│   │   ├── chord_agent.py
│   │   ├── melody_agent.py
│   │   ├── lyrics_agent.py
│   │   ├── sync_agent.py
│   │   ├── judge_agent.py
│   │   └── voice_agent.py
│   │
│   ├── orchestrator/
│   │   └── lead_producer.py
│   │
│   ├── utils/
│   │   ├── midi_utils.py
│   │   ├── audio_utils.py
│   │   └── llm_utils.py
│   │
│   ├── models/
│   │   └── schemas.py
│   │
│   └── api/
│       └── routes.py
│
├── outputs/
│   ├── melody.mid
│   ├── aligned.json
│   └── final.wav
│
├── requirements.txt
└── README.md
```

---

## Technologies Used

### AI & Language Models

* Ollama
* Llama 3
* Gemma 2

### Music Processing

* music21
* pretty_midi
* MIDIUtil
* librosa

### Synchronization

* pyphen
* DTW (Dynamic Time Warping)
* Aeneas

### Audio Generation

* DiffSinger
* HiFi-GAN
* FluidSynth

### Backend

* Python
* FastAPI

---

## Installation

### Clone Repository

```bash
git clone <repository-url>
cd echo-echo
```

### Create Virtual Environment

```bash
python -m venv venv
```

Activate environment:

Windows

```bash
venv\Scripts\activate
```

Linux/macOS

```bash
source venv/bin/activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Install Ollama

Download and install Ollama.

Pull the required model:

```bash
ollama pull llama3
```

Verify that Ollama is running locally before starting the application.

---

## Running the Project

Start the FastAPI server:

```bash
uvicorn app.main:app --reload
```

Server will start at:

```text
http://127.0.0.1:8000
```

API documentation:

```text
http://127.0.0.1:8000/docs
```

---

## Example Request

```json
{
  "prompt": "Generate a romantic piano song about memories"
}
```

---

## Example Output

```json
{
  "mood": {
    "emotion": "romantic",
    "tempo": 80,
    "key": "C Major"
  },
  "chords": [
    "C",
    "Am",
    "F",
    "G"
  ],
  "lyrics": "...",
  "alignment": [...]
}
```

---

## Development Roadmap

### Phase 1 - Foundation

* Mood Agent
* Chord Agent
* Melody Agent
* Lyrics Agent

Output:

* Chord Progression
* MIDI Melody
* Lyrics

### Phase 2 - Synchronization & Evaluation

* Sync Agent
* Judge Agent
* Lead Producer Feedback Loop

Output:

* Aligned Lyrics and Melody
* Quality Assessment
* Iterative Refinement

### Phase 3 - Singing Voice Synthesis

* DiffSinger Integration
* HiFi-GAN Vocoder
* Final Song Generation

Output:

* Fully Synthesized Song (.wav)

---

## Research Motivation

Most existing AI music generation systems focus on generating complete songs using a single model. Echo Echo explores a different direction by introducing a collaborative multi-agent framework where independent agents handle specific creative responsibilities while maintaining synchronization between musical components.

The primary contribution of this project lies in the synchronization and orchestration layer, which ensures that lyrics, melody, rhythm, and harmony remain aligned throughout the generation process.

---

## Future Enhancements

* Web-based music studio interface
* Real-time song editing
* Multiple singer voices
* Genre-specific fine-tuning
* User-controlled melody editing
* Automatic music mastering
* Multi-language lyric generation

---

## Contributors

Team IDEATORS

* Vyakhya Namdev
* Aryan Raj
* Harshita Gupta

---

## License

This project is developed for academic and research purposes.
All third-party libraries and models retain their respective licenses.
