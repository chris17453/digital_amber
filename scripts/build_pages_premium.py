#!/usr/bin/env python3
"""Build premium GitHub Pages site from markdown files."""

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

def create_premium_css():
    """Create premium CSS styling."""
    return """
    /* Reset and base styles */
    * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }

    :root {
        --primary-color: #2c3e50;
        --secondary-color: #3498db;
        --accent-color: #e74c3c;
        --text-dark: #2c3e50;
        --text-light: #7f8c8d;
        --bg-light: #ecf0f1;
        --bg-white: #ffffff;
        --shadow: rgba(0, 0, 0, 0.1);
        --border-radius: 8px;
        --transition: all 0.3s ease;
    }

    body {
        font-family: "Crimson Text", Georgia, serif;
        line-height: 1.7;
        color: var(--text-dark);
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        min-height: 100vh;
    }

    .container {
        max-width: 900px;
        margin: 0 auto;
        padding: 2rem;
        background: var(--bg-white);
        box-shadow: 0 10px 30px var(--shadow);
        border-radius: var(--border-radius);
        margin-top: 2rem;
        margin-bottom: 2rem;
    }

    /* Header and navigation */
    .header {
        text-align: center;
        margin-bottom: 3rem;
        padding: 2rem 0;
        border-bottom: 3px solid var(--secondary-color);
        position: relative;
        overflow: hidden;
    }

    .header::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(52, 152, 219, 0.1), transparent);
        animation: shimmer 3s infinite;
    }

    @keyframes shimmer {
        0% { left: -100%; }
        100% { left: 100%; }
    }

    .main-title {
        font-size: 3rem;
        font-weight: 700;
        color: var(--primary-color);
        margin-bottom: 0.5rem;
        letter-spacing: -1px;
        text-shadow: 2px 2px 4px var(--shadow);
    }

    .subtitle {
        font-size: 1.3rem;
        font-style: italic;
        color: var(--text-light);
        font-weight: 300;
        margin-bottom: 1rem;
    }

    .author {
        font-size: 1.1rem;
        color: var(--primary-color);
        font-weight: 500;
    }

    /* Chapter image styling */
    .chapter-image {
        width: 100%;
        max-width: 400px;
        height: 300px;
        object-fit: cover;
        border-radius: var(--border-radius);
        box-shadow: 0 8px 25px var(--shadow);
        margin: 2rem auto;
        display: block;
        transition: var(--transition);
    }

    .chapter-image:hover {
        transform: translateY(-5px);
        box-shadow: 0 15px 35px var(--shadow);
    }

    /* Navigation */
    .navigation {
        background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
        padding: 1.5rem;
        margin: 2rem 0;
        border-radius: var(--border-radius);
        box-shadow: 0 5px 15px var(--shadow);
    }

    .navigation a {
        color: white;
        text-decoration: none;
        font-weight: 500;
        transition: var(--transition);
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
    }

    .navigation a:hover {
        color: #ecf0f1;
        transform: translateX(-5px);
    }

    .navigation a::before {
        content: '←';
        font-weight: bold;
    }

    /* Typography */
    h1, h2, h3, h4, h5, h6 {
        color: var(--primary-color);
        margin: 2rem 0 1rem 0;
        line-height: 1.3;
        font-weight: 600;
    }

    h1 {
        font-size: 2.5rem;
        text-align: center;
        margin: 3rem 0 2rem 0;
        position: relative;
        padding-bottom: 1rem;
    }

    h1::after {
        content: '';
        position: absolute;
        bottom: 0;
        left: 50%;
        transform: translateX(-50%);
        width: 100px;
        height: 3px;
        background: linear-gradient(90deg, var(--secondary-color), var(--accent-color));
        border-radius: 2px;
    }

    h2 {
        font-size: 2rem;
        color: var(--secondary-color);
        border-left: 4px solid var(--secondary-color);
        padding-left: 1rem;
        margin-left: -1.25rem;
    }

    h3 {
        font-size: 1.5rem;
        color: var(--accent-color);
    }

    /* Paragraphs and text */
    p {
        margin: 1.5rem 0;
        font-size: 1.1rem;
        text-align: justify;
        text-indent: 2rem;
        line-height: 1.8;
    }

    p:first-of-type,
    h1 + p,
    h2 + p,
    h3 + p {
        text-indent: 0;
    }

    /* Links */
    a {
        color: var(--secondary-color);
        text-decoration: none;
        font-weight: 500;
        border-bottom: 2px solid transparent;
        transition: var(--transition);
        padding-bottom: 2px;
    }

    a:hover {
        color: var(--accent-color);
        border-bottom-color: var(--accent-color);
    }

    /* Table of contents */
    .toc {
        background: var(--bg-light);
        padding: 2rem;
        border-radius: var(--border-radius);
        margin: 2rem 0;
        box-shadow: inset 0 2px 5px var(--shadow);
    }

    .toc h2 {
        text-align: center;
        margin-bottom: 2rem;
        color: var(--primary-color);
        border: none;
        padding: 0;
        margin-left: 0;
    }

    .toc ul {
        list-style: none;
        padding: 0;
    }

    .toc li {
        margin: 0.75rem 0;
        padding: 0.5rem;
        border-radius: 4px;
        transition: var(--transition);
    }

    .toc li:hover {
        background: var(--bg-white);
        transform: translateX(10px);
    }

    .toc a {
        display: block;
        padding: 0.5rem 0;
        border-bottom: none;
        font-size: 1.05rem;
    }

    .part-title {
        font-weight: 700;
        color: var(--primary-color);
        font-size: 1.2rem;
        margin-top: 2rem;
        padding: 0.5rem 0;
        border-bottom: 2px solid var(--secondary-color);
    }

    .chapter-title {
        padding-left: 1.5rem;
        color: var(--text-light);
        position: relative;
    }

    .chapter-title::before {
        content: '▶';
        position: absolute;
        left: 0;
        color: var(--secondary-color);
        font-size: 0.8rem;
    }

    /* Chapter navigation */
    .chapter-nav {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin: 3rem 0;
        padding: 1.5rem;
        background: linear-gradient(135deg, var(--bg-light) 0%, #d5dbdb 100%);
        border-radius: var(--border-radius);
        box-shadow: 0 3px 10px var(--shadow);
    }

    .nav-button {
        background: var(--secondary-color);
        color: white;
        padding: 0.75rem 1.5rem;
        border: none;
        border-radius: var(--border-radius);
        text-decoration: none;
        font-weight: 500;
        transition: var(--transition);
        box-shadow: 0 3px 10px var(--shadow);
    }

    .nav-button:hover {
        background: var(--accent-color);
        transform: translateY(-2px);
        box-shadow: 0 5px 15px var(--shadow);
        color: white;
        border-bottom: none;
    }

    .nav-button:disabled {
        background: var(--text-light);
        cursor: not-allowed;
        transform: none;
    }

    /* Responsive design */
    @media (max-width: 768px) {
        .container {
            margin: 1rem;
            padding: 1.5rem;
        }

        .main-title {
            font-size: 2.2rem;
        }

        .subtitle {
            font-size: 1.1rem;
        }

        h1 {
            font-size: 2rem;
        }

        h2 {
            font-size: 1.6rem;
        }

        p {
            font-size: 1rem;
            text-indent: 1.5rem;
        }

        .chapter-nav {
            flex-direction: column;
            gap: 1rem;
        }

        .chapter-image {
            max-width: 100%;
            height: 250px;
        }
    }

    /* Print styles */
    @media print {
        .navigation,
        .chapter-nav {
            display: none;
        }

        .container {
            box-shadow: none;
            margin: 0;
        }

        body {
            background: white;
        }
    }
    """

def markdown_to_html(content, title="Digital Amber", chapter_name=None):
    """Convert markdown to HTML with premium styling."""
    # Simple markdown processing with image support
    html = content
    
    # Convert headers
    html = re.sub(r'^### (.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
    html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
    html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
    
    # Convert bold and italic
    html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
    html = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html)
    
    # Convert links
    html = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', html)
    
    # Convert paragraphs
    paragraphs = html.split('\n\n')
    html_paragraphs = []
    for p in paragraphs:
        p = p.strip()
        if p and not p.startswith('<'):
            p = f'<p>{p}</p>'
        html_paragraphs.append(p)
    html = '\n\n'.join(html_paragraphs)
    
    # Add chapter image if it exists
    chapter_image = ""
    if chapter_name:
        art_path = Path("art/pages") / f"{chapter_name}.png"
        if art_path.exists():
            chapter_image = f'<img src="../art/pages/{chapter_name}.png" alt="Chapter illustration" class="chapter-image" />'
    
    # Create premium HTML page
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link href="https://fonts.googleapis.com/css2?family=Crimson+Text:ital,wght@0,400;0,600;0,700;1,400&display=swap" rel="stylesheet">
    <style>
        {create_premium_css()}
    </style>
</head>
<body>
    <div class="container">
        <div class="navigation">
            <a href="/">Return to Table of Contents</a>
        </div>
        
        {chapter_image}
        
        <main>
            {html}
        </main>
        
        <div class="chapter-nav">
            <a href="#" class="nav-button" onclick="history.back()">← Previous</a>
            <a href="/" class="nav-button">Table of Contents</a>
            <a href="#" class="nav-button" onclick="window.location.href='#'">Next →</a>
        </div>
    </div>
</body>
</html>"""

def create_premium_index(readme_content):
    """Create premium index page."""
    # Process table of contents
    toc_html = readme_content
    
    # Convert links to HTML files
    toc_html = re.sub(r'\(story/([^)]+)\.md\)', r'(\1.html)', toc_html)
    
    # Convert markdown to HTML
    toc_html = re.sub(r'^# (.+)$', r'<h1 class="main-title">\1</h1>', toc_html, flags=re.MULTILINE)
    toc_html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', toc_html, flags=re.MULTILINE)
    toc_html = re.sub(r'^### (.+)$', r'<h3 class="part-title">\1</h3>', toc_html, flags=re.MULTILINE)
    
    # Convert bold and italic
    toc_html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', toc_html)
    toc_html = re.sub(r'\*(.+?)\*', r'<em class="subtitle">\1</em>', toc_html)
    
    # Convert links
    toc_html = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', toc_html)
    
    # Structure the TOC
    lines = toc_html.split('\n')
    processed_lines = []
    
    for line in lines:
        line = line.strip()
        if line:
            if line.startswith('1.') or line.startswith('2.') or any(str(i) + '.' in line for i in range(3, 25)):
                processed_lines.append(f'<li class="chapter-title">{line}</li>')
            elif not line.startswith('<') and line:
                processed_lines.append(f'<p>{line}</p>')
            else:
                processed_lines.append(line)
    
    content = '\n'.join(processed_lines)
    
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Digital Amber: When Consciousness Becomes Code</title>
    <link href="https://fonts.googleapis.com/css2?family=Crimson+Text:ital,wght@0,400;0,600;0,700;1,400&display=swap" rel="stylesheet">
    <style>
        {create_premium_css()}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1 class="main-title">Digital Amber</h1>
            <p class="subtitle">When Consciousness Becomes Code</p>
            <p class="author">By Charles Watkins</p>
        </div>
        
        <div class="toc">
            {content}
        </div>
        
        <div style="text-align: center; margin: 3rem 0; padding: 2rem; background: var(--bg-light); border-radius: var(--border-radius);">
            <p><em>A Speculative Exploration of AI, Identity, and the Future of Mind</em></p>
            <p><strong>Copyright © 2025 Charles Watkins. All rights reserved.</strong></p>
        </div>
    </div>
</body>
</html>"""

def build_premium_site():
    """Build the premium GitHub Pages site."""
    dist_dir = Path("dist")
    story_dir = Path("story")
    art_dir = Path("art/pages")
    
    # Clean and create dist directory
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    dist_dir.mkdir()
    
    # Copy art directory if it exists
    if art_dir.exists():
        shutil.copytree(art_dir, dist_dir / "art/pages")
    
    # Convert README to premium index.html
    readme_content = read_file("README.md")
    index_html = create_premium_index(readme_content)
    write_file(dist_dir / "index.html", index_html)
    
    # Convert all story files
    for md_file in story_dir.glob("*.md"):
        content = read_file(md_file)
        chapter_name = md_file.stem
        title = f"Digital Amber - {chapter_name.replace('_', ' ').title()}"
        html_content = markdown_to_html(content, title, chapter_name)
        write_file(dist_dir / f"{chapter_name}.html", html_content)
    
    print(f"Premium site built with {len(list(story_dir.glob('*.md')))} pages + index")
    print("GitHub Pages site ready in ./dist/")

if __name__ == "__main__":
    build_premium_site()