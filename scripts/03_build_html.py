"""REPORT.md を自己完結型 HTML に変換し、GitHub Pages 用サイトを生成する。

- 表・コードブロック・見出しアンカーに対応
- figures/*.png を base64 で埋め込み、HTML 単体で共有可能にする
- 目次(TOC)サイドバー + ヒーロー見出しで「整理された資料」として閲覧できる
- 出力:
    REPORT.html        … リポジトリ直下（GitHub から直接開ける）
    _site/index.html   … GitHub Pages 公開用（中身は同一）
"""

from __future__ import annotations

import base64
import os
import re
import shutil
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parent.parent
MD = ROOT / "REPORT.md"
HTML = ROOT / "REPORT.html"
SITE = ROOT / "_site"

REPO_URL = "https://github.com/gghatano/dpsynth-demo"
UPSTREAM_URL = "https://github.com/google/dpsynth"


def embed_images(md_text: str) -> str:
    """![alt](figures/x.png) を data URI に置換し HTML を自己完結化する。"""
    def repl(m: re.Match) -> str:
        alt, path = m.group(1), m.group(2)
        img = ROOT / path
        if not img.exists():
            return m.group(0)
        b64 = base64.b64encode(img.read_bytes()).decode()
        return f'![{alt}](data:image/png;base64,{b64})'
    return re.sub(r'!\[([^\]]*)\]\(([^)]+\.png)\)', repl, md_text)


CSS = """
:root { --fg:#1a1a1a; --muted:#666; --accent:#c0392b; --line:#e3e3e3; --bg:#fff;
  --code:#f6f8fa; --sidebar:#fbfbfc; }
* { box-sizing: border-box; }
html { scroll-behavior: smooth; }
body { font-family: -apple-system, "Segoe UI", "Hiragino Sans", "Yu Gothic UI", "Meiryo", sans-serif;
  color: var(--fg); background: #f3f4f6; line-height: 1.85; margin: 0; }

/* ヒーロー */
.hero { background: linear-gradient(135deg, #2c3e50 0%, #c0392b 130%); color: #fff;
  padding: 40px 24px; }
.hero .inner { max-width: 1180px; margin: 0 auto; }
.hero h1 { margin: 0 0 .3em; font-size: 1.9rem; border: none; color: #fff; }
.hero p { margin: .2em 0; opacity: .92; font-size: .95rem; }
.hero a { color: #ffe; text-decoration: underline; }
.badges { margin-top: 14px; display: flex; gap: 10px; flex-wrap: wrap; }
.badges a { display: inline-block; background: rgba(255,255,255,.15); color: #fff;
  padding: 6px 13px; border-radius: 20px; font-size: .85rem; text-decoration: none;
  border: 1px solid rgba(255,255,255,.3); }
.badges a:hover { background: rgba(255,255,255,.28); }

/* レイアウト */
.layout { max-width: 1180px; margin: 0 auto; display: grid;
  grid-template-columns: 250px 1fr; gap: 32px; padding: 28px 24px 96px; }
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
article > h1:first-of-type { display: none; }  /* ヒーローと重複するため隠す */
h1 { font-size: 1.9rem; }
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


def main() -> None:
    md_text = embed_images(MD.read_text(encoding="utf-8"))
    md = markdown.Markdown(
        extensions=["tables", "fenced_code", "toc", "codehilite", "sane_lists"],
        extension_configs={"codehilite": {"guess_lang": False},
                           "toc": {"toc_depth": "2-3"}},
    )
    body = md.convert(md_text)
    toc = md.toc  # サイドバー用の目次 HTML

    html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>DPSynth 解説・デモレポート</title>
<meta name="description" content="google/dpsynth（差分プライバシー合成テーブルデータ生成）の日本語解説・利用例・メリデメ・実証デモ">
<style>{CSS}</style>
</head>
<body>
<header class="hero"><div class="inner">
  <h1>DPSynth 解説・実証デモレポート</h1>
  <p>差分プライバシーを満たす合成テーブルデータ生成ライブラリ
     <a href="{UPSTREAM_URL}">google/dpsynth</a> の日本語解説・利用例・メリット/デメリット・実証デモ</p>
  <p>UCI Adult Income データで実際に生成・評価（WSL2 + Python 3.12 + uv）</p>
  <div class="badges">
    <a href="{UPSTREAM_URL}">📦 upstream: google/dpsynth</a>
    <a href="{REPO_URL}">🔗 このリポジトリ</a>
    <a href="{REPO_URL}/blob/main/REPORT.md">📝 REPORT.md</a>
  </div>
</div></header>

<div class="layout">
  <nav class="toc"><strong>目次</strong>{toc}</nav>
  <article>{body}</article>
</div>

<footer>
  Generated from <code>REPORT.md</code> · Source: <a href="{REPO_URL}">{REPO_URL}</a> ·
  Upstream: <a href="{UPSTREAM_URL}">google/dpsynth</a>
</footer>
</body>
</html>"""

    HTML.write_text(html, encoding="utf-8")
    # GitHub Pages 公開用（index.html）
    if SITE.exists():
        shutil.rmtree(SITE)
    SITE.mkdir(parents=True)
    (SITE / "index.html").write_text(html, encoding="utf-8")
    if os.environ.get("PAGES_NOJEKYLL"):
        (SITE / ".nojekyll").write_text("")

    kb = len(html.encode("utf-8")) / 1024
    print(f"wrote {HTML} and {SITE/'index.html'} ({kb:.0f} KB, images embedded)")


if __name__ == "__main__":
    main()
