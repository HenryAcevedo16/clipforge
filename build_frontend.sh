#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

command -v node >/dev/null || { echo "Instala Node.js 22 o superior."; exit 1; }
command -v npm >/dev/null || { echo "No se encontro npm."; exit 1; }

cd frontend
npm ci
npm run build
cd ..
mkdir -p web
cp -R frontend/out/. web/

echo "NovoClip Studio actualizado. Reinicia la app y recarga el navegador."
