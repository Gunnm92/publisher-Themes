#!/usr/bin/env python3
"""
Batch-enrich `_incomplete/**/ai_prompt.txt` prompts using local publisher metadata.

The goal is to avoid overly generic prompts by injecting publisher-specific themes
in a safe way (i.e., "evoking" a catalog rather than asserting hard facts).

For publishers with missing descriptions, the script can optionally query Wikipedia
for a short summary (rate-limited).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import time
import urllib.parse
from dataclasses import dataclass
from typing import Iterable, Optional

import requests


USER_AGENT = "publisher-themes-ai-prompt-enricher/1.0"
MAX_LINE_LEN = 800  # prompts are single-line; keep reasonably bounded


@dataclass(frozen=True)
class PublisherInfo:
    """Normalized publisher metadata loaded from publisher-info.json."""

    name: str
    country: str
    description: str
    notes: str
    website: str
    theme_bg: str
    theme_text: str
    theme_label: str


def load_publisher_info(folder: str) -> PublisherInfo:
    """Load publisher-info.json, returning a normalized PublisherInfo."""
    path = os.path.join(folder, "publisher-info.json")
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    theme = raw.get("theme") or {}
    return PublisherInfo(
        name=(raw.get("name") or os.path.basename(folder)).strip(),
        country=(raw.get("country") or "").strip(),
        description=(raw.get("description") or "").strip(),
        notes=(raw.get("notes") or "").strip(),
        website=(raw.get("website") or "").strip(),
        theme_bg=str(theme.get("bg") or "").strip(),
        theme_text=str(theme.get("text") or "").strip(),
        theme_label=str(theme.get("label") or "").strip(),
    )


def read_text(path: str) -> str:
    """Read a UTF-8 text file safely."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        return ""


def write_text(path: str, text: str) -> None:
    """Write a UTF-8 text file with trailing newline."""
    with open(path, "w", encoding="utf-8") as f:
        f.write(text.rstrip() + "\n")


def normalize_space(s: str) -> str:
    """Collapse whitespace and trim."""
    return re.sub(r"\s+", " ", s).strip()


def clamp_line(s: str, max_len: int = MAX_LINE_LEN) -> str:
    """Ensure a prompt stays single-line and within a max length."""
    s = normalize_space(s.replace("\n", " "))
    if len(s) <= max_len:
        return s
    return s[: max_len - 3].rstrip() + "..."


def has_generic_prompt(prompt: str) -> bool:
    """Heuristic: detect the common generic templates used in this repo."""
    p = prompt.lower().strip()
    if not p:
        return True
    if p.startswith("whimsical children's book illustration"):
        return True
    if p.startswith("japanese manga style landscape"):
        return True
    if p.startswith("film noir city at night"):
        return True
    if p.startswith("historical period architecture"):
        return True
    if p.startswith("whimsical cartoon town"):
        return True
    if "abstract artistic composition" in p:
        return True
    if "abstract artistic interpretation" in p:
        return True
    if "scenic landscape with natural elements" in p:
        return True
    return False


def looks_like_system_folder(publisher_name: str) -> bool:
    """Skip folders like `_downloads`."""
    return publisher_name.strip().startswith("_")


def wikipedia_summary(
    session: requests.Session, query: str, *, delay_s: float = 0.25
) -> Optional[str]:
    """Fetch a short French Wikipedia summary for a query, best-effort."""
    query = query.strip()
    if not query:
        return None

    # 1) Try direct summary by title
    title = urllib.parse.quote(query.replace(" ", "_"), safe="")
    url = f"https://fr.wikipedia.org/api/rest_v1/page/summary/{title}"
    try:
        resp = session.get(url, headers={"User-Agent": USER_AGENT}, timeout=20)
        if resp.status_code == 200:
            data = resp.json()
            extract = (data.get("extract") or "").strip()
            if extract:
                time.sleep(delay_s)
                return extract
    except requests.RequestException:
        pass

    # 2) Fallback: opensearch for best title
    search_url = "https://fr.wikipedia.org/w/api.php"
    try:
        resp = session.get(
            search_url,
            params={
                "action": "opensearch",
                "search": query,
                "limit": 1,
                "namespace": 0,
                "format": "json",
            },
            headers={"User-Agent": USER_AGENT},
            timeout=20,
        )
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, list) and len(data) >= 2 and data[1]:
            best_title = str(data[1][0])
            title2 = urllib.parse.quote(best_title.replace(" ", "_"), safe="")
            url2 = f"https://fr.wikipedia.org/api/rest_v1/page/summary/{title2}"
            resp2 = session.get(url2, headers={"User-Agent": USER_AGENT}, timeout=20)
            if resp2.status_code == 200:
                extract = (resp2.json().get("extract") or "").strip()
                if extract:
                    time.sleep(delay_s)
                    return extract
    except (requests.RequestException, ValueError, TypeError):
        pass

    return None


def extract_keywords(text: str) -> list[str]:
    """Extract lightweight thematic keywords from free text (French + English)."""
    t = text.lower()
    keywords: list[str] = []

    def add(k: str) -> None:
        if k not in keywords:
            keywords.append(k)

    patterns = [
        (r"\bjeunesse\b|\benfant", "jeunesse"),
        (r"\bmanga\b|\bsh[oō]nen\b|\bsh[oō]jo\b|\bseinen\b", "manga"),
        (r"\bbande\s+dessin[ée]e\b|\bbd\b", "bd"),
        (r"\bcomic\s+book\b|\bcomics\b", "comics"),
        (r"\bscience[- ]fiction\b|\bsf\b|\bfutur", "science-fiction"),
        (r"\bfantasy\b|\bfantastique\b|\bimaginaire\b", "fantasy"),
        (r"\bgothique\b|\bbit[- ]lit\b|\bvamp", "gothique"),
        (r"\bpolar\b|\bnoir\b|\bdétective\b", "noir"),
        (r"\bhistoire\b|\bhistorique\b|\bpatrimoine\b|\barchives?\b", "historique"),
        (r"\bhumou?r\b|\bsatir", "humour"),
        (r"\bpolit", "politique"),
        (r"\bécolog|\bnature\b|\banimal", "nature"),
        (r"\bart\b|\bil[l]ustr", "art"),
        (r"\bpoés", "poesie"),
        (r"\bspirit|\brelig|\bcathol|\bchr[eé]t", "spirituel"),
        (r"\baventure\b|\bexplor", "aventure"),
        (r"\bguerre\b|\bmilit", "guerre"),
        (r"\bromance\b|\bamour\b", "romance"),
    ]
    for pat, k in patterns:
        if re.search(pat, t):
            add(k)

    return keywords


def theme_phrases(keywords: list[str]) -> list[str]:
    """Map internal keywords to short human-friendly theme phrases."""
    mapping = {
        "jeunesse": "children's literature",
        "manga": "manga and Japanese pop-culture",
        "comics": "comic book storytelling",
        "science-fiction": "science-fiction",
        "fantasy": "fantasy and the fantastic",
        "gothique": "gothic and dark romance",
        "noir": "noir mystery",
        "historique": "history and heritage",
        "humour": "humour and satire",
        "politique": "society and politics",
        "nature": "nature and wildlife",
        "art": "art and illustration",
        "poesie": "poetry",
        "spirituel": "spirituality and faith",
        "aventure": "adventure",
        "guerre": "war stories",
        "romance": "romance",
    }
    out: list[str] = []
    for k in keywords:
        phrase = mapping.get(k)
        if phrase and phrase not in out:
            out.append(phrase)
    return out


def base_style(info: PublisherInfo, keywords: list[str]) -> str:
    """Pick a base style string."""
    if "manga" in keywords and ("bd" in keywords or "comics" in keywords):
        return "Franco-Belgian bande dessinée illustration style with subtle manga influences"
    if "manga" in keywords:
        return "Japanese manga/anime background art style"
    if "jeunesse" in keywords:
        return "refined children's book illustration, watercolor + gouache"
    if info.country.upper() in {"US", "USA"}:
        return "American comic book cover-art style"
    if "noir" in keywords:
        return "film noir graphic novel illustration style"
    if "historique" in keywords:
        return "classic European illustration with historical detail"
    if "humour" in keywords:
        return "Franco-Belgian humour comic illustration style"
    return "Franco-Belgian bande dessinée illustration style"


def scene_motifs(keywords: list[str], publisher_name: str) -> str:
    """Build a scene/motif clause from keywords and name cues."""
    name_lower = publisher_name.lower()

    if "politique" in keywords and "humour" in keywords:
        return (
            "satirical editorial atmosphere: newsroom desk and newspaper page textures "
            "(no readable text), playful caricature silhouettes, bold graphic shapes"
        )
    if "politique" in keywords:
        return (
            "contemporary city panorama with civic and editorial motifs, poster-like shapes "
            "(no readable text), strong graphic composition"
        )
    if "humour" in keywords:
        return "playful town panorama, exaggerated architecture, lively comedic details, bright cheerful mood"
    if "fantasy" in keywords and "gothique" in keywords:
        return (
            "moonlit castle silhouette in mist, ravens, thorny roses, faint glowing runes, "
            "dramatic chiaroscuro lighting"
        )
    if "fantasy" in keywords:
        return "enchanted forest clearing, distant castle ruins, subtle runes and magical glows"
    if "science-fiction" in keywords:
        return "futuristic skyline under a starfield, sleek spacecraft silhouettes, soft neon accents"
    if "noir" in keywords:
        return "rain-soaked city street at night, dramatic shadows, cinematic streetlights, mystery mood"
    if "historique" in keywords:
        return "historical panorama with period architecture cues, paper textures, engraving-like detail"
    if "nature" in keywords:
        return "lush landscape panorama, trees and wildlife silhouettes, warm atmospheric depth"
    if "spirituel" in keywords:
        return "cathedral-like architecture cues, stained-glass color washes, calm contemplative atmosphere"
    if "jeunesse" in keywords:
        return "friendly storybook landscape, playful characters hinted as silhouettes, gentle warm light"
    if "manga" in keywords:
        return "Tokyo street or school neighborhood vista, detailed signage shapes (no readable text), sunset glow"

    # Name-based gentle cues (safe, non-factual)
    if "soleil" in name_lower:
        return "sunlit Mediterranean landscape, golden warm light, airy panoramic depth"
    if "urban" in name_lower:
        return "modern city panorama, bold graphic shapes, street-art textures, dynamic perspective"
    if "marvel" in name_lower or "dc" in name_lower:
        return "dynamic city skyline with heroic scale, dramatic clouds, high-contrast lighting"

    return "symbolic panoramic environment evoking the publisher's catalog themes"


def palette_hint(info: PublisherInfo, keywords: list[str]) -> str:
    """Optional color palette hint, using theme colors when present."""
    colors_raw = [c for c in (info.theme_bg, info.theme_text, info.theme_label) if c.startswith("#")]
    colors: list[str] = []
    for c in colors_raw:
        if c not in colors:
            colors.append(c)
    if colors:
        return f"color palette inspired by {', '.join(colors[:3])}"
    if "gothique" in keywords:
        return "deep midnight blues and purples with silver highlights"
    if "jeunesse" in keywords:
        return "soft warm pastels with vibrant accents"
    if "science-fiction" in keywords:
        return "cool blues with neon magenta accents"
    if "historique" in keywords:
        return "muted sepia tones with ink-black linework"
    return ""


def build_prompt(info: PublisherInfo, current_prompt: str, wiki_extract: Optional[str]) -> str:
    """Build a single-line ai prompt tailored to the publisher."""
    text_for_keywords = " ".join(
        s for s in [current_prompt, info.description, info.notes, info.website, wiki_extract or ""] if s
    )
    keywords = extract_keywords(text_for_keywords)

    style = base_style(info, keywords)
    scene = scene_motifs(keywords, info.name)
    palette = palette_hint(info, keywords)

    parts = [
        f"{info.name} publisher header illustration",
        style,
        scene,
    ]
    if palette:
        parts.append(palette)
    parts.extend(
        [
            "wide panoramic banner format",
            "professional illustration",
            "highly detailed",
            "no text",
            "no words",
        ]
    )
    prompt = ", ".join(parts)
    return clamp_line(prompt)


def ensure_suffix_constraints(prompt: str) -> str:
    """Ensure required constraints are present."""
    p = prompt
    if "wide panoramic banner format" not in p.lower():
        p = f"{p}, wide panoramic banner format"
    if "professional illustration" not in p.lower():
        p = f"{p}, professional illustration"
    if "highly detailed" not in p.lower():
        p = f"{p}, highly detailed"
    # Keep "no text, no words" at the end for consistency
    if "no text" not in p.lower() and "no words" not in p.lower():
        p = f"{p}, no text, no words"
    elif "no text" not in p.lower():
        p = f"{p}, no text"
    elif "no words" not in p.lower():
        p = f"{p}, no words"
    return clamp_line(p)


def strip_constraint_parts(prompt: str) -> str:
    """Remove known constraint fragments so we can re-append them in a stable order."""
    parts = [x.strip() for x in prompt.split(",") if x.strip()]
    banned = {
        "wide panoramic banner format",
        "professional illustration",
        "highly detailed",
        "no text",
        "no words",
    }
    kept: list[str] = []
    for part in parts:
        if part.lower() in banned:
            continue
        kept.append(part)
    return ", ".join(kept)


def append_constraints(prompt: str) -> str:
    """Append constraints in a consistent order."""
    p = strip_constraint_parts(prompt)
    p = f"{p}, wide panoramic banner format, professional illustration, highly detailed, no text, no words"
    return clamp_line(p)


def ensure_prefix_name(prompt: str, publisher_name: str) -> str:
    """Ensure the prompt starts with '{name} publisher header illustration'."""
    p = prompt.strip()
    expected_prefix = f"{publisher_name} publisher header illustration"
    if p.lower().startswith(expected_prefix.lower()):
        return p
    # If it already starts with the publisher name, just add the missing phrase.
    if p.lower().startswith(publisher_name.lower()):
        return f"{publisher_name} publisher header illustration, {p[len(publisher_name):].lstrip(' ,')}"
    return f"{expected_prefix}, {p}"


def merge_enrichment(info: PublisherInfo, current_prompt: str, wiki_extract: Optional[str]) -> str:
    """Enrich an existing prompt without discarding its scene/style."""
    text_for_keywords = " ".join(
        s for s in [current_prompt, info.description, info.notes, info.website, wiki_extract or ""] if s
    )
    keywords = extract_keywords(text_for_keywords)
    phrases = theme_phrases(keywords)[:3]
    palette = palette_hint(info, keywords)

    p = ensure_prefix_name(strip_constraint_parts(current_prompt), info.name)
    lower = p.lower()
    if phrases and "evoking" not in lower:
        p = f"{p}, evoking {', '.join(phrases)}"
    if palette and "color palette inspired by" not in lower:
        p = f"{p}, {palette}"
    return append_constraints(p)


def iter_ai_prompt_files(root: str) -> Iterable[str]:
    """Yield ai_prompt.txt paths under root."""
    for dirpath, _dirnames, filenames in os.walk(root):
        if "ai_prompt.txt" in filenames:
            yield os.path.join(dirpath, "ai_prompt.txt")


def main() -> int:
    parser = argparse.ArgumentParser(description="Enrich ai_prompt.txt files under _incomplete/")
    parser.add_argument("--root", default="_incomplete", help="Root folder to scan")
    parser.add_argument("--dry-run", action="store_true", help="Print changes without writing")
    parser.add_argument("--limit", type=int, default=0, help="Max number of files to update (0 = no limit)")
    parser.add_argument("--use-wikipedia", action="store_true", help="Query Wikipedia when local info is empty")
    parser.add_argument("--delay", type=float, default=0.25, help="Delay between Wikipedia calls (seconds)")
    parser.add_argument(
        "--force-constraints",
        action="store_true",
        help="Also normalize prompts by enforcing prefix/suffix constraints even when not 'generic'",
    )
    parser.add_argument(
        "--enrich-all",
        action="store_true",
        help="Enrich non-generic prompts too (adds 'evoking …' themes when missing)",
    )
    args = parser.parse_args()

    session = requests.Session()

    updated = 0
    skipped = 0
    total = 0

    for path in sorted(iter_ai_prompt_files(args.root)):
        folder = os.path.dirname(path)
        info = load_publisher_info(folder)
        if looks_like_system_folder(info.name):
            skipped += 1
            continue

        current = read_text(path)
        total += 1

        wiki_extract: Optional[str] = None
        if args.use_wikipedia and len(info.description) < 20 and len(info.notes) < 10:
            wiki_extract = wikipedia_summary(session, info.name, delay_s=args.delay)

        should_rewrite = (not current) or has_generic_prompt(current) or info.name.lower() not in current.lower()
        if should_rewrite:
            new_prompt = build_prompt(info, current, wiki_extract)
        elif args.enrich_all:
            new_prompt = merge_enrichment(info, current, wiki_extract)
        elif args.force_constraints:
            new_prompt = ensure_suffix_constraints(ensure_prefix_name(current, info.name))
        else:
            new_prompt = merge_enrichment(info, current, wiki_extract)

        # Update if generic OR missing publisher name in prompt OR empty OR forced normalization
        if (
            should_rewrite
            or (args.enrich_all and new_prompt != current)
            or (args.force_constraints and new_prompt != current)
            or len(current) < 40
        ):
            if args.dry_run:
                print(f"UPDATE {path}")
                print(f"- {current}")
                print(f"+ {new_prompt}")
                print()
            else:
                write_text(path, new_prompt)
            updated += 1
            if args.limit and updated >= args.limit:
                break
        else:
            skipped += 1

    print(f"Scanned: {total}  Updated: {updated}  Skipped: {skipped}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
