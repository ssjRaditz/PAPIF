#!/usr/bin/env python3
"""
Image Loader — generates JS/JSON image cache files for the flashcard app.

Supports TWO images per plant (Ident Picture 1 & Ident Picture 2).
Image files should be named:  <id>a.<ext>  and  <id>b.<ext>
e.g.  1a.webp, 1b.webp, 2a.webp, 2b.webp …

For pests, use the same convention in the pestImages/ folder.
"""

import os
import json
import re

# ── Plants ─────────────────────────────────────────────
PLANTS_FILE        = "plants.txt"
PLANTS_IMG_DIR     = "plant_images"
PLANTS_RESULTS_FILE = "plant_image_results.json"
PLANTS_CACHE_FILE   = "plant_image_data.js"
PLANTS_CACHE_VAR    = "PLANT_IMAGE_CACHE"

# ── Pests ───────────────────────────────────────────────
PEST_FILE          = "pests.txt"
PESTS_IMG_DIR      = "pest_images"
PESTS_RESULTS_FILE = "pest_image_results.json"
PESTS_CACHE_FILE   = "pest_image_data.js"
PESTS_CACHE_VAR    = "PEST_IMAGE_CACHE"


def clean_to_common(name):
    """Strip botanical qualifiers to produce a friendly display name."""
    cleaned = re.sub(r"X |× | cv\.$| subsp\. .+| var\. .+|'[^']*'", "", name).strip()
    return cleaned


def load_items_from_file(filepath):
    """Read a text file and return [(id, name), ...] tuples."""
    items = []
    if not os.path.exists(filepath):
        print(f"❌ ERROR: Config file '{filepath}' not found!")
        return []

    with open(filepath, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "," in line:
                str_id, name = line.split(",", 1)
                try:
                    items.append((int(str_id.strip()), name.strip()))
                except ValueError:
                    print(f"⚠️  Line {line_num}: invalid ID '{str_id}'")
            else:
                print(f"⚠️  Line {line_num}: missing comma: '{line}'")
    return items


def find_local_images(item_id, img_dir):
    """
    Look in img_dir for files matching <id>a.<ext> and <id>b.<ext>.
    Falls back to plain <id>.<ext> for backwards compatibility.
    Returns (filename_or_None, filename_or_None).
    """
    if not os.path.exists(img_dir):
        return None, None

    str_id = str(item_id)
    files  = os.listdir(img_dir)

    def match(prefix):
        for f in files:
            name, _ = os.path.splitext(f)
            if name == prefix:
                return f
        return None

    img1 = match(str_id + "a") or match(str_id)   # prefer <id>a, fall back to <id>
    img2 = match(str_id + "b")
    return img1, img2


def process(items_file, img_dir, results_file, cache_file, cache_var, img_subfolder="images"):
    items = load_items_from_file(items_file)
    if not items:
        print(f"🛑 No items loaded from '{items_file}'. Skipping.")
        return

    results = {}
    print(f"\n📁 Loaded {len(items)} items from '{items_file}'")
    print(f"📁 Scanning '{img_dir}' for images…\n")

    for item_id, name in items:
        str_id   = str(item_id)
        f1, f2   = find_local_images(item_id, img_dir)
        common   = clean_to_common(name)

        if f1 or f2:
            entry = {
                "url":    "local_file",
                "url1":   f"{img_subfolder}/{f1}" if f1 else None,
                "url2":   f"{img_subfolder}/{f2}" if f2 else None,
                "common": common
            }
            results[str_id] = entry
            imgs = ", ".join(filter(None, [f1, f2]))
            print(f"  ✓ [{str_id:>3}] {name} → {imgs}")
        else:
            results[str_id] = None
            print(f"  ✗ [{str_id:>3}] No image file found for ID {str_id}")

    # Write JSON
    with open(results_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\n✅ Wrote {results_file}")

    # Write JS cache
    lines = [
        f"// Auto-generated — do not edit manually",
        f"window.{cache_var} = {{"
    ]
    for iid, info in sorted(results.items(), key=lambda x: int(x[0])):
        if info:
            entry = {
                "url":    info.get("url1") or info.get("url2"),   # legacy single-url compat
                "url1":   info.get("url1"),
                "url2":   info.get("url2"),
                "common": info.get("common", "")
            }
            # Remove None values
            entry = {k: v for k, v in entry.items() if v is not None}
            lines.append(f"  {iid}: {json.dumps(entry)},")
        else:
            lines.append(f"  {iid}: 'error',")
    lines.append("};")

    with open(cache_file, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"✅ Wrote {cache_file}")


def main():
    print("=" * 50)
    print("  Image Loader — Plants & Pests")
    print("=" * 50)

    process(
        items_file   = PLANTS_FILE,
        img_dir      = PLANTS_IMG_DIR,
        results_file = PLANTS_RESULTS_FILE,
        cache_file   = PLANTS_CACHE_FILE,
        cache_var    = PLANTS_CACHE_VAR,
        img_subfolder = "plant_images"
    )

    process(
        items_file   = PEST_FILE,
        img_dir      = PESTS_IMG_DIR,
        results_file = PESTS_RESULTS_FILE,
        cache_file   = PESTS_CACHE_FILE,
        cache_var    = PESTS_CACHE_VAR,
        img_subfolder = "pest_images"
    )


if __name__ == "__main__":
    main()
