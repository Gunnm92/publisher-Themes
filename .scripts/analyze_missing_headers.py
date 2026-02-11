#!/usr/bin/env python3
"""
Analyze incomplete publishers and identify which ones are missing headers.
"""

import os
import json
from pathlib import Path

def analyze_incomplete_publishers():
    """Find all publishers in _incomplete that are missing headers."""
    incomplete_dir = Path("_incomplete")

    if not incomplete_dir.exists():
        print("Error: _incomplete directory not found")
        return

    missing_headers = []
    has_headers = []

    for publisher_dir in sorted(incomplete_dir.iterdir()):
        if not publisher_dir.is_dir():
            continue

        # Check for header files
        header_jpg = publisher_dir / "header.jpg"
        header_png = publisher_dir / "header.png"

        publisher_name = publisher_dir.name

        if not header_jpg.exists() and not header_png.exists():
            # Check if there are work headers or test headers
            work_headers = list(publisher_dir.glob("header_work*.jpg")) + \
                          list(publisher_dir.glob("header_work*.png"))
            test_headers = list(publisher_dir.glob("header_*test*.jpg")) + \
                          list(publisher_dir.glob("header_*test*.png"))

            info = {
                "name": publisher_name,
                "path": str(publisher_dir),
                "has_work_headers": len(work_headers) > 0,
                "work_header_count": len(work_headers),
                "has_test_headers": len(test_headers) > 0,
                "test_header_count": len(test_headers)
            }

            # Check if publisher-info.json exists
            info_file = publisher_dir / "publisher-info.json"
            if info_file.exists():
                try:
                    with open(info_file, "r", encoding="utf-8") as f:
                        pub_info = json.load(f)
                        info["publisher_name"] = pub_info.get("name", publisher_name)
                        info["description"] = pub_info.get("description", "")[:100]
                except Exception as e:
                    info["error"] = str(e)

            missing_headers.append(info)
        else:
            has_headers.append(publisher_name)

    # Print summary
    print(f"\n{'='*80}")
    print(f"SUMMARY OF INCOMPLETE PUBLISHERS")
    print(f"{'='*80}\n")
    print(f"Total publishers in _incomplete: {len(list(incomplete_dir.iterdir()))}")
    print(f"Publishers WITH headers: {len(has_headers)}")
    print(f"Publishers MISSING headers: {len(missing_headers)}\n")

    # Print publishers missing headers
    print(f"{'='*80}")
    print(f"PUBLISHERS MISSING HEADERS ({len(missing_headers)})")
    print(f"{'='*80}\n")

    for idx, info in enumerate(missing_headers, 1):
        print(f"{idx}. {info['name']}")
        if info.get('has_work_headers'):
            print(f"   → Has {info['work_header_count']} work header(s)")
        if info.get('has_test_headers'):
            print(f"   → Has {info['test_header_count']} test header(s)")
        if info.get('description'):
            print(f"   → {info['description']}")
        print()

    # Save to JSON for processing
    output_file = Path(".scripts") / "missing_headers.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump({
            "total": len(missing_headers),
            "publishers": missing_headers
        }, f, indent=2, ensure_ascii=False)

    print(f"\nDetailed results saved to: {output_file}")

    return missing_headers

if __name__ == "__main__":
    analyze_incomplete_publishers()
