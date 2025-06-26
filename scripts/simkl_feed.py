# simkl_feed.py
import requests
import feedparser

README_URL = "https://raw.githubusercontent.com/Blackspirits/Blackspirits/main/README.md"
README_FILE = "README.md"  # local output

# Feed URLs and section markers
MOVIES_FEED = "https://api.simkl.com/feeds/list/movies/completed/rss/?token=872cca971c095c86cee4603e5e13ce1f&client_id=feeds&country=fr"
SERIES_FEED = "https://api.simkl.com/feeds/list/tv/watching/rss/?token=872cca971c095c86cee4603e5e13ce1f&client_id=feeds&country=fr"
SECTION_START = "<!-- SIMKL_START -->"
SECTION_END = "<!-- SIMKL_END -->"
MAX_ITEMS = 3

def fetch_readme_from_github():
    try:
        response = requests.get(README_URL)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Error fetching README.md: {e}")
        return None

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
    readme = fetch_readme_from_github()
    if readme is None:
        print("Failed to retrieve README.md from GitHub")
        return

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
    print(f"README.md successfully updated locally at '{README_FILE}'")

if __name__ == "__main__":
    main()
