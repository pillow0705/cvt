"""CLI entry point for cvt."""

from __future__ import annotations

import sys
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from cvt import __version__
from cvt.config import get_config
from cvt.log import setup_logging

console = Console()
err_console = Console(stderr=True)


# ---------------------------------------------------------------------------
# Root group
# ---------------------------------------------------------------------------

@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(__version__, "-V", "--version")
@click.option("-v", "--verbose", is_flag=True, default=False, help="Enable debug logging.")
@click.pass_context
def main(ctx: click.Context, verbose: bool) -> None:
    """cvt — Universal file format converter.

    Convert between office documents, config files, images, and more.
    Designed for use by humans and AI agents alike.

    Examples:\n
      cvt convert report.md report.pdf\n
      cvt convert data.json data.yaml\n
      cvt batch --from csv --to json --dir ./data\n
      cvt list formats\n
      cvt list backends --format md\n
    """
    cfg = get_config()
    effective_verbose = verbose or cfg.verbose
    setup_logging(effective_verbose)
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = effective_verbose


# ---------------------------------------------------------------------------
# `cvt convert`
# ---------------------------------------------------------------------------

@main.command("convert")
@click.argument("input", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.argument("output", type=click.Path(path_type=Path), required=False)
@click.option("--to", "dst_ext", metavar="EXT",
              help="Target format extension (e.g. pdf). Required when OUTPUT is omitted.")
@click.option("--backend", metavar="NAME",
              help="Force a specific backend (e.g. weasyprint, mammoth).")
@click.option("--no-overwrite", is_flag=True, default=False,
              help="Fail if the output file already exists.")
@click.pass_context
def cmd_convert(
    ctx: click.Context,
    input: Path,
    output: Path | None,
    dst_ext: str | None,
    backend: str | None,
    no_overwrite: bool,
) -> None:
    """Convert a single file from one format to another.

    INPUT  — source file path\n
    OUTPUT — destination file path (optional; derived from INPUT when omitted)\n

    Examples:\n
      cvt convert notes.md notes.pdf\n
      cvt convert config.yaml --to toml\n
      cvt convert photo.png photo.webp --backend pillow\n
    """
    from cvt.backends.base import BackendUnavailableError, ConversionError
    from cvt.converter import convert_file

    if output is None and dst_ext is None:
        raise click.UsageError(
            "Provide OUTPUT path or use --to EXT to specify the target format."
        )

    try:
        out_path = convert_file(
            src=input,
            dst=output,
            dst_ext=dst_ext,
            backend=backend,
            overwrite=not no_overwrite,
        )
        console.print(f"[green]✓[/green] {input} → {out_path}")
    except FileNotFoundError as exc:
        err_console.print(f"[red]Error:[/red] {exc}")
        sys.exit(1)
    except FileExistsError as exc:
        err_console.print(f"[yellow]Skipped:[/yellow] {exc}")
        sys.exit(2)
    except BackendUnavailableError as exc:
        err_console.print(f"[red]Backend unavailable:[/red] {exc}")
        sys.exit(3)
    except ConversionError as exc:
        err_console.print(f"[red]Conversion failed:[/red] {exc}")
        sys.exit(4)


# ---------------------------------------------------------------------------
# `cvt batch`
# ---------------------------------------------------------------------------

@main.command("batch")
@click.option("--from", "src_ext", required=True, metavar="EXT",
              help="Source format extension (e.g. md).")
@click.option("--to", "dst_ext", required=True, metavar="EXT",
              help="Target format extension (e.g. pdf).")
@click.option("--dir", "input_dir", default=".", show_default=True,
              type=click.Path(file_okay=False, exists=True, path_type=Path),
              help="Directory to search for source files.")
@click.option("--out-dir", "output_dir",
              type=click.Path(file_okay=False, path_type=Path),
              help="Directory to write output files. Defaults to per-file output-dir logic.")
@click.option("-r", "--recursive", is_flag=True, default=False,
              help="Search subdirectories recursively.")
@click.option("--backend", metavar="NAME",
              help="Force a specific backend.")
@click.option("--pattern", metavar="REGEX",
              help="Only convert files whose name matches this regex.")
@click.option("--no-overwrite", is_flag=True, default=False,
              help="Skip files whose output already exists.")
@click.pass_context
def cmd_batch(
    ctx: click.Context,
    src_ext: str,
    dst_ext: str,
    input_dir: Path,
    output_dir: Path | None,
    recursive: bool,
    backend: str | None,
    pattern: str | None,
    no_overwrite: bool,
) -> None:
    """Batch-convert all files of a given type in a directory.

    Examples:\n
      cvt batch --from md --to pdf --dir ./docs\n
      cvt batch --from csv --to json -r --out-dir ./output\n
      cvt batch --from png --to webp --pattern "^thumb_"\n
    """
    from cvt.converter import batch_convert

    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)

    results = batch_convert(
        src_ext=src_ext,
        dst_ext=dst_ext,
        input_dir=input_dir,
        output_dir=output_dir,
        recursive=recursive,
        backend=backend,
        overwrite=not no_overwrite,
        pattern=pattern,
    )

    if not results:
        console.print(f"[yellow]No .{src_ext} files found in {input_dir}[/yellow]")
        return

    ok = [(s, d) for s, d in results if isinstance(d, Path)]
    fail = [(s, d) for s, d in results if isinstance(d, Exception)]

    for src, dst in ok:
        console.print(f"[green]✓[/green] {src.name} → {dst.name}")
    for src, exc in fail:
        err_console.print(f"[red]✗[/red] {src.name}: {exc}")

    console.print(
        f"\n[bold]{len(ok)} converted[/bold], "
        f"[{'red' if fail else 'green'}]{len(fail)} failed[/{'red' if fail else 'green'}]"
    )

    if fail:
        sys.exit(1)


# ---------------------------------------------------------------------------
# `cvt list`
# ---------------------------------------------------------------------------

@main.group("list")
def cmd_list() -> None:
    """List supported formats and available backends."""


@cmd_list.command("formats")
@click.option("--all", "show_all", is_flag=True, default=False,
              help="Show all registered conversions, including unavailable ones.")
def cmd_list_formats(show_all: bool) -> None:
    """List supported format conversions.

    By default only shows conversions where at least one backend is installed.
    Use --all to see every registered pair.
    """
    from cvt.registry import get_registry
    reg = get_registry()

    if show_all:
        rows = reg.all_conversions()
        title = "All Registered Conversions"
    else:
        rows = reg.available_conversions()
        title = "Available Conversions (installed backends)"

    table = Table(title=title, show_lines=False)
    table.add_column("From", style="cyan", no_wrap=True)
    table.add_column("To", style="green", no_wrap=True)
    table.add_column("Backends", style="yellow")

    for src, dst, names in rows:
        table.add_row(src, dst, ", ".join(names))

    console.print(table)
    if not show_all:
        console.print("[dim]Tip: use --all to see conversions requiring additional packages[/dim]")


@cmd_list.command("backends")
@click.option("--format", "fmt", metavar="EXT",
              help="Filter by source format (e.g. md).")
def cmd_list_backends(fmt: str | None) -> None:
    """List all backends and their availability status."""
    from cvt.backends import ALL_BACKENDS

    table = Table(title="Backends", show_lines=False)
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Status", no_wrap=True)
    table.add_column("Formats supported", style="dim")
    table.add_column("Missing packages", style="red")

    for cls in ALL_BACKENDS:
        if fmt:
            pairs = [(s, d) for s, d in cls.supported if s == fmt.lower() or d == fmt.lower()]
            if not pairs:
                continue
        else:
            pairs = cls.supported

        available = cls.is_available()
        status = "[green]✓ available[/green]" if available else "[red]✗ missing[/red]"
        fmt_list = ", ".join(f"{s}→{d}" for s, d in pairs[:6])
        if len(pairs) > 6:
            fmt_list += f" (+{len(pairs)-6} more)"
        missing = ", ".join(cls.missing_packages())

        table.add_row(cls.name, status, fmt_list, missing)

    console.print(table)


# ---------------------------------------------------------------------------
# `cvt config`
# ---------------------------------------------------------------------------

@main.group("config")
def cmd_config() -> None:
    """View or modify cvt configuration."""


@cmd_config.command("show")
def cmd_config_show() -> None:
    """Print current configuration."""
    import json
    cfg = get_config()
    console.print(f"[dim]Config file:[/dim] {cfg.path}")
    console.print_json(json.dumps(cfg.as_dict(), indent=2))


@cmd_config.command("set")
@click.argument("key")
@click.argument("value")
def cmd_config_set(key: str, value: str) -> None:
    """Set a configuration value.

    KEY uses dot notation, e.g. defaults.output_dir or backends.md->pdf

    Examples:\n
      cvt config set defaults.output_dir source\n
      cvt config set backends.md->pdf weasyprint\n
    """
    cfg = get_config()
    # Coerce common value types
    if value.lower() == "true":
        val: object = True
    elif value.lower() == "false":
        val = False
    else:
        val = value
    cfg.set(key, val)
    console.print(f"[green]Set[/green] {key} = {val!r}  (saved to {cfg.path})")


@cmd_config.command("path")
def cmd_config_path() -> None:
    """Print the path to the config file."""
    console.print(get_config().path)
