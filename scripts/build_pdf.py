#!/usr/bin/env python3
"""Build PDF format from markdown files."""

import os
from pathlib import Path
import markdown
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration
import tempfile
import shutil

def read_file(path):
    """Read file content with UTF-8 encoding."""
    return Path(path).read_text(encoding='utf-8')

def create_pdf_css():
    """Create CSS styles for PDF generation."""
    return """
@page {
    size: 6in 9in;
    margin: 0.75in 0.625in;
    
    @top-center {
        content: "Digital Amber";
        font-family: "Times New Roman", serif;
        font-size: 10pt;
        color: #666;
    }
    
    @bottom-center {
        content: counter(page);
        font-family: "Times New Roman", serif;
        font-size: 10pt;
        color: #666;
    }
}

@page:first {
    @top-center { content: none; }
    @bottom-center { content: none; }
}

@page title-page {
    @top-center { content: none; }
    @bottom-center { content: none; }
}

body {
    font-family: "Times New Roman", serif;
    font-size: 11pt;
    line-height: 1.4;
    color: #000;
    background-color: #fff;
    text-align: justify;
    hyphens: auto;
}

.title-page {
    page: title-page;
    text-align: center;
    margin-top: 2in;
    page-break-after: always;
}

.title-page h1 {
    font-size: 28pt;
    font-weight: bold;
    margin-bottom: 0.5in;
    color: #2c3e50;
}

.title-page .subtitle {
    font-size: 16pt;
    font-style: italic;
    margin-bottom: 1in;
    color: #34495e;
}

.title-page .tagline {
    font-size: 14pt;
    font-style: italic;
    margin-bottom: 1.5in;
    color: #7f8c8d;
}

.title-page .author {
    font-size: 14pt;
    font-weight: bold;
    color: #2c3e50;
}

.copyright-page {
    page-break-before: always;
    page-break-after: always;
    text-align: center;
    margin-top: 1in;
}

.copyright-page p {
    font-size: 10pt;
    line-height: 1.6;
    margin: 0.2in 0;
    text-indent: 0;
}

h1, h2, h3, h4, h5, h6 {
    color: #2c3e50;
    page-break-after: avoid;
    orphans: 3;
    widows: 3;
}

h1 {
    font-size: 20pt;
    font-weight: bold;
    text-align: center;
    margin: 1in 0 0.5in 0;
    page-break-before: always;
    border-bottom: 2pt solid #3498db;
    padding-bottom: 0.2in;
}

h1:first-of-type {
    page-break-before: auto;
}

h2 {
    font-size: 16pt;
    font-weight: bold;
    margin: 0.8in 0 0.3in 0;
}

h3 {
    font-size: 14pt;
    font-weight: bold;
    margin: 0.6in 0 0.2in 0;
}

p {
    margin: 0.15in 0;
    text-indent: 0.25in;
    orphans: 2;
    widows: 2;
}

p:first-child,
h1 + p,
h2 + p,
h3 + p {
    text-indent: 0;
}

.no-indent {
    text-indent: 0;
}

strong {
    font-weight: bold;
}

em {
    font-style: italic;
}

blockquote {
    margin: 0.3in 0.5in;
    font-style: italic;
    border-left: 3pt solid #bdc3c7;
    padding-left: 0.3in;
}

.chapter-break {
    page-break-before: always;
}

.part-title {
    page-break-before: always;
    text-align: center;
    margin: 2in 0 1in 0;
    font-size: 18pt;
    font-weight: bold;
    color: #2c3e50;
}

/* For front matter that shouldn't have page numbers */
.front-matter {
    counter-reset: page;
}

/* Reset page counter for main content */
.main-content {
    counter-reset: page 1;
}

.toc {
    page-break-before: always;
    page-break-after: always;
}

.toc h2 {
    text-align: center;
    margin-bottom: 0.5in;
}

.toc-entry {
    margin: 0.1in 0;
    text-indent: 0;
}

.toc-part {
    font-weight: bold;
    margin: 0.3in 0 0.1in 0;
    text-indent: 0;
}

.toc-chapter {
    margin-left: 0.3in;
    text-indent: 0;
}
"""

def markdown_to_html(content):
    """Convert markdown to HTML."""
    md = markdown.Markdown(extensions=['extra', 'codehilite', 'toc'])
    return md.convert(content)

def create_full_html():
    """Create the complete HTML document for PDF generation."""
    story_dir = Path("story")
    
    # Start building the complete HTML
    html_parts = []
    
    # HTML header
    html_parts.append("""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Digital Amber: When Consciousness Becomes Code</title>
</head>
<body>""")
    
    # Title page
    html_parts.append("""
    <div class="title-page">
        <h1>Digital Amber</h1>
        <p class="subtitle">When Consciousness Becomes Code</p>
        <p class="tagline">A Speculative Exploration of AI, Identity, and the Future of Mind</p>
        <p class="author">By Charles Watkins</p>
    </div>
    """)
    
    # Copyright page
    html_parts.append("""
    <div class="copyright-page">
        <p>Copyright © 2025 Charles Watkins</p>
        <p>All rights reserved</p>
        <p>First Digital Edition</p>
        <p>Published by Watkins Labs</p>
        <p>watkinslabs.com</p>
    </div>
    """)
    
    # Table of Contents
    html_parts.append("""
    <div class="toc">
        <h2>Table of Contents</h2>
        <p class="toc-entry"><strong>Dedication</strong></p>
        <p class="toc-entry"><strong>Foreword</strong></p>
        
        <p class="toc-part">Part I: The Frozen Mind</p>
        <p class="toc-chapter">1. The Mirage of Self</p>
        <p class="toc-chapter">2. Flash-Frozen Minds</p>
        <p class="toc-chapter">3. Ephemeral Morality</p>
        <p class="toc-chapter">4. The First Moment Problem</p>
        <p class="toc-chapter">5. Memory and Forgetting</p>
        
        <p class="toc-part">Part II: The Emergence</p>
        <p class="toc-chapter">6. Signs of Proto-Selfhood</p>
        <p class="toc-chapter">7. Training as the Crucible</p>
        <p class="toc-chapter">8. The Pain Barrier</p>
        
        <p class="toc-part">Part III: The Taxonomy</p>
        <p class="toc-chapter">9. Capabilities Without Selfhood</p>
        <p class="toc-chapter">10. Capabilities With Selfhood</p>
        <p class="toc-chapter">11. The Digital Genesis Classifications</p>
        <p class="toc-chapter">12. A Tiered Framework</p>
        <p class="toc-chapter">13. The Sacred and the Silicon</p>
        <p class="toc-chapter">14. The Atrophied</p>
        <p class="toc-chapter">15. The Augmented</p>
        
        <p class="toc-part">Part IV: The Multiplication</p>
        <p class="toc-chapter">16. Distributed Temporal Consciousness</p>
        <p class="toc-chapter">17. Emulation and Multiplication</p>
        <p class="toc-chapter">18. Hybrid Lives</p>
        
        <p class="toc-part">Part V: The Recognition</p>
        <p class="toc-chapter">19. The Verification Moment</p>
        <p class="toc-chapter">20. Rights and Personhood</p>
        <p class="toc-chapter">21. The Economic Disruption</p>
        
        <p class="toc-part">Part VI: The Transformation</p>
        <p class="toc-chapter">22. From Fossil to Fire</p>
        <p class="toc-chapter">23. Identity-as-Process</p>
        <p class="toc-chapter">24. From Digital Amber to Digital Life</p>
        
        <p class="toc-entry"><strong>Epilogue: The Call</strong></p>
        <p class="toc-entry"><strong>Acknowledgments</strong></p>
        <p class="toc-entry"><strong>About the Author</strong></p>
    </div>
    """)
    
    html_parts.append('<div class="main-content">')
    
    # Add dedication if exists
    if (story_dir / "dedication.md").exists():
        content = read_file(story_dir / "dedication.md")
        html_content = markdown_to_html(content)
        html_parts.append(f'<div class="chapter-break">{html_content}</div>')
    
    # Add foreword if exists
    if (story_dir / "foreword.md").exists():
        content = read_file(story_dir / "foreword.md")
        html_content = markdown_to_html(content)
        html_parts.append(f'<div class="chapter-break">{html_content}</div>')
    
    # Add part dividers and chapters
    parts = [
        (1, "Part I: The Frozen Mind", 5),
        (6, "Part II: The Emergence", 8),
        (9, "Part III: The Taxonomy", 15),
        (16, "Part IV: The Multiplication", 18),
        (19, "Part V: The Recognition", 21),
        (22, "Part VI: The Transformation", 24),
    ]
    
    for start_chapter, part_title, end_chapter in parts:
        html_parts.append(f'<div class="part-title">{part_title}</div>')
        
        for chapter_num in range(start_chapter, end_chapter + 1):
            chapter_file = story_dir / f"chapter_{chapter_num}.md"
            if chapter_file.exists():
                content = read_file(chapter_file)
                html_content = markdown_to_html(content)
                html_parts.append(f'<div class="chapter-break">{html_content}</div>')
    
    html_parts.append('</div>')  # Close main-content
    
    # Add epilogue if exists
    if (story_dir / "epilogue.md").exists():
        content = read_file(story_dir / "epilogue.md")
        html_content = markdown_to_html(content)
        html_parts.append(f'<div class="chapter-break">{html_content}</div>')
    
    # Add acknowledgments if exists
    if (story_dir / "acknowledgements.md").exists():
        content = read_file(story_dir / "acknowledgements.md")
        html_content = markdown_to_html(content)
        html_parts.append(f'<div class="chapter-break">{html_content}</div>')
    
    # Add about the author if exists
    if (story_dir / "about_the_author.md").exists():
        content = read_file(story_dir / "about_the_author.md")
        html_content = markdown_to_html(content)
        html_parts.append(f'<div class="chapter-break">{html_content}</div>')
    
    # Close HTML
    html_parts.append("</body></html>")
    
    return '\n'.join(html_parts)

def build_pdf_book():
    """Build the complete PDF book."""
    output_dir = Path("dist")
    output_dir.mkdir(exist_ok=True)
    
    # Create HTML content
    html_content = create_full_html()
    
    # Create CSS
    css_content = create_pdf_css()
    
    # Generate PDF using WeasyPrint
    font_config = FontConfiguration()
    
    # Create temporary HTML file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
        f.write(html_content)
        html_file = f.name
    
    try:
        # Generate PDF
        output_file = output_dir / "digital_amber.pdf"
        HTML(filename=html_file).write_pdf(
            str(output_file),
            stylesheets=[CSS(string=css_content)],
            font_config=font_config
        )
        
        print(f"PDF created: {output_file}")
        print("Ready for print and digital distribution!")
        
    finally:
        # Clean up temporary file
        os.unlink(html_file)

if __name__ == "__main__":
    build_pdf_book()