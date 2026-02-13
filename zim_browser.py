#!/usr/bin/env python3
"""
ZIM Browser TUI - A textual-based browser for ZIM archives.
"""

import sys
import warnings
import webbrowser
import posixpath
from pathlib import Path
from urllib.parse import unquote

warnings.filterwarnings("ignore", category=DeprecationWarning, module="libzim")

try:
    from libzim.reader import Archive
    from libzim.suggestion import SuggestionSearcher
except ImportError:
    print("Error: libzim is not installed. Run: uv pip install libzim")
    sys.exit(1)

try:
    from markdownify import markdownify as md
except ImportError:
    print("Error: markdownify is not installed. Run: uv pip install markdownify")
    sys.exit(1)

from textual.app import App, ComposeResult
from textual.widgets import (
    Markdown,
    Input,
    ListView,
    ListItem,
    Label,
    Header,
    Footer,
)
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.reactive import reactive
from textual.binding import Binding
from textual.message import Message


class ArticleList(ListView):
    """List widget for displaying articles."""
    
    BINDINGS = [
        Binding("j", "cursor_down", "Down"),
        Binding("k", "cursor_up", "Up"),
        Binding("g", "cursor_top", "Top"),
        Binding("G", "cursor_bottom", "Bottom"),
        Binding("down", "cursor_down", "Down"),
        Binding("up", "cursor_up", "Up"),
    ]


class ContentView(VerticalScroll):
    """Content view with scrolling support."""
    
    BINDINGS = [
        Binding("j", "scroll_down", "Scroll Down"),
        Binding("k", "scroll_up", "Scroll Up"),
        Binding("down", "scroll_down", "Scroll Down"),
        Binding("up", "scroll_up", "Scroll Up"),
        Binding("space", "page_down", "Page Down"),
        Binding("pagedown", "page_down", "Page Down"),
        Binding("pageup", "page_up", "Page Up"),
        Binding("g", "scroll_home", "Scroll to Top"),
        Binding("G", "scroll_end", "Scroll to Bottom"),
        Binding("s", "focus_sidebar", "Focus Sidebar"),
        Binding("c", "focus_content", "Focus Content"),
    ]
    
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.markdown = Markdown(id="markdown-content")
        self.can_focus = True
    
    def compose(self) -> ComposeResult:
        yield self.markdown
    
    def update(self, content: str) -> None:
        """Update the markdown content."""
        self.markdown.update(content)
    
    def action_scroll_down(self) -> None:
        """Scroll down one line."""
        self.scroll_down()
    
    def action_scroll_up(self) -> None:
        """Scroll up one line."""
        self.scroll_up()
    
    def action_page_down(self) -> None:
        """Scroll down one page."""
        self.scroll_page_down()
    
    def action_page_up(self) -> None:
        """Scroll up one page."""
        self.scroll_page_up()
    
    def action_scroll_home(self) -> None:
        """Scroll to top."""
        self.scroll_home()
    
    def action_scroll_end(self) -> None:
        """Scroll to bottom."""
        self.scroll_end()
    
    def action_focus_sidebar(self) -> None:
        """Focus the sidebar."""
        self.app.sidebar.focus()
    
    def action_focus_content(self) -> None:
        """Focus the content area (self)."""
        self.focus()


class SearchModal(Input):
    """Search input widget."""
    
    def __init__(self, placeholder: str = "Search...", id: str | None = None):
        super().__init__(placeholder=placeholder, id=id)
    
    def on_mount(self) -> None:
        self.focus()
    
    def on_input_submitted(self, event: Input.Submitted) -> None:
        self.post_message(self.SearchSubmitted(event.value))
        event.stop()
    
    def key_escape(self, event) -> None:
        event.stop()
        self.post_message(self.SearchCancelled())
    
    class SearchSubmitted(Message):
        """Message sent when search is submitted."""
        def __init__(self, query: str) -> None:
            self.query = query
            super().__init__()
    
    class SearchCancelled(Message):
        """Message sent when search is cancelled."""
        pass


class Sidebar(Vertical):
    """Sidebar containing search and article list."""
    
    def __init__(self, archive: Archive) -> None:
        self.archive = archive
        self.suggestion_searcher = SuggestionSearcher(archive)
        self.all_articles: list[tuple[str, str]] = []  # (path, title)
        self.current_prefix: str = ""
        self.current_offset: int = 0
        self.batch_size: int = 100
        self.has_more: bool = True
        super().__init__(id="sidebar")
    
    def compose(self) -> ComposeResult:
        yield Label("Articles (press '/' to search)", id="sidebar-title")
        self.article_list = ArticleList(id="article-list")
        yield self.article_list
    
    def on_mount(self) -> None:
        self.load_articles("", 100)
        # Watch for highlight changes to trigger lazy loading
        self.article_list.watch(self.article_list, "index", self._on_highlight_changed)
    
    def load_articles(self, prefix: str = "", limit: int = 100) -> None:
        """Load articles from ZIM file."""
        if not prefix:
            prefix = "a"  # Default prefix if empty
        
        self.current_prefix = prefix
        self.current_offset = 0
        self.batch_size = limit
        self.has_more = True
        
        self._load_batch(0, limit, clear=True)
    
    def _load_batch(self, offset: int, limit: int, clear: bool = False) -> None:
        """Load a batch of articles."""
        suggestion = self.suggestion_searcher.suggest(self.current_prefix)
        results = suggestion.getResults(offset, limit)
        
        if clear:
            self.all_articles = []
            self.article_list.clear()
        
        items = []
        count = 0
        
        for path in results:
            try:
                entry = self.archive.get_entry_by_path(path)
                title = entry.title or path
                self.all_articles.append((path, title))
                items.append(ListItem(Label(title), name=path))
                count += 1
            except Exception:
                pass
        
        for item in items:
            self.article_list.append(item)
        
        # Update state
        self.current_offset = offset + count
        self.has_more = count >= limit
    
    def load_more_articles(self) -> None:
        """Load more articles if available."""
        if self.has_more:
            self._load_batch(self.current_offset, self.batch_size)
    
    def _on_highlight_changed(self, new_index: int | None) -> None:
        """Called when the highlighted item changes - trigger lazy loading near bottom."""
        if not self.has_more or new_index is None:
            return
        
        # Load more when within 10 items of the bottom
        threshold = 10
        list_size = len(self.all_articles)
        
        if list_size > 0 and new_index >= list_size - threshold:
            self.load_more_articles()
    
    def search_articles(self, query: str) -> None:
        """Search for articles matching query."""
        self.load_articles(query, 100)
    
    def get_selected_article(self) -> tuple[str, str] | None:
        """Get the currently selected article path and title."""
        if self.article_list.index is not None and 0 <= self.article_list.index < len(self.all_articles):
            return self.all_articles[self.article_list.index]
        return None


class ZimBrowser(App):
    """Main ZIM Browser application."""
    
    CSS = """
    Screen {
        align: center middle;
    }
    
    #sidebar {
        width: 30%;
        height: 100%;
        border: solid $primary;
    }
    
    #sidebar-title {
        height: auto;
        padding: 1;
        background: $primary;
        color: $text;
        text-align: center;
        text-style: bold;
    }
    
    #article-list {
        height: 1fr;
        border: none;
    }
    
    #article-list:focus {
        background: $surface-lighten-1;
    }
    
    #article-list > ListItem:focus {
        background: $primary-darken-2;
    }
    
    #content {
        width: 70%;
        height: 100%;
        border: solid $primary;
        padding: 1;
    }
    
    #markdown-content {
        width: 100%;
        height: auto;
    }
    
    #search-overlay {
        layer: overlay;
        width: 60%;
        height: auto;
        background: $surface;
        border: solid $primary;
        padding: 1;
        margin-top: 1;
    }
    
    #search-input {
        width: 100%;
    }
    
    .loading {
        text-align: center;
        text-style: bold;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("/", "search", "Search"),
        Binding("escape", "cancel_search", "Cancel"),
        Binding("tab", "focus_next", "Next Focus"),
        Binding("s", "focus_sidebar", "Focus Sidebar"),
        Binding("c", "focus_content", "Focus Content"),
    ]
    
    def __init__(self, archive: Archive) -> None:
        self.archive = archive
        self.current_article: reactive[str] = reactive("")
        self.current_article_path: str = ""
        super().__init__()
    
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        
        with Horizontal():
            self.sidebar = Sidebar(self.archive)
            yield self.sidebar
            
            self.content_view = ContentView(id="content")
            yield self.content_view
        
        yield Footer()
    
    def on_mount(self) -> None:
        self.sidebar.focus()
    
    def action_search(self) -> None:
        """Show search overlay."""
        # Check if search overlay already exists
        if not list(self.query("#search-overlay")):
            self.mount(SearchModal(placeholder="Search articles... (Enter to confirm, Esc to cancel)", id="search-overlay"))
    
    def action_cancel_search(self) -> None:
        """Cancel and hide search overlay or reset sidebar to normal articles."""
        # First, try to close search overlay if it exists
        try:
            search_overlay = self.query_one("#search-overlay", SearchModal)
            search_overlay.remove()
        except Exception:
            # Search overlay not present - we're in the sidebar after search
            pass
        
        # Always reset sidebar to normal articles and focus it
        self.sidebar.load_articles("", 100)
        self.sidebar.article_list.focus()
    
    def on_search_modal_search_submitted(self, message: SearchModal.SearchSubmitted) -> None:
        """Handle search submission."""
        search_overlay = self.query_one("#search-overlay", SearchModal)
        search_overlay.remove()
        self.sidebar.search_articles(message.query)
        self.sidebar.article_list.focus()
    
    def on_search_modal_search_cancelled(self, message: SearchModal.SearchCancelled) -> None:
        """Handle search cancellation."""
        search_overlay = self.query_one("#search-overlay", SearchModal)
        search_overlay.remove()
        # Reset sidebar to show normal articles
        self.sidebar.load_articles("", 100)
        self.sidebar.article_list.focus()
    
    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle article selection."""
        article = self.sidebar.get_selected_article()
        if article:
            path, title = article
            self.load_article(path, title)
    
    def on_markdown_link_clicked(self, event: Markdown.LinkClicked) -> None:
        """Handle clicked links in article content."""
        href = event.href
        
        # Skip external links (open in browser instead)
        if href.startswith("http://") or href.startswith("https://") or href.startswith("//"):
            webbrowser.open(href)
            return
        
        # Normalize the path for ZIM
        # Remove leading slash if present, ZIM paths typically don't have them
        path = href.lstrip("/")
        
        # Handle URL-encoded characters (e.g., %20 for space)
        path = unquote(path)
        
        # Remove query parameters (?key=value) - ZIM doesn't use them
        if "?" in path:
            path = path.split("?")[0]
        
        # Remove fragment identifier (#section) - ZIM doesn't store fragments separately
        # We load the article and ignore the fragment for now
        if "#" in path:
            path = path.split("#")[0]
        
        # Normalize relative paths (../ ./ etc.) against current article path
        if path.startswith("../") or path.startswith("./"):
            if not self.current_article_path:
                self.content_view.update(f"# Error\n\nCannot resolve relative link without a current article: `{href}`")
                return
            # Get directory of current article and join with relative path
            base_dir = posixpath.dirname(self.current_article_path)
            path = posixpath.normpath(posixpath.join(base_dir, path))
        
        # Try to load the article
        try:
            entry = self.archive.get_entry_by_path(path)
            title = entry.title or path
            self.load_article(path, title)
        except Exception:
            # Article not found, might be a special page or missing
            self.content_view.update(f"# Not Found\n\nArticle not found: `{path}`")
    
    def load_article(self, path: str, title: str) -> None:
        """Load and display an article."""
        try:
            entry = self.archive.get_entry_by_path(path)
            
            # Follow redirects
            if entry.is_redirect:
                try:
                    entry = entry.get_redirect_entry()
                    title = entry.title or entry.path
                except Exception as e:
                    self.content_view.update(f"# Error\n\nFailed to follow redirect: {e}")
                    return
            
            item = entry.get_item()
            content = item.content.tobytes()
            
            # Convert HTML to Markdown
            html_content = content.decode('utf-8', errors='replace')
            markdown_content = md(html_content, heading_style="ATX")
            
            # Update content
            self.content_view.update(markdown_content)
            self.current_article = title
            self.current_article_path = entry.path
            self.sub_title = title
            
        except Exception as e:
            self.content_view.update(f"# Error\n\nFailed to load article: {e}")
    
    def action_focus_sidebar(self) -> None:
        """Focus the sidebar."""
        self.sidebar.focus()
    
    def action_focus_content(self) -> None:
        """Focus the content area."""
        self.content_view.focus()
    
    def action_focus_next(self) -> None:
        """Focus next widget - toggle between sidebar and content."""
        focused = self.focused
        if focused is self.sidebar or focused is self.sidebar.article_list:
            self.content_view.focus()
        else:
            self.sidebar.focus()


def main():
    if len(sys.argv) < 2:
        print("Usage: python zim_browser.py <zim_file>")
        print(f"\nExample:")
        print(f"  uv run python zim_browser.py data/<example.zim>")
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
    
    app = ZimBrowser(archive)
    app.run()


if __name__ == "__main__":
    main()
