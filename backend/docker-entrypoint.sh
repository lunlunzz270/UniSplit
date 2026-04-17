#!/bin/sh
set -e

APP_JS="/app/frontend/src/js/app.js"

if [ -f "$APP_JS" ]; then
    sed -i "1s|^const API_BASE_URL = .*;|const API_BASE_URL = '';|" "$APP_JS"
fi

# Initialize database
python3 -c "from backend.app.core.database import Base, engine; Base.metadata.create_all(bind=engine)"

exec flask --app backend.main run --host=0.0.0.0 --port=5000
