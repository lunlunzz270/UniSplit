#!/bin/sh
set -e

APP_JS="/app/frontend/src/js/app.js"

if [ -f "$APP_JS" ]; then
    sed -i "1s|^const API_BASE_URL = .*;|const API_BASE_URL = '';|" "$APP_JS"
fi

exec flask --app backend.main run --host=0.0.0.0 --port=5000
