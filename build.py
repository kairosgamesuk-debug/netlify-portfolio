#!/usr/bin/env python3
"""
Build script: fetches all Netlify sites via API,
generates a static index.html with card layout.

Requires NETLIFY_ACCESS_TOKEN env var.
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from urllib.request import Request, urlopen

TOKEN = os.environ.get('NETLIFY_ACCESS_TOKEN', '')
if not TOKEN:
    print('ERROR: Set NETLIFY_ACCESS_TOKEN environment variable')
    sys.exit(1)


def fetch_sites():
    req = Request(
        'https://api.netlify.com/api/v1/sites?per_page=100',
        headers={'Authorization': f'Bearer {TOKEN}'},
    )
    with urlopen(req) as resp:
        if resp.status != 200:
            print(f'Netlify API error: {resp.status}')
            sys.exit(1)
        return json.loads(resp.read().decode())


def format_date(iso_str):
    if not iso_str:
        return ''
    try:
        dt = datetime.fromisoformat(iso_str.replace('Z', '+00:00'))
        return dt.strftime('%d %b %Y')
    except Exception:
        return iso_str[:10]


def slug_to_title(slug):
    return ' '.join(w.capitalize() for w in slug.replace('-', ' ').replace('_', ' ').split())


def generate_html(sites):
    public_sites = [s for s in sites if not s.get('password')]
    public_sites.sort(key=lambda s: s.get('updated_at', ''), reverse=True)

    cards = []
    for site in public_sites:
        name = site.get('name') or site.get('subdomain') or 'Untitled'
        title = slug_to_title(name)
        url = site.get('ssl_url') or site.get('url') or f'https://{name}.netlify.app'
        screenshot = site.get('screenshot_url') or ''
        updated = format_date(site.get('updated_at'))
        created = format_date(site.get('created_at'))
        build_settings = site.get('build_settings') or {}
        repo = build_settings.get('repo_url') or ''
        repo_name = repo.rstrip('/').split('/')[-1] if repo else ''

        if screenshot:
            img_html = f'<img src="{screenshot}" alt="{title}" loading="lazy" />'
        else:
            img_html = f'<div class="card-placeholder">{title[0] if title else "?"}</div>'

        repo_html = f'<span class="card-repo" title="{repo}">&#128193; {repo_name}</span>' if repo_name else ''

        cards.append(f'''
        <a href="{url}" target="_blank" rel="noopener" class="card">
          <div class="card-img">{img_html}</div>
          <div class="card-body">
            <h2>{title}</h2>
            <div class="card-meta">
              <span class="card-url">{name}.netlify.app</span>
              {repo_html}
            </div>
            <div class="card-dates">
              <span>Updated: {updated}</span>
              <span>Created: {created}</span>
            </div>
          </div>
        </a>''')

    build_date = datetime.now().strftime('%d %b %Y %H:%M')
    count = len(public_sites)

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>My Netlify Sites</title>
  <style>
    :root {{
      --bg: #0f1923;
      --card-bg: #1a2a3a;
      --card-hover: #243a4e;
      --text: #e0e8f0;
      --muted: #7a8fa0;
      --accent: #00d4aa;
      --accent2: #4488cc;
    }}
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      background: var(--bg);
      color: var(--text);
      min-height: 100vh;
    }}
    header {{
      text-align: center;
      padding: 48px 24px 32px;
    }}
    header h1 {{
      font-size: 2.2rem;
      font-weight: 700;
      background: linear-gradient(135deg, var(--accent), var(--accent2));
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
    }}
    header p {{
      color: var(--muted);
      margin-top: 8px;
      font-size: 0.95rem;
    }}
    .count {{
      display: inline-block;
      background: var(--card-bg);
      color: var(--accent);
      padding: 4px 14px;
      border-radius: 20px;
      font-size: 0.85rem;
      margin-top: 12px;
      border: 1px solid rgba(0,212,170,0.2);
    }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
      gap: 24px;
      padding: 0 32px 48px;
      max-width: 1400px;
      margin: 0 auto;
    }}
    .card {{
      background: var(--card-bg);
      border-radius: 12px;
      overflow: hidden;
      text-decoration: none;
      color: inherit;
      transition: transform 0.2s, box-shadow 0.2s, background 0.2s;
      border: 1px solid rgba(255,255,255,0.05);
    }}
    .card:hover {{
      transform: translateY(-4px);
      box-shadow: 0 12px 40px rgba(0,0,0,0.4);
      background: var(--card-hover);
    }}
    .card-img {{
      width: 100%;
      aspect-ratio: 16/10;
      overflow: hidden;
      background: #0a1520;
    }}
    .card-img img {{
      width: 100%;
      height: 100%;
      object-fit: cover;
      transition: transform 0.3s;
    }}
    .card:hover .card-img img {{ transform: scale(1.05); }}
    .card-placeholder {{
      width: 100%;
      height: 100%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 3rem;
      font-weight: 700;
      color: var(--accent);
      background: linear-gradient(135deg, #0a1520, #1a2a3a);
    }}
    .card-body {{ padding: 16px 20px 20px; }}
    .card-body h2 {{
      font-size: 1.15rem;
      font-weight: 600;
      margin-bottom: 8px;
    }}
    .card-meta {{
      display: flex;
      gap: 12px;
      align-items: center;
      flex-wrap: wrap;
      margin-bottom: 8px;
    }}
    .card-url {{
      font-size: 0.8rem;
      color: var(--accent);
      background: rgba(0,212,170,0.1);
      padding: 2px 8px;
      border-radius: 4px;
    }}
    .card-repo {{
      font-size: 0.78rem;
      color: var(--muted);
    }}
    .card-dates {{
      display: flex;
      gap: 16px;
      font-size: 0.75rem;
      color: var(--muted);
    }}
    footer {{
      text-align: center;
      padding: 24px;
      color: var(--muted);
      font-size: 0.8rem;
      border-top: 1px solid rgba(255,255,255,0.05);
    }}
    @media (max-width: 600px) {{
      .grid {{ padding: 0 16px 32px; gap: 16px; }}
      header {{ padding: 32px 16px 24px; }}
      header h1 {{ font-size: 1.6rem; }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>My Netlify Sites</h1>
    <p>Auto-generated directory of all deployed projects</p>
    <div class="count">{count} sites</div>
  </header>
  <div class="grid">
    {"".join(cards)}
  </div>
  <footer>
    Last built: {build_date} &mdash; Auto-generated from Netlify API
  </footer>
</body>
</html>'''


def main():
    print('Fetching sites from Netlify API...')
    sites = fetch_sites()
    print(f'Found {len(sites)} sites')

    dist_dir = Path(__file__).parent / 'dist'
    dist_dir.mkdir(exist_ok=True)

    html = generate_html(sites)
    (dist_dir / 'index.html').write_text(html, encoding='utf-8')
    public_count = len([s for s in sites if not s.get('password')])
    print(f'Generated dist/index.html ({public_count} public sites)')


if __name__ == '__main__':
    main()
