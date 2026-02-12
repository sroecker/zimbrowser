#!/usr/bin/env python3
"""
Simple script to list articles contained in a ZIM file.
Uses libzim to read ZIM archives.
"""

import sys
from pathlib import Path

import warnings

# Suppress deprecation warnings from libzim
warnings.filterwarnings("ignore", category=DeprecationWarning, module="libzim")

try:
    from libzim.reader import Archive
    from libzim.suggestion import SuggestionSearcher
    from libzim.search import Searcher, Query
except ImportError:
    print("Error: libzim is not installed.")
    print("Please install it with: uv pip install libzim")
    sys.exit(1)


def show_archive_info(archive: Archive):
    """Display general information about the ZIM archive."""
    print("=" * 80)
    print("ZIM Archive Information")
    print("=" * 80)
    print(f"Filename: {archive.filename}")
    print(f"File size: {archive.filesize / (1024*1024):.2f} MB")
    print(f"UUID: {archive.uuid}")
    print(f"Has main entry: {archive.has_main_entry}")
    if archive.has_main_entry:
        print(f"Main entry: {archive.main_entry.path}")
    print(f"Entry count: {archive.entry_count}")
    print(f"All entry count: {archive.all_entry_count}")
    print(f"Article count: {archive.article_count}")
    print(f"Media count: {archive.media_count}")
    print(f"Has fulltext index: {archive.has_fulltext_index}")
    print(f"Has title index: {archive.has_title_index}")
    print(f"Has checksum: {archive.has_checksum}")
    print(f"Has illustration: {archive.has_illustration()}")
    if archive.has_illustration():
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            sizes = archive.get_illustration_sizes()
        print(f"  Illustration sizes: {sizes}")
    print()


def list_by_suggestion(archive: Archive, query: str = "", limit: int = 100):
    """List articles using the suggestion search."""
    if not query:
        # Use a wildcard approach - iterate through common starting characters
        print("Note: Empty prefix returns no results. Using search for 'a' as example.")
        print("Use 'list <prefix>' to search with a specific prefix.")
        query = "a"
    
    searcher = SuggestionSearcher(archive)
    suggestion = searcher.suggest(query)
    results = suggestion.getResults(0, limit)
    
    count = 0
    print(f"{'Path':<60} {'Title':<40}")
    print("-" * 100)
    
    for path in results:
        try:
            entry = archive.get_entry_by_path(path)
            title = entry.title or "(no title)"
            path_display = (path[:57] + '...') if len(path) > 60 else path
            title_display = (title[:37] + '...') if len(title) > 40 else title
            print(f"{path_display:<60} {title_display:<40}")
            count += 1
        except Exception as e:
            print(f"{path:<60} (error: {e})")
    
    print("-" * 100)
    print(f"Shown: {count} articles")
    return count


def search_articles(archive: Archive, query: str, offset: int = 0, limit: int = 50):
    """Search for articles using fulltext search."""
    if not archive.has_fulltext_index:
        print("Archive does not have a fulltext index.")
        return 0
    
    searcher = Searcher(archive)
    q = Query()
    q.set_query(query)
    search = searcher.search(q)
    
    estimated = search.getEstimatedMatches()
    print(f"Estimated matches: {estimated}")
    
    results = search.getResults(offset, limit)
    
    count = 0
    print(f"{'Path':<60} {'Title':<40}")
    print("-" * 100)
    
    for path in results:
        try:
            entry = archive.get_entry_by_path(path)
            title = entry.title or "(no title)"
            path_display = (path[:57] + '...') if len(path) > 60 else path
            title_display = (title[:37] + '...') if len(title) > 40 else title
            print(f"{path_display:<60} {title_display:<40}")
            count += 1
        except Exception as e:
            print(f"{path:<60} (error: {e})")
    
    print("-" * 100)
    print(f"Shown: {count} articles (offset: {offset})")
    return count


def get_entry_details(archive: Archive, path: str):
    """Get detailed information about a specific entry."""
    try:
        entry = archive.get_entry_by_path(path)
        print(f"Path: {entry.path}")
        print(f"Title: {entry.title}")
        print(f"Is redirect: {entry.is_redirect}")
        
        if entry.is_redirect:
            redirect = entry.get_redirect_entry()
            print(f"Redirects to: {redirect.path}")
        else:
            item = entry.get_item()
            print(f"Mimetype: {item.mimetype}")
            print(f"Size: {item.size} bytes")
    except Exception as e:
        print(f"Error retrieving entry: {e}")


def dump_entry_content(archive: Archive, path: str, output_path: str | None = None):
    """Dump the content of a specific entry.
    
    Args:
        archive: The ZIM archive
        path: The path of the entry to dump
        output_path: Optional file path to write content to (default: stdout)
    """
    try:
        entry = archive.get_entry_by_path(path)
        
        # Follow redirects
        original_path = path
        if entry.is_redirect:
            redirect = entry.get_redirect_entry()
            print(f"Note: '{original_path}' is a redirect to '{redirect.path}'", file=sys.stderr)
            entry = redirect
        
        item = entry.get_item()
        content = item.content.tobytes()
        
        # Try to decode as text if it's a text type
        mimetype = item.mimetype
        is_text = 'text/' in mimetype or mimetype in ('application/javascript', 'application/json')
        
        if output_path:
            # Write to file
            mode = 'w' if is_text else 'wb'
            with open(output_path, mode) as f:
                if is_text:
                    f.write(content.decode('utf-8', errors='replace'))
                else:
                    f.write(content)
            print(f"Dumped {len(content)} bytes to '{output_path}' ({mimetype})")
        else:
            # Output to stdout
            if is_text:
                try:
                    text = content.decode('utf-8')
                    print(text)
                except UnicodeDecodeError:
                    # Fall back to binary output info
                    print(f"Binary content ({mimetype}): {len(content)} bytes", file=sys.stderr)
                    sys.stdout.buffer.write(content)
            else:
                print(f"# Content-Type: {mimetype}", file=sys.stderr)
                print(f"# Size: {len(content)} bytes", file=sys.stderr)
                print("# Binary content - writing raw bytes to stdout", file=sys.stderr)
                sys.stdout.buffer.write(content)
                
    except Exception as e:
        print(f"Error dumping entry: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    if len(sys.argv) < 2:
        print("Usage: python list_zim_articles.py <zim_file> [command] [args...]")
        print()
        print("Commands:")
        print("  info                          Show archive information")
        print("  list [prefix] [limit]         List articles (default: first 100)")
        print("  search <query> [offset]       Search articles")
        print("  get <path>                    Get details of a specific entry")
        print("  dump <path> [output_file]     Dump content of an entry to stdout or file")
        print()
        print("Examples:")
        print(f"  uv run python list_zim_articles.py data/<example.zim> info")
        print(f"  uv run python list_zim_articles.py data/<example.zim> list")
        print(f"  uv run python list_zim_articles.py data/<example.zim> list a 50")
        print(f"  uv run python list_zim_articles.py data/<example.zim> search test")
        print(f"  uv run python list_zim_articles.py data/<example.zim> get mainPage")
        print(f"  uv run python list_zim_articles.py data/<example.zim> dump Hauptseite")
        print(f"  uv run python list_zim_articles.py data/<example.zim> dump Hauptseite output.html")
        sys.exit(1)
    
    zim_path = sys.argv[1]
    zim_file = Path(zim_path)
    
    if not zim_file.exists():
        print(f"Error: File '{zim_path}' not found.")
        sys.exit(1)
    
    try:
        archive = Archive(zim_path)
    except Exception as e:
        print(f"Error opening ZIM file: {e}")
        sys.exit(1)
    
    command = sys.argv[2] if len(sys.argv) > 2 else "info"
    
    if command == "info":
        show_archive_info(archive)
        
    elif command == "list":
        prefix = sys.argv[3] if len(sys.argv) > 3 else ""
        limit = int(sys.argv[4]) if len(sys.argv) > 4 else 100
        list_by_suggestion(archive, prefix, limit)
        
    elif command == "search":
        if len(sys.argv) < 4:
            print("Error: search command requires a query")
            sys.exit(1)
        query = sys.argv[3]
        offset = int(sys.argv[4]) if len(sys.argv) > 4 else 0
        search_articles(archive, query, offset)
        
    elif command == "get":
        if len(sys.argv) < 4:
            print("Error: get command requires a path")
            sys.exit(1)
        path = sys.argv[3]
        get_entry_details(archive, path)
        
    elif command == "dump":
        if len(sys.argv) < 4:
            print("Error: dump command requires a path")
            sys.exit(1)
        path = sys.argv[3]
        output_path = sys.argv[4] if len(sys.argv) > 4 else None
        dump_entry_content(archive, path, output_path)
        
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
