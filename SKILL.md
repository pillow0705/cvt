# Skill: cvt — File Format Converter

## Overview

`cvt` is a command-line tool installed on this machine for converting files between different formats. It supports office documents, configuration files, markup languages, and images. It is designed to be called directly from the terminal without any interactive UI.

---

## Installation Check

```bash
cvt --version
```

If the command is not found, install it with:

```bash
pip install "cvt-tool[full]"
```

---

## Command: `cvt convert`

Convert a single file from one format to another.

### Syntax

```
cvt convert INPUT [OUTPUT] [--to EXT] [--backend NAME] [--no-overwrite] [-v]
```

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `INPUT` | path | Yes | Path to the source file |
| `OUTPUT` | path | No | Path to write the output file. If a directory is given, the file is placed inside it. If omitted, output goes to the **current working directory** with the same filename and new extension. |
| `--to EXT` | string | Conditional | Target format extension (e.g. `pdf`, `yaml`). Required when `OUTPUT` is omitted. |
| `--backend NAME` | string | No | Force a specific conversion backend (e.g. `weasyprint`, `mammoth`, `pillow`). If omitted, the best available backend is chosen automatically. |
| `--no-overwrite` | flag | No | Exit with code 2 instead of overwriting an existing output file. |
| `-v` / `--verbose` | flag | No | Enable debug-level logging. |

### Examples

```bash
# Markdown → PDF
cvt convert report.md report.pdf

# JSON → YAML (output to current directory as config.yaml)
cvt convert config.json --to yaml

# HTML → Markdown (explicit output path)
cvt convert page.html page.md

# DOCX → TXT using a specific backend
cvt convert document.docx document.txt --backend mammoth-txt

# PNG → WebP
cvt convert photo.png photo.webp

# CSV → JSON, save next to the source file
cvt convert data.csv data.json

# Do not overwrite existing file
cvt convert notes.md notes.html --no-overwrite
```

### Output path rules

1. If `OUTPUT` is a full file path → write there.
2. If `OUTPUT` is a directory → write `{INPUT_STEM}.{TARGET_EXT}` inside it.
3. If `OUTPUT` is omitted → write `{INPUT_STEM}.{TARGET_EXT}` in the **current working directory**.

---

## Command: `cvt batch`

Convert all files of a given type in a directory.

### Syntax

```
cvt batch --from EXT --to EXT [--dir PATH] [--out-dir PATH] [-r] [--backend NAME] [--pattern REGEX] [--no-overwrite]
```

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `--from EXT` | string | Yes | Source format extension (e.g. `md`, `csv`) |
| `--to EXT` | string | Yes | Target format extension (e.g. `pdf`, `json`) |
| `--dir PATH` | path | No | Directory to search. Defaults to current directory (`.`). |
| `--out-dir PATH` | path | No | Directory to write all output files. If omitted, each output follows the default output-dir rule (current working directory). |
| `-r` / `--recursive` | flag | No | Search subdirectories recursively. |
| `--backend NAME` | string | No | Force a specific backend for all conversions. |
| `--pattern REGEX` | string | No | Only convert files whose filename matches this regular expression. |
| `--no-overwrite` | flag | No | Skip files whose output already exists. |

### Examples

```bash
# Convert all Markdown files in ./docs to PDF, output to ./output
cvt batch --from md --to pdf --dir ./docs --out-dir ./output

# Convert all CSV files in current directory to JSON
cvt batch --from csv --to json

# Convert recursively, only files starting with "report_"
cvt batch --from xlsx --to csv --dir ./data -r --pattern "^report_"
```

---

## Command: `cvt list formats`

List all supported conversions.

```bash
# Show only conversions where at least one backend is installed
cvt list formats

# Show all conversions including those needing additional packages
cvt list formats --all
```

---

## Command: `cvt list backends`

Show all backends, their install status, and any missing packages.

```bash
cvt list backends

# Filter by format
cvt list backends --format md
```

---

## Command: `cvt config`

View or modify persistent configuration.

```bash
# Show current config and its file path
cvt config show

# Print the config file path
cvt config path

# Set output directory mode: "cwd" (current working directory) or "source" (next to source file)
cvt config set defaults.output_dir source

# Set a preferred backend for a conversion pair
cvt config set backends.md->pdf weasyprint
cvt config set backends.html->pdf weasyprint

# Enable verbose logging by default
cvt config set defaults.verbose true
```

Config file locations:
- **Linux / macOS**: `~/.config/cvt/config.toml`
- **Windows**: `%APPDATA%\cvt\config.toml`

---

## Supported Formats

### Data / Configuration (always available)

`json`, `yaml`, `toml`, `xml`, `csv`, `tsv`, `ini`

All pairs are supported bidirectionally.

### Markup (core install)

| From | To |
|------|----|
| `md` | `html`, `txt` |
| `html` | `md`, `txt` |
| `txt` | `md`, `html` |

### Markup → PDF (requires `pip install "cvt-tool[pdf]"`)

| From | To |
|------|----|
| `md` | `pdf` |
| `html` | `pdf` |

### Office Documents (requires `pip install "cvt-tool[office]"`)

| From | To |
|------|----|
| `docx` | `html`, `md`, `txt`, `pdf` |
| `xlsx` | `csv`, `json` |
| `csv` | `xlsx` |
| `pptx` | `txt`, `html` |

### PDF Extraction (requires `pip install "cvt-tool[pdf]"`)

| From | To |
|------|----|
| `pdf` | `txt`, `md` |

### Images (requires `pip install "cvt-tool[image]"`)

`png`, `jpg`, `jpeg`, `webp`, `bmp`, `gif`, `tiff` ↔ any of the above

---

## Exit Codes

| Code | Meaning |
|------|---------|
| `0` | Success |
| `1` | Source file not found, or one or more batch conversions failed |
| `2` | Output file already exists (`--no-overwrite` was set) |
| `3` | No backend available for the requested conversion (missing package) |
| `4` | Conversion failed due to a library or format error |

---

## Tips for AI Agents

- Always use **absolute paths** to avoid ambiguity with relative path resolution.
- If a conversion fails with exit code `3`, run `cvt list backends` to see what packages are missing, then install them.
- Use `--to EXT` instead of specifying an output path when you only care about the format, not the exact location.
- Use `cvt list formats` to check if a conversion is supported before attempting it.
- For batch jobs, `--out-dir` is recommended to keep outputs organised and predictable.
