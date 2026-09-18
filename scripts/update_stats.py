"""Render public GitHub metrics as a self-hosted SVG; Python standard library only."""
from datetime import datetime, timezone
from html import escape
import json
import os
from pathlib import Path
from urllib.parse import urlencode, quote
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
USERNAME = 'ArnavUplenchwar'


def api(path):
    headers = {'Accept': 'application/vnd.github+json', 'User-Agent': 'profile-arcade-stats'}
    if os.environ.get('GH_TOKEN'):
        headers['Authorization'] = 'Bearer ' + os.environ['GH_TOKEN']
    with urlopen(Request('https://api.github.com/' + path, headers=headers), timeout=30) as response:
        return json.load(response)


def collect():
    profile = api('users/' + quote(USERNAME))
    repos = []
    page = 1
    while True:
        batch = api(f'users/{quote(USERNAME)}/repos?type=owner&per_page=100&page={page}')
        repos.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    def search(kind):
        result = api('search/issues?' + urlencode({'q': f'author:{USERNAME} is:{kind} is:public', 'per_page': 1}))
        if result.get('incomplete_results'):
            raise RuntimeError('GitHub returned incomplete search results; keeping the previous stats image.')
        return result['total_count']
    return [
        ('PUBLIC REPOS', profile['public_repos'], '#67e8f9'),
        ('STARS RECEIVED', sum(repo['stargazers_count'] for repo in repos if not repo['fork']), '#f9a8d4'),
        ('PRS AUTHORED', search('pr'), '#c4b5fd'),
        ('ISSUES OPENED', search('issue'), '#86efac'),
    ], profile


def render(metrics, profile):
    cards = []
    for index, (label, value, color) in enumerate(metrics):
        x = 34 + index * 287
        cards.append(f'''<g transform="translate({x} 81)">
<rect width="270" height="130" rx="7" fill="#101729" stroke="#2b3651"/>
<rect x="18" y="19" width="6" height="6" fill="{color}"/>
<text x="35" y="26" fill="#96a6c7" font-size="12" letter-spacing="1">{label}</text>
<text x="19" y="96" fill="{color}" font-size="49" font-weight="bold">{value:02d}</text>
<path d="M185 104h14V88h14V72h14V56h14" stroke="{color}" stroke-opacity=".35" fill="none" stroke-width="3"/>
</g>''')
    date = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="285" viewBox="0 0 1200 285" role="img" aria-labelledby="title desc">
<title id="title">Public GitHub statistics for {escape(USERNAME)}</title>
<desc id="desc">{escape(', '.join(f'{label}: {value}' for label, value, _ in metrics))}. Updated {date} UTC. Public activity only; zeros are real counts.</desc>
<rect x=".5" y=".5" width="1199" height="284" rx="14" fill="#0b1020" stroke="#2b3651"/>
<g font-family="'Courier New',monospace">
<text x="34" y="42" fill="#e3edff" font-size="16" letter-spacing="3">GITHUB STATISTICS</text>
<text x="1164" y="42" fill="#7788ad" font-size="11" text-anchor="end">PUBLIC DATA / REFRESHED {date} UTC</text>
<path d="M34 59H1166" stroke="#2b3651"/>
{''.join(cards)}
<text x="35" y="253" fill="#96a6c7" font-size="12">{profile['followers']} FOLLOWERS  /  {profile['following']} FOLLOWING</text>
<text x="1164" y="253" fill="#798bab" font-size="12" text-anchor="end">PUBLIC OPEN-SOURCE ACTIVITY</text>
</g></svg>'''
    output = ROOT / 'assets' / 'github-stats.svg'
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix('.tmp')
    temporary.write_text(svg, encoding='utf-8')
    temporary.replace(output)
    print(f'Refreshed {output.name}: ' + ', '.join(f'{label}={value}' for label, value, _ in metrics))


if __name__ == '__main__':
    render(*collect())
