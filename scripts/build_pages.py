#!/usr/bin/env python3
"""Build GitHub Pages site from markdown files."""

import os
import shutil
from pathlib import Path
import re

def read_file(path):
    """Read file content with UTF-8 encoding."""
    return Path(path).read_text(encoding='utf-8')

def write_file(path, content):
    """Write file content with UTF-8 encoding."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(content, encoding='utf-8')

def markdown_to_html(content, title="Digital Amber", chapter_image=None):
    """Convert markdown to HTML with proper styling."""
    # Simple markdown processing - can be enhanced with a proper markdown library
    html = content
    
    # Convert headers
    html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
    html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
    html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
    
    # Convert bold and italic
    html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
    html = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html)
    
    # Convert links
    html = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', html)
    
    # Add chapter image if available
    if chapter_image:
        image_html = f'<div class="chapter-image"><img src="{chapter_image}" alt="{title}" /></div>\n\n'
        html = image_html + html
    
    # Convert paragraphs
    paragraphs = html.split('\n\n')
    html_paragraphs = []
    for p in paragraphs:
        p = p.strip()
        if p and not p.startswith('<'):
            p = f'<p>{p}</p>'
        html_paragraphs.append(p)
    html = '\n\n'.join(html_paragraphs)
    
    # Create full HTML page
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            font-family: Georgia, serif;
            line-height: 1.6;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #fefefe;
            color: #333;
        }}
        h1, h2, h3 {{
            color: #2c3e50;
            margin-top: 2em;
        }}
        h1 {{
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
        }}
        a {{
            color: #3498db;
            text-decoration: none;
        }}
        a:hover {{
            text-decoration: underline;
        }}
        .navigation {{
            background: #ecf0f1;
            padding: 20px;
            margin: 20px 0;
            border-left: 4px solid #3498db;
        }}
        .chapter-nav {{
            display: flex;
            justify-content: space-between;
            margin: 2em 0;
            padding: 1em;
            background: #f8f9fa;
            border-radius: 5px;
        }}
        .chapter-image {{
            text-align: center;
            margin: 2em 0;
        }}
        .chapter-image img {{
            max-width: 100%;
            height: auto;
            border-radius: 8px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }}
    </style>
</head>
<body>
    <div class="navigation">
        <a href="/">← Back to Table of Contents</a>
    </div>
    {html}
</body>
</html>"""

def build_site():
    """Build the complete GitHub Pages site."""
    docs_dir = Path("docs")
    story_dir = Path("story")
    art_dir = Path("art") / "pages"
    
    # Clean and create docs directory for GitHub Pages
    if docs_dir.exists():
        shutil.rmtree(docs_dir)
    docs_dir.mkdir()
    
    # Copy art images if they exist
    if art_dir.exists():
        art_docs_dir = docs_dir / "art"
        art_docs_dir.mkdir()
        for art_file in art_dir.glob("*.png"):
            shutil.copy2(art_file, art_docs_dir / art_file.name)
        print(f"Copied {len(list(art_dir.glob('*.png')))} art images")
    
    # Convert README to index.html
    readme_content = read_file("README.md")
    # Update links to point to HTML files
    readme_content = re.sub(r'\(story/([^)]+)\.md\)', r'(\1.html)', readme_content)
    index_html = markdown_to_html(readme_content, "Digital Amber - Table of Contents")
    write_file(docs_dir / "index.html", index_html)
    
    # Convert all story files
    for md_file in story_dir.glob("*.md"):
        content = read_file(md_file)
        title = f"Digital Amber - {md_file.stem.replace('_', ' ').title()}"
        
        # Check for corresponding art image
        art_file = art_dir / f"{md_file.stem}.png"
        chapter_image = f"art/{md_file.stem}.png" if art_file.exists() else None
        
        html_content = markdown_to_html(content, title, chapter_image)
        write_file(docs_dir / f"{md_file.stem}.html", html_content)
    
    print(f"Built {len(list(story_dir.glob('*.md')))} pages + index")
    print("GitHub Pages site ready in ./docs/")

if __name__ == "__main__":
    build_site()