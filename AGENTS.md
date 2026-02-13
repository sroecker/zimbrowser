# ZIM Browser Project

## Project Overview

This is a Python-based tool for browsing and exploring ZIM archives. ZIM files are compressed archive formats used primarily for offline storage of Wikipedia and other wiki content. This project provides command-line utilities to inspect ZIM files, list articles, search content, and retrieve entry details.

The project currently works with any ZIM archive file (e.g., Wikipedia dumps, Wikivoyage, etc.) from [OpenZIM Farm](https://farm.openzim.org/).

## Technology Stack

- **Language**: Python 3.12+
- **Package Manager**: `uv` (modern Python package manager)
- **Core Dependency**: `libzim` (v3.8.0) - Python bindings for the libzim C++ library
- **Virtual Environment**: Managed by `uv` (located at `.venv/`)

## Project Structure

```
zimbrowser/
├── pyproject.toml          # Project configuration and dependencies
├── uv.lock                 # Locked dependency versions for reproducibility
├── .python-version         # Specifies Python 3.12
├── .gitignore             # Standard Python gitignore
├── list_zim_articles.py   # Main CLI tool for ZIM file exploration
├── zim_browser.py         # TUI browser for interactive ZIM browsing
├── info.txt               # Reference to ZIM file source URL
├── data/                  # Data directory for ZIM files
│   └── <example.zim>  # Your ZIM file here
└── .venv/                 # Virtual environment (managed by uv)
```

## Key Components

### `list_zim_articles.py`

The primary utility script for interacting with ZIM archives. It provides the following commands:

| Command | Description | Example |
|---------|-------------|---------|
| `info` | Display archive metadata (size, entry count, UUID, etc.) | `python list_zim_articles.py data/<example.zim> info` |
| `list [prefix] [limit]` | List articles by suggestion search | `python list_zim_articles.py data/<example.zim> list a 50` |
| `search <query> [offset]` | Full-text search within the archive | `python list_zim_articles.py data/<example.zim> search test` |
| `get <path>` | Get detailed information about a specific entry | `python list_zim_articles.py data/<example.zim> get mainPage` |
| `dump <path> [output_file]` | Dump article content (HTML converted to Markdown) | `python list_zim_articles.py data/<example.zim> dump Hauptseite` |

### `zim_browser.py`

An interactive TUI (Text User Interface) browser built with [Textual](https://textual.textualize.io/). Features:

- **Sidebar**: Lists articles with quick navigation and lazy loading
- **Search**: Press `/` to search articles by prefix
- **Content View**: Displays article content with HTML converted to Markdown
- **Clickable Links**: Click any link to navigate (internal/external supported)
- **Random Article**: Press `r` to load a random article
- **Full Keyboard Navigation**

**Keyboard Shortcuts:**

| Key | Action |
|-----|--------|
| `/` | Search articles by prefix |
| `↓`/`↑` or `j`/`k` | Navigate list (sidebar) / Scroll content (content view) |
| `g` / `G` | Jump to top / bottom of article list |
| `Tab` | Toggle focus between sidebar and content view |
| `s` / `c` | Focus sidebar / content view |
| `r` | Load random article |
| `Space` / `PageDown` | Page down in content view |
| `PageUp` | Page up in content view |
| `Enter` | Select article from sidebar to display |
| `Escape` | Cancel search / Reset sidebar to normal articles |
| `q` | Quit |

**Link Handling:**
- Internal links navigate within the ZIM archive
- External links (`http://`, `https://`) open in default browser
- Supports relative paths (`../Article`, `./Article`)
- Handles URL-encoded characters (`%20` → space)
- Strips fragment identifiers (`#section`) and query params (`?key=value`)

**Lazy Loading:**
- Articles are loaded in batches (default 100)
- More articles auto-load when scrolling within 10 items of bottom
- Triggered by watching `ListView.index` changes

### Dependencies

- **libzim** (v3.8.0): Provides the core functionality for reading ZIM files
  - `Archive`: Main class for opening and accessing ZIM files
  - `Archive.get_random_entry()`: Get a random entry from the archive
  - `SuggestionSearcher`: For prefix-based article suggestions
  - `Searcher`/`Query`: For full-text search capabilities
- **textual** (v7.5.0): TUI framework for the interactive browser
- **markdownify** (v1.2.2): Converts HTML content to Markdown for display

## Build and Run Commands

### Setup

```bash
# Create virtual environment and install dependencies
uv sync

# Or manually:
uv venv .venv
uv pip install libzim>=3.8.0
```

### Running the Tools

#### CLI Tool

```bash
# Show archive info
uv run python list_zim_articles.py data/<example.zim> info

# List articles
uv run python list_zim_articles.py data/<example.zim> list a 50

# Search articles
uv run python list_zim_articles.py data/<example.zim> search test

# Dump article content
uv run python list_zim_articles.py data/<example.zim> dump Hauptseite
```

#### TUI Browser

```bash
# Launch the interactive TUI browser
uv run python zim_browser.py data/<example.zim>
```

**Keyboard Shortcuts:**

| Key | Action |
|-----|--------|
| `/` | Search articles by prefix |
| `↓`/`↑` or `j`/`k` | Navigate list (sidebar) / Scroll content (content view) |
| `g` / `G` | Jump to top / bottom of article list |
| `Tab` | Toggle focus between sidebar and content view |
| `s` / `c` | Focus sidebar / content view |
| `r` | Load random article |
| `Space` / `PageDown` | Page down in content view |
| `PageUp` | Page up in content view |
| `Enter` | Select article from sidebar to display |
| `Escape` | Cancel search / Reset sidebar to normal articles |
| `q` | Quit |

### Adding Dependencies

```bash
# Add a new dependency
uv add <package-name>

# Example
uv add requests
```

## Code Style Guidelines

- **Python Version**: 3.12+ (specified in `.python-version`)
- **Type Hints**: Use type annotations for function parameters and return types (as seen in `list_zim_articles.py`)
- **Docstrings**: Use Google-style docstrings for functions
- **Error Handling**: Use try-except blocks with informative error messages; handle libzim-specific exceptions gracefully
- **Deprecation Warnings**: Filter deprecation warnings from libzim (the library generates some warnings that can be safely ignored)

Example pattern from existing code:
```python
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning, module="libzim")
```

## Testing Instructions

Currently, there are no automated tests configured. Testing is done manually by running the CLI tool against the sample ZIM file:

```bash
# Test archive info retrieval
uv run python list_zim_articles.py data/<example.zim> info

# Test listing articles
uv run python list_zim_articles.py data/<example.zim> list a 20

# Test search functionality
uv run python list_zim_articles.py data/<example.zim> search "Beispiel"

# Test entry retrieval
uv run python list_zim_articles.py data/<example.zim> get "mainPage"
```

## Development Conventions

1. **ZIM File Location**: Place ZIM files in the `data/` directory (gitignored from tracking)
2. **CLI Interface**: When adding new commands, follow the existing pattern:
   - Accept ZIM file path as first argument
   - Use subcommands (info, list, search, get, dump)
   - Provide helpful error messages and usage examples
3. **TUI Interface**: When modifying the TUI browser:
   - Keep keyboard shortcuts consistent with vim-like navigation
   - Ensure Tab switches focus between major panes
   - Use `VerticalScroll` for scrollable content areas
   - Bind new features to single-key shortcuts where possible
4. **Path Handling**: Use `pathlib.Path` for file path operations
5. **Output Formatting**: Use formatted strings with consistent column widths for tabular output

## Security Considerations

- **ZIM File Sources**: Only use ZIM files from trusted sources (like [OpenZIM Farm](https://farm.openzim.org/))
- **File Validation**: The code validates that ZIM files exist before attempting to open them
- **Deprecation Warning Suppression**: The code intentionally suppresses libzim deprecation warnings to maintain clean output; review these warnings periodically when upgrading libzim

## Common Tasks

### Inspecting a New ZIM File

```bash
# 1. Copy the ZIM file to the data directory
cp /path/to/new_file.zim data/

# 2. Get archive information
uv run python list_zim_articles.py data/new_file.zim info

# 3. List first 50 articles
uv run python list_zim_articles.py data/new_file.zim list "" 50
```

### Searching for Content

```bash
# Search for articles containing specific text
uv run python list_zim_articles.py data/<example.zim> search "keyword"
```

## Resources

- **libzim Python Documentation**: https://github.com/openzim/python-libzim
- **OpenZIM Farm**: https://farm.openzim.org/ - Source for ZIM archives
- **ZIM File Format**: https://openzim.org/wiki/ZIM_file_format
