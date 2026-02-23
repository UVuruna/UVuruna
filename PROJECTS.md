# Projects

Full index of all UVuruna projects — local and GitHub.

---

## Table of Contents

- [AI & Machine Learning](#ai)
- [Desktop Applications & Utilities](#desktop)
- [Web Projects](#web)
- [Games & Experiments](#games)

---

<a id="ai"></a>

## 🤖 AI & Machine Learning

---

<a id="input-dna"></a>

### <img src="logos/InputDNA.svg" width="22" height="22"> Input DNA

**Local path:** `AI/Uncanny Valley/Input DNA/`
**GitHub:** [UVuruna/InputDNA](https://github.com/UVuruna/InputDNA)
**Type:** Desktop Application (Windows)
**Status:** 🟢 Active

**Description:** First module of the UVirtual platform — a system that builds a complete virtual replica of a user. InputDNA captures exactly how a specific person moves the mouse and types on the keyboard. It records raw input data into SQLite in real-time, then trains ML models on that behavioral fingerprint. The end goal is a replay engine that reproduces the user's input indistinguishably from the real thing.

**Tech Stack:** Python, PySide6, pynput, SQLite (WAL mode)

**Architecture:** 4-thread queue-based recorder — mouse/keyboard listeners → event queue → event processor → write queue → single DB writer. Recorder is intentionally dumb: capture and store only, no analysis in real-time.

**Key Features:**
- Raw mouse path capture (per-point coordinates, nanosecond timestamps)
- Keyboard capture using hardware scan codes (layout-independent)
- Session-based grouping (mouse sessions, click groups, drag detection)
- Batched SQLite writes (100 records or 2s interval)
- System tray + PySide6 GUI (login, dashboard, session validation)

**Build:** PyInstaller + NSIS, UAC-admin elevation (required for `SetWindowsHookEx`), Windows Defender exclusions, Task Scheduler autostart

**Docs:** [README](AI/Uncanny%20Valley/Input%20DNA/README.md)

---

<a id="desktop"></a>

## 🖥️ Desktop Applications & Utilities

---

<a id="pmUsage"></a>

### <img src="logos/PMUsage.svg" width="22" height="22"> Process Memory Usage (PMUsage)

**Local path:** `Gadgets/PMUsage/`
**GitHub:** [UVuruna/ProcessMemoryUsage](https://github.com/UVuruna/ProcessMemoryUsage)
**Type:** Desktop Application (Windows)
**Status:** 🟢 Active

**Description:** Lightweight Windows desktop gadget for real-time process monitoring. Shows the top N processes by CPU or Memory usage, tracks historical peak usage with timestamps, and displays CPU core/thread count per process. Minimal resource footprint — designed to always be visible without getting in the way.

**Tech Stack:** Python 3.11+, PySide6 (Qt6), psutil

**Architecture:** Single window — `ProcessMonitor` base class → `CPUMonitor` / `MemoryMonitor`, driven by `QTimer`. Monitor Pattern with inheritance for shared formatting and display logic.

**Build:** PyInstaller + NSIS, standard user (no UAC elevation), Registry `HKCU` autostart

**Docs:** [README](Gadgets/PMUsage/README.md)

---

<a id="domy-watch"></a>

### <img src="logos/DOMYWatch.svg" width="22" height="22"> DOMY Watch

**Local path:** `Gadgets/DOMY Watch/`
**GitHub:** [UVuruna/DOMY-Watch](https://github.com/UVuruna/DOMY-Watch)
**Type:** Desktop Application (Windows/Cross-platform)
**Status:** 🔵 Maintained

**Description:** Advanced analog clock that goes beyond just showing the time. Uses the Astral library to calculate location-aware astronomical data and visualizes it directly on the clock face — sunrise, sunset, dawn, dusk, moon phases, solar noon, and day-of-year position. Reads location from a hierarchical world location database.

**Tech Stack:** Python, Kivy (cross-platform GUI), Astral (astronomical calculations), timezonefinder, JSON data (moon phases, seasons, world locations)

**Key Features:**
- Multi-pointer analog clock (hours, minutes, seconds)
- Sunrise/sunset and dawn/dusk arc visualization
- Moon phase tracking
- Earth position (day-of-year) indicator
- Solar noon hexagon
- Location-aware timezone and daylight calculations

---

<a id="auto-openrgb"></a>

### <img src="logos/AutoOpenRGB.svg" width="22" height="22"> Auto OpenRGB

**Local path:** `Gadgets/Auto OpenRGB/`
**GitHub:** [UVuruna/Auto-OpenRGB](https://github.com/UVuruna/Auto-OpenRGB)
**Type:** Utility / Automation (Windows)
**Status:** 🟢 Active

**Description:** Automatic RGB lighting profile switching based on time of day. Reads a config file defining profiles per time slot (dawn, morning, day, evening, night), generates VBS scripts for keyboard shortcut triggers, and creates Windows Task Scheduler tasks that run OpenRGB with the correct profile automatically.

**Tech Stack:** PowerShell, Python, VBScript, Windows Task Scheduler, OpenRGB

**Key Features:**
- Time-slot-based profile scheduling (configurable via JSON)
- Auto-generated VBS keyboard shortcuts for manual switching
- Task Scheduler integration for background execution
- PySide6 GUI for profile management

---

<a id="autoread"></a>

### <img src="logos/AutoRead.svg" width="22" height="22"> AutoRead

**Local path:** `Gadgets/AutoRead/`
**GitHub:** [UVuruna/AutoRead](https://github.com/UVuruna/AutoRead)
**Type:** Automation Script
**Status:** 🔵 Maintained

**Description:** Python automation tool for completing online e-learning courses. Uses screen capture and OCR (tesseract) to read countdown timers from the screen, then automatically clicks through course sections and waits the required duration before proceeding. Keyboard shortcuts allow calibrating screen regions at runtime.

**Tech Stack:** Python, pyautogui (mouse/keyboard), pytesseract (OCR), OpenCV, keyboard

**Key Features:**
- Automatic course navigation and link clicking
- Timer detection and timed waiting via OCR
- Configurable screen regions via keyboard shortcuts at runtime
- Link color detection, scroll controls

---

<a id="rhmh"></a>

### <img src="logos/RHMH.svg" width="22" height="22"> RHMH — Patient Management System

**Local path:** `Applications/RHMH/`
**GitHub:** [UVuruna/RHMH](https://github.com/UVuruna/RHMH)
**Type:** Desktop Application (Windows)
**Status:** 🟢 Active

**Description:** Medical patient management system for a reconstructive surgery hospital department. Manages patient records, medical imaging files, MKB-10 diagnosis catalog, staff/employee data, and operational analytics. Includes AI-powered OCR for reading documents, Google Drive integration for cloud backup, and supports both online and offline modes.

**Tech Stack:** Python, ttkbootstrap (Tkinter), customtkinter, SQLite, Google Drive API, PyTorch, EasyOCR, OpenCV, Pillow, Matplotlib

**Key Features:**
- Patient records with comprehensive form entry (diagnosis, operation date, imaging, etc.)
- Medical imaging file management and display
- MKB-10 diagnosis catalog integration
- AI-powered OCR document reading (EasyOCR + PyTorch)
- Google Drive cloud synchronization and backup
- Analytics with graph/statistical visualizations
- Session logging with performance metrics
- GodMode privileged admin access
- Multi-user support with role-based access

---

<a id="aviator"></a>

### <img src="logos/Aviator.svg" width="22" height="22"> Robin / Vili / Aviator 🔒

**Local path:** `Applications/Robin/Vili/Aviator/`
**GitHub:** Private
**Type:** Automation Application (Windows)
**Status:** 🟡 In Development

**Description:** Multi-bookmaker Aviator game automation system. Collects real-time game data via OCR screen reading and WebSocket connections, runs ML models for round predictions, and executes automated betting decisions. Designed around a Worker Process pattern for parallel execution.

**Tech Stack:** Python, PySide6, OCR, WebSocket, SQLite, ML

**Architecture:** Worker Process Pattern — 1 Bookmaker = 1 Process = 1 CPU Core for parallel OCR execution across multiple bookmakers simultaneously.

**Key Features:**
- Parallel multi-bookmaker data collection
- OCR + WebSocket hybrid data extraction
- ML-powered round outcome predictions
- Automated bet placement and session management

---

<a id="web"></a>

## 🌐 Web Projects

---

<a id="mladen-vuruna"></a>

### <img src="logos/MladenVuruna.svg" width="22" height="22"> Mladen Vuruna

**Local path:** `WebSites/MladenVuruna/`
**GitHub:** [UVuruna/mladenvuruna](https://github.com/UVuruna/mladenvuruna)
**Type:** Website
**Status:** 🟢 Live — [mladenvuruna.com](https://mladenvuruna.com)

**Description:** Personal portfolio website for a Serbian writer and artist. Showcases books with an interactive page-flip animation, essays, and an art gallery. Includes a visitor analytics system (IP, geolocation, pages visited, time spent), an IP-gated admin panel for content management, and a contact/comments system.

**Tech Stack:** PHP 8.x, Vanilla JavaScript, HTML5, CSS3, SQLite

**Key Features:**
- Book viewer with page-flip animation (WebP pages converted from PDF)
- Essays and art gallery sections
- Visitor analytics (IP tracking, geolocation, page views, time spent)
- IP-gated admin panel (password-protected)
- PDF upload → automatic WebP conversion (multiple sizes)
- Comments/contact system

---

<a id="colorize-svg"></a>

### <img src="logos/ColorizeSVG.svg" width="22" height="22"> SVG Styler (Colorize SVG)

**Local path:** `API/Colorize SVG/`
**GitHub:** [UVuruna/SVG-Styler](https://github.com/UVuruna/SVG-Styler)
**Type:** Web Tool
**Status:** 🟢 Active

**Description:** Interactive browser-based tool for real-time SVG color and filter editing. Uses custom circular knob sliders with color-gradient visualization to adjust 7 CSS filter properties simultaneously. Features a build pipeline for production optimization.

**Tech Stack:** PHP, Vanilla JavaScript (ES modules), HTML5, CSS3, esbuild, SVGO, clean-css

**Key Features:**
- 7 real-time filters: brightness, contrast, saturation, hue-rotate, invert, sepia, grayscale
- Custom circular knob slider UI with color gradient visualization
- Real-time SVG preview
- SVG file upload and modified SVG export
- Production build pipeline (esbuild + SVGO + html-minifier)
- Mini version for embedding

---

<a id="mxd"></a>

### <img src="logos/MxD.svg" width="22" height="22"> MxD

**Local path:** `WebSites/MxD (first)/`
**GitHub:** [UVuruna/MxD](https://github.com/UVuruna/MxD)
**Type:** Website
**Status:** 🔴 Archived (job interview task)

**Description:** Corporate website for a B2B marketing and business strategy company. Showcases marketing services, industry verticals, and solutions. Built with a dynamic HTML component loading system and lazy loading for performance.

**Tech Stack:** HTML5, Vanilla JavaScript, CSS3

**Key Features:**
- Dynamic HTML component loading (JS-based module system)
- Dropdown navigation (Services, Verticals, Marketing Solutions)
- Carousel for partner/service showcase
- Lazy loading for performance
- AI chat feature

---

<a id="prirodni-sokovi"></a>

### <img src="logos/PrirodniSokovi.svg" width="22" height="22"> Prirodni Sokovi

**Local path:** `WebSites/PrirodniSokovi/`
**GitHub:** [UVuruna/Prirodni-Sokovi](https://github.com/UVuruna/Prirodni-Sokovi)
**Type:** Website
**Status:** 🔵 Maintained

**Description:** E-commerce website for a natural juice company. Features a product catalog with 11+ juice combinations and individual ingredient pages. Implements a time-based theme system that automatically switches color schemes 4 times throughout the day (morning, noon, afternoon, night) based on Belgrade timezone.

**Tech Stack:** PHP, HTML5, CSS3, Vanilla JavaScript, JSON (product data)

**Key Features:**
- Product catalog with customizable juice combinations
- Ingredient information pages (apple, beetroot, carrot, ginger, etc.)
- Automatic time-based theme switching (4 daily themes)
- Cookie-based theme persistence

---

<a id="vaske-komarnici"></a>

### <img src="logos/VaskeKomarnici.svg" width="22" height="22"> Vaske Komarnici

**Local path:** `WebSites/Vaske-Komarnici/`
**GitHub:** [UVuruna/vaske-komarnici](https://github.com/UVuruna/vaske-komarnici)
**Type:** Website
**Status:** 🔵 Maintained

**Description:** Commercial website for a window/door screen (mosquito net) products business. Features a product catalog with 3 categories (fixed, pleated, roller screens), a multi-step ordering system with persisted order state, installation guides, and SVG colorization for dynamic product visualization.

**Tech Stack:** PHP, HTML5, CSS3, Vanilla JavaScript (modular: interaction, media, ordering, style)

**Key Features:**
- Product catalog with 3 screen categories
- Ordering system with order memory/persistence
- Image preview and carousel
- Installation media guides
- SVG colorization for dynamic product color preview
- Time-based theme switching

---

<a id="games"></a>

## 🎮 Games & Experiments

These are standalone repositories not part of the local monorepo.

---

### Texas Hold'em Poker

**GitHub:** [UVuruna/TexasHoldemPoker](https://github.com/UVuruna/TexasHoldemPoker)
**Status:** 🔴 Archived

**Description:** Texas Hold'em Poker game in Python with real-time probability calculation. Computes win probabilities based on the cards dealt and remaining cards in the deck.

**Tech Stack:** Python

---

### Chess

**GitHub:** [UVuruna/Chess](https://github.com/UVuruna/Chess)
**Status:** 🔴 Archived

**Description:** Chess game implementation in Python.

**Tech Stack:** Python

---

### Tic-Tac-Toe

**GitHub:** [UVuruna/TicTacToe](https://github.com/UVuruna/TicTacToe)
**Status:** 🔴 Archived

**Description:** Classic Tic-Tac-Toe game in Python.

**Tech Stack:** Python

---

## Status Legend

| Badge | Meaning |
|-------|---------|
| 🟢 Active | Actively developed or in production |
| 🟡 In Development | Currently being built |
| 🔵 Maintained | Stable, occasional updates |
| 🔴 Archived | No longer maintained |
| 🔒 | Private repository |
