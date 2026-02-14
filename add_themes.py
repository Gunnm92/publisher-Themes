#!/usr/bin/env python3
"""
Scan Publishers/ for publisher-info.json files missing a "theme" key.
If a folder.css exists in the same directory, parse it to extract:
  - background-color from #group -> theme.bg and theme.text
  - color from .label -> theme.label
Then add the theme object to the JSON file.
"""

import json
import os
import re
import glob

PUBLISHERS_DIR = "/config/workspace/publisher-Themes/Publishers"

NAMED_COLORS = {
    "white": "#ffffff", "black": "#000000", "red": "#ff0000",
    "green": "#008000", "blue": "#0000ff", "yellow": "#ffff00",
    "orange": "#ffa500", "purple": "#800080", "gray": "#808080",
    "grey": "#808080", "silver": "#c0c0c0", "navy": "#000080",
    "teal": "#008080", "maroon": "#800000", "aqua": "#00ffff",
    "cyan": "#00ffff", "lime": "#00ff00", "fuchsia": "#ff00ff",
    "olive": "#808000", "darkgray": "#a9a9a9", "darkgrey": "#a9a9a9",
    "lightgray": "#d3d3d3", "lightgrey": "#d3d3d3", "darkblue": "#00008b",
    "darkgreen": "#006400", "darkred": "#8b0000", "coral": "#ff7f50",
    "crimson": "#dc143c", "gold": "#ffd700", "indigo": "#4b0082",
    "ivory": "#fffff0", "khaki": "#f0e68c", "lavender": "#e6e6fa",
    "pink": "#ffc0cb", "salmon": "#fa8072", "tan": "#d2b48c",
    "tomato": "#ff6347", "turquoise": "#40e0d0", "violet": "#ee82ee",
    "wheat": "#f5deb3", "transparent": "transparent",
}


def normalize_color(val):
    val = val.strip().lower()
    if val in NAMED_COLORS:
        return NAMED_COLORS[val]
    m = re.match(r'^#([0-9a-f])([0-9a-f])([0-9a-f])$', val)
    if m:
        return "#" + m.group(1)*2 + m.group(2)*2 + m.group(3)*2
    m = re.match(r'^#[0-9a-f]{6}$', val)
    if m:
        return val
    m = re.match(r'^#([0-9a-f]{6})[0-9a-f]{2}$', val)
    if m:
        return "#" + m.group(1)
    return val


def parse_css(css_text):
    css_text = re.sub(r'/\*.*?\*/', '', css_text, flags=re.DOTALL)
    bg_color = None
    label_color = None

    group_match = re.search(r'#group\s*\{([^}]*)\}', css_text)
    if group_match:
        block = group_match.group(1)
        bg_match = re.search(r'background-color\s*:\s*([^;!]+)', block)
        if bg_match:
            bg_color = normalize_color(bg_match.group(1).strip())

    label_match = re.search(r'\.label\s*\{([^}]*)\}', css_text)
    if label_match:
        block = label_match.group(1)
        color_match = re.search(r'(?<![a-z-])color\s*:\s*([^;!]+)', block)
        if color_match:
            label_color = normalize_color(color_match.group(1).strip())

    # Fallback: if no .label block, use color from #group
    if label_color is None and group_match:
        block = group_match.group(1)
        color_match = re.search(r'(?<!-)color\s*:\s*([^;!]+)', block)
        if color_match:
            label_color = normalize_color(color_match.group(1).strip())

    return bg_color, label_color


def main():
    json_files = glob.glob(os.path.join(PUBLISHERS_DIR, "*", "publisher-info.json"))
    json_files.sort()

    updated = 0
    skipped_has_theme = 0
    skipped_no_css = 0
    skipped_parse_fail = 0

    for json_path in json_files:
        dir_path = os.path.dirname(json_path)
        pub_name = os.path.basename(dir_path)

        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if "theme" in data:
            skipped_has_theme += 1
            continue

        css_path = os.path.join(dir_path, "folder.css")
        if not os.path.isfile(css_path):
            print(f"  SKIP (no folder.css): {pub_name}")
            skipped_no_css += 1
            continue

        with open(css_path, "r", encoding="utf-8") as f:
            css_text = f.read()

        bg_color, label_color = parse_css(css_text)

        if bg_color is None:
            print(f"  SKIP (no background-color in #group): {pub_name}")
            skipped_parse_fail += 1
            continue

        if label_color is None:
            print(f"  SKIP (no label color found): {pub_name}")
            skipped_parse_fail += 1
            continue

        data["theme"] = {
            "bg": bg_color,
            "text": bg_color,
            "label": label_color
        }

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write("\n")

        print(f"  UPDATED: {pub_name} -> bg={bg_color}, text={bg_color}, label={label_color}")
        updated += 1

    print(f"\n--- Summary ---")
    print(f"Total publisher-info.json files: {len(json_files)}")
    print(f"Already had theme (skipped): {skipped_has_theme}")
    print(f"No folder.css (skipped): {skipped_no_css}")
    print(f"CSS parse failure (skipped): {skipped_parse_fail}")
    print(f"Updated: {updated}")


if __name__ == "__main__":
    main()
