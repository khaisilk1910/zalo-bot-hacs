"""Text formatting helpers for Zalo messages.

The style tokens in this module intentionally follow zca-js 2.1.2 TextStyle.
All positions sent to zca-js are calculated as UTF-16 code units, matching
JavaScript/Zalo offsets so astral Unicode characters (for example emoji) do
not shift subsequent style ranges.
"""
from __future__ import annotations

import logging
import re
from typing import Any

_LOGGER = logging.getLogger(__name__)

ZALO_COLORS = {
    "red": "c_db342e",
    "orange": "c_f27806",
    "yellow": "c_f7b503",
    "green": "c_15a85f",
}

ZALO_SMALL = "f_13"
ZALO_BIG = "f_18"
ZALO_UNORDERED_LIST = "lst_1"
ZALO_ORDERED_LIST = "lst_2"
ZALO_INDENT = "ind_$"

# zca-js 2.1.2 exposes only Small (f_13) and Big (f_18). Keep the existing
# Markdown heading feature but map it only to supported tokens.
HEADING_STYLES = {
    1: f"{ZALO_BIG},b",
    2: f"{ZALO_BIG},b",
    3: "b",
    4: ZALO_SMALL,
    5: ZALO_SMALL,
    6: ZALO_SMALL,
}

CUSTOM_STYLE_TAGS = {
    **ZALO_COLORS,
    "big": ZALO_BIG,
    "small": ZALO_SMALL,
}

_COLOR_TOKENS = frozenset(ZALO_COLORS.values())
_STRUCTURAL_TOKENS = frozenset({ZALO_UNORDERED_LIST, ZALO_ORDERED_LIST, ZALO_INDENT})
_STYLE_TAG_RE = re.compile(r"\{(/?)(red|orange|yellow|green|big|small)\}", re.IGNORECASE)
_UNORDERED_LIST_RE = re.compile(r"^[-+*][ \t]+")
_ORDERED_LIST_RE = re.compile(r"^\d+[.)][ \t]+")
_HEADING_RE = re.compile(r"^(#+)(?:[ \t]+)?")


def _utf16_prefix_offsets(text: str) -> list[int]:
    """Build Python-index -> UTF-16-offset mapping in one linear pass."""
    offsets = [0] * (len(text) + 1)
    total = 0
    for index, char in enumerate(text, start=1):
        total += 2 if ord(char) >= 0x10000 else 1
        offsets[index] = total
    return offsets


def _split_line_ending(line: str) -> tuple[str, str]:
    """Split a line into content and its original line ending."""
    if line.endswith("\r\n"):
        return line[:-2], "\r\n"
    if line.endswith("\n") or line.endswith("\r"):
        return line[:-1], line[-1:]
    return line, ""


def _indent_width(prefix: str) -> int:
    """Convert leading whitespace to a conservative Zalo indent size.

    zca-js documents indentSize as the number of indentation spaces. Tabs are
    treated as four spaces. Extremely large indentation is capped to keep the
    generated ind_* token within a practical range while preserving excess
    whitespace as literal text.
    """
    return sum(4 if ch == "\t" else 1 for ch in prefix)


def _consume_indent(content: str) -> tuple[str, int, str]:
    """Remove up to eight leading indentation spaces and return any excess."""
    match = re.match(r"^[ \t]+", content)
    if not match:
        return content, 0, ""

    prefix = match.group(0)
    width = _indent_width(prefix)
    if not content[len(prefix):]:
        # Keep whitespace-only lines byte-for-byte compatible.
        return content, 0, ""

    indent_size = min(width, 8)
    excess = " " * max(0, width - indent_size)
    return content[len(prefix):], indent_size, excess


def _preprocess_line_syntax(text: str) -> tuple[str, list[list[dict[str, Any]]]]:
    """Strip line-level Markdown markers and retain formatting directives."""
    processed_lines: list[str] = []
    directives: list[list[dict[str, Any]]] = []

    for raw_line in text.splitlines(keepends=True):
        content, ending = _split_line_ending(raw_line)
        line_directives: list[dict[str, Any]] = []

        working, indent_size, excess_indent = _consume_indent(content)
        if indent_size:
            line_directives.append({"st": ZALO_INDENT, "indentSize": indent_size})

        # Preserve spaces beyond the supported indentation range as literal
        # text instead of silently dropping user content.
        if excess_indent:
            working = excess_indent + working

        heading_match = _HEADING_RE.match(working)
        if heading_match:
            level = len(heading_match.group(1))
            working = working[heading_match.end():]
            line_directives.append({"st": HEADING_STYLES.get(level, "i")})
        elif working.startswith(">"):
            working = working[1:]
            if working.startswith((" ", "\t")):
                working = working[1:]
            # Preserve the integration's existing blockquote behavior.
            line_directives.append({"st": "i"})
        else:
            unordered_match = _UNORDERED_LIST_RE.match(working)
            ordered_match = _ORDERED_LIST_RE.match(working)
            if unordered_match:
                working = working[unordered_match.end():]
                line_directives.append({"st": ZALO_UNORDERED_LIST})
            elif ordered_match:
                working = working[ordered_match.end():]
                line_directives.append({"st": ZALO_ORDERED_LIST})

        processed_lines.append(working + ending)
        directives.append(line_directives)

    # str.splitlines() returns [] only for an empty string. The caller already
    # handles empty input, but keep the shape predictable for completeness.
    if text and not processed_lines:
        processed_lines.append(text)
        directives.append([])

    return "".join(processed_lines), directives


def _has_closing_tag(text: str, tag: str, start: int) -> bool:
    pattern = re.compile(r"\{/" + re.escape(tag) + r"\}", re.IGNORECASE)
    return pattern.search(text, start) is not None


def _has_closing_marker(text: str, marker: str, start: int) -> bool:
    return text.find(marker, start) != -1


def _parse_inline_markup(text: str) -> tuple[str, list[dict[str, Any]]]:
    """Parse inline Markdown/custom tags, supporting nested formatting."""
    output: list[str] = []
    styles: list[dict[str, Any]] = []
    # Entries: (kind, marker/tag name, output_start, style_token)
    stack: list[tuple[str, str, int, str]] = []
    out_len = 0
    i = 0

    def append(value: str) -> None:
        nonlocal out_len
        output.append(value)
        out_len += len(value)

    while i < len(text):
        # Allow literal custom tags with a leading backslash, e.g. \{red}.
        if text[i] == "\\":
            escaped_tag = _STYLE_TAG_RE.match(text, i + 1)
            if escaped_tag:
                append(escaped_tag.group(0))
                i = escaped_tag.end()
                continue

        # Keep the integration's previous link behavior: [label](url) becomes
        # the URL text itself. This is intentionally handled before other
        # inline markers so Markdown inside the label is not interpreted.
        if text[i] == "[":
            close_bracket = text.find("](", i)
            if close_bracket != -1:
                close_paren = text.find(")", close_bracket + 2)
                if close_paren != -1:
                    append(text[close_bracket + 2:close_paren])
                    i = close_paren + 1
                    continue

        # Existing inline-code compatibility: render code spans as italic and
        # leave all inner Markdown characters literal.
        if text[i] == "`":
            close_tick = text.find("`", i + 1)
            if close_tick != -1:
                start = out_len
                content = text[i + 1:close_tick]
                append(content)
                if content:
                    styles.append({"start": start, "len": len(content), "st": "i"})
                i = close_tick + 1
                continue

        tag_match = _STYLE_TAG_RE.match(text, i)
        if tag_match:
            is_close = bool(tag_match.group(1))
            tag = tag_match.group(2).lower()
            token = CUSTOM_STYLE_TAGS[tag]
            literal = tag_match.group(0)

            if is_close:
                # Close the nearest matching custom tag while keeping invalid
                # closing tags literal rather than deleting user text.
                match_index = next(
                    (idx for idx in range(len(stack) - 1, -1, -1)
                     if stack[idx][0] == "tag" and stack[idx][1] == tag),
                    None,
                )
                if match_index is None:
                    append(literal)
                else:
                    _, _, start, opened_token = stack.pop(match_index)
                    if out_len > start:
                        styles.append({"start": start, "len": out_len - start, "st": opened_token})
                i = tag_match.end()
                continue

            if _has_closing_tag(text, tag, tag_match.end()):
                stack.append(("tag", tag, out_len, token))
                i = tag_match.end()
                continue

            append(literal)
            i = tag_match.end()
            continue

        # Longest markers first to keep *** distinct from ** and *.
        marker_info = None
        if text.startswith("***", i):
            marker_info = ("***", "bi", "b,i")
        elif text.startswith("**", i):
            marker_info = ("**", "b", "b")
        elif text.startswith("~~", i):
            marker_info = ("~~", "s", "s")
        elif text.startswith("__", i):
            marker_info = ("__", "u", "u")
        elif text.startswith("*", i):
            marker_info = ("*", "i", "i")

        if marker_info:
            marker, kind, token = marker_info
            if stack and stack[-1][0] == "md" and stack[-1][1] == kind:
                _, _, start, opened_token = stack.pop()
                if out_len > start:
                    styles.append({"start": start, "len": out_len - start, "st": opened_token})
                i += len(marker)
                continue

            if _has_closing_marker(text, marker, i + len(marker)):
                stack.append(("md", kind, out_len, token))
                i += len(marker)
                continue

            append(marker)
            i += len(marker)
            continue

        append(text[i])
        i += 1

    # Defensive fallback for malformed nesting. Normally openings are added
    # only when a closing marker exists later. If malformed cross-nesting
    # leaves entries behind, do not invent style ranges beyond the text.
    if stack:
        _LOGGER.debug("Unclosed text-format markers after parse: %s", stack)

    return "".join(output), styles


def _line_text_length(line: str) -> int:
    content, _ = _split_line_ending(line)
    return len(content)


def _apply_line_directives(
    final_msg: str,
    directives: list[list[dict[str, Any]]],
    styles: list[dict[str, Any]],
) -> None:
    """Apply heading/list/indent directives to final plain-text line ranges."""
    offset = 0
    final_lines = final_msg.splitlines(keepends=True)

    for line_index, line in enumerate(final_lines):
        content_len = _line_text_length(line)
        if content_len > 0 and line_index < len(directives):
            for directive in directives[line_index]:
                style = {"start": offset, "len": content_len, **directive}
                styles.append(style)
        offset += len(line)


def _resolve_style_token(style_input: str | None) -> str | None:
    """Resolve the Markdown Color/select override to a Zalo style token."""
    if not style_input or style_input == "off":
        return None
    style_input = style_input.strip().lower()
    color_token = ZALO_COLORS.get(style_input)
    if color_token:
        return color_token + ",b"
    return style_input


def _style_tokens(style: dict[str, Any]) -> list[str]:
    return [token for token in str(style.get("st", "")).split(",") if token]


def _canonicalize_tokens(tokens: list[str]) -> list[str]:
    """Return tokens in the stable order used by Zalo text properties.

    If users accidentally nest conflicting colors or font sizes over the exact
    same range, the innermost style is completed first by the parser and is
    therefore kept as the first color/size token.
    """
    unique: list[str] = []
    for token in tokens:
        if token not in unique:
            unique.append(token)

    size = next((token for token in unique if token in {ZALO_SMALL, ZALO_BIG}), None)
    color = next((token for token in unique if token in _COLOR_TOKENS), None)
    ordered: list[str] = []
    if size:
        ordered.append(size)
    if color:
        ordered.append(color)
    for token in ("b", "i", "u", "s"):
        if token in unique:
            ordered.append(token)
    for token in unique:
        if token not in ordered and token not in {ZALO_SMALL, ZALO_BIG} and token not in _COLOR_TOKENS:
            ordered.append(token)
    return ordered


def _ranges_overlap(first: dict[str, Any], second: dict[str, Any]) -> bool:
    first_end = first["start"] + first["len"]
    second_end = second["start"] + second["len"]
    return first["start"] < second_end and second["start"] < first_end


def _apply_style_override(styles: list[dict[str, Any]], style_override: str | None) -> None:
    """Apply the legacy Markdown Color setting to bold ranges.

    Explicit inline color tags have priority. This preserves the old setting
    while allowing per-range colors without creating conflicting color tokens.
    """
    override_token = _resolve_style_token(style_override)
    if not override_token:
        return

    override_parts = [part for part in override_token.split(",") if part]
    override_is_color = any(part in _COLOR_TOKENS for part in override_parts)
    explicit_color_styles = [
        style for style in styles
        if any(token in _COLOR_TOKENS for token in _style_tokens(style))
    ]

    applied = 0
    for style in styles:
        tokens = _style_tokens(style)
        if "b" not in tokens:
            continue

        if override_is_color and any(
            other is not style and _ranges_overlap(style, other)
            for other in explicit_color_styles
        ):
            continue
        if override_is_color and any(token in _COLOR_TOKENS for token in tokens):
            continue

        new_tokens: list[str] = []
        for token in tokens:
            if token == "b":
                for override_part in override_parts:
                    if override_part not in new_tokens:
                        new_tokens.append(override_part)
            elif token not in new_tokens:
                new_tokens.append(token)
        style["st"] = ",".join(_canonicalize_tokens(new_tokens))
        applied += 1

    _LOGGER.debug(
        "Applied Markdown style override %s to %d bold style range(s)",
        style_override,
        applied,
    )


def _is_structural(style: dict[str, Any]) -> bool:
    return any(token in _STRUCTURAL_TOKENS for token in _style_tokens(style))


def _merge_identical_ranges(styles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Merge compatible inline styles that cover exactly the same range."""
    merged: list[dict[str, Any]] = []
    index_by_range: dict[tuple[int, int], int] = {}

    for style in styles:
        if _is_structural(style):
            merged.append(style)
            continue

        key = (style["start"], style["len"])
        existing_index = index_by_range.get(key)
        if existing_index is None:
            index_by_range[key] = len(merged)
            merged.append(dict(style))
            continue

        existing = merged[existing_index]
        tokens = _style_tokens(existing)
        for token in _style_tokens(style):
            if token not in tokens:
                tokens.append(token)
        existing["st"] = ",".join(_canonicalize_tokens(tokens))

    for style in merged:
        if not _is_structural(style):
            style["st"] = ",".join(_canonicalize_tokens(_style_tokens(style)))
    return merged


def _to_utf16_styles(final_msg: str, styles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Convert positions to UTF-16 and expand every style to one TextStyle.

    zca-js 2.1.2 types each Style.st as a single TextStyle enum value. The
    parser may combine tokens internally for convenient nesting, but the
    payload emitted here is strictly atomic and therefore matches that public
    contract.
    """
    result: list[dict[str, Any]] = []
    seen: set[tuple[int, int, str, int | None]] = set()
    utf16_offsets = _utf16_prefix_offsets(final_msg)

    for style in styles:
        py_start = style["start"]
        py_len = style["len"]
        if py_len <= 0 or not style.get("st"):
            continue

        py_end = py_start + py_len
        js_start = utf16_offsets[py_start]
        js_len = utf16_offsets[py_end] - js_start

        if style.get("st") == ZALO_INDENT:
            indent_size = int(style.get("indentSize", 1))
            key = (js_start, js_len, ZALO_INDENT, indent_size)
            if key not in seen:
                seen.add(key)
                result.append({
                    "start": js_start,
                    "len": js_len,
                    "st": ZALO_INDENT,
                    "indentSize": indent_size,
                })
            continue

        for token in _canonicalize_tokens(_style_tokens(style)):
            key = (js_start, js_len, token, None)
            if key in seen:
                continue
            seen.add(key)
            result.append({
                "start": js_start,
                "len": js_len,
                "st": token,
            })

    return result


def markdown_to_zalo_styles(text: str, style_override: str | None = None) -> dict[str, Any]:
    """Convert supported Markdown/custom markup to zca-js 2.1.2 styles.

    Supported legacy syntax is preserved: bold, italic, bold+italic,
    underline, strike-through, headings, blockquotes, inline code and links.
    Additional syntax supports Zalo colors/sizes plus Markdown-style ordered
    and unordered lists and leading-space indentation.
    """
    if not text or not isinstance(text, str):
        return {"msg": text or "", "styles": []}

    preprocessed, directives = _preprocess_line_syntax(text)
    final_msg, styles = _parse_inline_markup(preprocessed)
    _apply_line_directives(final_msg, directives, styles)

    # Merge exact inline overlaps first so constructs such as
    # {red}**Warning**{/red} become a single c_db342e,b range where possible.
    styles = _merge_identical_ranges(styles)
    _apply_style_override(styles, style_override)

    styles.sort(key=lambda item: (item["start"], item["len"], str(item.get("st", ""))))
    utf16_styles = _to_utf16_styles(final_msg, styles)

    _LOGGER.debug(
        "Formatted Zalo message: input_len=%d output_len=%d styles=%d",
        len(text),
        len(final_msg),
        len(utf16_styles),
    )
    return {"msg": final_msg, "styles": utf16_styles}
