#!/usr/bin/env python3
"""
Fetch publisher images (logos) for missing French publishers.
Uses Wikipedia/Wikidata to discover official websites and logo files,
then downloads a usable image and saves it as folder.jpg in each publisher folder.
"""

import argparse
import csv
import json
import os
import re
import time
import unicodedata
from html import escape as html_escape
from html.parser import HTMLParser
from io import BytesIO
from urllib.parse import urljoin

import requests
from PIL import Image

USER_AGENT = "publisher-themes-image-fetcher/1.0"
WIKI_SEARCH_LIMIT = 1
DEFAULT_SIZE = 312


class SimpleHTMLImageParser(HTMLParser):
    def __init__(self, base_url):
        super().__init__()
        self.base_url = base_url
        self.candidates = []

    def handle_starttag(self, tag, attrs):
        attrs_dict = {k.lower(): v for k, v in attrs if k}
        if tag.lower() == "base":
            href = attrs_dict.get("href")
            if href:
                self.base_url = href
            return

        if tag.lower() == "meta":
            prop = (attrs_dict.get("property") or attrs_dict.get("name") or "").lower()
            content = attrs_dict.get("content") or ""
            if prop in {"og:image", "twitter:image", "twitter:image:src"} and content:
                self._add_candidate(content, 8, "meta")
            return

        if tag.lower() == "link":
            rel = (attrs_dict.get("rel") or "").lower()
            href = attrs_dict.get("href") or ""
            if href and ("icon" in rel or "apple-touch-icon" in rel):
                self._add_candidate(href, 6, "icon")
            return

        if tag.lower() == "img":
            src = attrs_dict.get("src") or ""
            if not src:
                return
            alt = attrs_dict.get("alt") or ""
            klass = attrs_dict.get("class") or ""
            img_id = attrs_dict.get("id") or ""
            score = score_image_candidate(src, alt, klass, img_id)
            self._add_candidate(src, score, "img")

    def _add_candidate(self, url, score, source):
        if not url or url.startswith("data:"):
            return
        full_url = urljoin(self.base_url, url)
        self.candidates.append({"url": full_url, "score": score, "source": source})


class BdbaseEditorParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.entries = []
        self._last_image_src = None
        self._last_image_alt = None
        self._in_link = False
        self._link_text = ""

    def handle_starttag(self, tag, attrs):
        attrs_dict = {k.lower(): v for k, v in attrs if k}
        if tag.lower() == "img":
            src = attrs_dict.get("src") or ""
            if "/images/editeurs/" in src:
                self._last_image_src = src
                self._last_image_alt = attrs_dict.get("alt") or ""
            return
        if tag.lower() == "a":
            href = attrs_dict.get("href") or ""
            if href.startswith("/editeurs/"):
                self._in_link = True
                self._link_text = ""

    def handle_data(self, data):
        if self._in_link:
            self._link_text += data

    def handle_endtag(self, tag):
        if tag.lower() == "a" and self._in_link:
            name = self._link_text.strip() or self._last_image_alt
            if name and self._last_image_src:
                self.entries.append((name, self._last_image_src))
            self._in_link = False
            self._link_text = ""


class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        if data:
            self.parts.append(data)

    def get_text(self):
        return " ".join(self.parts)


def score_image_candidate(url, alt, klass, img_id):
    score = 0
    text = " ".join([url, alt, klass, img_id]).lower()
    if "logo" in text:
        score += 6
    if "brand" in text:
        score += 3
    if "header" in text or "banner" in text:
        score += 1
    if "sprite" in text or "icon" in text:
        score -= 2
    if url.lower().endswith((".png", ".jpg", ".jpeg", ".webp", ".gif")):
        score += 2
    if url.lower().endswith(".svg"):
        score -= 2
    return score


def sanitize_folder_name(name):
    name = name.strip()
    return re.sub(r"[\\/:*?\"<>|]", "-", name)


def normalize_key(name):
    text = unicodedata.normalize("NFKD", name)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.lower()
    text = text.replace("&", "and")
    text = re.sub(r"['`’]", "", text)
    text = re.sub(r"[^a-z0-9]+", " ", text).strip()
    return re.sub(r"\s+", " ", text)


def strip_tags(html_text):
    parser = TextExtractor()
    parser.feed(html_text)
    return re.sub(r"\s+", " ", parser.get_text()).strip()


def parse_publishers(md_path):
    publishers = []
    with open(md_path, "r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line.startswith("- "):
                publishers.append(line[2:].strip())
    return publishers


def wiki_search(name, lang="fr"):
    url = f"https://{lang}.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "list": "search",
        "format": "json",
        "srlimit": WIKI_SEARCH_LIMIT,
        "srsearch": name,
    }
    resp = requests.get(url, params=params, headers={"User-Agent": USER_AGENT}, timeout=20)
    resp.raise_for_status()
    data = resp.json()
    results = data.get("query", {}).get("search", [])
    if not results:
        return None
    return results[0]["title"]


def wiki_pageprops(title, lang="fr"):
    url = f"https://{lang}.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "prop": "pageprops",
        "format": "json",
        "titles": title,
    }
    resp = requests.get(url, params=params, headers={"User-Agent": USER_AGENT}, timeout=20)
    resp.raise_for_status()
    data = resp.json()
    pages = data.get("query", {}).get("pages", {})
    for page in pages.values():
        props = page.get("pageprops", {})
        return props.get("wikibase_item")
    return None


def wikidata_claims(qid):
    url = "https://www.wikidata.org/w/api.php"
    params = {
        "action": "wbgetentities",
        "format": "json",
        "ids": qid,
        "props": "claims",
    }
    resp = requests.get(url, params=params, headers={"User-Agent": USER_AGENT}, timeout=20)
    resp.raise_for_status()
    data = resp.json()
    entity = data.get("entities", {}).get(qid, {})
    return entity.get("claims", {})


def first_claim_value(claims, prop):
    values = claims.get(prop)
    if not values:
        return None
    mainsnak = values[0].get("mainsnak", {})
    datavalue = mainsnak.get("datavalue", {})
    return datavalue.get("value")


def wikimedia_file_url(filename):
    return "https://commons.wikimedia.org/wiki/Special:FilePath/" + requests.utils.quote(filename)


def fetch_html_candidates(url):
    resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=20)
    resp.raise_for_status()
    parser = SimpleHTMLImageParser(resp.url)
    parser.feed(resp.text)
    return sorted(parser.candidates, key=lambda c: c["score"], reverse=True)


def fetch_bdbase_map():
    url = "https://www.bdbase.fr/editeurs"
    resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=20)
    resp.raise_for_status()
    parser = BdbaseEditorParser()
    parser.feed(resp.text)
    entries = {}
    for name, image_url in parser.entries:
        key = normalize_key(name)
        if key and key not in entries:
            entries[key] = image_url
    return entries


def slugify_bdbase(name):
    text = unicodedata.normalize("NFKD", name)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.lower()
    text = text.replace("&", " et ")
    text = re.sub(r"['`’]", " ", text)
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return re.sub(r"-{2,}", "-", text)


def fetch_bdbase_logo_by_slug(slug):
    url = f"https://www.bdbase.fr/editeurs/{slug}"
    resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=20)
    if resp.status_code != 200:
        return None
    match = re.search(r"https?://static\.bdbase\.fr/images/editeurs/[^\"']+", resp.text)
    if not match:
        return None
    return match.group(0)


def fetch_bdbase_details(name):
    slug = slugify_bdbase(name)
    url = f"https://www.bdbase.fr/editeurs/{slug}"
    resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=20)
    if resp.status_code != 200:
        return None
    description = None
    match = re.search(r'<div class="pre">(.*?)</div>', resp.text, re.S)
    if match:
        description = strip_tags(match.group(1))
    site_url = None
    match = re.search(r'class="icon website[^"]*"[^>]*data-url="([^"]+)"', resp.text)
    if match:
        site_url = match.group(1)
    return {"bdbase_url": url, "description": description, "website": site_url}


def download_image(url, max_bytes=5 * 1024 * 1024):
    resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=20, stream=True)
    resp.raise_for_status()
    content_type = (resp.headers.get("Content-Type") or "").lower()
    if "image/svg" in content_type:
        return None
    data = BytesIO()
    downloaded = 0
    for chunk in resp.iter_content(chunk_size=8192):
        if not chunk:
            break
        downloaded += len(chunk)
        if downloaded > max_bytes:
            return None
        data.write(chunk)
    data.seek(0)
    try:
        image = Image.open(data)
        image.load()
    except Exception:
        return None
    return image


def make_square(image, size):
    if image.mode in ("RGBA", "LA"):
        background = Image.new("RGB", image.size, (255, 255, 255))
        background.paste(image, mask=image.split()[-1])
        image = background
    elif image.mode != "RGB":
        image = image.convert("RGB")

    width, height = image.size
    min_side = min(width, height)
    left = (width - min_side) // 2
    top = (height - min_side) // 2
    right = left + min_side
    bottom = top + min_side
    image = image.crop((left, top, right, bottom))
    return image.resize((size, size), Image.LANCZOS)


def ensure_folder(path):
    os.makedirs(path, exist_ok=True)


def load_cache(cache_path):
    if not os.path.exists(cache_path):
        return {}
    with open(cache_path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def save_cache(cache_path, cache):
    with open(cache_path, "w", encoding="utf-8") as handle:
        json.dump(cache, handle, ensure_ascii=False, indent=2)


def resolve_publisher_info(name, lang="fr"):
    title = wiki_search(name, lang=lang)
    if not title and lang != "en":
        title = wiki_search(name, lang="en")
        lang = "en" if title else lang
    if not title:
        return {"wiki_title": None, "wiki_lang": lang, "qid": None, "official_url": None, "logo_filename": None}

    qid = wiki_pageprops(title, lang=lang)
    if not qid:
        return {"wiki_title": title, "wiki_lang": lang, "qid": None, "official_url": None, "logo_filename": None}

    claims = wikidata_claims(qid)
    official_url = first_claim_value(claims, "P856")
    logo_filename = first_claim_value(claims, "P154") or first_claim_value(claims, "P18")

    return {
        "wiki_title": title,
        "wiki_lang": lang,
        "qid": qid,
        "official_url": official_url,
        "logo_filename": logo_filename,
    }


def find_image_from_official_site(url):
    if not url:
        return None, None
    try:
        candidates = fetch_html_candidates(url)
    except Exception:
        return None, None

    for candidate in candidates:
        try:
            image = download_image(candidate["url"])
        except Exception:
            image = None
        if image:
            return image, candidate["url"]
    return None, None


def find_image_from_wikimedia(filename):
    if not filename:
        return None, None
    file_url = wikimedia_file_url(filename)
    try:
        image = download_image(file_url)
    except Exception:
        return None, None
    if not image:
        return None, None
    return image, file_url


def find_image_from_bdbase(name, bdbase_map):
    url = None
    key = normalize_key(name)
    if bdbase_map:
        url = bdbase_map.get(key)

    if not url:
        slug = slugify_bdbase(name)
        url = fetch_bdbase_logo_by_slug(slug)

    if not url:
        return None, None

    try:
        image = download_image(url)
    except Exception:
        return None, None
    if not image:
        return None, None
    return image, url


def build_description_block(description, website):
    parts = []
    if description:
        parts.append(f'<div class="publisher-description">{html_escape(description)}</div>')
    if website:
        safe_url = html_escape(website)
        parts.append(
            '<div class="publisher-website">'
            f'<a href="{safe_url}" target="_blank" rel="noopener">Site officiel</a>'
            "</div>"
        )
    if not parts:
        return ""
    return "\n".join(["<!-- publisher-description -->", *parts, "<!-- /publisher-description -->"])


def update_folder_info(folder_info_path, description, website):
    block = build_description_block(description, website)
    if not block:
        return False

    if os.path.exists(folder_info_path):
        with open(folder_info_path, "r", encoding="utf-8") as handle:
            content = handle.read()
    else:
        content = (
            '<link rel="stylesheet" type="text/css" href="[[FOLDER]]/folder.css">\n'
            '<div align="center"><img src="[[FOLDER]]/header.jpg" width="100%"></div>\n'
            '<script>document.getElementById("group").classList.add("publisherPage");</script>\n'
        )

    content = content.replace("\\n", "\n")

    if "<!-- publisher-description -->" in content and "<!-- /publisher-description -->" in content:
        content = re.sub(
            r"<!-- publisher-description -->.*?<!-- /publisher-description -->",
            block,
            content,
            flags=re.S,
        )
    else:
        script_idx = content.find("<script")
        if script_idx != -1:
            content = content[:script_idx] + block + "\n" + content[script_idx:]
        else:
            content = content.rstrip() + "\n" + block + "\n"

    with open(folder_info_path, "w", encoding="utf-8") as handle:
        handle.write(content)
    return True


def write_report_row(writer, row):
    writer.writerow(row)


def main():
    parser = argparse.ArgumentParser(description="Fetch publisher images for missing publishers.")
    parser.add_argument("--source", default="Publishers_NON-ENGLISH/FR/ToBeComplete.md", help="Source markdown list")
    parser.add_argument("--output-root", default="Publishers_NON-ENGLISH/FR", help="Output root for publisher folders")
    parser.add_argument("--size", type=int, default=DEFAULT_SIZE, help="Square size for folder.jpg")
    parser.add_argument("--delay", type=float, default=1.0, help="Delay between publishers (seconds)")
    parser.add_argument("--start", type=int, default=0, help="Start index in publisher list")
    parser.add_argument("--limit", type=int, default=0, help="Limit number of publishers (0 = no limit)")
    parser.add_argument("--prefer", choices=["official", "wikimedia"], default="official", help="Prefer official site or wikimedia")
    parser.add_argument("--dry-run", action="store_true", help="Do not write images")
    parser.add_argument(
        "--report-mode",
        choices=["append", "overwrite"],
        default="append",
        help="Append to existing report.csv or overwrite it",
    )
    parser.add_argument("--only-missing", action="store_true", help="Skip entries with existing folder.jpg")
    parser.add_argument("--use-bdbase", action="store_true", help="Use BDbase editor images as a fallback")
    parser.add_argument("--update-folder-info", action="store_true", help="Add description and website to folder-info.html")
    args = parser.parse_args()

    source_path = os.path.abspath(args.source)
    output_root = os.path.abspath(args.output_root)
    cache_dir = os.path.join(output_root, "_downloads")
    ensure_folder(cache_dir)
    cache_path = os.path.join(cache_dir, "cache.json")
    report_path = os.path.join(cache_dir, "report.csv")

    cache = load_cache(cache_path)
    publishers = parse_publishers(source_path)
    if args.only_missing:
        filtered = []
        for name in publishers:
            safe_name = sanitize_folder_name(name)
            target_image = os.path.join(output_root, safe_name, "folder.jpg")
            if not os.path.exists(target_image):
                filtered.append(name)
        publishers = filtered
    if args.start:
        publishers = publishers[args.start :]
    if args.limit:
        publishers = publishers[: args.limit]

    report_exists = os.path.exists(report_path)
    report_mode = "a" if args.report_mode == "append" else "w"
    write_header = not report_exists or report_mode == "w"

    bdbase_map = {}
    if args.use_bdbase:
        try:
            bdbase_map = fetch_bdbase_map()
        except Exception:
            bdbase_map = {}

    with open(report_path, report_mode, encoding="utf-8", newline="") as report_file:
        writer = csv.writer(report_file)
        if write_header:
            writer.writerow([
                "publisher",
                "safe_name",
                "wiki_title",
                "wiki_lang",
                "wikidata_id",
                "official_url",
                "logo_filename",
                "image_source_url",
                "output_path",
                "status",
            ])

        for idx, name in enumerate(publishers, start=1):
            safe_name = sanitize_folder_name(name)
            target_dir = os.path.join(output_root, safe_name)
            target_image = os.path.join(target_dir, "folder.jpg")
            folder_info_path = os.path.join(target_dir, "folder-info.html")

            image_exists = os.path.exists(target_image)
            if image_exists and not args.update_folder_info:
                write_report_row(writer, [name, safe_name, "", "", "", "", "", "", target_image, "exists"])
                print(f"[{idx}/{len(publishers)}] {name}: exists")
                continue

            info = cache.get(name)
            if not info:
                info = resolve_publisher_info(name)
                cache[name] = info
                save_cache(cache_path, cache)

            description = None
            website = None
            if args.update_folder_info and args.use_bdbase:
                if "bdbase_description" not in info or "bdbase_website" not in info:
                    details = fetch_bdbase_details(name)
                    if details:
                        info["bdbase_description"] = details.get("description")
                        info["bdbase_website"] = details.get("website")
                        info["bdbase_url"] = details.get("bdbase_url")
                        cache[name] = info
                        save_cache(cache_path, cache)
                description = info.get("bdbase_description")
                website = info.get("bdbase_website")

            if image_exists:
                if args.update_folder_info and (description or website):
                    ensure_folder(target_dir)
                    update_folder_info(folder_info_path, description, website)
                write_report_row(writer, [name, safe_name, "", "", "", "", "", "", target_image, "exists"])
                print(f"[{idx}/{len(publishers)}] {name}: exists")
                continue

            image = None
            source_url = None

            if args.prefer == "official":
                image, source_url = find_image_from_official_site(info.get("official_url"))
                if not image and args.use_bdbase:
                    image, source_url = find_image_from_bdbase(name, bdbase_map)
                if not image:
                    image, source_url = find_image_from_wikimedia(info.get("logo_filename"))
            else:
                image, source_url = find_image_from_wikimedia(info.get("logo_filename"))
                if not image and args.use_bdbase:
                    image, source_url = find_image_from_bdbase(name, bdbase_map)
                if not image:
                    image, source_url = find_image_from_official_site(info.get("official_url"))

            if not image:
                write_report_row(writer, [
                    name,
                    safe_name,
                    info.get("wiki_title"),
                    info.get("wiki_lang"),
                    info.get("qid"),
                    info.get("official_url"),
                    info.get("logo_filename"),
                    source_url or "",
                    target_image,
                    "no_image",
                ])
                if args.update_folder_info and (description or website):
                    ensure_folder(target_dir)
                    update_folder_info(folder_info_path, description, website)
                print(f"[{idx}/{len(publishers)}] {name}: no image")
                time.sleep(args.delay)
                continue

            if not args.dry_run:
                ensure_folder(target_dir)
                image = make_square(image, args.size)
                image.save(target_image, format="JPEG", quality=90)
                if args.update_folder_info and (description or website):
                    update_folder_info(folder_info_path, description, website)

            write_report_row(writer, [
                name,
                safe_name,
                info.get("wiki_title"),
                info.get("wiki_lang"),
                info.get("qid"),
                info.get("official_url"),
                info.get("logo_filename"),
                source_url,
                target_image,
                "ok" if not args.dry_run else "dry_run",
            ])
            print(f"[{idx}/{len(publishers)}] {name}: ok")

            time.sleep(args.delay)


if __name__ == "__main__":
    main()
