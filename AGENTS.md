# AGENTS.md - Guide for Agentic Coding Agents

## Project Overview

This is a Ubooquity Publisher Themes repository that hosts publisher and series metadata, images, and styling for the Ubooquity comic server. The repository contains:

- Publisher themes with logos, headers, and metadata
- Series information and artwork
- Python scripts for automated content fetching and processing
- Templates for generating new publisher/series entries
- Assistant assets for UI generation

## Build/Test Commands

### Python Scripts
```bash
# Fetch publisher images and metadata
python3 .scripts/fetch_publisher_images.py --help

# Convert Comixology data to Ubooquity format
python3 .scripts/comixology-to-ubooquity.py --help

# Generate assistant eye assets via ComfyUI
python3 Assistant/generate_eyes.py

# Create SVG elements for assistant
python3 Assistant/create_svg_elements.py

# Find non-WebP images in archives
python3 .scripts/find-nonwebp.py

# Generate ComicVine info files
python3 .scripts/cvinfogen.py PATH_TO_COMICS

# Test archive integrity
perl .scripts/testarchives.pl
```

### Testing Individual Scripts
```bash
# Test syntax of Python files
python3 -m py_compile path/to/script.py

# Test specific functionality
python3 .scripts/fetch_publisher_images.py --dry-run --limit 1
```

## Code Style Guidelines

### Python

#### Import Organization
```python
# Standard library imports first
import argparse
import json
import os
import re
from html.parser import HTMLParser
from urllib.parse import urljoin

# Third-party imports next
import requests
from PIL import Image

# Local imports last (if any)
```

#### Formatting & Structure
- Use 4 spaces for indentation (no tabs)
- Maximum line length: 100 characters
- Use f-strings for string formatting
- Include docstrings for all functions and classes
- Use type hints where appropriate

#### Naming Conventions
- Functions and variables: `snake_case`
- Classes: `PascalCase`
- Constants: `UPPER_SNAKE_CASE`
- Files: `snake_case.py`

#### Error Handling
```python
try:
    resp = requests.get(url, headers=headers, timeout=20)
    resp.raise_for_status()
    return resp.json()
except requests.RequestException as e:
    print(f"Error fetching {url}: {e}")
    return None
except json.JSONDecodeError as e:
    print(f"Error parsing JSON: {e}")
    return None
```

### JSON Files

#### Structure
Publisher metadata files (`publisher-info.json`) follow this structure:
```json
{
  "name": "Publisher Name",
  "slug": "publisher-slug",
  "country": "",
  "description": "",
  "website": "",
  "assets": {
    "header": "[[FOLDER]]/header.jpg",
    "logo": "[[FOLDER]]/logo.jpg"
  },
  "links": [],
  "labels": [],
  "notes": "",
  "last_updated": "YYYY-MM-DD",
  "theme": {
    "bg": "#000000",
    "text": "#000000",
    "label": "#ffffff"
  }
}
```

#### Series metadata
Series files (`series.json`) contain metadata in a structured format with descriptions and other relevant information.

### File Organization

#### Directory Structure
```
Publishers/
├── Publisher Name/
│   ├── publisher-info.json
│   ├── folder.css
│   ├── folder-info.html
│   ├── header.jpg
│   ├── logo.jpg
│   └── folder.jpg
Series/
├── Publisher Name/
│   ├── Series Name/
│   │   └── series.json
.scripts/
├── fetch_publisher_images.py
├── comixology-to-ubooquity.py
└── ...
Assistant/
├── generate_eyes.py
├── create_svg_elements.py
└── ...
.templates/
├── Comics/Series/
└── ...
```

### Coding Patterns

#### API Requests
```python
USER_AGENT = "publisher-themes-image-fetcher/1.0"

def make_request(url, timeout=20):
    """Make HTTP request with proper headers and timeout."""
    try:
        resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=timeout)
        resp.raise_for_status()
        return resp
    except requests.RequestException as e:
        print(f"Request failed: {e}")
        return None
```

#### File Operations
```python
def ensure_folder(path):
    """Create directory if it doesn't exist."""
    os.makedirs(path, exist_ok=True)

def load_json(file_path):
    """Load and parse JSON file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading {file_path}: {e}")
        return {}
```

#### HTML Parsing
Use the built-in `html.parser` module for parsing HTML content. Create custom parser classes for specific needs.

### Dependencies

#### Core Dependencies
- `requests` - HTTP requests
- `Pillow` (PIL) - Image processing (use `Image.Resampling.LANCZOS` for modern Pillow)
- `beautifulsoup4` - HTML parsing (for some scripts)
- `html5lib` - HTML parser

#### Installation
```bash
pip install requests pillow beautifulsoup4 html5lib
```

#### External Services
- Wikipedia/Wikidata APIs for publisher information
- ComfyUI for asset generation
- Various comic database APIs

### Security & Best Practices

#### Input Sanitization
```python
import re
def sanitize_folder_name(name):
    """Sanitize folder names for filesystem compatibility."""
    name = name.strip()
    return re.sub(r"[\\/:*?\"<>|]", "-", name)
```

#### Rate Limiting
Always implement delays between API calls to avoid being blocked:
```python
import time
time.sleep(args.delay)  # Between requests
```

#### User Agents
Always set appropriate User-Agent headers for web requests to identify your bot.

## Development Workflow

1. **Before committing**: Run syntax checks on modified Python files
2. **Testing**: Use `--dry-run` flags where available
3. **Image processing**: Test with small samples before bulk operations
4. **API calls**: Respect rate limits and implement proper error handling
5. **File paths**: Use `os.path.join()` for cross-platform compatibility

## Notes

- Some legacy Python files use Python 2 syntax and may need updating
- Image processing requires PIL/Pillow for format conversion and resizing
- Web scraping should be done responsibly with proper delays
- The repository contains both English and non-English publisher content
- Template files provide standardized formats for new entries