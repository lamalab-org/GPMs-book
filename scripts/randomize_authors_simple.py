#!/usr/bin/env python3
"""
Simple script to replace static author list with randomized JavaScript version.
This version uses basic regex instead of XML parsing for broader compatibility.
"""

import re
from pathlib import Path
import argparse


def extract_authors_from_text(author_text):
    """Extract individual authors from the author text string."""
    # Remove extra whitespace and split by comma
    authors = [author.strip() for author in author_text.split(',') if author.strip()]
    return authors


def create_randomize_script(authors):
    """Create JavaScript code to randomize author order."""
    # Escape authors for JavaScript
    escaped_authors = [author.replace('"', '\\"').replace("'", "\\'") for author in authors]
    
    js_authors_array = '["' + '", "'.join(escaped_authors) + '"]'
    
    script = f'''<script>
document.addEventListener('DOMContentLoaded', function() {{
    // Array of authors
    const authors = {js_authors_array};
    
    // Shuffle function using Fisher-Yates algorithm
    function shuffleArray(array) {{
        const shuffled = [...array];
        for (let i = shuffled.length - 1; i > 0; i--) {{
            const j = Math.floor(Math.random() * (i + 1));
            [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
        }}
        return shuffled;
    }}
    
    // Find the author content div and randomize authors
    const authorContentDiv = document.querySelector('#title-block-header .quarto-title-meta-contents p');
    if (authorContentDiv) {{
        const shuffledAuthors = shuffleArray(authors);
        authorContentDiv.textContent = shuffledAuthors.join(', ') + ' ';
    }}
}});
</script>'''
    return script


def process_html_file_regex(file_path, output_path=None):
    """Process the HTML file using regex to add author randomization."""
    if output_path is None:
        output_path = file_path
    
    # Read the HTML file
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Pattern to find the author paragraph within the title block
    author_pattern = r'<div class="quarto-title-meta-heading">Author</div>\s*<div class="quarto-title-meta-contents">\s*<p>(.*?)</p>'
    
    match = re.search(author_pattern, content, re.DOTALL)
    
    if not match:
        print("Warning: Could not find author section with expected pattern")
        return False
    
    # Extract author text
    author_text = match.group(1).strip()
    print(f"Found authors: {author_text}")
    
    # Extract individual authors
    authors = extract_authors_from_text(author_text)
    print(f"Parsed {len(authors)} authors: {authors}")
    
    # Create randomization script
    randomize_script = create_randomize_script(authors)
    
    # Insert script before </head>
    if '</head>' in content:
        content = content.replace('</head>', f'{randomize_script}\n</head>')
    else:
        print("Warning: Could not find </head> tag")
        return False
    
    # Write the modified HTML
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Successfully updated {output_path} with author randomization script")
    return True


def main():
    parser = argparse.ArgumentParser(description='Add author randomization to Quarto book index.html file')
    parser.add_argument('input_file', nargs='?', help='Path to the HTML file to process')
    parser.add_argument('--output', '-o', help='Output file path (default: overwrites input)')
    parser.add_argument('--docs-dir', help='Process index.html in docs directory')
    
    args = parser.parse_args()
    
    if args.docs_dir:
        # Process only index.html in the docs directory
        docs_path = Path(args.docs_dir)
        if not docs_path.exists():
            print(f"Error: Directory {docs_path} does not exist")
            exit(1)
            
        index_file = docs_path / 'index.html'
        if not index_file.exists():
            print(f"Error: index.html not found in {docs_path}")
            exit(1)
        
        print(f"Processing {index_file}...")
        success = process_html_file_regex(index_file)
        if not success:
            exit(1)
        
    elif args.input_file:
        # Process single file
        success = process_html_file_regex(args.input_file, args.output)
        if not success:
            exit(1)
    else:
        print("Error: Must specify either input_file or --docs-dir")
        exit(1)


if __name__ == '__main__':
    main()
