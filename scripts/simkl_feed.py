import os
import feedparser

README_PATH = "README.md"
START_MARKER = "<!-- SIMKL_START -->"
END_MARKER = "<!-- SIMKL_END -->"
SIMKL_TOKEN = os.getenv("SIMKL_TOKEN")
MAX_ITEMS = 3

MOVIES_FEED = f"https://api.simkl.com/feeds/list/movies/completed/rss/?token={SIMKL_TOKEN}&client_id=feeds"
SERIES_FEED = f"https://api.simkl.com/feeds/list/tv/watching/rss/?token={SIMKL_TOKEN}&client_id=feeds"

def format_entry_html(entry):
    title = entry.get("title", "Unknown Title")
    link = entry.get("link", "#")

    # Tenta obter a imagem do thumbnail ou content
    img_url = None
    if 'media_thumbnail' in entry:
        img_url = entry.media_thumbnail[0]['url']
    elif 'media_content' in entry:
        img_url = entry.media_content[0]['url']
    else:
        # Fallback para tentar extrair da descrição
        import re
        match = re.search(r'<img src="([^"]+)"', entry.get('description', ''))
        img_url = match.group(1) if match else "https://via.placeholder.com/100x150?text=No+Image"

    return (
        f'<td align="center" width="33%">'
        f'<a href="{link}" target="_blank" rel="noopener noreferrer">'
        f'<img src="{img_url}" width="100" style="border-radius:8px;" alt="{title}"/>'
        f'</a><br/><sub><strong>{title}</strong></sub></td>'
    )

def make_table_html(entries):
    row = [format_entry_html(entry) for entry in entries[:MAX_ITEMS]]
    while len(row) < 3:
        row.append("<td></td>")
    return f"<table width='100%' style='table-layout: fixed;'><tbody><tr>{''.join(row)}</tr></tbody></table>"

def update_readme_section(content, new_section):
    start = content.find(START_MARKER)
    end = content.find(END_MARKER)
    if start == -1 or end == -1:
        raise ValueError("Markers not found in README.md")
    return content[:start + len(START_MARKER)] + "\n" + new_section + "\n" + content[end:]

def main():
    if not SIMKL_TOKEN:
        print("Error: SIMKL_TOKEN is not set.")
        return

    movies_feed = feedparser.parse(MOVIES_FEED)
    series_feed = feedparser.parse(SERIES_FEED)

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

    print(f"{README_PATH} successfully updated!")

if __name__ == "__main__":
    main()
