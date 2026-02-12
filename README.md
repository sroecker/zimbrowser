# ZIM Browser

A Python-based tool for browsing and exploring ZIM (Zeno Information Model) archives. ZIM files are compressed archive formats used primarily for offline storage of Wikipedia and other wiki content.

![Python Version](https://img.shields.io/badge/python-3.12+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## Features

- **CLI Tool** (`list_zim_articles.py`): List, search, and dump articles from ZIM files
- **TUI Browser** (`zim_browser.py`): Interactive terminal UI for browsing ZIM archives with:
  - Sidebar article list with search
  - HTML to Markdown content rendering
  - Full keyboard navigation

## Quick Start

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) package manager

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd zimbrowser

# Install dependencies
uv sync
```

### Usage

#### CLI Tool

```bash
# Show archive info
uv run python list_zim_articles.py data/<example.zim> info

# List articles starting with "a"
uv run python list_zim_articles.py data/<example.zim> list a 50

# Search for articles
uv run python list_zim_articles.py data/<example.zim> search "test"

# Dump article content
uv run python list_zim_articles.py data/<example.zim> dump Hauptseite
```

#### TUI Browser

```bash
uv run python zim_browser.py data/<example.zim>
```

**Keyboard Shortcuts:**

| Key | Action |
|-----|--------|
| `/` | Search articles |
| `↓`/`↑` or `j`/`k` | Navigate list / Scroll content |
| `Tab` | Switch focus between sidebar and content |
| `s` / `c` | Focus sidebar / content |
| `Space` / `PageDown` | Page down in content |
| `PageUp` | Page up in content |
| `g` / `G` | Jump to top / bottom |
| `q` | Quit |

## Project Structure

```
zimbrowser/
├── list_zim_articles.py    # CLI tool for ZIM exploration
├── zim_browser.py          # Interactive TUI browser
├── pyproject.toml          # Project configuration
├── uv.lock                 # Locked dependencies
├── data/                   # ZIM files directory
│   └── <example.zim>
└── .venv/                  # Virtual environment
```

## Dependencies

- [libzim](https://github.com/openzim/python-libzim) - ZIM file reading
- [textual](https://textual.textualize.io/) - TUI framework
- [markdownify](https://github.com/matthewwithanm/python-markdownify) - HTML to Markdown conversion

## License

MIT License - see LICENSE file for details.

## Resources

- [OpenZIM Farm](https://farm.openzim.org/) - Download ZIM archives
- [ZIM File Format](https://openzim.org/wiki/ZIM_file_format)
