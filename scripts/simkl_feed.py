import os
import requests
import re

README_PATH = "README.md"
START_MARKER = "<!-- SIMKL_START -->"
END_MARKER = "<!-- SIMKL_END -->"
MAX_ITEMS = 3

CLIENT_ID = os.getenv("SIMKL_CLIENT_ID")
ACCESS_TOKEN = os.getenv("SIMKL_ACCESS_TOKEN")

HEADERS = {
    "simkl-api-key": CLIENT_ID,
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Content-Type": "application/json"
}

API_BASE_URL = "https://api.simkl.com"

def fetch_last_watched(media_type):
    """
    Busca os últimos vistos para o tipo media_type: "movies" ou "shows"
    """
    url = f"{API_BASE_URL}/users/last_watched/{media_type}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code != 200:
        raise Exception(f"Erro ao buscar {media_type}: {response.status_code} - {response.text}")
    return response.json()

def format_entry_html(item):
    title = item.get("title", "Unknown Title")
    link = item.get("url", "#")

    # Tentar obter a imagem do item
    img_url = item.get("images", {}).get("poster", "")
    if not img_url:
        img_url = "https://via.placeholder.com/100x150?text=No+Image"

    return (
        f'<td align="center" width="33%">'
        f'<a href="{link}" target="_blank" rel="noopener noreferrer">'
        f'<img src="{img_url}" width="100" style="border-radius:8px;" alt="{title}"/>'
        f'</a><br/><sub><strong>{title}</strong></sub></td>'
    )

def make_table_html(items):
    rows = []
    row = []
    for i, item in enumerate(items[:MAX_ITEMS]):
        row.append(format_entry_html(item))
        if (i + 1) % 3 == 0:
            rows.append("<tr>" + "".join(row) + "</tr>")
            row = []
    if row:
        while len(row) < 3:
            row.append("<td></td>")
        rows.append("<tr>" + "".join(row) + "</tr>")
    return f"<div align='center'><table width='100%' style='table-layout: fixed;'>{''.join(rows)}</table></div>"

def update_readme_section(content, new_section):
    start = content.find(START_MARKER)
    end = content.find(END_MARKER)
    if start == -1 or end == -1:
        raise ValueError("Markers not found in README.md")
    return content[:start + len(START_MARKER)] + "\n" + new_section + "\n" + content[end:]

def main():
    if not CLIENT_ID or not ACCESS_TOKEN:
        print("Erro: variáveis de ambiente SIMKL_CLIENT_ID e/ou SIMKL_ACCESS_TOKEN não definidas.")
        return

    movies = fetch_last_watched("movies")
    shows = fetch_last_watched("shows")

    movies_html = make_table_html(movies)
    shows_html = make_table_html(shows)

    section_md = (
        "## 🎞️ Recently Watched\n\n"
        "### Movies\n"
        f"{movies_html}\n\n"
        "### TV Shows\n"
        f"{shows_html}\n\n"
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
