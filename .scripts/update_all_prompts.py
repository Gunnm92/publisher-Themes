#!/usr/bin/env python3
"""
Manually update all ai_prompt.txt files based on publisher-info.json descriptions.
This processes all remaining publishers efficiently.
"""
import json
from pathlib import Path

# Publisher-specific prompts based on their descriptions
CUSTOM_PROMPTS = {
    "Dédales Éditions": "Angoulême art school aesthetics, young artists collective BD, experimental graphic creations, thematic annual review illustrations, Charente artist association atmosphere, contemporary sequential art, wide panoramic banner, no text",

    "De La Martinière Jeunesse": "premium French youth publishing, quality children's illustrated books, educational documentaries for kids, elegant juvenile literature aesthetics, refined graphic design, wide panoramic banner, no text",

    "Denoël": "Denoël Graphic literary BD, science fiction Philip K. Dick and Ray Bradbury atmosphere, Sempé and Topor humor illustrations, engaged literature aesthetics, thriller and fantasy novels, dark contemporary themes, wide panoramic banner, no text",

    "Des ronds dans l'O": "independent quirky BD publishing, freedom of expression comics, unconventional storytelling aesthetics, playful circular logo inspired compositions, bold artistic liberty, wide panoramic banner, no text",

    "Desinge - Hugo & Cie": "graphic design label aesthetics, BD and illustration focus, Hugo publishing imprint style, contemporary visual narratives, modern illustrated storytelling, wide panoramic banner, no text",

    "Dominique et compagnie": "Quebec youth literature 0-12 years, francophone children's books, playful learning illustrations, colorful educational stories, international translations success, vibrant kid-friendly aesthetics, wide panoramic banner, no text",

    "Drugstore": "Drugstore Glénat imprint, independent comics reprints, alternative BD collections, eclectic catalog mix, wide panoramic banner, no text",

    "Dynamite": "Dynamite Entertainment comics, The Boys and Vampirella series, action-packed pulp adventures, Red Sonja and The Shadow characters, explosive American comic style, wide panoramic banner, no text",

    "Édition pirate": "pirate publishing aesthetics, underground unauthorized editions, rebellious counter-culture BD, bootleg comic art style, subversive illustration atmosphere, wide panoramic banner, no text",

    "Éditions Bréal": "educational textbooks and BD, pedagogical illustrations, scholarly publishing aesthetics, academic learning materials, instructional graphics style, wide panoramic banner, no text",

    "Éditions Carabas": "independent literary publishing, intimate storytelling BD, artisanal book aesthetics, small press quality, personal narrative illustrations, wide panoramic banner, no text",

    "Éditions de la Séguinière": "Jean Tabary Iznogoud publisher, Francis Slomka editorial vision, 1979 independent BD house, classic French humor comics, wide panoramic banner, no text",

    "Editions du Miroir": "mirror-themed publishing, reflective narrative aesthetics, philosophical BD themes, introspective illustration style, conceptual artistic composition, wide panoramic banner, no text",

    "Ego comme X": "X-rated adult BD, erotic comics aesthetics, mature sensual illustrations, sophisticated adult graphic novels, explicit artistic expression, wide panoramic banner, no text",

    "Emmanuel Proust Éditions": "manga and manhwa specialist, Asian comics in France, Japanese and Korean BD imports, anime-influenced aesthetics, dynamic manga composition, wide panoramic banner, no text",

    "EP Media": "media publishing group aesthetics, multimedia BD projects, contemporary editorial design, cross-platform storytelling, modern graphic communications, wide panoramic banner, no text",

    "Eyrolles": "technical and professional books, computer programming manuals aesthetics, educational technology illustrations, IT and business graphics, instructional design style, wide panoramic banner, no text",

    "Filidalo": "niche BD publishing, specialized comic themes, targeted audience aesthetics, focused editorial line, wide panoramic banner, no text",

    "Flammarion": "prestigious French publishing house, literary excellence aesthetics, classic book design tradition, sophisticated editorial standards, cultural heritage atmosphere, wide panoramic banner, no text",

    "Fleurus": "Catholic youth publishing, religious children's books, family values BD, spiritual education illustrations, traditional wholesome aesthetics, wide panoramic banner, no text",

    "Fordis": "distribution and publishing, BD retail aesthetics, comic book merchandising atmosphere, wide panoramic banner, no text",

    "France Loisirs": "book club editions, popular literature BD, mass market publishing aesthetics, accessible reading collections, wide panoramic banner, no text",
}

def update_prompts():
    """Update prompts for publishers in CUSTOM_PROMPTS"""
    incomplete_dir = Path("_incomplete")

    updated_count = 0
    for pub_name, prompt in CUSTOM_PROMPTS.items():
        # Find publisher directory
        pub_dirs = list(incomplete_dir.glob(f"*"))
        matching_dir = None

        for pub_dir in pub_dirs:
            if not pub_dir.is_dir():
                continue
            info_file = pub_dir / "publisher-info.json"
            if info_file.exists():
                with open(info_file, "r", encoding="utf-8") as f:
                    info = json.load(f)
                if info.get("name") == pub_name:
                    matching_dir = pub_dir
                    break

        if matching_dir:
            prompt_file = matching_dir / "ai_prompt.txt"
            with open(prompt_file, "w", encoding="utf-8") as f:
                f.write(prompt)
            print(f"✓ Updated: {pub_name}")
            updated_count += 1
        else:
            print(f"✗ Not found: {pub_name}")

    print(f"\nUpdated {updated_count} prompts")

if __name__ == "__main__":
    update_prompts()
