import os
import requests
import feedparser

README_URL = "https://raw.githubusercontent.com/Blackspirits/Blackspirits/main/README.md"
README_FILE = "README.md"  # local output

SIMKL_TOKEN = os.getenv("SIMKL_TOKEN")
BASE_URL = "https://api.simkl.com/feeds/list"

# Feed URLs and section markers
MOVIES_FEED = f"{BASE_URL}/movies/completed/rss/?token={SIMKL_TOKEN}&client_id=feeds&country=fr"
SERIES_FEED = f"{BASE_URL}/tv/watching/rss/?token={SIMKL_TOKEN}&client_id=feeds&country=fr"
SECTION_START = "<!-- SIMKL_START -->"
SECTION_END = "<!-- SIMKL_END -->"
MAX_ITEMS = 6  # more like 2 lines (3x2)

def fetch_readme_from_github():
    try:
        response = requests.get(README_URL)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Error fetching README.md: {e}")
        return None

def format_entry_html(entry):
    title = entry.get("title", "Unknown Title")
    link = entry.get("link", "#")
    # Try to get an image of the poster
    img_url = None
    if 'media_thumbnail' in entry:
        img_url = entry.media_thumbnail[0]['url']
    elif 'media_content' in entry:
        img_url = entry.media_content[0]['url']
    else:
        # Placeholder if there is no image
        img_url = "https://via.placeholder.com/100x150?text=No+Image"

    html = f'''
    <td align="center" width="33%">
      <a href="{link}" target="_blank" rel="noopener noreferrer">
        <img src="{img_url}" width="100" style="border-radius:8px;" alt="{title}"/>
      </a>
      <br/>
      <sub><strong>{title}</strong></sub>
    </td>
    '''
    return html

def make_table_html(entries):
    rows = []
    row = []
    for i, entry in enumerate(entries):
        row.append(format_entry_html(entry))
        if (i + 1) % 3 == 0:
            rows.append("<tr>" + "".join(row) + "</tr>")
            row = []
    # Complete the last line if necessary
    if row:
        while len(row) < 3:
            row.append('<td></td>')
        rows.append("<tr>" + "".join(row) + "</tr>")

    table_html = "<table width='100%' style='table-layout: fixed;'><tbody>" + "".join(rows) + "</tbody></table>"
    return table_html

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

    movies_entries = feedparser.parse(MOVIES_FEED).entries[:MAX_ITEMS]
    series_entries = feedparser.parse(SERIES_FEED).entries[:MAX_ITEMS]

    movies_table = make_table_html(movies_entries)
    series_table = make_table_html(series_entries)

    section_content = [
        "## 🎞️ Recently Watched",
        "",
        "### Movies",
        movies_table,
        "",
        "### TV Shows",
        series_table,
        "",
        "[📖 View more on Simkl](https://simkl.com/598901/dashboard/)"
    ]

    updated = update_readme_section(readme, "\n".join(section_content))

    with open(README_FILE, "w", encoding="utf-8") as f:
        f.write(updated)
    print(f"README.md successfully updated locally at '{README_FILE}'")

if __name__ == "__main__":
    main()
