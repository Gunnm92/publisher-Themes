#!/usr/bin/env python3
"""
Generate publisher headers using ComfyUI with Juggernaut XL.
Optimized for SDXL-based models with simplified prompts.
"""

import argparse
import json
import os
import random
import time
import urllib.request
import urllib.parse
from pathlib import Path
from typing import Dict, Any, Optional

# ComfyUI configuration
COMFYUI_URL = "http://10.1.1.1:8188"
WORKFLOW_FILE = "workflow_juggernaut_xl.json"


def load_workflow(workflow_path: str) -> Dict[str, Any]:
    """Load ComfyUI workflow JSON."""
    with open(workflow_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_publisher_info(publisher_dir: Path) -> Optional[Dict[str, Any]]:
    """Load publisher-info.json from a directory."""
    info_file = publisher_dir / "publisher-info.json"
    if not info_file.exists():
        return None

    try:
        with open(info_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {info_file}: {e}")
        return None


def generate_prompt_for_publisher(pub_info: Dict[str, Any]) -> str:
    """
    Generate an optimized prompt for Juggernaut XL.
    Creates VARIED compositions: landscapes, objects, abstract, scenes, etc.
    """
    name = pub_info.get("name", "Unknown Publisher")
    description = pub_info.get("description", "")
    country = pub_info.get("country", "")

    # Analyze description for style keywords
    desc_lower = description.lower()

    # Use hash of publisher name to get consistent but varied prompts
    import hashlib
    name_hash = int(hashlib.md5(name.encode()).hexdigest(), 16)
    variety_seed = name_hash % 7  # 7 different composition types

    # Build specific subject matter with VARIETY
    subject_tags = []
    style_tags = []
    atmosphere_tags = []
    negative_avoid = ["superhero", "marvel", "dc comics"]  # What to avoid by default

    # Varied composition types based on hash
    composition_types = [
        "scenic landscape panorama",           # 0: Paysage
        "atmospheric cityscape",               # 1: Ville
        "collection of iconic objects",        # 2: Objets
        "abstract artistic composition",       # 3: Abstrait
        "dynamic character group scene",       # 4: Personnages
        "architectural environment",           # 5: Architecture
        "symbolic thematic elements"           # 6: Symbolique
    ]

    base_composition = composition_types[variety_seed]

    # Country-specific styles - BE VERY SPECIFIC
    if country == "FR":
        style_tags.extend([
            "Franco-Belgian bande dessinée style",
            "European comic art",
            "ligne claire illustration"
        ])
        subject_tags.append("European comic book scene")
        # Avoid American superhero style
        negative_avoid.extend(["American superhero", "spandex costumes"])
    elif country == "JP":
        style_tags.extend(["manga illustration", "Japanese comic art"])
        subject_tags.append("manga characters")
        negative_avoid.extend(["western comics", "superhero"])
    elif country == "BE":
        style_tags.extend(["Belgian comic style", "bande dessinée"])
        subject_tags.append("Belgian comic characters")
        negative_avoid.extend(["American superhero"])

    # Genre detection - VARIED SUBJECTS based on genre AND composition type
    if any(word in desc_lower for word in ["humour", "humor", "comique", "drôle"]):
        if variety_seed in [0, 1]:  # Landscape/cityscape
            subject_tags.insert(0, "whimsical cartoon city with funny details")
        elif variety_seed == 2:  # Objects
            subject_tags.insert(0, "collection of humorous cartoon props and gags")
        elif variety_seed == 3:  # Abstract
            subject_tags.insert(0, "playful abstract shapes and colors")
        else:  # Characters
            subject_tags.insert(0, "funny cartoon characters in comedic situation")
        atmosphere_tags.extend(["playful", "humorous", "lighthearted"])
        style_tags.append("humor comic art style")
        negative_avoid.extend(["serious", "dramatic"])

    if any(word in desc_lower for word in ["jeunesse", "enfant", "kids", "children", "young"]):
        if variety_seed in [0, 1]:
            subject_tags.insert(0, "magical children's storybook landscape")
        elif variety_seed == 2:
            subject_tags.insert(0, "colorful toys and friendly objects for kids")
        elif variety_seed == 3:
            subject_tags.insert(0, "cheerful abstract patterns and shapes")
        else:
            subject_tags.insert(0, "friendly colorful characters for children")
        atmosphere_tags.extend(["bright", "cheerful", "innocent"])
        style_tags.append("children's picture book art")
        negative_avoid.extend(["dark", "scary", "superhero"])

    if any(word in desc_lower for word in ["noir", "dark", "thriller", "policier", "crime"]):
        if variety_seed in [0, 1]:
            subject_tags.insert(0, "noir dark city street at night with rain")
        elif variety_seed == 2:
            subject_tags.insert(0, "detective's desk with gun, badge, and evidence")
        elif variety_seed == 3:
            subject_tags.insert(0, "shadowy abstract noir composition")
        else:
            subject_tags.insert(0, "noir detective silhouette in foggy street")
        atmosphere_tags.extend(["moody", "shadowy", "mysterious"])
        style_tags.append("film noir illustration style")
        negative_avoid.extend(["bright", "superhero"])

    if any(word in desc_lower for word in ["fantasy", "fantastique", "magic", "medieval", "dragon"]):
        if variety_seed in [0, 1]:
            subject_tags.insert(0, "epic fantasy landscape with castles and mountains")
        elif variety_seed == 2:
            subject_tags.insert(0, "magical items, swords, crystals and spell books")
        elif variety_seed == 3:
            subject_tags.insert(0, "mystical magical energy abstract composition")
        else:
            subject_tags.insert(0, "fantasy wizard and warriors in epic scene")
        atmosphere_tags.extend(["epic", "mystical", "fantastical"])
        style_tags.append("fantasy illustration art")
        negative_avoid.extend(["modern", "superhero"])

    if any(word in desc_lower for word in ["science-fiction", "sci-fi", "futuriste", "space"]):
        if variety_seed in [0, 1]:
            subject_tags.insert(0, "futuristic sci-fi cityscape with flying vehicles")
        elif variety_seed == 2:
            subject_tags.insert(0, "collection of sci-fi gadgets and technology")
        elif variety_seed == 3:
            subject_tags.insert(0, "cosmic nebula and stars abstract space")
        else:
            subject_tags.insert(0, "astronaut and alien scene in space station")
        atmosphere_tags.extend(["futuristic", "cosmic", "technological"])
        style_tags.append("sci-fi illustration")
        negative_avoid.extend(["fantasy", "superhero"])

    if any(word in desc_lower for word in ["western", "cowboy"]):
        if variety_seed in [0, 1]:
            subject_tags.insert(0, "western desert landscape with saloon town")
        elif variety_seed == 2:
            subject_tags.insert(0, "cowboy hat, gun, horseshoe and western items")
        else:
            subject_tags.insert(0, "cowboy silhouette in desert sunset")
        atmosphere_tags.extend(["rugged", "dusty"])
        style_tags.append("western comic art")
        negative_avoid.extend(["superhero", "modern"])

    if any(word in desc_lower for word in ["indépendant", "independent", "alternatif", "underground", "avant-garde"]):
        if variety_seed in [0, 1, 2]:
            subject_tags.insert(0, "abstract artistic collage composition")
        else:
            subject_tags.insert(0, "unconventional experimental art illustration")
        atmosphere_tags.extend(["unconventional", "artistic", "experimental"])
        style_tags.append("alternative underground comic art")
        negative_avoid.extend(["mainstream", "superhero"])

    if any(word in desc_lower for word in ["manga", "japanese", "japon"]):
        if variety_seed in [0, 1]:
            subject_tags.insert(0, "Japanese town landscape anime style")
        elif variety_seed == 2:
            subject_tags.insert(0, "collection of manga items and symbols")
        else:
            subject_tags.insert(0, "manga characters in anime style scene")
        style_tags.append("manga illustration")
        negative_avoid.extend(["western comics", "superhero"])

    if any(word in desc_lower for word in ["adventure", "aventure"]):
        if variety_seed in [0, 1]:
            subject_tags.insert(0, "exotic adventure landscape with ancient ruins")
        elif variety_seed == 2:
            subject_tags.insert(0, "treasure map, compass and adventure equipment")
        else:
            subject_tags.insert(0, "adventurer explorer discovering ancient temple")
        atmosphere_tags.append("adventurous")

    # If still no specific subject, use variety-based composition
    if not subject_tags:
        name_lower = name.lower()
        if "manga" in name_lower or "tonkam" in name_lower or "kana" in name_lower:
            if variety_seed in [0, 1]:
                subject_tags.append("Japanese street scene manga style")
            else:
                subject_tags.append("manga style characters")
            style_tags.append("Japanese manga art")
        elif "marvel" in name_lower or "dc" in name_lower:
            if variety_seed in [0, 1]:
                subject_tags.append("superhero city skyline")
            else:
                subject_tags.append("superhero action scene")
        else:
            # Generic varied compositions based on type
            if variety_seed == 0:  # Landscape
                subject_tags.append("European countryside landscape illustration")
            elif variety_seed == 1:  # Cityscape
                subject_tags.append("European city street scene")
            elif variety_seed == 2:  # Objects
                subject_tags.append("collection of vintage European items")
            elif variety_seed == 3:  # Abstract
                subject_tags.append("artistic abstract composition")
            elif variety_seed == 5:  # Architecture
                subject_tags.append("European architecture and buildings")
            elif variety_seed == 6:  # Symbolic
                subject_tags.append("symbolic artistic elements")
            else:  # Characters
                subject_tags.append("European comic book characters")
            style_tags.append("bande dessinée illustration")

    # Build the optimized prompt
    subject_str = subject_tags[0] if subject_tags else "illustrated characters"
    style_str = ", ".join(style_tags[:2]) if style_tags else "professional comic book art"
    atmosphere_str = ", ".join(atmosphere_tags[:3]) if atmosphere_tags else "dynamic, vibrant"

    # Add explicit negative concepts in the positive prompt to guide away from them
    avoid_str = f"NOT {', NOT '.join(negative_avoid[:3])}" if negative_avoid else ""

    # SDXL-optimized prompt
    prompt = f"{subject_str}, {style_str}, wide panoramic banner composition, {atmosphere_str}, professional illustration, highly detailed, no text, no words, masterpiece, {avoid_str}"

    return prompt


def create_comfyui_prompt(
    workflow: Dict[str, Any],
    user_prompt: str,
    seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    Modify the SDXL workflow with custom prompt.
    """
    # Clone the workflow
    prompt = json.loads(json.dumps(workflow))

    # Update the positive prompt (node 6)
    if "6" in prompt:
        prompt["6"]["inputs"]["text"] = user_prompt

    # Update seed for randomness
    if seed is None:
        seed = random.randint(0, 0xffffffffffffffff)

    if "3" in prompt:
        prompt["3"]["inputs"]["seed"] = seed

    return prompt


def queue_prompt(prompt: Dict[str, Any], client_id: str = "") -> Dict[str, Any]:
    """Send a prompt to ComfyUI queue."""
    data = json.dumps({
        "prompt": prompt,
        "client_id": client_id
    }).encode('utf-8')

    req = urllib.request.Request(
        f"{COMFYUI_URL}/prompt",
        data=data,
        headers={'Content-Type': 'application/json'}
    )

    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read())
    except Exception as e:
        print(f"Error queuing prompt: {e}")
        return {}


def get_history(prompt_id: str) -> Dict[str, Any]:
    """Get the execution history for a prompt."""
    try:
        with urllib.request.urlopen(f"{COMFYUI_URL}/history/{prompt_id}") as response:
            return json.loads(response.read())
    except Exception as e:
        print(f"Error getting history: {e}")
        return {}


def wait_for_completion(prompt_id: str, timeout: int = 300) -> bool:
    """Wait for ComfyUI to complete the generation."""
    start_time = time.time()

    while time.time() - start_time < timeout:
        history = get_history(prompt_id)

        if prompt_id in history:
            # Check if there are outputs
            if history[prompt_id].get("outputs"):
                return True

            # Check for errors
            if "error" in history[prompt_id].get("status", {}):
                print(f"Error in execution: {history[prompt_id]['status']['error']}")
                return False

        time.sleep(2)

    print("Timeout waiting for completion")
    return False


def download_image(prompt_id: str, output_path: Path) -> bool:
    """Download the generated image and resize to 2200x400."""
    from PIL import Image
    import io

    history = get_history(prompt_id)

    if prompt_id not in history:
        print("Prompt not found in history")
        return False

    # Find the output image
    outputs = history[prompt_id].get("outputs", {})

    for node_id, node_output in outputs.items():
        if "images" in node_output:
            for image in node_output["images"]:
                filename = image["filename"]
                subfolder = image.get("subfolder", "")
                image_type = image.get("type", "output")

                # Build URL to download image
                params = {
                    "filename": filename,
                    "subfolder": subfolder,
                    "type": image_type
                }
                url = f"{COMFYUI_URL}/view?{urllib.parse.urlencode(params)}"

                try:
                    # Download to temp path
                    temp_path = output_path.with_suffix('.tmp.jpg')
                    urllib.request.urlretrieve(url, temp_path)

                    # Resize to exact dimensions 2200x400
                    img = Image.open(temp_path)
                    img_resized = img.resize((2200, 400), Image.Resampling.LANCZOS)
                    img_resized.save(output_path, 'JPEG', quality=95)

                    # Clean up temp file
                    temp_path.unlink()

                    print(f"  → Downloaded and resized to 2200x400")
                    return True
                except Exception as e:
                    print(f"  → Error downloading/resizing: {e}")
                    return False

    return False


def generate_header_for_publisher(
    publisher_dir: Path,
    workflow: Dict[str, Any],
    dry_run: bool = False
) -> bool:
    """Generate a header image for a publisher."""
    pub_info = load_publisher_info(publisher_dir)

    if not pub_info:
        print(f"  → No publisher-info.json found")
        return False

    publisher_name = pub_info.get("name", publisher_dir.name)
    print(f"\n[{publisher_name}]")

    # Generate new headers even if one exists (to pick the best)
    # header_jpg = publisher_dir / "header.jpg"
    # header_png = publisher_dir / "header.png"

    # if header_jpg.exists() or header_png.exists():
    #     print(f"  → Header already exists, skipping")
    #     return True

    # Check for pre-enriched prompt
    prompt_file = publisher_dir / "ai_prompt.txt"
    if prompt_file.exists():
        with open(prompt_file, "r", encoding="utf-8") as f:
            user_prompt = f.read().strip()
        print(f"  → Using enriched prompt")
    else:
        # Generate prompt
        user_prompt = generate_prompt_for_publisher(pub_info)
    print(f"  → Prompt: {user_prompt[:80]}...")

    if dry_run:
        print(f"  → [DRY RUN] Would generate header")
        return True

    # Create ComfyUI prompt
    comfy_prompt = create_comfyui_prompt(workflow, user_prompt)

    # Queue the prompt
    result = queue_prompt(comfy_prompt)
    prompt_id = result.get("prompt_id")

    if not prompt_id:
        print(f"  → Failed to queue prompt")
        return False

    print(f"  → Queued (ID: {prompt_id[:8]}...)")

    # Wait for completion
    if not wait_for_completion(prompt_id):
        print(f"  → Generation failed or timed out")
        return False

    # Download the image directly as header.jpg
    output_path = publisher_dir / "header.jpg"
    if download_image(prompt_id, output_path):
        print(f"  → ✓ Success")
        return True
    else:
        print(f"  → ✗ Failed to download")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Generate publisher headers using Juggernaut XL"
    )
    parser.add_argument(
        "--workflow",
        default=WORKFLOW_FILE,
        help="Path to ComfyUI workflow JSON file"
    )
    parser.add_argument(
        "--publisher",
        help="Specific publisher directory to process"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Limit number of publishers to process (0 = all)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Don't actually generate images"
    )
    parser.add_argument(
        "--delay",
        type=int,
        default=3,
        help="Delay in seconds between generations"
    )

    args = parser.parse_args()

    # Load workflow
    workflow_path = Path(args.workflow)
    if not workflow_path.exists():
        print(f"Error: Workflow file not found: {workflow_path}")
        return 1

    workflow = load_workflow(str(workflow_path))
    print(f"Loaded workflow: {workflow_path.name}")

    # Get list of publishers to process
    incomplete_dir = Path("_incomplete")

    if args.publisher:
        publishers = [incomplete_dir / args.publisher]
    else:
        # Load missing headers list
        missing_file = Path(".scripts/missing_headers.json")
        if missing_file.exists():
            with open(missing_file, "r", encoding="utf-8") as f:
                missing_data = json.load(f)
                publishers = [
                    Path(pub["path"])
                    for pub in missing_data["publishers"]
                ]
        else:
            # Fall back to scanning directory
            publishers = [
                p for p in sorted(incomplete_dir.iterdir())
                if p.is_dir()
            ]

    # Apply limit
    if args.limit > 0:
        publishers = publishers[:args.limit]

    print(f"Processing {len(publishers)} publishers")
    print("=" * 60)

    success_count = 0
    failed_count = 0

    for idx, pub_dir in enumerate(publishers, 1):
        print(f"\n[{idx}/{len(publishers)}] ", end="")

        if generate_header_for_publisher(pub_dir, workflow, args.dry_run):
            success_count += 1
        else:
            failed_count += 1

        # Delay between generations
        if idx < len(publishers) and not args.dry_run:
            time.sleep(args.delay)

    print("\n" + "=" * 60)
    print(f"SUMMARY: {success_count} success, {failed_count} failed")

    return 0


if __name__ == "__main__":
    exit(main())
