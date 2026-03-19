#!/usr/bin/env python3

from __future__ import annotations

import hashlib
import html as html_stdlib
import json
import mimetypes
import os
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable
from urllib.parse import urljoin, urlparse, urlsplit, urlunsplit

import requests
from lxml import html


BASE_URL = "https://noiristudio.framer.website"
ALLOWED_PAGE_HOSTS = {"noiristudio.framer.website"}
LOCALIZABLE_ASSET_HOSTS = {
    "framerusercontent.com",
    "noiristudio.framer.website",
    "framer.com",
}
PAGE_ROUTES = [
    "/",
    "/about",
    "/contact",
    "/projects",
    "/services",
    "/projects/urban-crossings",
    "/projects/soft-focus",
    "/projects/intimate-faces",
    "/projects/game-in-motion",
    "/projects/pixel-perfect",
    "/projects/wanderlust-japan",
    "/privacy-policy",
    "/terms-conditions",
    "/404",
]
TEXT_EXTENSIONS = {
    ".css",
    ".framercms",
    ".html",
    ".js",
    ".json",
    ".mjs",
    ".svg",
    ".txt",
    ".webmanifest",
    ".xml",
}
ASSET_EXTENSIONS = {
    ".avif",
    ".bmp",
    ".css",
    ".gif",
    ".ico",
    ".jpeg",
    ".jpg",
    ".js",
    ".json",
    ".mjs",
    ".mp4",
    ".otf",
    ".png",
    ".svg",
    ".ttf",
    ".txt",
    ".webmanifest",
    ".webm",
    ".webp",
    ".woff",
    ".woff2",
    ".xml",
}
ATTRS_WITH_URLS = (
    "src",
    "href",
    "poster",
    "data-src",
    "data-srcset",
    "content",
)
URL_PATTERN = re.compile(r"https://[^\s\"'<>`)]+")
FRAMER_CMS_PATTERN = re.compile(
    r"new URL\(`(?P<file>\./[^`]+\.framercms)`,`(?P<base>(?:https://framerusercontent\.com/modules/[^`]+\.js|\.\./\.\./modules/[^`]+\.js))`\)\.href\.replace\(`/modules/`,`/cms/`\)"
)
RELATIVE_TEXT_ASSET_PATTERN = re.compile(
    r"(?P<quote>['\"`])(?P<spec>(?:\./|\.\./)[^'\"`\s]+?\.(?:avif|bmp|css|gif|ico|jpe?g|js|json|mjs|mp4|otf|png|svg|ttf|txt|webm|webmanifest|webp|woff2?|xml))(?P=quote)"
)
RUNTIME_ASSET_LITERAL_PATTERN = re.compile(
    r"(?<!new URL\()(?P<quote>['\"`])(?P<spec>(?:\./|\.\./)[^'\"`\s]+?\.(?:avif|bmp|gif|ico|jpe?g|mp4|otf|pdf|png|svg|ttf|txt|wav|webm|webp|woff2?))(?:\?(?:[^'\"`#\s]+))?(?:#[^'\"`\s]+)?(?P=quote)"
)
RUNTIME_SRCSET_PATTERN = re.compile(r"srcSet:(?P<quote>['\"`])(?P<value>[^'\"`]+)(?P=quote)")
ROUTE_PATH_PATTERN = re.compile(r"path:`(/[^`]+|/)`")
CANONICAL_PATTERN = re.compile(r"siteCanonicalURL:`[^`]*`")
EDITOR_INIT_PATTERN = re.compile(r"import\(`https://framer\.com/edit/init\.mjs`\)")
LOW_OPACITY_PATTERN = re.compile(r"^0(?:\.0+)?(?:1)?$")
TRANSLATE_Y_PATTERN = re.compile(r"translateY\([^)]*\)")
FRAMER_BADGE_STYLE_PATTERN = re.compile(
    r"@supports \(z-index:calc\(infinity\)\)\{#__framer-badge-container\{--infinity:infinity\}\}"
    r"#__framer-badge-container\{[^}]+\}"
)

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
ASSETS_ROOT = REPO_ROOT / "assets"
MIRROR_ROOT = ASSETS_ROOT / "mirror"
LOCAL_ASSETS_ROOT = ASSETS_ROOT / "local"
BUILD_VERSION = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
VERSIONED_EXTENSIONS = {".css", ".framercms", ".js", ".json", ".mjs", ".webmanifest", ".xml"}
VERCEL_CONFIG = {
    "headers": [
        {
            "source": "/(.*)",
            "headers": [{"key": "Cache-Control", "value": "no-store"}],
        }
    ]
}
SESSION = requests.Session()
SESSION.headers.update(
    {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36"
        )
    }
)
ASSET_CACHE: dict[str, Path] = {}
INERT_FRAMER_HREF = "javascript:void(0)"
HOST_DIR_MAP = {
    "framerusercontent.com": "content",
    "noiristudio.framer.website": "site",
    "framer.com": "support",
}
SERVICE_DETAILS = {
    "Photography": {
        "description": (
            "Our photography blends cinematic atmosphere with editorial precision to "
            "create imagery that feels intentional, expressive, and timeless. Every "
            "frame is crafted to highlight emotion, detail, and story."
        ),
        "items": [
            "Cinematic & Editorial Photoshoots",
            "On-site or Studio Production",
            "High-Resolution Final Images",
            "Curated Photo Selections",
        ],
    },
    "Cinematography": {
        "description": (
            "We produce cinematic films that merge narrative depth with visual polish, "
            "designed to communicate your brand or story with clarity and impact."
        ),
        "items": [
            "Concept & Story Development",
            "High-End Video Production",
            "Cinematic Editing & Color Grading",
            "Final Deliverables in Multiple Formats",
        ],
    },
    "Retouching": {
        "description": (
            "Our retouching elevates each image through refined beauty work, texture "
            "control, and tonal balance while preserving realism and editorial quality."
        ),
        "items": [
            "Editorial Beauty Retouch",
            "Color Correction & Grading",
            "Cleanup & Background Refinement",
            "Final High-End Export",
        ],
    },
    "Art Direction": {
        "description": (
            "We guide the visual identity of each project through concept development, "
            "styling, and cohesive direction to ensure every frame serves a clear creative vision."
        ),
        "items": [
            "Creative Concept Development",
            "Moodboards & Visual Planning",
            "Styling & Set Direction",
            "Narrative & Aesthetic Guidance",
        ],
    },
}


def normalize_route(path: str) -> str:
    clean = urlparse(path).path or "/"
    if clean != "/" and clean.endswith("/"):
        clean = clean.rstrip("/")
    return clean or "/"


def page_output_path(route: str) -> Path:
    route = normalize_route(route)
    if route == "/":
        return REPO_ROOT / "index.html"
    if route == "/404":
        return REPO_ROOT / "404" / "index.html"
    return REPO_ROOT / route.lstrip("/") / "index.html"


def route_relative_href(from_route: str, to_route: str) -> str:
    from_output = page_output_path(from_route)
    target_output = page_output_path(to_route)
    if target_output.name == "index.html":
        rel = os.path.relpath(target_output.parent, start=from_output.parent)
        rel = rel.replace(os.sep, "/")
        if rel == ".":
            return "./"
        return rel.rstrip("/") + "/"
    rel = os.path.relpath(target_output, start=from_output.parent)
    return rel.replace(os.sep, "/")


def asset_relative_href(from_output: Path, to_output: Path) -> str:
    return os.path.relpath(to_output, start=from_output.parent).replace(os.sep, "/")


def strip_url_suffix(value: str) -> str:
    return value.split("#", 1)[0].split("?", 1)[0]


def versioned_href(href: str) -> str:
    parts = urlsplit(href)
    if Path(parts.path).suffix.lower() not in VERSIONED_EXTENSIONS:
        return href

    query_parts = [part for part in parts.query.split("&") if part and not part.startswith("v=")]
    query_parts.append(f"v={BUILD_VERSION}")
    return urlunsplit(
        (parts.scheme, parts.netloc, parts.path, "&".join(query_parts), parts.fragment)
    )


def should_keep_external_link(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme in {"mailto", "tel"} or (
        parsed.scheme in {"http", "https"}
        and parsed.netloc not in ALLOWED_PAGE_HOSTS
        and parsed.netloc not in {"framer.com", "www.framer.com", "framer.link"}
        and parsed.netloc not in {"events.framer.com"}
    )


def neutralize_framer_link(url: str) -> str | None:
    parsed = urlparse(url)
    if parsed.netloc in {"framer.link", "www.framer.com"}:
        return INERT_FRAMER_HREF
    if parsed.netloc == "framer.com" and parsed.path != "/edit/init.mjs":
        return INERT_FRAMER_HREF
    return None


def is_page_url(url: str) -> bool:
    parsed = urlparse(urljoin(BASE_URL, url))
    if parsed.scheme not in {"http", "https"} or parsed.netloc not in ALLOWED_PAGE_HOSTS:
        return False
    path = normalize_route(parsed.path or "/")
    return Path(path).suffix.lower() not in ASSET_EXTENSIONS


def page_route_from_url(url: str) -> str | None:
    parsed = urlparse(urljoin(BASE_URL, url))
    if parsed.netloc not in ALLOWED_PAGE_HOSTS:
        return None
    route = normalize_route(parsed.path or "/")
    if Path(route).suffix.lower() in ASSET_EXTENSIONS:
        return None
    return route


def should_localize_asset(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        return False
    if parsed.netloc == "events.framer.com":
        return False
    if parsed.netloc == "framer.com":
        return parsed.path == "/edit/init.mjs"
    if parsed.netloc == "framerusercontent.com":
        if parsed.path.startswith("/node_modules/"):
            return False
        if not Path(parsed.path).suffix:
            return False
    if parsed.netloc not in LOCALIZABLE_ASSET_HOSTS:
        return False
    if parsed.netloc in ALLOWED_PAGE_HOSTS and is_page_url(url):
        return False
    return True


def guess_extension(url: str, content_type: str) -> str:
    suffix = Path(urlparse(url).path).suffix
    if suffix:
        return suffix
    content_type = (content_type or "").split(";")[0].strip().lower()
    return mimetypes.guess_extension(content_type) or ""


def asset_output_path(url: str, content_type: str = "") -> Path:
    parsed = urlparse(url)
    host_dir = HOST_DIR_MAP.get(parsed.netloc, parsed.netloc.replace(":", "_"))
    raw_path = parsed.path.lstrip("/")
    if not raw_path:
        raw_path = "asset"
    path_obj = Path(raw_path)
    if path_obj.name in {"", "."} or raw_path.endswith("/"):
        suffix = guess_extension(url, content_type)
        filename = f"asset-{hashlib.sha1(url.encode('utf-8')).hexdigest()[:12]}{suffix}"
        rel_path = Path(host_dir) / path_obj / filename
        return MIRROR_ROOT / rel_path
    if parsed.query:
        suffix = path_obj.suffix or guess_extension(url, content_type)
        stem = path_obj.stem or "asset"
        digest = hashlib.sha1(parsed.query.encode("utf-8")).hexdigest()[:12]
        filename = f"{stem}-{digest}{suffix}"
        rel_path = Path(host_dir) / path_obj.parent / filename
    else:
        rel_path = Path(host_dir) / raw_path
    return MIRROR_ROOT / rel_path


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def decode_text_response(response: requests.Response) -> str:
    for encoding in ("utf-8", response.encoding, response.apparent_encoding):
        if not encoding:
            continue
        try:
            return response.content.decode(encoding)
        except (LookupError, UnicodeDecodeError):
            continue
    return response.text


def remove_generated_output() -> None:
    for path in [
        MIRROR_ROOT,
        REPO_ROOT / "about",
        REPO_ROOT / "contact",
        REPO_ROOT / "projects",
        REPO_ROOT / "services",
        REPO_ROOT / "privacy-policy",
        REPO_ROOT / "terms-conditions",
        REPO_ROOT / "404",
        REPO_ROOT / "index.html",
        REPO_ROOT / "404.html",
        REPO_ROOT / ".nojekyll",
    ]:
        if path.is_dir():
            shutil.rmtree(path)
        elif path.exists():
            path.unlink()


def rewrite_css_urls(css_text: str, source_url: str, output_path: Path) -> str:
    def replace_url(match: re.Match[str]) -> str:
        raw_url = match.group("url").strip(" \"'")
        if not raw_url or raw_url.startswith(("data:", "#")):
            return match.group(0)
        absolute = urljoin(source_url, html_stdlib.unescape(raw_url))
        if should_localize_asset(absolute):
            local_output = localize_asset(absolute)
            rel = versioned_href(asset_relative_href(output_path, local_output))
            return f'url("{rel}")'
        if is_page_url(absolute):
            route = page_route_from_url(absolute)
            if route:
                return f'url("{route}")'
        return match.group(0)

    css_text = re.sub(
        r"@import\s+(?:url\()?(?P<url>[^)\"';]+|\"[^\"]+\"|'[^']+')\)?",
        replace_url,
        css_text,
    )
    css_text = re.sub(r"url\((?P<url>[^)]+)\)", replace_url, css_text)
    return css_text


def patch_framer_module(text: str, output_path: Path) -> str:
    editor_stub_rel = versioned_href(
        asset_relative_href(output_path, LOCAL_ASSETS_ROOT / "framer-editor-init.mjs")
    )
    text = EDITOR_INIT_PATTERN.sub(f'import(`{editor_stub_rel}`)', text)
    text = text.replace(
        "e.url.startsWith(`https://framerusercontent.com/third-party-assets/fontshare/`)?`fontshare`",
        "e.url.includes(`/third-party-assets/fontshare/`)?`fontshare`",
    )
    text = text.replace("https://www.framer.com/contact/", INERT_FRAMER_HREF)
    text = re.sub(
        r"\b\w+\.open\(`javascript:void\(0\)\)\}`\)",
        "void 0",
        text,
    )
    text = re.sub(
        r"function bt\(e,t\)\{let n=t instanceof Error\?t\.stack\?\?t\.message:t;return.*?\}function xt",
        "function bt(e,t){let n=t instanceof Error?t.stack??t.message:t;return n?`${e?`${e}\\n`:``}${n}`:`.`}function xt",
        text,
        flags=re.S,
    )
    text = CANONICAL_PATTERN.sub(
        "siteCanonicalURL:window.location.origin+(window.__NOIRI_BASE_PATH__||``)",
        text,
    )
    text = ROUTE_PATH_PATTERN.sub(
        lambda match: f"path:(window.__NOIRI_BASE_PATH__||``)+`{match.group(1)}`",
        text,
    )
    return text


def rewrite_text_urls(text: str, source_url: str, output_path: Path, page_route: str | None = None) -> str:
    def localize_runtime_spec(spec: str) -> str | None:
        candidate = (output_path.parent / strip_url_suffix(spec)).resolve()
        try:
            candidate.relative_to(REPO_ROOT)
        except ValueError:
            candidate = None
        if candidate is not None and candidate.exists():
            return spec
        absolute = urljoin(source_url, strip_url_suffix(spec))
        if not should_localize_asset(absolute):
            return None
        local_output = localize_asset(absolute)
        return asset_relative_href(output_path, local_output)

    def replace_framer_cms(match: re.Match[str]) -> str:
        relative_file = match.group("file")
        base_spec = match.group("base")
        modules_url = base_spec if base_spec.startswith("http") else urljoin(source_url, base_spec)
        cms_base = modules_url.replace("/modules/", "/cms/", 1)
        cms_url = urljoin(cms_base, relative_file)
        local_output = localize_asset(cms_url)
        rel = versioned_href(asset_relative_href(output_path, local_output))
        return f"new URL(`{rel}`,import.meta.url).href"

    def replace_absolute(match: re.Match[str]) -> str:
        raw_url = html_stdlib.unescape(match.group(0))
        if raw_url.startswith("https://events.framer.com"):
            return ""
        if raw_url == "https://framer.com/edit/init.mjs":
            local_output = LOCAL_ASSETS_ROOT / "framer-editor-init.mjs"
            return versioned_href(asset_relative_href(output_path, local_output))
        neutralized = neutralize_framer_link(raw_url)
        if neutralized:
            return neutralized
        if should_localize_asset(raw_url):
            local_output = localize_asset(raw_url)
            return versioned_href(asset_relative_href(output_path, local_output))
        route = page_route_from_url(raw_url)
        if route:
            if page_route:
                return route_relative_href(page_route, route)
            return route
        return match.group(0)

    def ensure_relative_asset(match: re.Match[str]) -> str:
        spec = match.group("spec")
        absolute = urljoin(source_url, strip_url_suffix(spec))
        if should_localize_asset(absolute):
            localize_asset(absolute)
        quote = match.group("quote")
        return f"{quote}{versioned_href(spec)}{quote}"

    def rewrite_runtime_asset_literal(match: re.Match[str]) -> str:
        spec = match.group("spec")
        rel = localize_runtime_spec(spec)
        if rel is None:
            return match.group(0)
        quote = match.group("quote")
        return f"new URL({quote}{versioned_href(rel)}{quote},import.meta.url).href"

    def rewrite_runtime_srcset(match: re.Match[str]) -> str:
        parts: list[str] = []
        for item in match.group("value").split(","):
            entry = item.strip()
            if not entry:
                continue
            bits = entry.split()
            spec = bits[0]
            rel = localize_runtime_spec(spec)
            if rel is None:
                return match.group(0)
            descriptor = f" {' '.join(bits[1:])}" if len(bits) > 1 else ""
            parts.append(f"${{new URL(`{versioned_href(rel)}`,import.meta.url).href}}{descriptor}")
        return f"srcSet:`{', '.join(parts)}`"

    rewritten = FRAMER_CMS_PATTERN.sub(replace_framer_cms, text)
    rewritten = RELATIVE_TEXT_ASSET_PATTERN.sub(ensure_relative_asset, rewritten)
    rewritten = URL_PATTERN.sub(replace_absolute, rewritten)
    if output_path.suffix == ".mjs":
        rewritten = RUNTIME_SRCSET_PATTERN.sub(rewrite_runtime_srcset, rewritten)
        rewritten = RUNTIME_ASSET_LITERAL_PATTERN.sub(rewrite_runtime_asset_literal, rewritten)
        rewritten = patch_framer_module(rewritten, output_path)
    return rewritten


def is_text_asset(output_path: Path, content_type: str) -> bool:
    content_type = (content_type or "").split(";")[0].strip().lower()
    if output_path.suffix.lower() in TEXT_EXTENSIONS:
        return True
    return content_type.startswith("text/") or content_type in {
        "application/javascript",
        "application/json",
        "application/ld+json",
        "application/manifest+json",
        "application/xml",
        "image/svg+xml",
        "text/javascript",
    }


def localize_asset(url: str) -> Path:
    if url in ASSET_CACHE:
        return ASSET_CACHE[url]

    if url == "https://framer.com/edit/init.mjs":
        stub_path = LOCAL_ASSETS_ROOT / "framer-editor-init.mjs"
        ASSET_CACHE[url] = stub_path
        return stub_path

    response = SESSION.get(url, timeout=60)
    response.raise_for_status()
    output_path = asset_output_path(url, response.headers.get("content-type", ""))
    ensure_parent(output_path)

    if is_text_asset(output_path, response.headers.get("content-type", "")):
        text = decode_text_response(response)
        text = rewrite_text_urls(text, url, output_path)
        if output_path.suffix == ".css":
            text = rewrite_css_urls(text, url, output_path)
        output_path.write_text(text, encoding="utf-8")
    else:
        output_path.write_bytes(response.content)

    ASSET_CACHE[url] = output_path
    return output_path


def rewrite_srcset(srcset: str, source_url: str, page_output: Path) -> str:
    rewritten: list[str] = []
    for part in srcset.split(","):
        item = part.strip()
        if not item:
            continue
        bits = item.split()
        absolute = urljoin(source_url, html_stdlib.unescape(bits[0]))
        if should_localize_asset(absolute):
            bits[0] = versioned_href(asset_relative_href(page_output, localize_asset(absolute)))
        rewritten.append(" ".join(bits))
    return ", ".join(rewritten)


def rewrite_inline_script(script_text: str, page_url: str, page_output: Path, page_route: str) -> str:
    return rewrite_text_urls(script_text, page_url, page_output, page_route=page_route)


def script_contains(script: html.HtmlElement, needle: str) -> bool:
    return needle in ((script.text or "").strip())


def drop_runtime_nodes(doc: html.HtmlElement) -> None:
    for meta in doc.xpath("//meta[translate(@name, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz')='generator']"):
        parent = meta.getparent()
        if parent is not None:
            parent.remove(meta)

    for meta in doc.xpath("//meta[starts-with(translate(@name, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'framer-search-index')]"):
        parent = meta.getparent()
        if parent is not None:
            parent.remove(meta)

    for link in doc.xpath("//link[contains(concat(' ', normalize-space(@rel), ' '), ' modulepreload ')]"):
        parent = link.getparent()
        if parent is not None:
            parent.remove(link)

    for script in doc.xpath("//script"):
        script_type = (script.get("type") or "").strip().lower()
        if script_type.startswith("framer/"):
            parent = script.getparent()
            if parent is not None:
                parent.remove(script)
            continue
        if script.get("data-framer-appear-animation") is not None:
            parent = script.getparent()
            if parent is not None:
                parent.remove(script)
            continue
        if script_type == "module" and script.get("data-framer-bundle") is not None:
            parent = script.getparent()
            if parent is not None:
                parent.remove(script)
            continue
        if any(
            script_contains(script, needle)
            for needle in (
                "__framer_force_showing_editorbar_since",
                "var animator=(()=>{",
                'document.querySelectorAll("[data-nested-link]")',
                "var w=\"framer_variant\"",
                'NODE_ENV:"production"',
            )
        ):
            parent = script.getparent()
            if parent is not None:
                parent.remove(script)

    for node in doc.xpath('//*[@id="__framer-badge-container"] | //*[@id="template-overlay"]'):
        parent = node.getparent()
        if parent is not None:
            parent.remove(node)


def clean_inert_links(doc: html.HtmlElement) -> None:
    for anchor in doc.xpath("//a[@href='javascript:void(0)']"):
        for attr in ("href", "target", "rel"):
            if attr in anchor.attrib:
                del anchor.attrib[attr]
        anchor.tag = "span"


def clean_runtime_attributes(doc: html.HtmlElement) -> None:
    for attr in (
        "data-framer-hydrate-v2",
        "data-framer-generated-page",
        "data-framer-ssr-released-at",
        "data-framer-page-optimized-at",
        "data-framer-root",
        "data-framer-cursor",
    ):
        for el in doc.xpath(f"//*[@{attr}]"):
            if attr in el.attrib:
                del el.attrib[attr]


def normalize_style(style_value: str, *, force_motion_reset: bool = False) -> str:
    declarations: list[tuple[str, str]] = []
    low_opacity = False
    for part in style_value.split(";"):
        if ":" not in part:
            continue
        prop, value = part.split(":", 1)
        prop = prop.strip().lower()
        value = value.strip()
        if not prop:
            continue
        if prop == "opacity" and LOW_OPACITY_PATTERN.match(value):
            low_opacity = True
        declarations.append((prop, value))

    animate = force_motion_reset or low_opacity

    if not animate:
        for prop, value in declarations:
            if prop != "transform":
                continue
            match = re.search(r"translateY\((-?\d+(?:\.\d+)?)px\)", value)
            if match and abs(float(match.group(1))) >= 24:
                animate = True
                break

    normalized: list[tuple[str, str]] = []
    for prop, value in declarations:
        if prop == "will-change":
            continue
        if prop == "opacity" and (animate or LOW_OPACITY_PATTERN.match(value)):
            value = "1"
        elif prop == "transform" and animate:
            value = TRANSLATE_Y_PATTERN.sub("translateY(0px)", value)
        normalized.append((prop, value))

    return ";".join(f"{prop}:{value}" for prop, value in normalized)


def normalize_motion_markup(doc: html.HtmlElement) -> None:
    for el in doc.iter():
        style_value = el.get("style")
        if not style_value:
            continue
        force_motion_reset = el.get("data-framer-appear-id") is not None
        if not force_motion_reset and "opacity:" not in style_value and "will-change:" not in style_value:
            continue
        new_style = normalize_style(style_value, force_motion_reset=force_motion_reset)
        if new_style:
            el.set("style", new_style)
        elif "style" in el.attrib:
            del el.attrib["style"]


def clean_style_blocks(doc: html.HtmlElement) -> None:
    for style_tag in doc.xpath("//style"):
        if not style_tag.text:
            continue
        style_tag.text = FRAMER_BADGE_STYLE_PATTERN.sub("", style_tag.text)


def build_service_panel(detail: dict[str, list[str] | str], contact_href: str) -> html.HtmlElement:
    description = html_stdlib.escape(str(detail["description"]))
    items = "".join(
        (
            '<li class="noiri-service-list-item">'
            '<span class="noiri-service-list-bullet">--</span>'
            f"<span>{html_stdlib.escape(item)}</span>"
            "</li>"
        )
        for item in detail["items"]
    )
    snippet = f"""
    <div class="framer-jknhlk noiri-service-panel" hidden aria-hidden="true">
      <div class="framer-v95lb0">
        <div class="framer-sq6hi3" data-framer-component-type="RichTextContainer">
          <p class="framer-text framer-styles-preset-1ljkjf9" data-styles-preset="Aren2whxy">{description}</p>
        </div>
      </div>
      <div class="framer-41zn2m">
        <ul class="framer-4d30w1 noiri-service-list">{items}</ul>
      </div>
      <div class="framer-umqj99">
        <div class="framer-1lkwpva-container">
          <a class="noiri-service-cta" href="{contact_href}">Book a Call</a>
        </div>
      </div>
    </div>
    """.strip()
    return html.fragment_fromstring(snippet)


def augment_services_page(doc: html.HtmlElement, page_route: str) -> None:
    contact_href = route_relative_href(page_route, "/contact")
    rows = doc.xpath(
        "//*[@data-framer-name='Row Close' or @data-framer-name='Row Close Phone']"
    )
    for row in rows:
        title = " ".join(" ".join(row.xpath(".//h1/text() | .//h2/text() | .//p/text()")).split())
        if title not in SERVICE_DETAILS:
            continue
        row.set("data-noiri-service-row", title.lower().replace(" ", "-"))
        row.set("data-noiri-service-open-class", "framer-v-iivdbu" if "Phone" in (row.get("data-framer-name") or "") else "framer-v-14lylx1")
        row.set("role", "button")
        row.set("tabindex", "0")
        row.set("aria-expanded", "false")
        if not row.xpath(".//*[contains(@class, 'noiri-service-panel')]"):
            row.append(build_service_panel(SERVICE_DETAILS[title], contact_href))


def inject_runtime_helpers(doc: html.HtmlElement, page_route: str) -> None:
    head = doc.find("head")
    body = doc.find("body")
    if head is None or body is None:
        return

    style_href = route_relative_href(page_route, "/") + "assets/local/site.css"
    head.append(
        html.fragment_fromstring(
            f'<link rel="stylesheet" href="{versioned_href(style_href)}">'
        )
    )

    site_script_src = route_relative_href(page_route, "/") + "assets/local/site.js"
    form_handler_src = route_relative_href(page_route, "/") + "assets/local/form-handler.js"
    body.append(
        html.fragment_fromstring(
            f'<script src="{versioned_href(site_script_src)}" defer></script>'
        )
    )
    body.append(
        html.fragment_fromstring(
            f'<script src="{versioned_href(form_handler_src)}" defer></script>'
        )
    )


def rewrite_page(route: str) -> None:
    page_url = urljoin(BASE_URL, route if route != "/" else "/")
    response = SESSION.get(page_url, timeout=60)
    if route != "/404" or response.status_code < 400:
        response.raise_for_status()
    doc = html.fromstring(decode_text_response(response), base_url=page_url)

    for base in doc.xpath("//base"):
        parent = base.getparent()
        if parent is not None:
            parent.remove(base)

    drop_runtime_nodes(doc)


    for script in doc.xpath("//script[@src]"):
        src = script.get("src")
        if not src:
            continue
        absolute = urljoin(page_url, html_stdlib.unescape(src))
        if absolute.startswith("https://events.framer.com"):
            parent = script.getparent()
            if parent is not None:
                parent.remove(script)
            continue
        if should_localize_asset(absolute):
            script.set(
                "src",
                versioned_href(asset_relative_href(page_output_path(route), localize_asset(absolute))),
            )

    for link in doc.xpath("//link[@href]"):
        href = link.get("href")
        if not href:
            continue
        rel = " ".join(link.get("rel", [])).lower()
        absolute = urljoin(page_url, html_stdlib.unescape(href))
        if "canonical" in rel:
            parent = link.getparent()
            if parent is not None:
                parent.remove(link)
            continue
        if should_localize_asset(absolute):
            link.set(
                "href",
                versioned_href(asset_relative_href(page_output_path(route), localize_asset(absolute))),
            )
            continue
        target_route = page_route_from_url(absolute)
        if target_route:
            link.set("href", route_relative_href(route, target_route))

    for meta in doc.xpath("//meta[@content]"):
        content = meta.get("content")
        if not content:
            continue
        prop = (meta.get("property") or "").lower()
        name = (meta.get("name") or "").lower()
        if not content.startswith(("/", "./", "../", "http://", "https://")):
            continue
        absolute = urljoin(page_url, html_stdlib.unescape(content))
        if prop == "og:url" or name == "twitter:url":
            parent = meta.getparent()
            if parent is not None:
                parent.remove(meta)
            continue
        if should_localize_asset(absolute):
            meta.set(
                "content",
                versioned_href(asset_relative_href(page_output_path(route), localize_asset(absolute))),
            )
            continue
        target_route = page_route_from_url(absolute)
        if target_route:
            meta.set("content", route_relative_href(route, target_route))

    for style_tag in doc.xpath("//style"):
        if style_tag.text:
            style_tag.text = rewrite_css_urls(style_tag.text, page_url, page_output_path(route))

    for el in doc.iter():
        style_value = el.get("style")
        if style_value and "url(" in style_value:
            el.set("style", rewrite_css_urls(style_value, page_url, page_output_path(route)))

        if el.tag == "a":
            href = el.get("href")
            if not href:
                continue
            absolute = urljoin(page_url, html_stdlib.unescape(href))
            neutralized = neutralize_framer_link(absolute)
            if neutralized:
                el.set("href", neutralized)
                for attr in ("target", "rel"):
                    if attr in el.attrib:
                        del el.attrib[attr]
                continue
            target_route = page_route_from_url(absolute)
            if target_route:
                el.set("href", route_relative_href(route, target_route))
            elif should_localize_asset(absolute):
                el.set(
                    "href",
                    versioned_href(asset_relative_href(page_output_path(route), localize_asset(absolute))),
                )
            elif not should_keep_external_link(absolute):
                el.set("href", href)
            continue

        for attr in ("src", "poster", "data-src"):
            value = el.get(attr)
            if not value:
                continue
            if value.startswith(("data:", "#", "./assets/", "../assets/", "assets/")):
                continue
            if "://" not in value and not value.startswith("/"):
                continue
            absolute = urljoin(page_url, html_stdlib.unescape(value))
            if should_localize_asset(absolute):
                el.set(
                    attr,
                    versioned_href(asset_relative_href(page_output_path(route), localize_asset(absolute))),
                )

        srcset = el.get("srcset")
        if srcset:
            el.set("srcset", rewrite_srcset(srcset, page_url, page_output_path(route)))

        for attr in ("data-framer-search-index",):
            value = el.get(attr)
            if not value:
                continue
            absolute = urljoin(page_url, html_stdlib.unescape(value))
            if should_localize_asset(absolute):
                el.set(
                    attr,
                    versioned_href(asset_relative_href(page_output_path(route), localize_asset(absolute))),
                )

    for script in doc.xpath("//script[not(@src)]"):
        if script.text:
            script.text = rewrite_inline_script(script.text, page_url, page_output_path(route), route)

    normalize_motion_markup(doc)
    clean_style_blocks(doc)
    clean_runtime_attributes(doc)
    clean_inert_links(doc)
    if route == "/services":
        augment_services_page(doc, route)
    inject_runtime_helpers(doc, route)

    output = page_output_path(route)
    ensure_parent(output)
    rendered = html.tostring(doc, encoding="unicode", method="html", doctype="<!DOCTYPE html>")
    rendered = rendered.replace("<!--$-->", "").replace("<!--/$-->", "")
    output.write_text(rendered, encoding="utf-8")

    if route == "/404":
        (REPO_ROOT / "404.html").write_text(rendered, encoding="utf-8")


def write_support_files() -> None:
    ensure_parent(REPO_ROOT / ".nojekyll")
    (REPO_ROOT / ".nojekyll").write_text("", encoding="utf-8")
    (REPO_ROOT / "vercel.json").write_text(json.dumps(VERCEL_CONFIG, indent=2) + "\n", encoding="utf-8")


def mirror_site(routes: Iterable[str]) -> None:
    remove_generated_output()
    for route in routes:
        print(f"Mirroring {route}")
        rewrite_page(route)
    write_support_files()


if __name__ == "__main__":
    mirror_site(PAGE_ROUTES)
