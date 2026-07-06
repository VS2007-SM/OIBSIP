<div align="center">

# 🌦️ Task 3 — Advanced Weather App

**Oasis Infobyte Python Programming Internship (OIBSIP)**

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Level](https://img.shields.io/badge/Level-Advanced-red?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Complete-success?style=for-the-badge)
![API](https://img.shields.io/badge/Data-Open--Meteo-0ea5e9?style=for-the-badge)
![GUI](https://img.shields.io/badge/GUI-Tkinter-yellow?style=for-the-badge)

[Features](#-features) • [Architecture](#-architecture) • [Setup](#-how-to-run) • [Concepts](#-key-concepts-demonstrated) • [Error Handling](#-error-handling--edge-cases)

</div>

---

## 📌 Overview

A desktop weather application built with Tkinter that goes well beyond the standard "temperature + forecast" brief. It combines real-time weather, air quality, and UV data into a single dashboard, backed by production-style engineering: caching, offline fallback, intelligent location resolution, and a strict separation between data logic and the UI.

Built on **[Open-Meteo](https://open-meteo.com)** — a free, no-API-key weather and air-quality data source, chosen specifically to remove signup/key-management friction for a learning project.

## ✨ Features

| Feature | Description |
|---|---|
| 🔍 **City/place search** | Type any city, town, or place name — resolved via geocoding to coordinates |
| 🌡️ **Current conditions** | Temperature, condition description, "feels like" with a plain-language explanation of *why* it differs (wind chill vs. heat index) |
| 📈 **Day-over-day trend** | Compares the current hour's temperature to the same hour yesterday |
| 💨 **Wind** | Speed + compass direction (N/NE/E/etc.) |
| 🌧️ **Rain chance** | Precipitation probability, not just a yes/no |
| 🌅 **Sunrise / Sunset** | Pulled from the daily forecast |
| 🌬️ **Air Quality Index** | US AQI scale with a plain-language health recommendation |
| ☀️ **UV Index** | WHO/EPA UV scale with exposure guidance |
| 🌡️ **Today's range** | High/low for the day |
| °C / °F toggle | Instantly re-renders all values in the selected unit |
| ⭐ **Favorites** | Save cities to a persistent list; reload with one click |
| 💾 **Caching** | Repeated lookups within 15 minutes skip the API entirely |
| 📡 **Offline fallback** | If the network fails, shows the last cached data with a clear "stale data" banner instead of crashing |
| 🎯 **Approximate-match transparency** | If you search something the geocoder can't resolve exactly (e.g. an institution name like "IIT Dharwad"), it tells you it's showing the nearest known place instead of silently substituting |
| 💡 **"Did you mean?" suggestions** | If a search matches nothing at all, offers clickable alternative suggestions instead of a dead end |
| 🧵 **Non-blocking UI** | Network calls run on a background thread so the window never freezes |

## 🏗️ Architecture

This project is deliberately split into two files with a hard boundary between them:

```
weather_service.py   →  the "brain": API calls, caching, parsing, interpretation logic
weather_gui.py         →  the "face": Tkinter window, layout, rendering only
```

`weather_gui.py` never calls `urllib` or parses JSON directly — it only asks `weather_service.py` for already-processed data. This means the service layer could be reused behind a CLI, a web frontend, or any other interface without changes. This pattern is called **separation of concerns**, and it's the difference between a script and a maintainable application.

```
Task3_WeatherApp/
├── weather_service.py
├── weather_gui.py
├── cache/              (auto-created; stores recent API responses — not tracked in git)
└── favorites.json       (auto-created; stores saved cities — not tracked in git)
```

## 🛠️ Tech Stack

![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)
![Tkinter](https://img.shields.io/badge/Tkinter-GUI-yellow?style=flat-square)
![urllib](https://img.shields.io/badge/urllib-standard%20library-2b2b2b?style=flat-square)
![threading](https://img.shields.io/badge/threading-standard%20library-2b2b2b?style=flat-square)
![difflib](https://img.shields.io/badge/difflib-standard%20library-2b2b2b?style=flat-square)

Python 3.10+ (standard library only — `tkinter`, `urllib`, `json`, `threading`, `datetime`, `difflib`, `socket`). No external packages, no API key required.

> ⚠️ Requires Python 3.10+ due to `X | None` type-hint syntax used in `weather_service.py`. On Python < 3.10, swap these for `Optional[X]` from the `typing` module.

## 🚀 How to Run
```bash
python weather_gui.py
```
Make sure `weather_service.py` is in the same folder — `weather_gui.py` imports it directly. (Run `weather_gui.py`, not `weather_service.py` — the latter only defines the logic layer and has no visible entry point on its own.)

## 🧠 Key Concepts Demonstrated

- **Separation of concerns** — logic layer and UI layer are fully decoupled; the GUI never touches `urllib` or parses JSON
- **Threading in GUI apps** — network calls run off the main thread (`threading.Thread`) so the window stays responsive; results are handed back safely via `self.after(0, ...)`, since Tkinter widgets can only be updated from the main thread
- **Caching with TTL** — API responses are cached to disk with a timestamp and considered "fresh" for 15 minutes, cutting redundant network calls
- **Graceful degradation** — if a live API call fails, the app falls back to the last cached response instead of crashing, and visibly flags the data as stale
- **Real meteorological reasoning** — the "feels like" explanation distinguishes between wind chill (cold + wind) and heat index (hot + humidity) rather than just showing a second number
- **Honest scope on "trend" analysis** — the day-over-day comparison is simple arithmetic on real historical data, not a predictive model; documented as such to avoid overstating it
- **Fuzzy-match detection** — a word-coverage heuristic (backed by `difflib` string similarity) detects when the geocoder resolved a *broader* place than what was searched (e.g. an institution resolving to its host city), and flags this transparently rather than silently substituting
- **"Did you mean?" recovery** — when a search matches nothing at all, a fallback search strategy (broader result count + per-word search) surfaces plausible alternatives, ranked by similarity, offered as clickable buttons
- **Custom exceptions carrying structured data** — `LocationNotFoundError` carries `.query` and `.suggestions` as real attributes, not just a formatted string, so the UI layer can act on the data directly
- **Avoiding the "exception variable" closure bug** — Python deletes `except ... as exc` variables as soon as the block ends; capturing values into plain variables *before* scheduling a delayed callback (`self.after(0, ...)`) avoids a `NameError` that only appears once the callback actually runs
- **Avoiding the loop-closure bug** — dynamically created buttons use a default-argument trick (`lambda s=suggestion: ...`) to bind each button to its own value, instead of every button referencing whatever the loop variable happens to be by the time it's clicked
- **Persistent local storage** — favorites and cache are stored as JSON files that survive between runs, without needing a database

## 🛡️ Error Handling & Edge Cases

| Scenario | Behavior |
|---|---|
| City doesn't exist at all (e.g. "asdkfj") | Clean "couldn't find" message, with "Did you mean?" suggestions if any plausible candidates exist |
| Minor typo (e.g. "Bhopl") | Resolved automatically to the correct city — no warning needed, since it's confidently the same place |
| Searching an institution/landmark (e.g. "IIT Dharwad") | Resolves to the host city, with a clear banner explaining a broader location is being shown |
| Network unavailable | Falls back to last cached result (if any) with a visible "offline" banner, instead of crashing |
| Any unexpected error | Caught by a safety-net handler — the UI always shows *some* feedback rather than hanging silently on "Searching..." |

## 📹 Demo
[Link to demo video / LinkedIn post — add after recording]

---
<div align="center">

Part of the **[OIBSIP](../)** repository — Oasis Infobyte Python Programming Internship

</div>
