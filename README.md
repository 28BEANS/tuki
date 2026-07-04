# 🚐 Tuki

> A hyperlocal commuting application for Angeles City, Pampanga — helping commuters navigate the city's color-coded jeepney transportation network.

## What is Tuki?

Tuki provides **multimodal route planning** for Angeles City commuters, offering:

- 🗺️ **Custom routing engine** — understands jeepney routes, transfers, walking paths, and tricycle terminals
- 💰 **Fare estimation** — accurate fare calculations using the national fare matrix
- 🏫 **Landmark-based navigation** — directions using landmarks, not street names
- 🚐 **Jeep Route Explorer** — browse all color-coded jeepney routes and stops
- 🚗 **Ride-hailing comparison** — Grab & Maxim fare estimates side-by-side

Unlike Google Maps, Tuki uses a **custom routing engine** built specifically for Angeles City's public transportation system.

## Monorepo Structure

```
tuki/
├── apps/
│   ├── mobile/          # Flutter mobile app
│   └── backend/         # FastAPI Python backend
│
├── packages/
│   ├── routing_engine/  # Standalone multimodal routing (NetworkX)
│   ├── shared_models/   # Shared Pydantic models
│   ├── gis/             # GIS utilities
│   └── utilities/       # Common helpers
│
├── database/
│   ├── migrations/      # Alembic migrations
│   ├── seeds/           # Data import scripts
│   ├── geojson/         # GeoJSON data files
│   ├── osm/             # OpenStreetMap data scripts
│   ├── fare_matrix/     # National fare matrix
│   ├── reference_maps/  # Visual reference maps
│   └── sql/             # Raw SQL scripts
│
├── docker/              # Docker configs
├── docs/                # Documentation
├── scripts/             # Dev/ops scripts
└── .github/workflows/   # CI/CD
```

## Tech Stack

| Layer | Technologies |
|-------|-------------|
| **Mobile** | Flutter, Riverpod, GoRouter, Dio, MapLibre |
| **Backend** | Python 3.12+, FastAPI, SQLAlchemy 2.0, Pydantic v2 |
| **Database** | PostgreSQL, PostGIS, Supabase |
| **Routing** | NetworkX, Shapely, OSMnx |
| **Maps/GIS** | Google Places API, OpenStreetMap, PostGIS |

## Getting Started

### Quick Start (Recommended)

Run both the backend and the mobile app with a single command:

```bash
./scripts/dev.sh
```

The script will:
- Create the Python virtual environment if it doesn't exist
- Install backend dependencies automatically
- Start the FastAPI backend with hot-reload on `http://localhost:8000`
- Launch the Flutter app on an auto-detected device/emulator

**Options:**

| Flag | Description |
|------|-------------|
| `--backend-only` | Start only the FastAPI backend |
| `--mobile-only` | Start only the Flutter mobile app |
| `--device <id>` | Target a specific Flutter device or emulator |
| `--port <port>` | Override the backend port (default: `8000`) |
| `-h, --help` | Show usage information |

**Examples:**

```bash
# Start everything (default)
./scripts/dev.sh

# Backend only
./scripts/dev.sh --backend-only

# Mobile only (assumes backend is already running)
./scripts/dev.sh --mobile-only

# Target a specific simulator
./scripts/dev.sh --device "iPhone 15 Pro"

# Use a different backend port
./scripts/dev.sh --port 9000
```

> **Tip:** Press `Ctrl+C` to gracefully stop all running services at once.

---

### Manual Setup

If you prefer to run services individually:

#### Backend

```bash
cd apps/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

API docs available at `http://localhost:8000/docs`.

#### Mobile

```bash
cd apps/mobile
flutter pub get
flutter run
```

#### Docker (full stack with PostGIS)

```bash
docker compose -f docker/docker-compose.yml up
```

## Architecture

The backend follows a **layered architecture**:

- **API Layer** → receives requests, validates input
- **Service Layer** → business logic, orchestration
- **Repository Layer** → database queries
- **Routing Engine** → standalone package, independent of FastAPI

## Jeepney Routes

Angeles City has **11 color-coded jeepney routes**:

| Route | Color |
|-------|-------|
| Main Gate – Friendship | Sand |
| C'Point – Balibago – H'way | Grey |
| SM City – Main Gate – Dau | Various |
| Checkpoint – Hensonville – Holy | White |
| Sapang Bato – Angeles | Maroon |
| Checkpoint – Holy – Highway | Lavender |
| Marisol – Pampang | Green |
| Pandang – Pampang | Blue |
| Sunset – Nepo | Orange |
| Villa – Pampang – SM Telebestagen | Yellow |
| Capaya – Angeles | Pink |

## License

See [LICENSE](LICENSE) for details.