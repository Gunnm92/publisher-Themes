#!/usr/bin/env python3
"""
Generate publisher headers using ComfyUI.
This script reads publisher metadata and generates appropriate header images.
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
WORKFLOW_FILE = "workflow_header_bd.json"


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
    Generate a text prompt for creating a publisher header image.
    Creates artistic scene descriptions based on publisher characteristics.
    """
    name = pub_info.get("name", "Unknown Publisher")
    description = pub_info.get("description", "")
    country = pub_info.get("country", "")

    # Extract theme colors
    theme = pub_info.get("theme", {})
    bg_color = theme.get("bg", "#000000")
    text_color = theme.get("text", "#ffffff")

    # Analyze description for keywords to determine style
    desc_lower = description.lower()

    # Determine artistic style based on publisher characteristics
    style_keywords = []
    atmosphere_keywords = []

    # Country-specific styles
    if country == "FR":
        style_keywords.append("Franco-Belgian comic art style")
        style_keywords.append("European bande dessinée aesthetic")
    elif country == "JP":
        style_keywords.append("manga style")
        style_keywords.append("Japanese comic art")
    elif country == "US":
        style_keywords.append("American comic book style")
        style_keywords.append("superhero comic aesthetic")

    # Genre detection
    if any(word in desc_lower for word in ["humour", "humor", "comique", "drôle"]):
        atmosphere_keywords.extend(["playful", "humorous", "lighthearted", "fun"])
    if any(word in desc_lower for word in ["jeunesse", "enfant", "kids", "children"]):
        atmosphere_keywords.extend(["colorful", "friendly", "whimsical", "cheerful"])
        style_keywords.append("children's book illustration style")
    if any(word in desc_lower for word in ["noir", "dark", "thriller", "policier"]):
        atmosphere_keywords.extend(["dramatic", "noir", "mysterious", "shadowy"])
        style_keywords.append("film noir aesthetic")
    if any(word in desc_lower for word in ["fantasy", "fantastique", "magic", "medieval"]):
        atmosphere_keywords.extend(["epic", "fantastical", "magical", "adventurous"])
        style_keywords.append("fantasy art style")
    if any(word in desc_lower for word in ["science-fiction", "sci-fi", "futuriste"]):
        atmosphere_keywords.extend(["futuristic", "technological", "cosmic"])
        style_keywords.append("science fiction illustration")
    if any(word in desc_lower for word in ["indépendant", "independent", "alternatif", "underground"]):
        atmosphere_keywords.extend(["artistic", "unconventional", "creative", "bold"])
        style_keywords.append("independent comic art")

    # Build the artistic prompt
    style_str = ", ".join(style_keywords[:3]) if style_keywords else "professional comic book art"
    atmosphere_str = ", ".join(atmosphere_keywords[:3]) if atmosphere_keywords else "dynamic and engaging"

    # Color theme description
    color_desc = f"dominant colors {bg_color} and {text_color}"

    # Create a rich artistic scene prompt
    prompt = f"""<scene_description>
An artistic banner illustration for {name}, a comic book publisher.
Style: {style_str}, high-quality digital illustration, professional graphic design.
Atmosphere: {atmosphere_str}, visually impactful, captures the essence of the publisher's catalog.
Composition: Wide panoramic banner format, dynamic scene with depth and visual interest.
Elements: Artistic interpretation of comic book themes, narrative visual storytelling, professional branding aesthetic.
Colors: {color_desc}, vibrant palette, excellent contrast.
Quality: Masterpiece quality, extremely detailed, professional grade artwork.
Context: {description[:150] if description else 'Professional comic book publisher'}.
</scene_description>"""

    return prompt


def create_comfyui_prompt(
    workflow: Dict[str, Any],
    user_prompt: str,
    caption: str,
    seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    Modify the workflow with custom prompts.
    """
    # Clone the workflow
    prompt = json.loads(json.dumps(workflow))

    # Update the user prompt (node 48)
    if "48" in prompt:
        prompt["48"]["inputs"]["value"] = user_prompt

    # Update the caption (node 44)
    if "44" in prompt:
        prompt["44"]["inputs"]["value"] = caption

    # Update seed for randomness
    if seed is None:
        seed = random.randint(0, 0xffffffffffffffff)

    if "41:3" in prompt:
        prompt["41:3"]["inputs"]["seed"] = seed

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
            # Check if execution is complete
            if history[prompt_id].get("status", {}).get("completed", False):
                return True

            # Check for errors
            if "error" in history[prompt_id]:
                print(f"Error in execution: {history[prompt_id]['error']}")
                return False

        time.sleep(2)

    print("Timeout waiting for completion")
    return False


def download_image(prompt_id: str, output_path: Path) -> bool:
    """Download the generated image."""
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
                    urllib.request.urlretrieve(url, output_path)
                    print(f"Downloaded image to {output_path}")
                    return True
                except Exception as e:
                    print(f"Error downloading image: {e}")
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
        print(f"No publisher-info.json found in {publisher_dir}")
        return False

    publisher_name = pub_info.get("name", publisher_dir.name)
    print(f"\nProcessing: {publisher_name}")

    # Check if header already exists
    header_jpg = publisher_dir / "header.jpg"
    header_png = publisher_dir / "header.png"

    if header_jpg.exists() or header_png.exists():
        print(f"  → Header already exists, skipping")
        return True

    # Generate prompts
    user_prompt = generate_prompt_for_publisher(pub_info)
    caption = f"Professional header banner for {publisher_name} comic book publisher"

    print(f"  → Prompt: {user_prompt[:100]}...")

    if dry_run:
        print(f"  → [DRY RUN] Would generate header")
        return True

    # Create ComfyUI prompt
    comfy_prompt = create_comfyui_prompt(workflow, user_prompt, caption)

    # Queue the prompt
    result = queue_prompt(comfy_prompt)
    prompt_id = result.get("prompt_id")

    if not prompt_id:
        print(f"  → Failed to queue prompt")
        return False

    print(f"  → Queued with ID: {prompt_id}")

    # Wait for completion
    if not wait_for_completion(prompt_id):
        print(f"  → Generation failed or timed out")
        return False

    print(f"  → Generation complete")

    # Download the image
    output_path = publisher_dir / "header_generated.jpg"
    if download_image(prompt_id, output_path):
        print(f"  → Saved to {output_path}")
        return True
    else:
        print(f"  → Failed to download image")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Generate publisher headers using ComfyUI"
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
        default=5,
        help="Delay in seconds between generations"
    )

    args = parser.parse_args()

    # Load workflow
    workflow_path = Path(args.workflow)
    if not workflow_path.exists():
        print(f"Error: Workflow file not found: {workflow_path}")
        return 1

    workflow = load_workflow(str(workflow_path))
    print(f"Loaded workflow from {workflow_path}")

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

    print(f"\nProcessing {len(publishers)} publishers")
    print("=" * 80)

    success_count = 0
    failed_count = 0

    for idx, pub_dir in enumerate(publishers, 1):
        print(f"\n[{idx}/{len(publishers)}]")

        if generate_header_for_publisher(pub_dir, workflow, args.dry_run):
            success_count += 1
        else:
            failed_count += 1

        # Delay between generations to avoid overwhelming ComfyUI
        if idx < len(publishers) and not args.dry_run:
            print(f"  → Waiting {args.delay} seconds...")
            time.sleep(args.delay)

    print("\n" + "=" * 80)
    print(f"SUMMARY")
    print("=" * 80)
    print(f"Total processed: {len(publishers)}")
    print(f"Successful: {success_count}")
    print(f"Failed: {failed_count}")

    return 0


if __name__ == "__main__":
    exit(main())
