#!/bin/bash
# Quran Visual Cards — Run the pipeline server
echo ""
echo "  ╔══════════════════════════════════════════════════════╗"
echo "  ║  Quran Visual Cards Pipeline                         ║"
echo "  ║  Mental Model Synthesis Engine — Nano Banana 2       ║"
echo "  ╚══════════════════════════════════════════════════════╝"
echo ""

# Install dependencies if needed
pip install flask anthropic google-genai Pillow 2>/dev/null || \
pip install flask anthropic google-genai Pillow --break-system-packages 2>/dev/null

# Optional: Set your API keys here (or enter them in the web UI)
# export ANTHROPIC_API_KEY="sk-ant-..."
# export GOOGLE_AI_API_KEY="AIzaSy..."

echo "  Starting server at http://localhost:5000"
echo "  Open http://localhost:5000 in your browser"
echo ""
echo "  API Keys (enter in web UI or set as environment variables):"
echo "    - Anthropic API key: for text analysis (Claude)"
echo "    - Google AI API key: for image generation (Gemini / Nano Banana 2)"
echo ""
echo "  Press Ctrl+C to stop"
echo ""

python3 app.py
