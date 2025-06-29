import os
import feedparser
import re

README_PATH = "README.md"
START_MARKER = "<!-- SIMKL_START -->"
END_MARKER = "<!-- SIMKL_END -->"
SIMKL_TOKEN = os.getenv("SIMKL_TOKEN")
MAX_ITEMS = 3

MOVIES_FEED = f"https://api.simkl.com/feeds/list/movies/completed/rss/?token={SIMKL_TOKEN}&client_id=feeds"
SERIES_FEED = f"https://api.simkl.com/feeds/list/tv/watching/rss/?token={SIMKL_TOKEN}&client_id=feeds"

def debug_feed_entries(entries, feed_name):
    print(f"\n=== {feed_name} ===")
    for i, entry in enumerate(entries[:3]):
        print(f"Entry {i+1}:")
        print(f"  title: {entry.get('title')}")
        print(f"  link: {entry.get('link')}")
        print(f"  media_thumbnail: {entry.get('media_thumbnail')}")
        print(f"  media_content: {entry.get('media_content')}")
        desc = entry.get('description', '')
        print(f"  description (first 100 chars): {desc[:100]}")
        print()

def format_entry_html(entry):
    title = entry.get("title", "Unknown Title")
    link = entry.get("link", "#")

    media_thumbnail = entry.get("media_thumbnail")
    media_content = entry.get("media_content")

    img_url = None
    if media_thumbnail and len(media_thumbnail) > 0:
        img_url = media_thumbnail[0].get('url')
    elif media_content and len(media_content) > 0:
        img_url = media_content[0].get('url')
    else:
        desc = entry.get('description', '')
        match = re.search(r'<img src="([^"]+)"', desc)
        img_url = match.group(1) if match else "https://via.placeholder.com/100x150?text=No+Image"

    if not img_url:
        img_url = "https://via.placeholder.com/100x150?text=No+Image"

    return (
        f'<td align="center" width="33%">'
        f'<a href="{link}" target="_blank" rel="noopener noreferrer">'
        f'<img src="{img_url}" width="100" style="border-radius:8px;" alt="{title}"/>'
        f'</a><br/><sub><strong>{title}</strong></sub></td>'
    )

def make_table_html(entries):
    rows = []
    row = []
    for i, entry in enumerate(entries[:MAX_ITEMS]):
        row.append(format_entry_html(entry))
        if (i + 1) % 3 == 0:
            rows.append("<tr>" + "".join(row) + "</tr>")
            row = []
    if row:
        while len(row) < 3:
            row.append("<td></td>")
        rows.append("<tr>" + "".join(row) + "</tr>")
    
    # Centro a tabela dentro de um div
    return f"<div align='center'><table width='100%' style='table-layout: fixed;'>{''.join(rows)}</table></div>"

def update_readme_section(content, new_section):
    start = content.find(START_MARKER)
    end = content.find(END_MARKER)
    if start == -1 or end == -1:
        raise ValueError("Markers not found in README.md")
    return content[:start + len(START_MARKER)] + "\n" + new_section + "\n" + content[end:]

def main():
    if not SIMKL_TOKEN:
        print("Erro: variável de ambiente SIMKL_TOKEN não está definida.")
        return

    print(f"Token Simkl: {SIMKL_TOKEN}\n")
    print(f"Fetching movies feed from: {MOVIES_FEED}")
    print(f"Fetching series feed from: {SERIES_FEED}")

    movies_feed = feedparser.parse(MOVIES_FEED)
    series_feed = feedparser.parse(SERIES_FEED)

    debug_feed_entries(movies_feed.entries, "Movies Feed")
    debug_feed_entries(series_feed.entries, "Series Feed")

    movies_html = make_table_html(movies_feed.entries)
    series_html = make_table_html(series_feed.entries)

    section_md = (
        "## 🎞️ Recently Watched\n\n"
        "### Movies\n"
        f"{movies_html}\n\n"
        "### TV Shows\n"
        f"{series_html}\n\n"
        "[📖 View more on Simkl](https://simkl.com/598901/dashboard/)"
    )

    with open(README_PATH, "r", encoding="utf-8") as f:
        readme_content = f.read()

    updated = update_readme_section(readme_content, section_md)

    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(updated)

    print(f"\n{README_PATH} successfully updated!")

if __name__ == "__main__":
    main()
