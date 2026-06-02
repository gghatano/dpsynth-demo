"""REPORT.md / EXPERIMENTS.md を自己完結型 HTML に変換し、GitHub Pages サイトを生成する。

- 表・コードブロック・見出しアンカーに対応
- figures/*.png を base64 で埋め込み、HTML 単体で共有可能にする
- 目次(TOC)サイドバー + ヒーロー + ページ切替ナビ
- 出力（htmls/ に集約。直接閲覧と GitHub Pages 公開の両方に使う）:
    htmls/index.html        … メインレポート（Pages のトップ）
    htmls/experiments.html  … 追加実験
    htmls/.nojekyll
"""

from __future__ import annotations

import base64
import re
import shutil
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parent.parent
OUTDIR = ROOT / "htmls"

REPO_URL = "https://github.com/gghatano/dpsynth-demo"
UPSTREAM_URL = "https://github.com/google/dpsynth"

# (markdown, 出力HTMLファイル名(htmls/配下・Pagesの公開名), ヒーロー副題, ナビキー)
PAGES = [
    {"md": "REPORT.md", "out": "index.html",
     "subtitle": "差分プライバシーを満たす合成テーブルデータ生成ライブラリ "
                 f'<a href="{UPSTREAM_URL}">google/dpsynth</a> の解説・利用例・メリデメ・実証デモ',
     "key": "report"},
    {"md": "EXPERIMENTS.md", "out": "experiments.html",
     "subtitle": "本体レポートの発見を深掘りする追加実験（numerical_bins・マルチシード頑健性・2-way 忠実度）",
     "key": "experiments"},
]


def embed_images(md_text: str) -> str:
    def repl(m: re.Match) -> str:
        alt, path = m.group(1), m.group(2)
        img = ROOT / path
        if not img.exists():
            return m.group(0)
        b64 = base64.b64encode(img.read_bytes()).decode()
        return f'![{alt}](data:image/png;base64,{b64})'
    return re.sub(r'!\[([^\]]*)\]\(([^)]+\.png)\)', repl, md_text)


def extract_mermaid(md_text: str):
    """```mermaid ブロックを退避し、プレースホルダ段落に置換する。

    codehilite に処理されてソースが壊れるのを避けるため、変換前に抜き出す。
    戻り値: (置換後テキスト, [mermaidソース, ...])
    """
    blocks: list[str] = []

    def repl(m: re.Match) -> str:
        blocks.append(m.group(1).strip())
        return f"\n\nxMERMAIDBLOCKx{len(blocks) - 1}x\n\n"

    new = re.sub(r"```mermaid\s*\n(.*?)```", repl, md_text, flags=re.DOTALL)
    return new, blocks


def inject_mermaid(html: str, blocks: list[str]) -> str:
    for i, src in enumerate(blocks):
        div = f'<div class="mermaid">\n{src}\n</div>'
        html = html.replace(f"<p>xMERMAIDBLOCKx{i}x</p>", div)
    return html


def rewrite_links(html: str) -> str:
    """Pages では HTML しか配信されないため、ページ内リンクを実在先へ書き換える。

    - REPORT.md / EXPERIMENTS.md → 同一サイトの index.html / experiments.html
    - その他のリポジトリ相対パス(.md/.txt/patches/ 等) → GitHub の blob URL(Pages に無いため)
    - 絶対URL・アンカー(#)・data: はそのまま
    """
    html = html.replace('href="REPORT.md"', 'href="index.html"')
    html = html.replace('href="EXPERIMENTS.md"', 'href="experiments.html"')

    def repl(m: re.Match) -> str:
        href = m.group(1)
        if href.startswith(("http://", "https://", "#", "mailto:", "data:",
                            "index.html", "experiments.html")):
            return m.group(0)
        return f'href="{REPO_URL}/blob/main/{href}"'

    return re.sub(r'href="([^"]+)"', repl, html)


CSS = """
:root { --fg:#1a1a1a; --muted:#666; --accent:#c0392b; --line:#e3e3e3; --bg:#fff;
  --code:#f6f8fa; --sidebar:#fbfbfc; }
* { box-sizing: border-box; }
html { scroll-behavior: smooth; }
body { font-family: -apple-system, "Segoe UI", "Hiragino Sans", "Yu Gothic UI", "Meiryo", sans-serif;
  color: var(--fg); background: #f3f4f6; line-height: 1.85; margin: 0; }
.hero { background: linear-gradient(135deg, #2c3e50 0%, #c0392b 130%); color: #fff; padding: 36px 24px 0; }
.hero .inner { max-width: 1180px; margin: 0 auto; }
.hero h1 { margin: 0 0 .3em; font-size: 1.8rem; border: none; color: #fff; }
.hero p { margin: .2em 0; opacity: .92; font-size: .94rem; }
.hero a { color: #ffe; }
.nav { max-width: 1180px; margin: 16px auto 0; display: flex; gap: 6px; }
.nav a { padding: 9px 18px; border-radius: 8px 8px 0 0; background: rgba(255,255,255,.14);
  color: #fff; text-decoration: none; font-size: .9rem; border: 1px solid rgba(255,255,255,.25);
  border-bottom: none; }
.nav a.active { background: #f3f4f6; color: #c0392b; font-weight: 600; }
.nav a:hover:not(.active) { background: rgba(255,255,255,.26); }
.layout { max-width: 1180px; margin: 0 auto; display: grid;
  grid-template-columns: 250px 1fr; gap: 32px; padding: 24px 24px 96px; }
nav.toc { position: sticky; top: 18px; align-self: start; max-height: calc(100vh - 36px);
  overflow-y: auto; background: var(--sidebar); border: 1px solid var(--line);
  border-radius: 10px; padding: 14px 16px; font-size: .86rem; }
nav.toc strong { display: block; margin-bottom: 8px; color: var(--accent); }
nav.toc ul { list-style: none; padding-left: 0; margin: 0; }
nav.toc ul ul { padding-left: 12px; }
nav.toc li { margin: 3px 0; }
nav.toc a { color: #34495e; text-decoration: none; display: block; padding: 2px 0; }
nav.toc a:hover { color: var(--accent); }
article { background: var(--bg); border: 1px solid var(--line); border-radius: 10px;
  padding: 12px 40px 56px; box-shadow: 0 1px 10px rgba(0,0,0,.04); min-width: 0; }
article > h1:first-of-type { display: none; }
h2 { font-size: 1.45rem; margin-top: 2.2em; border-bottom: 1px solid var(--line);
  padding-bottom: .3em; scroll-margin-top: 16px; }
h3 { font-size: 1.16rem; margin-top: 1.7em; color: #222; scroll-margin-top: 16px; }
h4 { font-size: 1.0rem; margin-top: 1.3em; color: var(--accent); }
a { color: #1565c0; text-decoration: none; } a:hover { text-decoration: underline; }
code { background: var(--code); padding: .15em .4em; border-radius: 4px; font-size: .88em;
  font-family: "Cascadia Code", Consolas, "SF Mono", monospace; }
pre { background: var(--code); padding: 15px 18px; border-radius: 8px; overflow-x: auto;
  border: 1px solid var(--line); }
pre code { background: none; padding: 0; }
table { border-collapse: collapse; width: 100%; margin: 1.2em 0; font-size: .9rem; display: block;
  overflow-x: auto; }
th, td { border: 1px solid var(--line); padding: 8px 11px; text-align: left; white-space: nowrap; }
th { background: #f2f4f7; font-weight: 600; }
tr:nth-child(even) td { background: #fbfbfc; }
img { max-width: 100%; height: auto; display: block; margin: 1.2em auto; border: 1px solid var(--line);
  border-radius: 8px; }
.mermaid { background: #fff; border: 1px solid var(--line); border-radius: 8px;
  padding: 14px; margin: 1.4em 0; text-align: center; overflow-x: auto; }
blockquote { border-left: 4px solid var(--accent); margin: 1.2em 0; padding: .4em 1.2em;
  background: #fdf3f2; color: #444; border-radius: 0 6px 6px 0; }
hr { border: none; border-top: 1px solid var(--line); margin: 2.2em 0; }
footer { max-width: 1180px; margin: 0 auto; padding: 24px; color: var(--muted); font-size: .85rem;
  text-align: center; }
@media (max-width: 860px) {
  .layout { grid-template-columns: 1fr; }
  nav.toc { position: static; max-height: none; }
  article { padding: 12px 20px 40px; }
}
"""


def build_nav(active_key: str, available: set[str]) -> str:
    items = [("report", "index.html", "📄 レポート"),
             ("experiments", "experiments.html", "🧪 追加実験")]
    links = []
    for key, href, label in items:
        if key not in available:
            continue
        cls = " class=\"active\"" if key == active_key else ""
        links.append(f'<a href="{href}"{cls}>{label}</a>')
    return f'<nav class="nav">{"".join(links)}</nav>'


MERMAID_JS = """
<script type="module">
  import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs';
  mermaid.initialize({ startOnLoad: true, theme: 'neutral', securityLevel: 'loose' });
</script>
"""


def render(page: dict, available: set[str]) -> str:
    md_text = embed_images((ROOT / page["md"]).read_text(encoding="utf-8"))
    md_text, mermaid_blocks = extract_mermaid(md_text)
    md = markdown.Markdown(
        extensions=["tables", "fenced_code", "toc", "codehilite", "sane_lists"],
        extension_configs={"codehilite": {"guess_lang": False}, "toc": {"toc_depth": "2-3"}},
    )
    body = rewrite_links(inject_mermaid(md.convert(md_text), mermaid_blocks))
    toc = md.toc
    nav = build_nav(page["key"], available)
    mermaid_js = MERMAID_JS if mermaid_blocks else ""
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>DPSynth 解説・デモレポート</title>
<style>{CSS}</style>
</head>
<body>
<header class="hero"><div class="inner">
  <h1>DPSynth 解説・実証デモ</h1>
  <p>{page['subtitle']}</p>
</div>{nav}</header>
<div class="layout">
  <nav class="toc"><strong>目次</strong>{toc}</nav>
  <article>{body}</article>
</div>
<footer>
  Source: <a href="{REPO_URL}">{REPO_URL}</a> · Upstream: <a href="{UPSTREAM_URL}">google/dpsynth</a>
</footer>
{mermaid_js}
</body>
</html>"""


def main() -> None:
    pages = [p for p in PAGES if (ROOT / p["md"]).exists()]
    available = {p["key"] for p in pages}
    if OUTDIR.exists():
        shutil.rmtree(OUTDIR)
    OUTDIR.mkdir(parents=True)
    # GitHub Pages（Jekyll 無効化）。htmls/ をそのまま公開・直接閲覧の両方に使う
    (OUTDIR / ".nojekyll").write_text("")
    for p in pages:
        html = render(p, available)
        (OUTDIR / p["out"]).write_text(html, encoding="utf-8")
        print(f"wrote {OUTDIR.name}/{p['out']} ({len(html.encode())/1024:.0f} KB)")


if __name__ == "__main__":
    main()
