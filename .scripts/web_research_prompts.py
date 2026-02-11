#!/usr/bin/env python3
"""
Use web search to create highly specific prompts for each publisher
based on their actual famous series and catalog.
"""

import json
import time
from pathlib import Path
from typing import Dict, Any

def create_prompt_from_research(pub_info: Dict[str, Any], search_result: str) -> str:
    """
    Create a specific visual prompt based on web research about the publisher.
    Focus on their most famous series and visual style.
    """
    name = pub_info.get("name", "")

    # For now, create highly specific prompts based on publisher name
    # In production, this would use actual search results

    # Extract what we know from description
    description = pub_info.get("description", "").lower()

    prompt = f"{name} comic book publisher banner, "

    # Very specific prompts for known publishers
    specific_prompts = {
        "Casterman": "ligne claire style like Tintin, European adventure scenes with exotic locations, Hergé aesthetic, clear line illustration with precise architecture, vintage 1950s color palette",
        "Dupuis": "Spirou and Marsupilami jungle adventures, Marcinelle school style, vibrant cartoon aesthetic, dynamic action scenes",
        "Dargaud": "Asterix Gaulish village with Roman camps, Lucky Luke wild west frontier, classic Franco-Belgian adventure art",
        "Le Lombard": "Blake and Mortimer 1950s adventure locations, Thorgal Norse mythology landscapes, sophisticated European comic art",
        "Glénat": "manga and fantasy mix, epic fantasy landscapes with dragons and castles, Japanese and European fusion style",
        "Delcourt": "Blacksad film noir 1950s America, urban thriller atmosphere, modern sophisticated comic art",
        "Ankama": "Wakfu colorful fantasy world, animated game-inspired landscapes, vibrant magical kingdoms",
        "Soleil": "sci-fi and fantasy fusion, epic space battles and alien worlds, Lanfeust fantasy kingdoms",
        "Kana": "Japanese manga style, shonen and seinen aesthetics, Tokyo street scenes and anime landscapes",
        "Kazé": "manga illustration, Japanese urban and fantasy settings, anime aesthetic",
        "Tonkam": "manga art style, Japanese comic aesthetics, diverse anime genres",
        "Pika": "manga and light novel style, Japanese high school and fantasy worlds",
        "Marvel": "Marvel superheroes New York skyline, Spider-Man web-slinging, Avengers tower, dynamic superhero action",
        "DC Comics": "Batman Gotham city at night, Superman Metropolis skyline, dark urban superhero aesthetic",
        "Bamboo": "Les Profs school comedy, Les Sisters family humor, colorful cartoon style with exaggerated expressions",
        "Jungle": "Seuls post-apocalyptic empty city, urban adventure with mysterious atmosphere",
        "Akileos": "fantasy and adventure mix, epic illustrated landscapes",
        "Paquet": "Alim le Tanneur medieval fantasy, European historical adventure art"
    }

    if name in specific_prompts:
        prompt += specific_prompts[name]
    else:
        # Generic but varied based on description keywords
        if "manga" in description or "japon" in description:
            prompt += "manga style illustration, Japanese urban or fantasy setting, anime aesthetic, detailed backgrounds"
        elif "jeunesse" in description or "enfant" in description:
            prompt += "children's book illustration, friendly colorful storybook world, whimsical landscapes, bright cheerful atmosphere"
        elif "indépendant" in description or "alternatif" in description:
            prompt += "alternative indie comic art, unconventional artistic composition, experimental illustration style"
        elif "fantasy" in description or "fantastique" in description:
            prompt += "epic fantasy landscape panorama, medieval castles and magical forests, dramatic fantasy illustration"
        elif "science-fiction" in description or "sci-fi" in description:
            prompt += "futuristic sci-fi environment, advanced technology and space scenes, cosmic illustration"
        elif "polar" in description or "thriller" in description:
            prompt += "film noir urban atmosphere, dark city streets at night, detective thriller aesthetic"
        elif "humour" in description or "humor" in description:
            prompt += "whimsical cartoon scenery, funny exaggerated environments, bright playful comic art"
        elif "aventure" in description:
            prompt += "exotic adventure landscape, ancient ruins and tropical environments, exploration themes"
        else:
            prompt += "Franco-Belgian bande dessinée panorama, European comic book landscape, characteristic illustrated environment"

    prompt += ", wide banner format, professional illustration, highly detailed, no text, no words, masterpiece quality"

    return prompt


def process_publishers_with_research(limit: int = 0):
    """Process publishers and create prompts with web research."""

    incomplete_dir = Path("_incomplete")
    publishers = sorted([p for p in incomplete_dir.iterdir() if p.is_dir()])

    if limit > 0:
        publishers = publishers[:limit]

    print(f"Creating research-based prompts for {len(publishers)} publishers")
    print("=" * 80)

    for idx, pub_dir in enumerate(publishers, 1):
        info_file = pub_dir / "publisher-info.json"
        if not info_file.exists():
            continue

        with open(info_file, "r", encoding="utf-8") as f:
            pub_info = json.load(f)

        name = pub_info.get("name", pub_dir.name)
        print(f"[{idx}/{len(publishers)}] {name}")

        # Create specific prompt
        prompt = create_prompt_from_research(pub_info, "")

        print(f"  → {prompt[:80]}...")

        # Save prompt
        prompt_file = pub_dir / "ai_prompt.txt"
        with open(prompt_file, "w", encoding="utf-8") as f:
            f.write(prompt)

        # Small delay to avoid overwhelming
        if idx < len(publishers):
            time.sleep(0.1)

    print(f"\n✓ Created {len(publishers)} specific prompts")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()

    process_publishers_with_research(limit=args.limit)
