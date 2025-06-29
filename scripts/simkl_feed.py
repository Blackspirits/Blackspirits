import os
import requests

# Constants
SIMKL_TOKEN = os.getenv("SIMKL_TOKEN")
API_BASE_URL = "https://api.simkl.com"
README_PATH = "README.md"
START_MARKER = "<!-- SIMKL_START -->"
END_MARKER = "<!-- SIMKL_END -->"
POSTER_PLACEHOLDER = "https://via.placeholder.com/100x150?text=No+Image"

def fetch_recent_history(limit=20):
    """Fetch recent watched history from Simkl API."""
    url = f"{API_BASE_URL}/history/all-items?limit={limit}"
    headers = {"Authorization": f"Bearer {SIMKL_TOKEN}"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

def format_entries(entries, kind, max_items=6):
    """Format a list of movie or show entries as an HTML table."""
    filtered = [e for e in entries if e["type"] == kind][:max_items]

    title = "🎬 Movies" if kind == "movie" else "📺 TV Shows"
    table_lines = [f"### {title}\n", "<table width='100%' style='table-layout: fixed;'><tbody><tr>"]

    count = 0
    for item in filtered:
        info = item.get(kind, {})
        name = info.get("title", "Untitled")
        year = info.get("year", "")
        slug = info.get("ids", {}).get("slug", "")
        poster = info.get("poster", {}).get("url") or POSTER_PLACEHOLDER
        simkl_url = f"https://simkl.com/{'movies' if kind == 'movie' else 'shows'}/{slug}"

        table_lines.append(
            f'<td align="center" width="33%">'
            f'<a href="{simkl_url}" target="_blank" rel="noopener noreferrer">'
            f'<img src="{poster}" width="100" style="border-radius:8px;" alt="{name} ({year})"/>'
            f'</a><br/><sub><strong>{name} ({year})</strong></sub>'
            f'</td>'
        )
        count += 1
        if count % 3 == 0:
            table_lines.append("</tr><tr>")

    table_lines.append("</tr></tbody></table>\n")
    return "\n".join(table_lines)

def update_readme_section(content, new_section):
    """Replace the section between START_MARKER and END_MARKER in README.md."""
    start_index = content.find(START_MARKER)
    end_index = content.find(END_MARKER)
    if start_index == -1 or end_index == -1:
        raise ValueError("Markers not found in README.md")

    updated_content = (
        content[: start_index + len(START_MARKER)]
        + "\n"
        + new_section.strip()
        + "\n"
        + content[end_index:]
    )
    return updated_content

def main():
    if not SIMKL_TOKEN:
        print("Error: SIMKL_TOKEN environment variable is not set.")
        return

    print("Fetching recent watched items from Simkl...")
    history = fetch_recent_history()

    print("Formatting Markdown content...")
    movies_md = format_entries(history, "movie", max_items=6)
    shows_md = format_entries(history, "show", max_items=6)

    markdown_section = (
        "## 🎞️ Recently Watched\n\n"
        + movies_md
        + "\n"
        + shows_md
        + "\n"
        + "[📖 View more on Simkl](https://simkl.com/598901/dashboard/)\n"
    )

    print(f"Reading {README_PATH}...")
    with open(README_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    print("Updating README.md content...")
    updated = update_readme_section(content, markdown_section)

    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(updated)

    print(f"{README_PATH} successfully updated!")

if __name__ == "__main__":
    main()
