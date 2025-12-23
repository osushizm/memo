# tools/gen_index.py
from pathlib import Path
import html
import os

ROOT = Path(".")
POSTS_DIR = ROOT / "posts"
OUT = ROOT / "index.html"

EXCLUDE_DIRS = {".git", ".github", "tools", "assets"}
EXTS = {".md", ".html"}

def safe(s: str) -> str:
    return html.escape(s, quote=True)

def build_tree():
    if not POSTS_DIR.exists():
        return "<p><b>posts/ が見つかりません。</b></p>"

    lines = []

    for dirpath, dirnames, filenames in os.walk(POSTS_DIR):
        dirpath = Path(dirpath)

        # 除外ディレクトリ
        dirnames[:] = [
            d for d in dirnames
            if d not in EXCLUDE_DIRS and not d.startswith(".")
        ]

        filenames = [
            f for f in filenames
            if Path(f).suffix in EXTS and not f.startswith(".")
        ]

        depth = len(dirpath.relative_to(POSTS_DIR).parts)
        indent = "  " * depth

        # ディレクトリ見出し
        if dirpath != POSTS_DIR:
            lines.append(f'{indent}<li><details open>')
            lines.append(f'{indent}<summary><b>{safe(dirpath.name)}/</b></summary>')
            lines.append(f'{indent}<ul>')

        # ファイル一覧
        for f in sorted(filenames):
            p = dirpath / f
            href = p.as_posix()
            lines.append(
                f'{indent}  <li><a href="{safe(href)}">{safe(f)}</a></li>'
            )

        # 閉じタグ
        if dirpath != POSTS_DIR:
            lines.append(f'{indent}</ul>')
            lines.append(f'{indent}</details></li>')

    return "<ul>\n" + "\n".join(lines) + "\n</ul>"

def main():
    tree_html = build_tree()

    OUT.write_text(f"""<!doctype html>
<html lang="ja">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>memo | tech notes</title>
  <style>
    body {{
      font-family: system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
      margin: 24px;
      line-height: 1.6;
    }}
    h1 {{ margin-bottom: 0.2em; }}
    .hint {{ color: #555; font-size: 0.9em; }}
    ul {{ list-style: none; padding-left: 1em; }}
    li {{ margin: 4px 0; }}
    details > summary {{ cursor: pointer; }}
    a {{ text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    .box {{
      border: 1px solid #ddd;
      border-radius: 10px;
      padding: 16px;
      margin-top: 16px;
    }}
  </style>
</head>
<body>
  <h1>memo</h1>
  <p class="hint">ディレクトリ構造から自動生成された技術メモ集</p>

  <div class="box">
    {tree_html}
  </div>

  <hr>
  <p class="hint">
    このページは GitHub Actions により自動生成されています。
  </p>
</body>
</html>
""", encoding="utf-8")

    print("generated index.html")

if __name__ == "__main__":
    main()
