#!/bin/sh
# Setup script — copy NanoBanana generated images into the project
# Run this from your 02-Quran-Visual-Cards folder on your Mac
# Compatible with macOS default shell (no bash 4+ features)

echo ""
echo "  Quran Visual Cards — Image Setup"
echo "  ================================="
echo ""

# Find the project root (where this script lives)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
IMG_DIR="$SCRIPT_DIR/static/images"
SOURCE_DIR="$HOME/Documents/nanobanana_generated"

mkdir -p "$IMG_DIR"

echo "  Source: $SOURCE_DIR"
echo "  Target: $IMG_DIR"
echo ""

COPIED=0

copy_card() {
  src_name="$1"
  dest_name="$2"
  src_path="$SOURCE_DIR/$src_name"
  dest_path="$IMG_DIR/$dest_name"

  if [ -f "$src_path" ]; then
    cp "$src_path" "$dest_path"
    echo "  [OK] $src_name -> $dest_name"
    COPIED=$((COPIED + 1))
  else
    echo "  [!!] Not found: $src_path"
  fi
}

copy_card "generated_1773409704983.png" "card1_quranic_mission_synthesis.png"
copy_card "generated_1773409744510.png" "card2_maslows_hammer.png"
copy_card "generated_1773409778249.png" "card3_zero_sum_fallacy.png"
copy_card "generated_1773409809296.png" "card4_tawakkul_paradox.png"
copy_card "generated_1773409852278.png" "card5_dunya_trap.png"

echo ""
echo "  Copied $COPIED of 5 images."

if [ "$COPIED" -eq 5 ]; then
  echo "  All images ready! Open gallery.html or preview.html in your browser."
else
  echo "  Some images are missing. Check ~/Documents/nanobanana_generated/"
fi
echo ""
