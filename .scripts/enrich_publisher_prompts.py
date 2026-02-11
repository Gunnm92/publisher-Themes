#!/usr/bin/env python3
"""
Enrich publisher descriptions with web research for better header generation.
"""

import argparse
import json
import time
from pathlib import Path
from typing import Dict, Any, Optional
import urllib.request
import urllib.parse


def search_publisher_info(name: str, existing_description: str) -> str:
    """
    Use web search to get more specific information about the publisher.
    This creates a richer prompt for image generation.
    """
    # For now, analyze existing description and enhance it
    # In production, this could use actual web search API

    desc_lower = existing_description.lower()

    # Extract key characteristics
    characteristics = []

    # Style indicators
    if "indépendant" in desc_lower or "independent" in desc_lower:
        characteristics.append("independent alternative comics")
    if "jeunesse" in desc_lower or "enfant" in desc_lower:
        characteristics.append("children's books")
    if "manga" in desc_lower:
        characteristics.append("manga publisher")
    if "comics" in desc_lower:
        characteristics.append("american comics")
    if "bande dessinée" in desc_lower or "bd" in desc_lower:
        characteristics.append("franco-belgian comics")

    # Notable series or authors
    if "tintin" in desc_lower or "hergé" in desc_lower:
        characteristics.append("ligne claire style like Tintin")
    if "spirou" in desc_lower or "franquin" in desc_lower:
        characteristics.append("classic belgian comics")
    if "marvel" in desc_lower:
        characteristics.append("Marvel superheroes")
    if "dc" in desc_lower:
        characteristics.append("DC Comics superheroes")

    # Genre indicators
    genres = []
    if any(word in desc_lower for word in ["fantasy", "fantastique", "heroic-fantasy"]):
        genres.append("fantasy adventures")
    if any(word in desc_lower for word in ["science-fiction", "sci-fi", "futuriste"]):
        genres.append("science fiction")
    if any(word in desc_lower for word in ["polar", "thriller", "detective", "policier"]):
        genres.append("crime/noir detective stories")
    if any(word in desc_lower for word in ["western"]):
        genres.append("western stories")
    if any(word in desc_lower for word in ["humour", "humor", "comique"]):
        genres.append("humor and comedy")
    if any(word in desc_lower for word in ["historique", "historical"]):
        genres.append("historical narratives")
    if any(word in desc_lower for word in ["aventure", "adventure"]):
        genres.append("adventure stories")

    # Build enriched description
    parts = []
    if characteristics:
        parts.append(f"Specializes in {', '.join(characteristics)}")
    if genres:
        parts.append(f"Known for {', '.join(genres)}")

    if parts:
        return f"{existing_description}\n\nKey characteristics: {' and '.join(parts)}."

    return existing_description


def create_specific_prompt(pub_info: Dict[str, Any], enriched_desc: str) -> str:
    """
    Create a very specific prompt using publisher name, description, and key works.
    Focus on landscapes/scenes inspired by their catalog, not generic cities.
    """
    name = pub_info.get("name", "")
    description = pub_info.get("description", "")
    desc_lower = description.lower()

    # Extract key series/characters from description
    key_works = []

    # Famous series/characters detection
    famous_series = {
        "tintin": "Tintin adventures world",
        "spirou": "Spirou and Fantasio adventures",
        "astérix": "Gaulish village and Roman empire",
        "lucky luke": "Wild West frontier towns",
        "blake et mortimer": "1950s adventure locations",
        "corto maltese": "maritime adventure ports",
        "thorgal": "Norse mythology landscapes",
        "blacksad": "film noir 1950s America",
        "xiii": "conspiracy thriller locations",
        "largo winch": "international business world",
        "sillage": "sci-fi alien worlds",
        "valerian": "futuristic space cities",
        "marsupilami": "exotic jungle adventures",
        "gaston": "chaotic office scenes",
        "boule et bill": "suburban family home",
        "cedric": "school and neighborhood",
        "titeuf": "schoolyard and home",
        "seuls": "post-apocalyptic city",
        "lastman": "urban street fighting world",
    }

    for series, setting in famous_series.items():
        if series in desc_lower:
            key_works.append(setting)

    # Check for very specific publisher styles with character context
    if "tintin" in desc_lower or "hergé" in desc_lower:
        return f"clean ligne claire Tintin-style panorama, {name} publisher header, European travel adventure locations, clear line illustration with precise architecture, Hergé aesthetic, vintage 1950s color palette, exotic destinations, no text"

    if "spirou" in desc_lower or "franquin" in desc_lower:
        return f"dynamic Spirou-style adventure scene, {name} publisher, Marcinelle school comic art, energetic Belgian comic aesthetic, vibrant colors, cartoon adventure locations, Franquin-inspired, no text"

    if "marvel" in name.lower() and "marvel" not in desc_lower:
        # It's actually Marvel publisher
        return "Marvel superhero city skyline, iconic superhero silhouettes, dynamic action composition, New York cityscape, comic book art"

    if "dc" in name.lower() and "dc" not in desc_lower:
        return "DC Comics Gotham and Metropolis skyline, superhero emblems, dramatic urban landscape, comic book illustration"

    # Genre-based visuals (non-character focused)
    if "manga" in desc_lower:
        if "shonen" in desc_lower:
            return "dynamic manga action scene landscape, Japanese urban environment, anime art style, speed lines and energy"
        elif "shojo" in desc_lower:
            return "beautiful shojo manga flower garden, romantic atmosphere, sparkles and roses, pastel colors"
        else:
            return "Japanese manga style landscape, Tokyo street scene, anime aesthetic, detailed architectural background"

    if "children" in desc_lower or "jeunesse" in desc_lower:
        return "whimsical children's book illustration, friendly forest landscape, colorful storybook village, soft watercolor style"

    if "crime" in desc_lower or "noir" in desc_lower or "policier" in desc_lower:
        return "film noir city at night, rain-soaked streets, vintage 1940s architecture, dramatic shadows, detective atmosphere"

    if "fantasy" in desc_lower or "fantastique" in desc_lower:
        return "epic fantasy landscape, medieval castle on mountain, magical forest, mystical atmosphere, detailed fantasy illustration"

    if "sci-fi" in desc_lower or "science-fiction" in desc_lower:
        return "futuristic sci-fi cityscape, advanced technology, flying vehicles, neon lights, cyberpunk atmosphere"

    if "western" in desc_lower:
        return "western desert landscape, old west saloon town, dusty frontier, dramatic sunset, classic western illustration"

    if "historical" in desc_lower or "historique" in desc_lower:
        return "historical period architecture, vintage European city scene, accurate historical detail, classical illustration"

    if "humor" in desc_lower or "humour" in desc_lower:
        return "whimsical cartoon town, exaggerated funny architecture, bright cheerful colors, humor comic strip style"

    # Build prompt from publisher description
    prompt_parts = []

    # Start with publisher context
    prompt_parts.append(f"{name} publisher header illustration")

    # Add specific settings from key works
    if key_works:
        prompt_parts.append(f"featuring {key_works[0]}")

    # Franco-Belgian style
    if any(word in desc_lower for word in ["franco", "belgian", "belge", "français", "bande dessinée", "bd"]):
        prompt_parts.append("Franco-Belgian bande dessinée art style")

        # Determine subject from description content - VARY THE SUBJECTS
        if any(word in desc_lower for word in ["aventure", "exploration", "voyage", "travel"]):
            prompt_parts.append("exotic adventure landscape panorama, ancient ruins and tropical forests")
        elif any(word in desc_lower for word in ["médiéval", "château", "moyen-âge", "knight", "castle"]):
            prompt_parts.append("medieval castle on hilltop with countryside below")
        elif any(word in desc_lower for word in ["pirate", "maritime", "mer", "ocean", "sea"]):
            prompt_parts.append("maritime harbor with sailing ships and coastal scenery")
        elif any(word in desc_lower for word in ["space", "espace", "cosmos", "planet"]):
            prompt_parts.append("cosmic space scene with planets and stars")
        elif any(word in desc_lower for word in ["nature", "forest", "montagne", "mountain"]):
            prompt_parts.append("natural landscape with forests and mountains")
        else:
            # Use hash for variety
            import hashlib
            name_hash = int(hashlib.md5(name.encode()).hexdigest(), 16) % 5
            varied_subjects = [
                "European countryside village panorama with rolling hills",
                "dramatic mountain landscape with valley below",
                "coastal seaside scenery with cliffs and ocean",
                "peaceful forest clearing with sunlight filtering through trees",
                "abstract artistic interpretation with symbolic elements"
            ]
            prompt_parts.append(varied_subjects[name_hash])

    # Manga style
    elif "manga" in desc_lower or "japon" in desc_lower:
        prompt_parts.append("manga illustration style")
        prompt_parts.append("Japanese setting with anime aesthetic")

    # Children's books
    elif any(word in desc_lower for word in ["jeunesse", "enfant", "kids"]):
        prompt_parts.append("children's book illustration style")
        prompt_parts.append("friendly colorful storybook world")

    # Noir/thriller
    elif any(word in desc_lower for word in ["noir", "policier", "thriller"]):
        prompt_parts.append("film noir illustration")
        prompt_parts.append("dark moody urban night scene")

    # Fantasy
    elif any(word in desc_lower for word in ["fantasy", "fantastique", "magic"]):
        prompt_parts.append("fantasy illustration art")
        prompt_parts.append("epic magical landscape with castles")

    # Sci-fi
    elif any(word in desc_lower for word in ["science-fiction", "sci-fi", "futur"]):
        prompt_parts.append("science fiction illustration")
        prompt_parts.append("futuristic technological cityscape")

    # Independent/alternative
    elif "independent" in desc_lower or "indépendant" in desc_lower or "alternatif" in desc_lower:
        prompt_parts.append("alternative indie comic art")
        prompt_parts.append("artistic experimental composition")

    # Generic European comic - add variety
    else:
        prompt_parts.append("European comic art style")
        # Vary based on hash
        import hashlib
        name_hash = int(hashlib.md5(name.encode()).hexdigest(), 16) % 4
        varied_scenes = [
            "scenic landscape with natural elements",
            "abstract artistic composition with colors and shapes",
            "atmospheric environment with dramatic lighting",
            "panoramic vista with depth and perspective"
        ]
        prompt_parts.append(varied_scenes[name_hash])

    # Add quality modifiers
    prompt_parts.append("wide panoramic banner format")
    prompt_parts.append("professional illustration")
    prompt_parts.append("highly detailed")
    prompt_parts.append("no text, no words")

    return ", ".join(prompt_parts)


def process_publishers(limit: int = 0, dry_run: bool = False):
    """Process publishers and enrich their descriptions."""

    incomplete_dir = Path("_incomplete")
    publishers = sorted([p for p in incomplete_dir.iterdir() if p.is_dir()])

    if limit > 0:
        publishers = publishers[:limit]

    print(f"Processing {len(publishers)} publishers")
    print("=" * 80)

    enriched_data = {}

    for idx, pub_dir in enumerate(publishers, 1):
        info_file = pub_dir / "publisher-info.json"
        if not info_file.exists():
            continue

        with open(info_file, "r", encoding="utf-8") as f:
            pub_info = json.load(f)

        name = pub_info.get("name", pub_dir.name)
        description = pub_info.get("description", "")

        print(f"\n[{idx}/{len(publishers)}] {name}")

        # Enrich description
        enriched_desc = search_publisher_info(name, description)

        # Create specific prompt
        specific_prompt = create_specific_prompt(pub_info, enriched_desc)

        print(f"  Prompt: {specific_prompt[:80]}...")

        enriched_data[name] = {
            "path": str(pub_dir),
            "enriched_description": enriched_desc,
            "specific_prompt": specific_prompt
        }

        if not dry_run:
            # Save enriched prompt
            prompt_file = pub_dir / "ai_prompt.txt"
            with open(prompt_file, "w", encoding="utf-8") as f:
                f.write(specific_prompt)

    # Save all enriched data
    if not dry_run:
        output_file = Path(".scripts") / "enriched_prompts.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(enriched_data, f, indent=2, ensure_ascii=False)
        print(f"\n✓ Saved enriched prompts to {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Enrich publisher descriptions for better image generation"
    )
    parser.add_argument("--limit", type=int, default=0, help="Limit number of publishers")
    parser.add_argument("--dry-run", action="store_true", help="Don't save files")

    args = parser.parse_args()

    process_publishers(limit=args.limit, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
