const API_BASE_URL =
  window.location.protocol.startsWith("http") && window.location.port === "8000"
    ? window.location.origin
    : "http://localhost:8000";
const STATUS_POLL_MS = 2000;
const GENERATION_POLL_MS = 1000;
const RING_CIRCUMFERENCE = 327;

let modelReady = false;
let isGenerating = false;
let generationPollTimer = null;
let lastSongId = "";

const options = {
  moods: ["Happy", "Hopeful", "Dreamy", "Melancholic", "Sad", "Dark", "Energetic", "Romantic", "Nostalgic", "Epic", "Relaxed"],
  genres: ["Lo-fi", "Jazz", "Neo Soul", "Pop", "Rock", "Ambient", "EDM", "Classical", "Cinematic", "Indie Folk"],
  themes: ["Sunset", "Space", "Rainy Day", "Fantasy", "Cyberpunk", "Adventure", "Love", "Memories", "Heartbreak", "Rain", "Night", "Summer", "Nature", "City Night"],
  instruments: ["Piano", "Acoustic Guitar", "Electric Guitar", "Violin", "Strings", "Bass", "Drums", "Synth", "Saxophone", "Flute", "Choir Pads"],
};

const defaults = {
  moods: new Set(["Hopeful", "Dreamy"]),
  genres: new Set(["Lo-fi"]),
  themes: new Set(["Memories"]),
  instruments: new Set(["Piano", "Bass", "Drums"]),
};

function renderCheckboxes(groupName, values) {
  const container = document.querySelector(`[data-group="${groupName}"]`);

  values.forEach((value) => {
    const id = `${groupName}-${value.toLowerCase().replaceAll(" ", "-")}`;
    const label = document.createElement("label");
    label.className = "choice";
    label.setAttribute("for", id);

    const input = document.createElement("input");
    input.type = "checkbox";
    input.id = id;
    input.name = groupName;
    input.value = value;
    input.checked = defaults[groupName].has(value);

    const text = document.createElement("span");
    text.textContent = value;

    label.append(input, text);
    container.appendChild(label);
  });
}

function getCheckedValues(groupName) {
  return Array.from(document.querySelectorAll(`input[name="${groupName}"]:checked`)).map((input) => input.value);
}

function updateRangeLabel(inputId, outputId, suffix = "") {
  const input = document.getElementById(inputId);
  const output = document.getElementById(outputId);
  output.textContent = `${input.value}${suffix}`;
  input.addEventListener("input", () => {
    output.textContent = `${input.value}${suffix}`;
  });
}

function selectedGenerationMode() {
  return document.querySelector('input[name="generation-mode"]:checked')?.value || "musicgen";
}

function canGenerate() {
  return selectedGenerationMode() === "api" || modelReady;
}

function setGenerating(isLoading) {
  isGenerating = isLoading;
  const button = document.getElementById("generate-button");
  const buttonText = button.querySelector(".button-text");
  const statusMessage = document.getElementById("status-message");

  button.disabled = isLoading || !canGenerate();
  button.classList.toggle("is-loading", isLoading);
  buttonText.textContent = isLoading ? "Generating..." : "Generate Inspiration";
  statusMessage.textContent = isLoading ? "Generating..." : "";
}

function setModelStatus(status, message = "") {
  const button = document.getElementById("generate-button");
  const statusMessage = document.getElementById("status-message");
  const mode = selectedGenerationMode();

  modelReady = status === "ready";
  button.disabled = !canGenerate() || isGenerating;
  button.classList.toggle("is-loading", (mode === "musicgen" && status === "loading") || isGenerating);

  if (isGenerating) {
    statusMessage.textContent = "Generating...";
  } else if (mode === "api") {
    statusMessage.textContent = "Fast API generation is ready.";
  } else if (status === "ready") {
    statusMessage.textContent = "EchoEcho is ready.";
  } else if (status === "error") {
    statusMessage.textContent = "The AI model could not be prepared.";
    showError(message || "MusicGen failed to load. Check the backend terminal for details.");
  } else {
    statusMessage.textContent = "Preparing AI model... this only happens once.";
  }
}

function showError(message) {
  const errorCard = document.getElementById("error-card");
  errorCard.textContent = message;
  errorCard.hidden = false;
}

function clearError() {
  document.getElementById("error-card").hidden = true;
}

function formatDuration(totalSeconds) {
  const safeSeconds = Math.max(0, Number(totalSeconds) || 0);
  const minutes = String(Math.floor(safeSeconds / 60)).padStart(2, "0");
  const seconds = String(safeSeconds % 60).padStart(2, "0");
  return `${minutes}:${seconds}`;
}

function formatFriendlyDuration(totalSeconds) {
  const safeSeconds = Math.max(0, Number(totalSeconds) || 0);
  const minutes = Math.floor(safeSeconds / 60);
  const seconds = safeSeconds % 60;
  return minutes ? `${minutes}m ${String(seconds).padStart(2, "0")}s` : `${seconds}s`;
}

function formatInstrumentSummary(instruments = []) {
  if (!instruments.length) {
    return "None";
  }
  if (instruments.length === 1) {
    return `${instruments[0]} Only`;
  }
  return `${instruments.join(" + ")} Only`;
}

function isInstrumentalSong(song) {
  const prompt = String(song.prompt || "").toLowerCase();
  return prompt.includes("instrumental") || prompt.includes("no vocals") || prompt.includes("no lyrics");
}

function usableLyrics(song) {
  const lyrics = song.lyrics && typeof song.lyrics === "object" ? song.lyrics : {};
  const text = String(lyrics.text || "").trim();
  if (!text || lyrics.structure === "unavailable") {
    return "";
  }
  return text;
}

function copyrightStatusText(copyright) {
  if (!copyright || typeof copyright !== "object") {
    return "Copyright check not run yet.";
  }

  const score =
    copyright.similarity_score === null || copyright.similarity_score === undefined
      ? "N/A"
      : copyright.similarity_score;
  const notes = copyright.notes || copyright.details || "No notes returned.";
  const matches = Array.isArray(copyright.matches)
    ? copyright.matches
        .map((match) => [match.title, match.artist].filter(Boolean).join(" by "))
        .filter(Boolean)
        .join("; ")
    : "";

  return [
    `Status: ${copyright.status || "unavailable"}`,
    `Similarity score: ${score}`,
    `Notes: ${notes}`,
    matches ? `Matched results: ${matches}` : "",
  ]
    .filter(Boolean)
    .join("\n");
}

function renderLyricsSection(song) {
  const section = document.createElement("section");
  section.className = "history-section";

  const heading = document.createElement("h4");
  heading.textContent = "Lyrics";

  const text = document.createElement("p");
  text.className = "lyrics-text";
  const lyricsText = usableLyrics(song);
  if (lyricsText) {
    text.textContent = lyricsText;
  } else if (isInstrumentalSong(song)) {
    text.textContent = "Instrumental track — no lyrics generated.";
  } else {
    text.textContent = "No lyrics generated for this song.";
  }

  section.append(heading, text);
  return section;
}

function renderCopyrightSection(song) {
  const section = document.createElement("section");
  section.className = "history-section copyright-section";

  const heading = document.createElement("h4");
  heading.textContent = "Copyright";

  const text = document.createElement("p");
  text.className = "copyright-result";
  text.textContent = copyrightStatusText(song.copyright);

  section.append(heading, text);
  return { section, text };
}

async function checkSongCopyright(song, resultElement, button) {
  const originalText = button.textContent;
  button.disabled = true;
  button.textContent = "Checking...";
  resultElement.textContent = "Checking copyright...";

  try {
    const response = await fetch(`${API_BASE_URL}/api/copyright/check`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        song_id: song.song_id,
        lyrics: usableLyrics(song),
        title: song.song_id || "",
        prompt: song.prompt || "",
        description: [song.mood, song.theme, song.style].filter(Boolean).join(" "),
      }),
    });
    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
      throw new Error(data.detail || "Copyright check failed.");
    }

    song.copyright = data;
    resultElement.textContent = copyrightStatusText(data);
  } catch (error) {
    resultElement.textContent = `Copyright check failed. ${error.message || "Unknown error."}`;
  } finally {
    button.disabled = false;
    button.textContent = originalText;
  }
}

function updateProgress(status) {
  const progress = Math.max(0, Math.min(Number(status.progress) || 0, 100));
  const stage = status.stage || "Preparing prompt";
  const remaining = Number(status.estimated_remaining_seconds) || 0;
  const remainingText = progress >= 100 ? "00:00" : formatDuration(Math.max(1, remaining));

  document.getElementById("progress-panel").hidden = false;
  document.getElementById("progress-stage").textContent = `${stage}...`;
  document.getElementById("progress-percent").textContent = `${progress}%`;
  document.getElementById("progress-fill").style.width = `${progress}%`;
  document.getElementById("progress-note").style.left = `${progress}%`;
  document.getElementById("elapsed-time").textContent = formatDuration(status.elapsed_seconds);
  document.getElementById("remaining-time").textContent = remainingText;
  document.getElementById("ring-progress").style.strokeDashoffset =
    RING_CIRCUMFERENCE - (RING_CIRCUMFERENCE * progress) / 100;
}

async function pollGenerationStatus() {
  try {
    const response = await fetch(`${API_BASE_URL}/generation-status`, { cache: "no-store" });
    const data = await response.json();
    updateProgress(data);

    if (data.progress >= 100) {
      stopGenerationPolling();
    }
  } catch (error) {
    document.getElementById("progress-stage").textContent = "Waiting for generation status...";
  }
}

function startGenerationPolling() {
  stopGenerationPolling();
  updateProgress({
    stage: "Preparing prompt",
    progress: 0,
    elapsed_seconds: 0,
    estimated_remaining_seconds: 120,
  });
  pollGenerationStatus();
  generationPollTimer = setInterval(pollGenerationStatus, GENERATION_POLL_MS);
}

function stopGenerationPolling() {
  if (generationPollTimer) {
    clearInterval(generationPollTimer);
    generationPollTimer = null;
  }
}

function buildPayload() {
  const mode = selectedGenerationMode();
  return {
    mode,
    fast: mode === "api",
    duration: 30,
    moods: getCheckedValues("moods"),
    genres: getCheckedValues("genres"),
    themes: getCheckedValues("themes"),
    instruments: getCheckedValues("instruments"),
    tempo: Number(document.getElementById("tempo").value),
    complexity: document.getElementById("complexity").value,
    energy: Number(document.getElementById("energy").value),
    custom_prompt: document.getElementById("custom-prompt").value.trim(),
  };
}

function scrollToLibrary() {
  document.getElementById("song-library").scrollIntoView({ behavior: "smooth", block: "start" });
}

async function copyText(value) {
  if (!value) {
    return;
  }

  try {
    await navigator.clipboard.writeText(value);
  } catch (error) {
    const textArea = document.createElement("textarea");
    textArea.value = value;
    document.body.appendChild(textArea);
    textArea.select();
    document.execCommand("copy");
    textArea.remove();
  }
}

function renderGeneratedSong(data) {
  const audioUrl = `${API_BASE_URL}${data.audio_url}?t=${Date.now()}`;
  const audioPlayer = document.getElementById("audio-player");
  const downloadLink = document.getElementById("download-link");

  lastSongId = data.song_id;
  document.getElementById("song-id").textContent = data.song_id;
  document.getElementById("generation-time").textContent =
    data.generation_time || formatFriendlyDuration(data.generation_time_seconds);
  document.getElementById("audio-file").textContent = data.output_file;
  document.getElementById("prompt-used").textContent = data.prompt_used;

  audioPlayer.src = audioUrl;
  audioPlayer.load();
  downloadLink.href = audioUrl;
  downloadLink.download = data.download_filename || `${data.song_id}.wav`;
  document.getElementById("results").hidden = false;
}

async function generateInspiration(event) {
  event.preventDefault();

  if (isGenerating) {
    return;
  }

  if (selectedGenerationMode() === "musicgen" && !modelReady) {
    showError("MusicGen is still preparing. Please wait until EchoEcho is ready.");
    return;
  }

  clearError();
  setGenerating(true);
  startGenerationPolling();

  try {
    const response = await fetch(`${API_BASE_URL}/generate`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(buildPayload()),
    });

    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
      throw new Error(data.detail || "Generation failed.");
    }

    renderGeneratedSong(data);
    updateProgress({
      stage: "Completed",
      progress: 100,
      elapsed_seconds: data.generation_time_seconds,
      estimated_remaining_seconds: 0,
    });
    await loadSongHistory();
  } catch (error) {
    showError(`Generation failed. Reason: ${error.message || "Unknown error"}`);
  } finally {
    await pollGenerationStatus();
    stopGenerationPolling();
    setGenerating(false);
    setModelStatus(modelReady ? "ready" : "loading");
  }
}

function renderHistorySong(song) {
  const songAudioUrl = song.audio_url || `/audio/${song.song_id}.wav`;
  const filename = song.filename || song.audio_filename || `${song.song_id}.wav`;
  const card = document.createElement("article");
  card.className = "history-card";

  const title = document.createElement("h3");
  title.textContent = song.song_id;

  const meta = document.createElement("div");
  meta.className = "history-meta";

  const fields = [
    ["Date", song.created_at ? new Date(song.created_at).toLocaleString() : ""],
    ["Mood", song.mood || "None"],
    ["Theme", song.theme || "None"],
    ["Mode", song.mode === "api" ? "Fast API" : "MusicGen"],
    ["Instruments", formatInstrumentSummary(song.instruments || [])],
    ["Generation Time", song.generation_time || formatFriendlyDuration(song.generation_time_seconds)],
    ["Audio File", song.output_file || `generated/${filename}`],
  ];

  fields.forEach(([label, value]) => {
    const item = document.createElement("span");
    const strong = document.createElement("strong");
    strong.textContent = `${label}: `;
    item.append(strong, document.createTextNode(value || ""));
    meta.appendChild(item);
  });

  const prompt = document.createElement("p");
  prompt.className = "history-prompt";
  prompt.textContent = song.prompt || "";

  const lyricsSection = renderLyricsSection(song);
  const copyright = renderCopyrightSection(song);

  const audio = document.createElement("audio");
  audio.controls = true;
  audio.src = `${API_BASE_URL}${songAudioUrl}?t=${Date.now()}`;

  const actions = document.createElement("div");
  actions.className = "history-actions";

  const download = document.createElement("a");
  download.className = "download-button";
  download.href = audio.src;
  download.download = filename;
  download.textContent = "Download";

  const copy = document.createElement("button");
  copy.className = "icon-button";
  copy.type = "button";
  copy.textContent = "Copy Song ID";
  copy.addEventListener("click", () => copyText(song.song_id));

  const copyrightButton = document.createElement("button");
  copyrightButton.className = "secondary-button";
  copyrightButton.type = "button";
  copyrightButton.textContent = "Check Copyright";
  copyrightButton.addEventListener("click", () => checkSongCopyright(song, copyright.text, copyrightButton));

  actions.append(download, copy, copyrightButton);
  card.append(title, meta, prompt, lyricsSection, copyright.section, audio, actions);
  return card;
}

async function loadSongHistory() {
  const historyList = document.getElementById("history-list");
  historyList.textContent = "";

  try {
    const response = await fetch(`${API_BASE_URL}/songs`, { cache: "no-store" });
    const data = await response.json();
    const songs = Array.isArray(data.songs) ? data.songs : [];

    if (!songs.length) {
      const empty = document.createElement("p");
      empty.className = "empty-history";
      empty.textContent = "No songs saved yet.";
      historyList.appendChild(empty);
      return;
    }

    songs.forEach((song) => {
      historyList.appendChild(renderHistorySong(song));
    });
  } catch (error) {
    const empty = document.createElement("p");
    empty.className = "empty-history";
    empty.textContent = "Song history could not be loaded.";
    historyList.appendChild(empty);
  }
}

async function pollModelStatus() {
  try {
    const response = await fetch(`${API_BASE_URL}/health`, { cache: "no-store" });
    const data = await response.json();
    setModelStatus(data.status, data.message);
  } catch (error) {
    modelReady = false;
    document.getElementById("generate-button").disabled = selectedGenerationMode() === "musicgen";
    document.getElementById("generate-button").classList.remove("is-loading");
    document.getElementById("status-message").textContent = "Waiting for backend connection...";
  }
}

Object.entries(options).forEach(([groupName, values]) => renderCheckboxes(groupName, values));
updateRangeLabel("tempo", "tempo-value", " BPM");
updateRangeLabel("energy", "energy-value");
document.getElementById("generator-form").addEventListener("submit", generateInspiration);
document.getElementById("history-button").addEventListener("click", scrollToLibrary);
document.getElementById("result-history-button").addEventListener("click", scrollToLibrary);
document.getElementById("refresh-history").addEventListener("click", loadSongHistory);
document.getElementById("copy-song-id").addEventListener("click", () => copyText(lastSongId));
document.querySelectorAll('input[name="generation-mode"]').forEach((input) => {
  input.addEventListener("change", () => setModelStatus(modelReady ? "ready" : "loading"));
});
setModelStatus("loading");
pollModelStatus();
loadSongHistory();
setInterval(pollModelStatus, STATUS_POLL_MS);
