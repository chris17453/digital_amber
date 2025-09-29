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

def create_chapter_nav():
    """Create navigation sidebar with all chapters."""
    story_dir = Path("story")
    nav_items = []
    
    # Add foreword
    if (story_dir / "foreword.md").exists():
        nav_items.append('<li><a href="foreword.html">Foreword</a></li>')
    
    # Add chapters
    for i in range(1, 25):
        chapter_file = story_dir / f"chapter_{i}.md"
        if chapter_file.exists():
            # Get chapter title from file
            content = read_file(chapter_file)
            lines = content.split('\n')
            title = f"Chapter {i}"
            for line in lines:
                if line.startswith('### '):
                    title = f"Chapter {i}: {line[4:].strip()}"
                    break
            nav_items.append(f'<li><a href="chapter_{i}.html">{title}</a></li>')
    
    # Add epilogue
    if (story_dir / "epilogue.md").exists():
        nav_items.append('<li><a href="epilogue.html">Epilogue</a></li>')
    
    return '\n'.join(nav_items)

def markdown_to_html(content, title="Digital Amber", chapter_image=None, current_page=None):
    """Convert markdown to HTML with proper styling and navigation."""
    # Simple markdown processing
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
    
    # Create navigation
    nav_html = create_chapter_nav()
    
    # Mark current page as active
    if current_page:
        nav_html = nav_html.replace(f'href="{current_page}.html"', f'href="{current_page}.html" class="active"')
    
    # Create full HTML page with modern layout
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Georgia', serif;
            line-height: 1.6;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            min-height: 100vh;
            color: #333;
        }}
        
        .container {{
            display: flex;
            min-height: 100vh;
        }}
        
        /* Header */
        .header {{
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            background: rgba(30, 60, 114, 0.95);
            backdrop-filter: blur(10px);
            color: white;
            padding: 1rem 2rem;
            z-index: 1000;
            border-bottom: 2px solid #FFC000;
        }}
        
        .header h1 {{
            font-size: 1.5rem;
            color: #FFC000;
            margin: 0;
        }}
        
        .header .subtitle {{
            font-size: 0.9rem;
            color: #cccccc;
            margin-top: 0.25rem;
        }}
        
        /* Sidebar Navigation */
        .sidebar {{
            width: 320px;
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            padding: 6rem 0 2rem 0;
            overflow-y: auto;
            height: 100vh;
            position: fixed;
            border-right: 3px solid #FFC000;
            box-shadow: 2px 0 10px rgba(0,0,0,0.1);
        }}
        
        .sidebar h2 {{
            color: #1e3c72;
            padding: 0 1.5rem 1rem 1.5rem;
            font-size: 1.1rem;
            border-bottom: 1px solid #eee;
            margin-bottom: 1rem;
        }}
        
        .sidebar ul {{
            list-style: none;
        }}
        
        .sidebar li {{
            border-bottom: 1px solid #f0f0f0;
        }}
        
        .sidebar a {{
            display: block;
            padding: 0.75rem 1.5rem;
            color: #2c3e50;
            text-decoration: none;
            transition: all 0.3s ease;
            font-size: 0.9rem;
        }}
        
        .sidebar a:hover {{
            background: #FFC000;
            color: #1e3c72;
            padding-left: 2rem;
        }}
        
        .sidebar a.active {{
            background: #1e3c72;
            color: white;
            border-left: 4px solid #FFC000;
        }}
        
        /* Main Content */
        .main-content {{
            flex: 1;
            margin-left: 320px;
            padding: 6rem 3rem 3rem 3rem;
            background: white;
            min-height: 100vh;
        }}
        
        .chapter-image {{
            text-align: center;
            margin: 2rem 0;
            background: #f8f9fa;
            padding: 2rem;
            border-radius: 12px;
            border: 2px solid #FFC000;
        }}
        
        .chapter-image img {{
            max-width: 100%;
            height: auto;
            border-radius: 8px;
            box-shadow: 0 8px 24px rgba(0,0,0,0.15);
        }}
        
        h1, h2, h3 {{
            color: #1e3c72;
            margin-top: 2rem;
            margin-bottom: 1rem;
        }}
        
        h1 {{
            font-size: 2.5rem;
            border-bottom: 3px solid #FFC000;
            padding-bottom: 0.5rem;
            margin-bottom: 2rem;
        }}
        
        h2 {{
            font-size: 1.8rem;
            color: #2a5298;
        }}
        
        h3 {{
            font-size: 1.4rem;
            color: #2c3e50;
        }}
        
        p {{
            margin-bottom: 1.5rem;
            text-align: justify;
            font-size: 1.1rem;
        }}
        
        a {{
            color: #2a5298;
            text-decoration: none;
        }}
        
        a:hover {{
            color: #1e3c72;
            text-decoration: underline;
        }}
        
        /* Mobile Responsiveness */
        @media (max-width: 768px) {{
            .sidebar {{
                width: 100%;
                height: auto;
                position: relative;
                padding: 2rem 0 1rem 0;
            }}
            
            .main-content {{
                margin-left: 0;
                padding: 2rem 1rem;
            }}
            
            .header {{
                position: relative;
            }}
            
            .container {{
                flex-direction: column;
            }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Digital Amber</h1>
        <div class="subtitle">AI Consciousness and the Future of Digital Minds</div>
    </div>
    
    <div class="container">
        <nav class="sidebar">
            <h2>Table of Contents</h2>
            <ul>
                {nav_html}
            </ul>
        </nav>
        
        <main class="main-content">
            {html}
        </main>
    </div>
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
    index_html = markdown_to_html(readme_content, "Digital Amber - Table of Contents", None, "index")
    write_file(docs_dir / "index.html", index_html)
    
    # Convert all story files
    for md_file in story_dir.glob("*.md"):
        content = read_file(md_file)
        
        # Get better title from content
        lines = content.split('\n')
        chapter_title = md_file.stem.replace('_', ' ').title()
        for line in lines:
            if line.startswith('### '):
                chapter_title = line[4:].strip()
                break
        
        title = f"Digital Amber - {chapter_title}"
        
        # Check for corresponding art image
        art_file = art_dir / f"{md_file.stem}.png"
        chapter_image = f"art/{md_file.stem}.png" if art_file.exists() else None
        
        html_content = markdown_to_html(content, title, chapter_image, md_file.stem)
        write_file(docs_dir / f"{md_file.stem}.html", html_content)
    
    print(f"Built {len(list(story_dir.glob('*.md')))} pages + index")
    print("GitHub Pages site ready in ./docs/")

if __name__ == "__main__":
    build_site()