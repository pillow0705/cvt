# cvt — Universal File Format Converter

A fast, extensible command-line tool for converting between dozens of file formats. Designed for use by humans and AI agents alike.

> **For AI agents:** Please follow [agent.md](agent.md) to complete software installation and skill installation. You do not need to read any other code.

## Features

- **Data formats**: JSON ↔ YAML ↔ TOML ↔ XML ↔ CSV ↔ TSV ↔ INI
- **Markup**: Markdown ↔ HTML ↔ TXT, Markdown/HTML → PDF
- **Office documents**: DOCX → HTML / Markdown / TXT / PDF, XLSX ↔ CSV / JSON, PPTX → TXT / HTML
- **Images**: PNG, JPG, WebP, BMP, GIF, TIFF (any ↔ any via Pillow)
- **Batch conversion** with recursive directory support
- **Modular backend system** — choose which library handles each conversion
- **Cross-platform**: Linux and Windows

---

## Installation

### Minimal (data + markup formats)

```bash
pip install cvt-tool
```

### With office document support

```bash
pip install "cvt-tool[office]"
```

### With PDF support

```bash
pip install "cvt-tool[pdf]"
```

### With image support

```bash
pip install "cvt-tool[image]"
```

### Full installation (everything)

```bash
pip install "cvt-tool[full]"
```

---

## Quick Start

```bash
# Convert a Markdown file to HTML
cvt convert README.md README.html

# Convert a Markdown file to PDF
cvt convert README.md README.pdf

# Convert JSON to YAML
cvt convert config.json config.yaml

# Convert CSV to JSON (output goes to current directory)
cvt convert data.csv --to json

# Batch-convert all Markdown files in a directory to PDF
cvt batch --from md --to pdf --dir ./docs --out-dir ./output

# Batch-convert recursively
cvt batch --from csv --to json --dir ./data -r

# Convert an image
cvt convert photo.png photo.webp
```

---

## CLI Reference

### `cvt convert`

```
cvt convert INPUT [OUTPUT] [OPTIONS]

Arguments:
  INPUT   Source file path
  OUTPUT  Destination file path (optional)

Options:
  --to EXT          Target format extension (used when OUTPUT is omitted)
  --backend NAME    Force a specific backend (e.g. weasyprint, mammoth)
  --no-overwrite    Fail if the output file already exists
  -v, --verbose     Enable debug logging
  -h, --help        Show help
```

**Output path rules:**
- If `OUTPUT` is given, use it directly.
- If `OUTPUT` is a directory, place the file inside it.
- If `OUTPUT` is omitted, the file is written to the **current working directory** with the same stem and the new extension.

### `cvt batch`

```
cvt batch --from EXT --to EXT [OPTIONS]

Options:
  --from EXT        Source format extension (required)
  --to EXT          Target format extension (required)
  --dir PATH        Directory to search (default: current directory)
  --out-dir PATH    Directory to write output files
  -r, --recursive   Search subdirectories
  --backend NAME    Force a specific backend
  --pattern REGEX   Only convert files matching this regex
  --no-overwrite    Skip files whose output already exists
```

### `cvt list formats`

```
cvt list formats [--all]
```

Shows supported format conversions. Without `--all`, only shows conversions where at least one backend is installed.

### `cvt list backends`

```
cvt list backends [--format EXT]
```

Shows all backends, their availability, and which packages are missing.

### `cvt config`

```
cvt config show
cvt config set KEY VALUE
cvt config path
```

**Config keys:**

| Key | Default | Description |
|-----|---------|-------------|
| `defaults.output_dir` | `cwd` | Where output goes: `cwd` or `source` |
| `defaults.verbose` | `false` | Always enable debug logging |
| `backends.md->pdf` | _(auto)_ | Preferred backend for md→pdf |
| `backends.html->pdf` | _(auto)_ | Preferred backend for html→pdf |

Config file location:
- Linux/macOS: `~/.config/cvt/config.toml`
- Windows: `%APPDATA%\cvt\config.toml`

---

## Supported Format Matrix

### Data / Configuration

| From ↓ \ To → | JSON | YAML | TOML | XML | CSV | TSV | INI |
|---------------|------|------|------|-----|-----|-----|-----|
| JSON          | —    | ✓    | ✓    | ✓   | ✓   | ✓   | ✓   |
| YAML          | ✓    | —    | ✓    | ✓   | ✓   | ✓   | ✓   |
| TOML          | ✓    | ✓    | —    | ✓   | ✓   | ✓   | ✓   |
| XML           | ✓    | ✓    | ✓    | —   | ✓   | ✓   | ✓   |
| CSV           | ✓    | ✓    | ✓    | ✓   | —   | ✓   | ✓   |
| TSV           | ✓    | ✓    | ✓    | ✓   | ✓   | —   | ✓   |
| INI           | ✓    | ✓    | ✓    | ✓   | ✓   | ✓   | —   |

### Markup / Documents

| From \ To | HTML | MD | TXT | PDF |
|-----------|------|----|-----|-----|
| Markdown  | ✓    | —  | ✓   | ✓ * |
| HTML      | —    | ✓  | ✓   | ✓ * |
| TXT       | ✓    | ✓  | —   | —   |
| DOCX      | ✓ *  | ✓ *| ✓ * | ✓ * |
| PPTX      | ✓ *  | —  | ✓ * | —   |
| PDF       | —    | ✓ *| ✓ * | —   |

`*` requires optional packages (see Installation)

### Office / Spreadsheet

| From \ To | CSV | JSON | XLSX |
|-----------|-----|------|------|
| XLSX      | ✓ * | ✓ *  | —    |
| CSV       | —   | ✓    | ✓ *  |

### Images (requires `[image]`)

PNG, JPG/JPEG, WebP, BMP, GIF, TIFF ↔ any of the above

---

## Backends

cvt uses a pluggable backend system. Each conversion can have multiple backends; cvt picks the first one that is installed.

| Backend | Package | Conversions |
|---------|---------|-------------|
| `data` | pyyaml, lxml, tomli-w | All data format pairs |
| `markdown` | markdown | md → html |
| `markdown-txt` | markdown, html2text | md → txt |
| `weasyprint` | weasyprint | md → pdf, html → pdf |
| `html2text` | html2text | html → md |
| `mammoth` | mammoth | docx → html/md/txt |
| `mammoth-md` | mammoth | docx → md |
| `docx2pdf` | docx2pdf / weasyprint | docx → pdf |
| `pdfminer` | pdfminer.six | pdf → txt/md |
| `openpyxl-csv` | openpyxl | xlsx → csv |
| `openpyxl-json` | openpyxl | xlsx → json |
| `openpyxl-xlsx` | openpyxl | csv → xlsx |
| `pptx-txt` | python-pptx | pptx → txt |
| `pptx-html` | python-pptx | pptx → html |
| `pillow` | Pillow | image ↔ image |

### Selecting a backend

```bash
# Force a specific backend
cvt convert doc.md doc.pdf --backend weasyprint

# Set a permanent preference in config
cvt config set backends.md->pdf weasyprint
```

---

## Exit Codes

| Code | Meaning |
|------|---------|
| 0    | Success |
| 1    | File not found or batch had failures |
| 2    | Output already exists (--no-overwrite) |
| 3    | Backend unavailable (missing package) |
| 4    | Conversion failed |

---

## Development

```bash
git clone https://github.com/pillow0705/cvt
cd cvt
pip install -e ".[dev]"
pytest
```

---

## License

MIT
