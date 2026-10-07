"""Collect complete public comments; never truncate or generate dataset text."""
import concurrent.futures
import datetime as dt
from html.parser import HTMLParser
import json
from pathlib import Path
import ssl
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
STORIES = [49996259, 49997073, 49994443, 49991227, 49993857, 49980626,
           49990224, 49991823, 49992257, 49993188, 49995539, 49991243,
           49994481, 49991580, 49994065, 49980399, 49949680, 49992057,
           49991986, 49954015, 49990204, 49982498, 49986862, 49978333]


class PlainText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
    def handle_starttag(self, tag, attrs):
        if tag in ('p', 'br', 'pre'):
            self.parts.append('\n')
    def handle_data(self, data):
        self.parts.append(data)


def clean(html):
    parser = PlainText()
    parser.feed(html)
    return '\n'.join(line.strip() for line in ''.join(parser.parts).strip().splitlines() if line.strip())


def get(item):
    # macOS system CA bundle; verification stays enabled.
    ctx = ssl.create_default_context(cafile='/etc/ssl/cert.pem') if Path('/etc/ssl/cert.pem').exists() else ssl.create_default_context()
    url = f'https://hacker-news.firebaseio.com/v0/item/{item}.json'
    with urllib.request.urlopen(url, context=ctx, timeout=30) as response:
        return json.load(response)


def main():
    stories = {s['id']: s for s in json.loads((ROOT/'evidence/source_stories.json').read_text())}
    pairs = [(sid, kid) for sid in STORIES for kid in stories[sid].get('kids', [])[:25]]
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        items = list(pool.map(get, [kid for _, kid in pairs]))
    rows, seen = [], set()
    for (sid, _), item in zip(pairs, items):
        if not item or item.get('deleted') or item.get('dead') or item.get('type') != 'comment':
            continue
        text = clean(item.get('text', ''))
        # Select whole short comments instead of clipping long ones.
        if not 8 <= len(text.split()) <= 180 or text.casefold() in seen:
            continue
        seen.add(text.casefold())
        rows.append({'id': item['id'], 'story_id': sid, 'story_title': stories[sid]['title'],
                     'source_url': f"https://news.ycombinator.com/item?id={item['id']}",
                     'author': item.get('by'), 'posted_at': item.get('time'),
                     'text': text, 'raw_html': item['text']})
    # Interleave topics so the first reading batch does not cover just one thread.
    grouped = {sid: [r for r in rows if r['story_id'] == sid] for sid in STORIES}
    rows = [grouped[sid][i] for i in range(25) for sid in STORIES if len(grouped[sid]) > i]
    output = {'collected_at': dt.datetime.now(dt.timezone.utc).isoformat(),
              'source_api': 'https://github.com/HackerNews/API',
              'method': 'First 25 direct comments per selected technology thread; whole comments, 8–180 whitespace words, live and unique; interleaved by thread.',
              'comments': rows}
    (ROOT/'evidence/source_comments.json').write_text(json.dumps(output, ensure_ascii=False, indent=2))
    print(f'Collected {len(rows)} complete comments across {len(grouped)} threads.')
    for i, row in enumerate(rows[:40], 1):
        print(f"\n{i}. [{row['id']}] {row['text']}")


if __name__ == '__main__':
    main()
