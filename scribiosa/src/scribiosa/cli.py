from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from collections import deque
from datetime import datetime, timezone
from importlib.resources import files
from pathlib import Path
from urllib.parse import unquote, urlsplit

import click
from markdown_it import MarkdownIt

FORMATS = {"html": "html", "docx": "docx", "pdf": "pdf"}
MARKDOWN_EXTENSIONS = {".md", ".markdown"}


def linked_markdown(root: Path) -> tuple[list[Path], list[Path]]:
    parser = MarkdownIt()
    pending = deque([root])
    visited: set[Path] = set()
    references: set[Path] = set()

    while pending:
        document = pending.popleft().resolve()
        if document in visited:
            continue
        if not document.is_file():
            raise click.ClickException(f"Linked Markdown file does not exist: {document}")
        visited.add(document)

        for token in parser.parse(document.read_text(encoding="utf-8")):
            for child in token.children or []:
                if child.type == "link_open":
                    target = child.attrGet("href") or ""
                elif child.type == "image":
                    target = child.attrGet("src") or ""
                else:
                    continue

                parsed = urlsplit(target)
                if parsed.scheme or parsed.netloc or not parsed.path:
                    continue
                referenced = (document.parent / unquote(parsed.path)).resolve()
                if referenced.suffix.lower() in MARKDOWN_EXTENSIONS:
                    if not referenced.is_file():
                        raise click.ClickException(f"Linked Markdown file does not exist: {referenced}")
                    if referenced not in visited:
                        pending.append(referenced)
                elif referenced.is_file():
                    references.add(referenced)

    return sorted(visited), sorted(references)


def output_path(document: Path, source_root: Path, destination: Path, extension: str) -> Path:
    relative = document.relative_to(source_root)
    return destination / relative.with_suffix(f".{extension}")


def convert(
    source: Path, destination: Path, output_format: str, stylesheet: Path | None = None
) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    command = [
        "pandoc", str(source), "--standalone", "--from", "markdown", "--to", output_format,
        "--lua-filter", str(files("scribiosa").joinpath("link-target.lua")),
    ]
    if output_format == "html" and stylesheet is not None:
        command.extend(["--css", os.path.relpath(stylesheet, destination.parent)])
    command.extend(["--output", str(destination)])
    subprocess.run(
        command,
        check=True,
    )


def copy_references(references: list[Path], source_root: Path, destination: Path) -> list[Path]:
    copied: list[Path] = []
    for reference in references:
        relative = reference.relative_to(source_root)
        output = destination / relative
        output.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(reference, output)
        copied.append(output)
        click.echo(f"Copied {output}")
    return copied


def copy_stylesheet(destination: Path) -> Path:
    stylesheet = destination / "github.css"
    stylesheet.parent.mkdir(parents=True, exist_ok=True)
    with files("scribiosa").joinpath("github.css").open("rb") as source:
        with stylesheet.open("wb") as target:
            shutil.copyfileobj(source, target)
    return stylesheet


def build_report(
    root: Path,
    source_root: Path,
    formats: list[str],
    outputs: list[Path],
    destination: Path,
    started: datetime,
) -> str:
    lines = [
        "---",
        "title: Build Report",
        "---",
        "",
        "# Build Report",
        "",
        "## Build Information",
        "",
        f"- Started: {started.isoformat()}",
        f"- Completed: {datetime.now(timezone.utc).isoformat()}",
        "",
        "## Settings",
        "",
        f"- Root document: `{root}`",
        f"- Formats: {', '.join(formats)}",
        "",
        "## Build Log",
        "",
        f"- Generated {len(outputs)} document and asset file(s).",
        "",
        "## Root Document",
        "",
    ]
    for output in outputs:
        root_output = root.relative_to(source_root).with_suffix(output.suffix)
        if output.relative_to(destination) == root_output:
            relative_output = output.relative_to(destination)
            lines.append(f"- [{relative_output.name}]({relative_output.as_posix()})")
    lines.extend(["", "## Generated Files", ""])
    lines.extend(f"- `{output.relative_to(destination).as_posix()}`" for output in outputs)
    return "\n".join(lines) + "\n"


@click.group()
def main() -> None:
    """Build linked Markdown documentation."""


@main.command()
@click.argument("root_document", type=click.Path(path_type=Path, exists=True, dir_okay=False))
@click.option(
    "--format", "format_name", type=click.Choice(["html", "docx", "pdf", "all"]),
    default="html", show_default=True,
)
@click.option("--output-dir", type=click.Path(path_type=Path, file_okay=False))
@click.option("--no-build-report", is_flag=True, help="Do not generate a build report.")
def conjure(root_document: Path, format_name: str, output_dir: Path | None,
            no_build_report: bool) -> None:
    """Convert a root Markdown document and its linked Markdown files."""
    if shutil.which("pandoc") is None:
        raise click.ClickException("Pandoc was not found on PATH.")

    root = root_document.resolve()
    destination = output_dir.resolve() if output_dir else Path(tempfile.mkdtemp(prefix="scribiosa-"))
    formats = list(FORMATS) if format_name == "all" else [format_name]
    started = datetime.now(timezone.utc)
    documents, references = linked_markdown(root)
    source_root = Path(
        os.path.commonpath(
            [
                str(root.parent),
                *(str(document.parent) for document in documents),
                *(str(reference.parent) for reference in references),
            ]
        )
    )
    outputs: list[Path] = []

    try:
        outputs.extend(copy_references(references, source_root, destination))
        stylesheet = copy_stylesheet(destination) if "html" in formats else None
        if stylesheet is not None:
            outputs.append(stylesheet)

        for document in documents:
            for selected_format in formats:
                output = output_path(document, source_root, destination, selected_format)
                convert(document, output, FORMATS[selected_format], stylesheet)
                outputs.append(output)
                click.echo(f"Generated {output}")

        if not no_build_report:
            report_markdown = build_report(root, source_root, formats, outputs, destination, started)
            with tempfile.TemporaryDirectory(prefix="scribiosa-report-") as temporary_dir:
                report_source = Path(temporary_dir) / "build-report.md"
                report_source.write_text(report_markdown, encoding="utf-8")
                for selected_format in formats:
                    report_output = destination / f"build-report.{selected_format}"
                    convert(report_source, report_output, FORMATS[selected_format], stylesheet)
                    outputs.append(report_output)
                    click.echo(f"Generated {report_output}")
    except subprocess.CalledProcessError as error:
        raise click.ClickException(f"Pandoc failed with exit code {error.returncode}.") from error

    click.echo(f"Output directory: {destination}")