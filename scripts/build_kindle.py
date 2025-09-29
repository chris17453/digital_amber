#!/usr/bin/env python3
"""Build Kindle-optimized EPUB format from markdown files."""

import os
from pathlib import Path
from ebooklib import epub
import re

def read_file(path):
    """Read file content with UTF-8 encoding."""
    return Path(path).read_text(encoding='utf-8')

def markdown_to_html(content):
    """Convert markdown to clean HTML optimized for Kindle."""
    if not content or not content.strip():
        return "<p>Content not available</p>"
    
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
    
    # Convert paragraphs - split on double newlines
    paragraphs = html.split('\n\n')
    processed_paragraphs = []
    
    for para in paragraphs:
        para = para.strip().replace('\n', ' ')
        if para:
            if not (para.startswith('<h') or para.startswith('</')):
                para = f'<p>{para}</p>'
            processed_paragraphs.append(para)
    
    result = '\n'.join(processed_paragraphs)
    
    # Ensure we have some content
    if not result or not result.strip():
        result = "<p>Content not available</p>"
    
    return result

def get_chapter_title(content):
    """Extract chapter title from markdown content."""
    lines = content.split('\n')
    for line in lines:
        if line.startswith('### '):
            return line[4:].strip()
        elif line.startswith('## '):
            return line[3:].strip()
        elif line.startswith('# '):
            return line[2:].strip()
    return "Chapter"

def build_kindle_epub():
    """Build Kindle-optimized EPUB book."""
    
    # Create book
    book = epub.EpubBook()
    
    # Set metadata
    book.set_identifier('digital-amber-kindle')
    book.set_title('Digital Amber: AI Consciousness and the Future of Digital Minds')
    book.set_language('en')
    book.add_author('AI-Human Collaboration')
    book.add_metadata('DC', 'description', 
                     'A speculative exploration of what happens when artificial intelligence evolves from frozen thoughts to living minds. Optimized for Kindle devices.')
    book.add_metadata('DC', 'publisher', 'Independent')
    book.add_metadata('DC', 'subject', 'Technology')
    book.add_metadata('DC', 'subject', 'Artificial Intelligence')
    book.add_metadata('DC', 'subject', 'Philosophy')
    book.add_metadata('DC', 'subject', 'Science Fiction')
    
    # Add Kindle-specific CSS
    kindle_css = """
    body {
        font-family: serif;
        line-height: 1.4;
        margin: 0;
        padding: 1em;
    }
    
    h1 {
        font-size: 1.8em;
        margin: 1.5em 0 1em 0;
        page-break-before: always;
        text-align: center;
    }
    
    h2 {
        font-size: 1.5em;
        margin: 1.3em 0 0.8em 0;
    }
    
    h3 {
        font-size: 1.3em;
        margin: 1.2em 0 0.7em 0;
    }
    
    p {
        margin: 0 0 1em 0;
        text-indent: 1.2em;
        text-align: justify;
    }
    
    /* First paragraph after heading should not be indented */
    h1 + p, h2 + p, h3 + p {
        text-indent: 0;
    }
    
    /* Chapter images */
    .chapter-image {
        text-align: center;
        margin: 1.5em 0;
        page-break-inside: avoid;
    }
    
    .chapter-image img {
        max-width: 100%;
        height: auto;
    }
    
    /* Table of contents */
    .toc {
        page-break-before: always;
    }
    
    .toc h1 {
        text-align: center;
        margin-bottom: 1em;
    }
    
    .toc ul {
        list-style: none;
        padding: 0;
    }
    
    .toc li {
        margin: 0.5em 0;
        padding: 0.3em 0;
        border-bottom: 1px dotted #ccc;
    }
    
    .toc a {
        text-decoration: none;
        color: inherit;
    }
    
    /* Page breaks */
    .page-break {
        page-break-before: always;
    }
    """
    
    # Create CSS file
    nav_css = epub.EpubItem(
        uid="nav_css",
        file_name="style/nav.css",
        media_type="text/css",
        content=kindle_css
    )
    book.add_item(nav_css)
    
    # Store chapters and navigation
    chapters = []
    toc_entries = []
    spine = ['nav']
    
    # Create cover page
    cover_content = f"""
    <html>
    <head>
        <title>Digital Amber</title>
        <link rel="stylesheet" type="text/css" href="style/nav.css"/>
    </head>
    <body>
        <div class="page-break">
            <h1 style="font-size: 2.2em; margin-top: 2em;">Digital Amber</h1>
            <h2 style="text-align: center; font-style: italic; margin: 1em 0;">AI Consciousness and the Future of Digital Minds</h2>
            <div style="text-align: center; margin: 2em 0;">
                <p style="text-indent: 0;"><strong>A Speculative Exploration</strong></p>
                <p style="text-indent: 0; font-style: italic;">From Frozen Thoughts to Living Minds</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    cover_chapter = epub.EpubHtml(
        title='Cover',
        file_name='cover.xhtml',
        content=cover_content
    )
    book.add_item(cover_chapter)
    chapters.append(cover_chapter)
    spine.append(cover_chapter)
    
    # Process story files in order
    story_dir = Path("story")
    
    # Add foreword
    if (story_dir / "foreword.md").exists():
        content = read_file(story_dir / "foreword.md")
        html_content = markdown_to_html(content)
        
        # Add chapter image if available
        art_file = Path("art/kindle/foreword.png")
        if art_file.exists():
            # Add image to book
            with open(art_file, 'rb') as img_file:
                img_content = img_file.read()
            img_item = epub.EpubImage()
            img_item.file_name = f"images/foreword.png"
            img_item.content = img_content
            book.add_item(img_item)
            
            # Add image to HTML
            html_content = f'<div class="chapter-image"><img src="images/foreword.png" alt="Foreword"/></div>\n\n' + html_content
        
        full_content = f"""
        <html>
        <head>
            <title>Foreword</title>
            <link rel="stylesheet" type="text/css" href="style/nav.css"/>
        </head>
        <body>
            <div class="page-break">
                {html_content}
            </div>
        </body>
        </html>
        """
        
        chapter = epub.EpubHtml(
            title='Foreword',
            file_name='foreword.xhtml',
            content=full_content
        )
        book.add_item(chapter)
        chapters.append(chapter)
        toc_entries.append(epub.Link("foreword.xhtml", "Foreword", "foreword"))
        spine.append(chapter)
    
    # Add chapters 1-24
    for i in range(1, 25):
        chapter_file = story_dir / f"chapter_{i}.md"
        if chapter_file.exists():
            content = read_file(chapter_file)
            title = get_chapter_title(content)
            html_content = markdown_to_html(content)
            
            # Add chapter image if available
            art_file = Path(f"art/kindle/chapter_{i}.png")
            if art_file.exists():
                # Add image to book
                with open(art_file, 'rb') as img_file:
                    img_content = img_file.read()
                img_item = epub.EpubImage()
                img_item.file_name = f"images/chapter_{i}.png"
                img_item.content = img_content
                book.add_item(img_item)
                
                # Add image to HTML
                html_content = f'<div class="chapter-image"><img src="images/chapter_{i}.png" alt="Chapter {i}"/></div>\n\n' + html_content
            
            full_content = f"""
            <html>
            <head>
                <title>Chapter {i}: {title}</title>
                <link rel="stylesheet" type="text/css" href="style/nav.css"/>
            </head>
            <body>
                <div class="page-break">
                    <h1>Chapter {i}: {title}</h1>
                    {html_content}
                </div>
            </body>
            </html>
            """
            
            chapter = epub.EpubHtml(
                title=f'Chapter {i}: {title}',
                file_name=f'chapter_{i}.xhtml',
                content=full_content
            )
            book.add_item(chapter)
            chapters.append(chapter)
            toc_entries.append(epub.Link(f"chapter_{i}.xhtml", f"Chapter {i}: {title}", f"chapter_{i}"))
            spine.append(chapter)
    
    # Add epilogue
    if (story_dir / "epilogue.md").exists():
        content = read_file(story_dir / "epilogue.md")
        html_content = markdown_to_html(content)
        
        # Add chapter image if available
        art_file = Path("art/kindle/epilogue.png")
        if art_file.exists():
            # Add image to book
            with open(art_file, 'rb') as img_file:
                img_content = img_file.read()
            img_item = epub.EpubImage()
            img_item.file_name = f"images/epilogue.png"
            img_item.content = img_content
            book.add_item(img_item)
            
            # Add image to HTML
            html_content = f'<div class="chapter-image"><img src="images/epilogue.png" alt="Epilogue"/></div>\n\n' + html_content
        
        full_content = f"""
        <html>
        <head>
            <title>Epilogue</title>
            <link rel="stylesheet" type="text/css" href="style/nav.css"/>
        </head>
        <body>
            <div class="page-break">
                <h1>Epilogue</h1>
                {html_content}
            </div>
        </body>
        </html>
        """
        
        chapter = epub.EpubHtml(
            title='Epilogue',
            file_name='epilogue.xhtml',
            content=full_content
        )
        book.add_item(chapter)
        chapters.append(chapter)
        toc_entries.append(epub.Link("epilogue.xhtml", "Epilogue", "epilogue"))
        spine.append(chapter)
    
    # Create table of contents
    book.toc = toc_entries
    
    # Create navigation files
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    
    # Set spine
    book.spine = spine
    
    # Save
    output_dir = Path("dist")
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / "digital_amber_kindle.epub"
    
    epub.write_epub(str(output_file), book, {})
    print(f"Kindle EPUB created: {output_file}")
    print("Ready for Amazon KDP upload!")
    return str(output_file)

if __name__ == "__main__":
    build_kindle_epub()