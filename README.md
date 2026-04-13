# UniSplit

UniSplit is a web application for managing shared expenses. The project currently uses a single-container deployment model:

- Flask serves both the backend API and the frontend static pages
- Docker Compose starts one service only
- For local development, the backend and frontend can also be started separately

## Requirements

- Python 3.11+
- Docker / Docker Compose

## Docker Compose

This is the recommended way to run the project. It builds the backend image and exposes the application on port `3000` on your machine.

The Compose file maps the host port to the container port with:

- `3000:5000`

If you want to change the local port, edit the first number. For example, `3001:5000` exposes the app on port `3001` while keeping Flask inside the container on `5000`.

The database location is controlled by `DATABASE_URL`. By default, the container uses:

- `sqlite:////app/backend/instance/unisplit.db`

This path is mounted to the named Docker volume `backend-instance`, so the database survives container restarts. If you want to store the SQLite file somewhere else, update `DATABASE_URL` in `docker-compose.yml`.

```bash
docker compose up -d --build
```

After startup, open:

- Application: `http://localhost:3000`
- API: `http://localhost:3000/api/...`

Stop the service with:

```bash
docker compose down
```

## Backend

If you want to run only the backend service locally, run the following from the `backend/` directory:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

The backend listens on:

- `http://127.0.0.1:5000`

## Frontend

The frontend pages live under `frontend/src/`. If you want to view the static pages separately, you can use Python's built-in static server:

```bash
cd frontend/src
python -m http.server 8000
```

Then open:

- `http://localhost:8000`

Notes:

- This local static setup expects the backend to be available at `http://127.0.0.1:5000`
- The current frontend script defaults to that backend address

## Project Structure

- `backend/` - Flask application, business logic, database layer, and Docker build files
- `frontend/src/` - Static HTML, CSS, and JavaScript pages
- `docker-compose.yml` - Single-container deployment configuration
- `tests/` - Automated tests

## Tests

Run the test suite with:

```bash
pytest
```
