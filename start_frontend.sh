#!/bin/bash
# ORION — Quick start frontend
set -e

cd "$(dirname "$0")/frontend"

echo "Installing npm dependencies..."
npm install

echo "Starting ORION frontend on http://localhost:3000 ..."
npm run dev
