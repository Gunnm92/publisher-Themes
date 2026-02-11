#!/usr/bin/env python3
"""
Integrate generated headers into publisher-info.json and verify logo presence.
"""

import json
import shutil
from pathlib import Path


def integrate_headers():
    """Check and integrate headers into publisher-info.json"""

    incomplete_dir = Path("_incomplete")
    publishers = sorted([p for p in incomplete_dir.iterdir() if p.is_dir()])

    stats = {
        "total": len(publishers),
        "has_generated_header": 0,
        "has_logo": 0,
        "missing_logo": 0,
        "integrated": 0
    }

    print(f"Checking {len(publishers)} publishers")
    print("=" * 80)

    for idx, pub_dir in enumerate(publishers, 1):
        info_file = pub_dir / "publisher-info.json"
        if not info_file.exists():
            continue

        # Load publisher info
        with open(info_file, "r", encoding="utf-8") as f:
            pub_info = json.load(f)

        name = pub_info.get("name", pub_dir.name)
        print(f"\n[{idx}/{len(publishers)}] {name}")

        # Check for generated header
        header_generated = pub_dir / "header_generated.jpg"
        header_final = pub_dir / "header.jpg"

        if header_generated.exists():
            stats["has_generated_header"] += 1
            print(f"  ✓ Generated header found")

            # Move to final location if not exists
            if not header_final.exists():
                shutil.copy(header_generated, header_final)
                print(f"  → Copied to header.jpg")
                stats["integrated"] += 1

        # Check for logo
        logo_jpg = pub_dir / "logo.jpg"
        logo_png = pub_dir / "logo.png"

        if logo_jpg.exists() or logo_png.exists():
            stats["has_logo"] += 1
            logo_file = "logo.jpg" if logo_jpg.exists() else "logo.png"
            print(f"  ✓ Logo found: {logo_file}")

            # Update publisher-info assets if needed
            if "assets" not in pub_info:
                pub_info["assets"] = {}

            expected_header = "[[FOLDER]]/header.jpg"
            expected_logo = f"[[FOLDER]]/{logo_file}"

            if pub_info["assets"].get("header") != expected_header:
                pub_info["assets"]["header"] = expected_header
                print(f"  → Updated header asset path")

            if pub_info["assets"].get("logo") != expected_logo:
                pub_info["assets"]["logo"] = expected_logo
                print(f"  → Updated logo asset path")

            # Save updated info
            with open(info_file, "w", encoding="utf-8") as f:
                json.dump(pub_info, f, indent=2, ensure_ascii=False)

        else:
            stats["missing_logo"] += 1
            print(f"  ✗ No logo found")

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total publishers: {stats['total']}")
    print(f"Has generated header: {stats['has_generated_header']}")
    print(f"Has logo: {stats['has_logo']}")
    print(f"Missing logo: {stats['missing_logo']}")
    print(f"Headers integrated: {stats['integrated']}")


if __name__ == "__main__":
    integrate_headers()
