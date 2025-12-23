# tools/build_site.py
from __future__ import annotations

from pathlib import Path
import datetime as dt
import re
import html as html_escape

import markdown  # pip install markdown

ROOT = Path(".")
POSTS_DIR = ROOT / "posts"
ASSETS_DIR = ROOT / "assets"
OUT_INDEX = ROOT / "index.html"

EXCLUDE_DIRS = {".git", ".github", "tools", "assets", "__pycache__"}

# 見た目（必要なら後でいじれる）
BASE_CSS = """
:root { color-scheme: light; }
body{
  font-family: system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;
  margin: 24px; line-height: 1.75; max-width: 980px;
}
a{ text-decoration: none; }
a:hover{ text-decoration: underline; }
hr{ margin: 24px 0; }
pre{ overflow:auto; padding: 12px; border:1px solid #e5e5e5; border-radius:10px; }
code{ font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace; }
blockquote{ border-left: 4px solid #ddd; padding-left: 12px; color:#444; }
.container{ border:1px solid #ddd; border-radius: 12px; padding: 16px; }
.hint{ color:#555; font-size:.92em; }
.small{ color:#666; font-size:.9em; }
"""

def read_title_from_md(md_text: str, fallback: str) -> str:
    # 最初の "# " をタイトル扱い。なければファイル名
    for line in md_text.splitlines():
        m = re.match(r"^\s*#\s+(.+)\s*$", line)
        if m:
            return m.group(1).strip()
    return fallback

def md_to_html(md_path: Path) -> tuple[str, str]:
    md_text = md_path.read_text(encoding="utf-8")
    title = read_title_from_md(md_text, md_path.stem)

    body = markdown.markdown(
        md_text,
        extensions=["fenced_code", "tables", "toc"],
        output_format="html5",
    )

    # ルートへの戻りリンク（memo/ 直下に戻る）
    # 記事が posts/<cat>/file.html なので、../../ で memo/ に戻れる
    back_href = "../../index.html"

    html_doc = f"""<!doctype html>
<html lang="ja">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html_escape.escape(title)}</title>
  <style>{BASE_CSS}</style>
</head>
<body>
  <p class="small"><a href="{back_href}">← indexへ戻る</a></p>
  <h1>{html_escape.escape(title)}</h1>
  <div class="hint">{md_path.as_posix()}</div>
  <hr>
  {body}
  <hr>
  <p class="small">Generated: {dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
</body>
</html>
"""
    return title, html_doc

def build_posts_html() -> dict[Path, str]:
    """
    .md -> .html を生成。戻り値は md_path -> title の辞書。
    """
    titles: dict[Path, str] = {}
    if not POSTS_DIR.exists():
        return titles

    for md_path in sorted(POSTS_DIR.rglob("*.md")):
        # 除外（隠しファイルなど）
        if any(part.startswith(".") for part in md_path.parts):
            continue
        if any(part in EXCLUDE_DIRS for part in md_path.parts):
            continue

        title, html_doc = md_to_html(md_path)
        html_path = md_path.with_suffix(".html")
        html_path.write_text(html_doc, encoding="utf-8")
        titles[md_path] = title

    return titles

def esc(s: str) -> str:
    return html_escape.escape(s, quote=True)

def build_index(titles: dict[Path, str]) -> None:
    """
    posts/ のディレクトリ構造を <details> ツリーで表示。
    リンクは .html（生成済み）へ。
    """
    if not POSTS_DIR.exists():
        tree_html = "<p><b>posts/ が見つかりません。</b></p>"
    else:
        # ディレクトリ -> 子要素の辞書を作る
        # 単純に walk して、フォルダごとに一覧化
        tree_lines: list[str] = []

        for dirpath in sorted([p for p in POSTS_DIR.rglob("*") if p.is_dir()]):
            if any(part.startswith(".") for part in dirpath.parts):
                continue
            if any(part in EXCLUDE_DIRS for part in dirpath.parts):
                continue

        # os.walk でツリー作成
        import os
        for dirpath, dirnames, filenames in os.walk(POSTS_DIR):
            dirpath_p = Path(dirpath)

            dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS and not d.startswith(".")]
            filenames = [f for f in filenames if f.endswith(".md") and not f.startswith(".")]

            depth = len(dirpath_p.relative_to(POSTS_DIR).parts)
            indent = "  " * depth

            if dirpath_p != POSTS_DIR:
                tree_lines.append(f'{indent}<li><details open>')
                tree_lines.append(f'{indent}<summary><b>{esc(dirpath_p.name)}/</b></summary>')
                tree_lines.append(f'{indent}<ul>')

            for f in sorted(filenames):
                md_path = dirpath_p / f
                html_path = md_path.with_suffix(".html")
                href = html_path.as_posix()
                title = titles.get(md_path, md_path.stem)
                tree_lines.append(f'{indent}  <li><a href="{esc(href)}">{esc(title)}</a> <span class="small">({esc(f)})</span></li>')

            if dirpath_p != POSTS_DIR:
                tree_lines.append(f'{indent}</ul>')
                tree_lines.append(f'{indent}</details></li>')

        tree_html = "<ul>\n" + "\n".join(tree_lines) + "\n</ul>"

    OUT_INDEX.write_text(f"""<!doctype html>
<html lang="ja">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>memo | tech notes</title>
  <style>{BASE_CSS}</style>
</head>
<body>
  <h1>memo</h1>
  <p class="hint">Markdownから自動生成された技術メモ集（HTML変換＋目次自動生成）</p>

  <div class="container">
    {tree_html}
  </div>

  <hr>
  <p class="hint">このページは GitHub Actions により自動生成されています。</p>
</body>
</html>
""", encoding="utf-8")

def main() -> None:
    titles = build_posts_html()
    build_index(titles)
    print("built: posts html + index.html")

if __name__ == "__main__":
    main()
