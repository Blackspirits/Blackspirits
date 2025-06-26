# scripts/simkl_feed.py
import os
import requests
import feedparser

README_FILE = "README.md"
SECTION_START = "<!-- SIMKL_START -->"
SECTION_END = "<!-- SIMKL_END -->"
MAX_ITEMS = 3

# Feeds com token vindo do ambiente
TOKEN = os.getenv("SIMKL_TOKEN")
BASE_URL = f"https://api.simkl.com/feeds/list"
MOVIES_FEED = f"{BASE_URL}/movies/completed/rss/?token={TOKEN}&client_id=feeds&country=fr"
SERIES_FEED = f"{BASE_URL}/tv/watching/rss/?token={TOKEN}&client_id=feeds&country=fr"

def format_entry(entry):
    title = entry.get("title", "Unknown Title")
    link = entry.get("link", "")
    emoji = "📺" if "/tv/" in link else "🎬"
    return f"- {emoji} [{title}]({link})"

def get_feed_items(feed_url, max_items):
    feed = feedparser.parse(feed_url)
    return [format_entry(entry) for entry in feed.entries[:max_items]]

def update_readme_section(content, new_section):
    start = content.find(SECTION_START)
    end = content.find(SECTION_END)
    if start == -1 or end == -1:
        raise ValueError("Section markers not found in README.md")
    before = content[:start + len(SECTION_START)]
    after = content[end:]
    return f"{before}\n{new_section}\n{after}"

def main():
    with open(README_FILE, "r", encoding="utf-8") as f:
        readme = f.read()

    movies = get_feed_items(MOVIES_FEED, MAX_ITEMS)
    shows = get_feed_items(SERIES_FEED, MAX_ITEMS)

    section_content = [
        "## 🎞️ Recently Watched",
        "",
        "### Movies", *movies,
        "",
        "### TV Shows", *shows,
        "",
        "[📖 View more on Simkl](https://simkl.com/598901/dashboard/)"
    ]

    updated = update_readme_section(readme, "\n".join(section_content))

    with open(README_FILE, "w", encoding="utf-8") as f:
        f.write(updated)

    print("README.md updated successfully.")

if __name__ == "__main__":
    main()
