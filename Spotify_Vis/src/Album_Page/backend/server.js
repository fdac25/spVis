require("dotenv").config();
const express = require("express");
const cors = require("cors");
const fs = require("fs");
const path = require("path");

const app = express();
const PORT = process.env.PORT || 3000;

app.use(cors());

// ===== Load Spotify Listening History =====

const historyPath = path.join(__dirname, "data", "listening_history.json");
let listeningHistory = [];

try {
  const raw = fs.readFileSync(historyPath, "utf8");
  const json = JSON.parse(raw);

  listeningHistory = json
    .map((item) => {
      const ts = item.ts || item.endTime;
      const album =
        item.master_metadata_album_album_name || item.albumName || null;
      const artist =
        item.master_metadata_album_artist_name ||
        item.master_metadata_artist_name ||
        item.artistName ||
        null;
      const track =
        item.master_metadata_track_name || item.trackName || "Unknown Track";
      const msPlayed = item.ms_played || item.msPlayed || 0;

      if (!ts || !album || !artist) return null;

      return {
        date: new Date(ts),
        album,
        artist,
        track,
        msPlayed,
      };
    })
    .filter(Boolean);

  console.log(
    `Loaded ${listeningHistory.length} listening records from Spotify history`
  );
} catch (err) {
  console.error("Error loading listening history JSON:", err.message);
  listeningHistory = [];
}

// ===== FILTER HELPERS =====

function inDateRange(d, startStr, endStr) {
  if (!startStr && !endStr) return true;

  if (startStr) {
    const start = new Date(startStr + "T00:00:00");
    if (d < start) return false;
  }
  if (endStr) {
    const end = new Date(endStr + "T23:59:59");
    if (d > end) return false;
  }
  return true;
}

function matchesTimeOfDay(d, timeFilter) {
  const hour = d.getHours();

  switch (timeFilter) {
    case "morning":
      return hour >= 6 && hour < 12;
    case "afternoon":
      return hour >= 12 && hour < 17;
    case "evening":
      return hour >= 17 && hour < 21;
    case "night":
      return hour >= 21 || hour < 6;
    default:
      return true;
  }
}

function matchesSeason(d, season) {
  const month = d.getMonth() + 1;

  switch (season) {
    case "spring":
      return month >= 3 && month <= 5;
    case "summer":
      return month >= 6 && month <= 8;
    case "fall":
      return month >= 9 && month <= 11;
    case "winter":
      return month === 12 || month === 1 || month === 2;
    default:
      return true;
  }
}

// ===== API ROUTES =====

// GET /api/top-albums
app.get("/api/top-albums", (req, res) => {
  const { start, end, time = "all", season = "all" } = req.query;

  const filtered = listeningHistory.filter((play) => {
    return (
      inDateRange(play.date, start, end) &&
      matchesTimeOfDay(play.date, time) &&
      matchesSeason(play.date, season)
    );
  });

  const albumMap = new Map();

  filtered.forEach((play) => {
    const key = `${play.album}::${play.artist}`;
    const countedPlay = play.msPlayed >= 30000 ? 1 : 0;

    if (!albumMap.has(key)) {
      albumMap.set(key, {
        title: play.album,
        artist: play.artist,
        plays: countedPlay,
        cover: null,
      });
    } else {
      albumMap.get(key).plays += countedPlay;
    }
  });

  const result = Array.from(albumMap.values()).sort(
    (a, b) => b.plays - a.plays
  );

  res.json(result);
});

// Health check
app.get("/api/health", (req, res) => {
  res.json({ status: "ok", loaded: listeningHistory.length });
});

// Start server
app.listen(PORT, () => {
  console.log(`Backend listening on http://localhost:${PORT}`);
});
