"""Type-check every Python snippet in the mailchannels-python skill.

For each Markdown file under `.agents/skills/mailchannels-python/`:

1. Extract every fenced Python code block (```python … ```).
2. Substitute the documentation placeholder `{...}` (a set containing a
   single `Ellipsis` literal) with `{}` so payloads written as
   `Emails.queue({...})` round-trip through the type-checker. This is the
   only textual rewrite the script performs.
3. Concatenate the surviving blocks for that file into a single Python
   source so cross-block references resolve (e.g. `MySyncTransport`
   defined in one block and used in the next).
4. Prepend a fixed preamble that defines standard "dummy" names so
   documentation can use them without writing the boilerplate inline.
   See "Documentation Dummies" below.
5. If the resulting body uses `await` / `async with` / `async for` at top
   level — illegal at module scope — wrap just the body in
   `async def _runner(): …` (the preamble stays at module scope).
6. Hand the assembled source to mypy with the project's `pyproject.toml`
   config and report failures, attributing errors back to the source
   Markdown file.

Exit code is `0` when every file's snippets pass, `1` otherwise.

## Documentation Dummies

Snippets may freely reference these names; the script's preamble defines
them with correct types so doc authors don't have to litter examples
with boilerplate. Use the same names across resources for consistency:

- `message: SendParams` — a pre-built send payload, for snippets that
  want to write `mailchannels.Emails.queue(message)` rather than spelling
  out a full dict in every example.
- `payload: list[dict[str, Any]]` — the JSON-array body a webhook
  endpoint receives.
- `result: Any` — an opaque return value placeholder.
- `logger: logging.Logger` — a standard logger; saves an import + setup
  every time logging is illustrated.
- `time` — imported, so `time.sleep(exc.retry_after or 10)` works.
- `cast` — imported from `typing`, available for snippets that need to
  narrow a value's static type.
- `some_coroutine` — an `async def` stand-in; snippets that need to
  illustrate awaiting an arbitrary coroutine can write
  `await some_coroutine()`.

Run with `--show-source` to print the assembled Python before checking;
useful when an error message points at a line you'd like to inspect.
"""

from __future__ import annotations

import argparse
import logging
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / ".agents" / "skills" / "mailchannels-python"

PYTHON_BLOCK = re.compile(
    r"^```python[ \t]*\n(?P<body>.*?)\n^```[ \t]*$",
    re.DOTALL | re.MULTILINE,
)
PLACEHOLDER_DICT = re.compile(r"\{\.\.\.\}")
# Top-level use of async constructs — match only column-0 occurrences so
# that indented `await`s inside an already-defined async function aren't
# treated as needing the wrapper.
TOPLEVEL_ASYNC = re.compile(
    r"^(await\b|async\s+with\b|async\s+for\b)",
    re.MULTILINE,
)

# Auto-injected scaffolding prepended to every assembled snippet group.
# Defines the standard documentation dummies described in the module
# docstring. Keep this in sync with that docstring.
PREAMBLE = '''\
"""Auto-injected preamble for documentation snippet type-checking."""
from __future__ import annotations

import asyncio  # noqa: F401
import logging
import time  # noqa: F401
from typing import Any, cast  # noqa: F401

import mailchannels

logger = logging.getLogger(__name__)
message = cast("mailchannels.SendParams", {})
payload: list[dict[str, Any]] = [{"url": "foo"}]
result: Any = None


async def some_coroutine() -> None:
    """Stand-in for an arbitrary coroutine in async snippets."""
'''


@dataclass(frozen=True)
class Block:
    """Python code block extracted from a Markdown file."""
    body: str
    """1-based Markdown line of the first line *inside* the ```python fence."""
    start_line: int


@dataclass(frozen=True)
class SourceLine:
    """Line of assembled Python with its origin in the source Markdown."""
    text: str
    """1-based Markdown source line, or None for synthetic scaffolding."""
    md_line: int | None


@dataclass(frozen=True)
class AssembledSource:
    """Synthesized Python source for one Markdown file, with a line-origin map."""
    source: str
    """1-based Python line → 1-based Markdown line, or None for synthetic lines."""
    py_to_md: tuple[int | None, ...]


@dataclass(frozen=True)
class MypyResult:
    """Outcome of running mypy on one assembled snippet group."""
    returncode: int
    output: str


def extract_blocks(markdown: str) -> list[Block]:
    """
    `Block.start_line` points at the first line *inside* the opening
    ```` ```python ```` fence — the same place mypy lands when it reports
    an error on the snippet's first line.
    """
    blocks: list[Block] = []
    for match in PYTHON_BLOCK.finditer(markdown):
        body = match.group("body")
        opening_fence_line = markdown.count("\n", 0, match.start()) + 1
        blocks.append(Block(body=body, start_line=opening_fence_line + 1))
    return blocks


def needs_async_wrap(source: str) -> bool:
    """Return True if the source has column-0 await/async with/async for."""
    return TOPLEVEL_ASYNC.search(source) is not None


def assemble(blocks: list[Block]) -> AssembledSource:
    """Concatenate blocks into one Python source plus a py→markdown line map.

    The result has three layers (top to bottom): the fixed `PREAMBLE`
    (always module-scope), the body assembled from `blocks`, and the
    optional async-wrapper tail. `AssembledSource.py_to_md[i]` is the
    1-based Markdown line for synthesized Python line `i` (1-based),
    or `None` for synthetic lines (the preamble, block separators, the
    async wrapper scaffolding).
    """
    lines: list[SourceLine] = []

    # Layer 1 — preamble (always module-scope, never gets indented).
    for preamble_line in PREAMBLE.splitlines():
        lines.append(SourceLine(text=preamble_line, md_line=None))

    # Layer 2 — the body collected from the snippet blocks.
    body_start = len(lines)
    for index, block in enumerate(blocks):
        if index > 0:
            lines.append(SourceLine(text="", md_line=None))
        # Replace {...} placeholders with an empty object {}
        cleaned = PLACEHOLDER_DICT.sub("{}", block.body).splitlines()
        for offset, text in enumerate(cleaned):
            lines.append(SourceLine(text=text, md_line=block.start_line + offset))

    body_text = "\n".join(line.text for line in lines[body_start:])

    # Layer 3 — wrap only the body when it has top-level async syntax.
    if needs_async_wrap(body_text):
        body_lines = lines[body_start:]
        lines = lines[:body_start]
        lines.append(SourceLine(text="async def _runner() -> None:", md_line=None))
        for line in body_lines:
            indented = ("    " + line.text) if line.text else ""
            lines.append(SourceLine(text=indented, md_line=line.md_line))
        lines.append(SourceLine(text="", md_line=None))
        lines.append(SourceLine(text="asyncio.run(_runner())", md_line=None))

    source = "\n".join(line.text for line in lines) + "\n"
    py_to_md: tuple[int | None, ...] = (None, *(line.md_line for line in lines))
    return AssembledSource(source=source, py_to_md=py_to_md)


def rewrite_line_numbers(
    output: str,
    label: str,
    py_to_md: tuple[int | None, ...],
) -> str:
    """Substitute synthetic Python line numbers with their Markdown sources."""
    pattern = re.compile(
        rf"^({re.escape(label)}):(\d+):", re.MULTILINE
    )

    def replacement(match: re.Match[str]) -> str:
        py_line = int(match.group(2))
        if 0 < py_line < len(py_to_md):
            md_line = py_to_md[py_line]
            if md_line is not None:
                return f"{match.group(1)}:{md_line}:"
        return f"{match.group(1)}:?(py {py_line}):"

    return pattern.sub(replacement, output)


def run_mypy(source: str, label: str) -> MypyResult:
    """Write source to a temp file, run mypy, return its result."""
    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".py",
        delete=False,
        dir=ROOT,
    ) as handle:
        handle.write(source)
        tmp_path = Path(handle.name)
    try:
        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "mypy",
                "--config-file",
                str(ROOT / "pyproject.toml"),
                "--show-error-codes",
                "--no-error-summary",
                "--no-incremental",
                str(tmp_path),
            ],
            capture_output=True,
            text=True,
            cwd=ROOT,
            check=False,
        )
        # mypy may emit either the absolute path or just the basename;
        # rewrite both forms so error lines point back at the Markdown file.
        # Line-number remapping happens separately in main().
        output = completed.stdout + completed.stderr
        output = output.replace(str(tmp_path), label)
        output = output.replace(tmp_path.name, label)
        return MypyResult(returncode=completed.returncode, output=output)
    finally:
        tmp_path.unlink(missing_ok=True)


def discover_markdown() -> list[Path]:
    """Return SKILL.md plus every resource Markdown file, in stable order."""
    files: list[Path] = []
    skill_md = SKILL_DIR / "SKILL.md"
    if skill_md.is_file():
        files.append(skill_md)
    resources = SKILL_DIR / "resources"
    if resources.is_dir():
        files.extend(sorted(resources.glob("*.md")))
    return files


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description=(
            "Type-check Python snippets embedded in the mailchannels-python skill."
        )
    )
    parser.add_argument(
        "resource",
        nargs="?",
        metavar="RESOURCE",
        help=(
            "Optional resource file name to check (e.g. 'emails' or 'emails.md'). "
            "Also matches 'SKILL' for SKILL.md. If omitted, all files are checked."
        ),
    )
    parser.add_argument(
        "--show-source",
        action="store_true",
        help="Print the assembled Python source for each file before checking.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Log debug-level messages (e.g. skipped blocks).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Run mypy against every snippet under the mailchannels-python skill."""
    args = parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(message)s",
    )

    if not SKILL_DIR.is_dir():
        logger.error("Skill directory not found: %s", SKILL_DIR)
        return 2

    md_files = discover_markdown()
    if not md_files:
        logger.error("No Markdown files found under %s", SKILL_DIR)
        return 2

    if args.resource:
        target = Path(args.resource).with_suffix(".md").name
        md_files = [f for f in md_files if f.name == target]
        if not md_files:
            logger.error("Resource not found: %s (expected a file named %s)",
                         args.resource, target)
            return 2

    total_blocks = 0
    failed: list[str] = []

    for md in md_files:
        rel = md.relative_to(ROOT)
        blocks = extract_blocks(md.read_text(encoding="utf-8"))
        if not blocks:
            logger.info("[skip] %s — no Python blocks", rel)
            continue
        total_blocks += len(blocks)
        assembled = assemble(blocks)
        if args.show_source:
            logger.info(
                "--- assembled source for %s ---\n%s---", rel, assembled.source
            )
        mypy_result = run_mypy(assembled.source, str(rel))
        output = rewrite_line_numbers(
            mypy_result.output, str(rel), assembled.py_to_md
        )
        if mypy_result.returncode == 0:
            logger.info("[ ok ] %s (%d block%s)",
                        rel, len(blocks), "" if len(blocks) == 1 else "s")
        else:
            failed.append(str(rel))
            logger.error("[FAIL] %s (%d block%s)\n%s",
                         rel, len(blocks), "" if len(blocks) == 1 else "s",
                         output.rstrip() or "(no output)")

    logger.info(
        "\nChecked %d file%s / %d block%s. %d failed.",
        len(md_files),
        "" if len(md_files) == 1 else "s",
        total_blocks,
        "" if total_blocks == 1 else "s",
        len(failed),
    )
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
