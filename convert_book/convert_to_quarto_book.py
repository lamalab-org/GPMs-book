#!/usr/bin/env python3
"""
LaTeX to Quarto Book Converter

This script converts a LaTeX document with multiple sections into a Quarto book
with each section as a separate webpage.
"""

import os
import subprocess
import re
import shutil
from pathlib import Path
import tempfile
import argparse
import yaml
import zipfile

def clean_bibliography_content(content):
    """
    Clean bibliography content by fixing problematic Unicode characters.
    """
    # Fix problematic Unicode characters
    content = content.replace('‑', '-')  # Replace non-breaking hyphen with regular hyphen
    content = content.replace('–', '-')  # Replace en-dash with hyphen
    content = content.replace('—', '-')  # Replace em-dash with hyphen
    content = content.replace(''', "'")  # Replace smart quote
    content = content.replace(''', "'")  # Replace smart quote
    content = content.replace('"', '"')  # Replace smart quote
    content = content.replace('"', '"')  # Replace smart quote
    content = content.replace('…', '...')  # Replace ellipsis
    content = content.replace('×', 'x')  # Replace multiplication sign
    content = content.replace('°', 'deg')  # Replace degree symbol
    content = content.replace('±', '+/-')  # Replace plus-minus
    content = content.replace('α', 'alpha')  # Replace Greek alpha
    content = content.replace('β', 'beta')   # Replace Greek beta
    content = content.replace('γ', 'gamma')  # Replace Greek gamma
    content = content.replace('δ', 'delta')  # Replace Greek delta
    content = content.replace('ε', 'epsilon')  # Replace Greek epsilon
    content = content.replace('θ', 'theta')  # Replace Greek theta
    content = content.replace('λ', 'lambda')  # Replace Greek lambda
    content = content.replace('μ', 'mu')     # Replace Greek mu
    content = content.replace('π', 'pi')     # Replace Greek pi
    content = content.replace('σ', 'sigma')  # Replace Greek sigma
    content = content.replace('τ', 'tau')    # Replace Greek tau
    content = content.replace('φ', 'phi')    # Replace Greek phi
    content = content.replace('χ', 'chi')    # Replace Greek chi
    content = content.replace('ψ', 'psi')    # Replace Greek psi
    content = content.replace('ω', 'omega')  # Replace Greek omega
    
    # Fix other problematic characters
    content = content.replace('\u2009', ' ')  # Replace thin space
    content = content.replace('\u202F', ' ')  # Replace narrow no-break space
    content = content.replace('\u2011', '-')  # Replace non-breaking hyphen
    content = content.replace('\u2012', '-')  # Replace figure dash
    content = content.replace('\u2013', '-')  # Replace en dash
    content = content.replace('\u2014', '-')  # Replace em dash
    content = content.replace('\u2015', '-')  # Replace horizontal bar
    content = content.replace('\u2212', '-')  # Replace minus sign
    
    return content

def clean_latex_content(content):
    """
    Clean LaTeX content by removing/modifying problematic commands for pandoc conversion.
    """
    # Remove \usepackage commands
    content = re.sub(r'\\usepackage(?:\[.*?\])?\{.*?\}', '', content, flags=re.MULTILINE)
    
    # Remove \input commands for preamble, authors, etc. but keep section inputs
    # Note: section inputs are now handled by resolve_input_commands before this function
    content = re.sub(r'\\input\{(?!sections/).*?\}', '', content)
    
    # Remove document class
    content = re.sub(r'\\documentclass(?:\[.*?\])?\{.*?\}', '', content)
    
    # Remove \begin{document} and \end{document}
    content = re.sub(r'\\begin\{document\}', '', content)
    content = re.sub(r'\\end\{document\}', '', content)
    
    # Remove \maketitle
    content = re.sub(r'\\maketitle', '', content)
    
    # Remove \clearpage
    content = re.sub(r'\\clearpage', '', content)
    
    # Remove \tableofcontents
    content = re.sub(r'\\tableofcontents', '', content)
    
    # Remove bibliography commands (will be handled by pandoc)
    content = re.sub(r'\\printbibliography', '', content)
    
    # Remove glossary commands
    content = re.sub(r'\\glsaddall', '', content)
    content = re.sub(r'\\printnoidxglossary.*', '', content)
    
    # Remove \title commands (will be handled in YAML frontmatter)
    content = re.sub(r'\\title\{.*?\}', '', content, flags=re.DOTALL)
    
    # Convert \section* to \section (pandoc handles this better)
    content = re.sub(r'\\section\*', r'\\section', content)
    
    # Clean up citation issues before conversion
    # Fix citation issues - remove double commas and trailing/leading commas
    content = re.sub(r'\\(cite|textcite|autocite|parencite|citet|citep)\{([^}]*),\s*,\s*([^}]*)\}', r'\\\1{\2,\3}', content)
    content = re.sub(r'\\(cite|textcite|autocite|parencite|citet|citep)\{,\s*([^}]*)\}', r'\\\1{\2}', content)
    content = re.sub(r'\\(cite|textcite|autocite|parencite|citet|citep)\{([^}]*),\s*\}', r'\\\1{\2}', content)
    content = re.sub(r'\\(cite|textcite|autocite|parencite|citet|citep)\{([^}]*),\s*,\s*\}', r'\\\1{\2}', content)
    
    # Fix problematic Unicode characters
    content = content.replace('‑', '-')  # Replace en-dash with hyphen
    content = content.replace('–', '-')  # Replace em-dash with hyphen
    content = content.replace('—', '-')  # Replace em-dash with hyphen
    content = content.replace(''', "'")  # Replace smart quote
    content = content.replace(''', "'")  # Replace smart quote
    content = content.replace('"', '"')  # Replace smart quote
    content = content.replace('"', '"')  # Replace smart quote
    
    # Remove empty lines (more than 2 consecutive)
    content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
    
    return content.strip()

def extract_title_from_section(content):
    """Extract the title from a section file."""
    match = re.search(r'\\section\{(.*?)\}', content)
    if match:
        # Clean LaTeX commands from title
        title = match.group(1)
        title = re.sub(r'\\.*?\{(.*?)\}', r'\1', title)  # Remove LaTeX commands but keep content
        title = re.sub(r'\\.*?\s', '', title)  # Remove standalone LaTeX commands
        return title.strip()
    return "Untitled"

def create_section_frontmatter(title, section_name):
    """Create YAML frontmatter for a section."""
    return f"""---
title: "{title}"
---

"""

def convert_citations_to_markdown(content):
    """Convert LaTeX citations to markdown format that Quarto can process."""
    
    # Function to clean citation keys
    def clean_citation_keys(keys_str):
        """Clean and format citation keys."""
        keys = [k.strip() for k in keys_str.split(',')]
        # Remove empty keys and clean up problematic characters
        cleaned_keys = []
        for key in keys:
            if key and not key.isspace():
                # Remove any trailing/leading commas or spaces
                key = key.strip(' ,')
                if key:
                    cleaned_keys.append(key)
        return cleaned_keys
    
    # Convert \cite{} to [@key]
    def replace_cite(match):
        keys = clean_citation_keys(match.group(1))
        if keys:
            return '[@' + '; @'.join(keys) + ']'
        return ''
    
    # Convert \textcite{} to @key (for single citations) or [@key1; @key2] for multiple
    def replace_textcite(match):
        keys = clean_citation_keys(match.group(1))
        if not keys:
            return ''
        if len(keys) == 1:
            return f'@{keys[0]}'
        else:
            return '[@' + '; @'.join(keys) + ']'
    
    # Apply replacements
    content = re.sub(r'\\cite\{([^}]+)\}', replace_cite, content)
    content = re.sub(r'\\textcite\{([^}]+)\}', replace_textcite, content)
    content = re.sub(r'\\autocite\{([^}]+)\}', replace_cite, content)
    content = re.sub(r'\\parencite\{([^}]+)\}', replace_cite, content)
    content = re.sub(r'\\citet\{([^}]+)\}', replace_textcite, content)
    content = re.sub(r'\\citep\{([^}]+)\}', replace_cite, content)
    
    # Handle any remaining malformed citations (like those with extra commas)
    content = re.sub(r'\[@([^]]*),\s*,\s*([^]]*)\]', r'[@\1; @\2]', content)
    content = re.sub(r'\[@,\s*([^]]*)\]', r'[@\1]', content)
    content = re.sub(r'\[@([^]]*),\s*\]', r'[@\1]', content)
    
    # Fix any remaining cases where backslashes got added before @ symbols
    content = re.sub(r'\\@', '@', content)
    
    # Additional cleanup for the specific issue: fix \@key patterns inside citation brackets
    # This handles cases like [@key1; \@key2; \@key3] -> [@key1; @key2; @key3]
    content = re.sub(r'(\[@[^]]*?)\\@', r'\1@', content)
    
    return content

def resolve_input_commands(content, base_dir):
    """Resolve \input{} commands by including the content of referenced files."""
    def replace_input(match):
        input_file = match.group(1)
        input_path = base_dir / input_file
        
        # Try with .tex extension if file doesn't exist
        if not input_path.exists():
            input_path = base_dir / f"{input_file}.tex"
        
        if input_path.exists():
            try:
                with open(input_path, 'r', encoding='utf-8') as f:
                    input_content = f.read()
                print(f"  Including content from {input_path}")
                return input_content
            except Exception as e:
                print(f"  Warning: Could not read {input_path}: {e}")
                return f"% Could not include {input_file}"
        else:
            print(f"  Warning: Input file {input_file} not found")
            return f"% Input file {input_file} not found"
    
    # Replace \input{} commands with file contents
    content = re.sub(r'\\input\{([^}]+)\}', replace_input, content)
    
    return content

def convert_section_to_markdown(section_path, output_path, extract_media_dir):
    """Convert a single section LaTeX file to markdown."""
    print(f"Converting {section_path} to {output_path}")
    
    # Read and clean the section content
    with open(section_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Resolve any \input{} commands in the content
    content = resolve_input_commands(content, section_path.parent.parent)
    
    # Extract title for frontmatter
    title = extract_title_from_section(content)
    
    # Clean the content
    cleaned_content = clean_latex_content(content)
    
    # Convert citations to markdown format
    cleaned_content = convert_citations_to_markdown(cleaned_content)
    
    # Create temporary file with cleaned content
    with tempfile.NamedTemporaryFile(mode='w', suffix='.tex', delete=False, encoding='utf-8') as temp_file:
        temp_file.write(cleaned_content)
        temp_file_path = temp_file.name
    
    try:
        # Convert with pandoc (without --citeproc since Quarto will handle citations)
        pandoc_cmd = [
            'pandoc', temp_file_path,
            '-s',
            '--from=latex',
            '--to=markdown+yaml_metadata_block+raw_tex',
            f'--extract-media={extract_media_dir}',
            '-o', output_path
        ]
        
        result = subprocess.run(pandoc_cmd, capture_output=True, text=True, check=False)
        
        if result.returncode != 0:
            print(f"Warning: pandoc conversion had issues for {section_path}")
            print(f"stderr: {result.stderr}")
            
            # Create a basic markdown file manually
            basic_content = f"""---
title: "{title}"
---

# {title}

*Note: This section had conversion issues and needs manual review.*

{cleaned_content}
"""
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(basic_content)
            return
        
        # Only proceed if output file was created
        if not output_path.exists():
            print(f"Error: Output file {output_path} was not created")
            return
        
        # Read the converted content and add proper frontmatter
        with open(output_path, 'r', encoding='utf-8') as f:
            markdown_content = f.read()
        
        # Remove any existing frontmatter and add our own
        if markdown_content.startswith('---'):
            # Find the end of existing frontmatter
            lines = markdown_content.split('\n')
            frontmatter_end = -1
            for i, line in enumerate(lines[1:], 1):
                if line.strip() == '---':
                    frontmatter_end = i
                    break
            if frontmatter_end > 0:
                markdown_content = '\n'.join(lines[frontmatter_end + 1:])
        
        # Add our frontmatter
        final_content = create_section_frontmatter(title, section_path.stem) + markdown_content
        
        # Clean up any remaining citation formatting issues
        final_content = clean_citation_formatting_in_markdown(final_content)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(final_content)
        
        # Update image references to use PNG instead of PDF
        update_image_references_in_markdown(output_path, "media")
            
    finally:
        # Clean up temporary file
        os.unlink(temp_file_path)

def create_index_page(main_tex_path, output_path, extract_media_dir):
    """Create the index page from main.tex."""
    print(f"Creating index page from {main_tex_path}")
    
    with open(main_tex_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract title
    title_match = re.search(r'\\title\{\\textsf\{(.*?)\}\}', content)
    if not title_match:
        title_match = re.search(r'\\title\{(.*?)\}', content, re.DOTALL)
    
    title = "General Purpose Models for the Chemical Sciences"
    if title_match:
        title = title_match.group(1)
        title = re.sub(r'\\.*?\{(.*?)\}', r'\1', title)
        title = re.sub(r'\\.*?\s', '', title)
        title = title.strip()
    
    # Extract abstract
    abstract_match = re.search(r'\\begin\{abstract\}(.*?)\\end\{abstract\}', content, re.DOTALL)
    abstract = ""
    if abstract_match:
        abstract = abstract_match.group(1).strip()
        abstract = re.sub(r'\\noindent\s*', '', abstract)
        abstract = clean_latex_content(abstract)
    
    # Create index content
    index_content = f"""---
title: "{title}"
---

# {title}

## Abstract

{abstract}

## Acknowledgments

This work was supported by the Carl-Zeiss Foundation. 

A.A.\ acknowledges financial support for this research by the Fulbright U.S. Student Program, which is sponsored by the U.S. Department of State and the German-American Fulbright Commission. Its contents are solely the responsibility of the author and do not necessarily represent the official views of the Fulbright Program, the Government of the United States, or the German-American Fulbright Commission. 
 
M. S.-W.\ was supported by Intel and Merck via the AWASES research center. 

A.M.'s work was funded by the SOL-AI project, funded as part of the Helmholtz Foundation Model Initiative of the Helmholtz Association. 

G.P.'s work was supported by the HPC Gateway measure of the Helmholtz Association.

K.M.J.\ is part of the NFDI consortium FAIRmat funded by the Deutsche Forschungsgemeinschaft (DFG, German Research Foundation) – project 460197019.

We thank Mimi Lavin and Maximilian Greiner for their feedback on a draft of this article.

## Author contributions

N. A. was the lead contributor for the [Building Principles of GPMs](03-architectures.qmd) section. Including its writing and figures (excluding the [Model Level Adaptation](03-architectures.qmd#sec:model_adaptation) subsection). N. A. also reviewed the [Introduction](01-introduction.qmd), [The Shape and Structure of Chemical Data](02-data_taxonomy.qmd), [Evaluations](04-evals.qmd), [Implications of GPMs: Education, Safety, and Ethics](06-safety.qmd), and [Property Prediction](05-applications.qmd#sec:prediction) and [Molecular and Material Generation](05-applications.qmd#sec:mol_generation) sections.

A. A. was the primary contributor to the writing of the [Property Prediction](05-applications.qmd#sec:prediction), [Molecular and Material Generation](05-applications.qmd#sec:mol_generation), [Safety](06-safety.qmd#sec:safety), and [Ethics](06-safety.qmd#sec:ethics) sections, conceptualized the outline for safety and ethics sections, designed and created all figures/schematics/plots in sections with primary contribution, was one of the contributors to the [AI Scientists](05-applications.qmd#sec:ai-scientists) overview, edited [Introduction](01-introduction.qmd), [Evaluations](04-evals.qmd), [Building Principles of GPMs](03-architectures.qmd), [Knowledge Gathering](05-applications.qmd#sec:information_gathering), [Experiment Execution](05-applications.qmd#sec:experiment_execution), and [Education](06-safety.qmd#sec:education) sections.

M.R.-G. was the primary contributor to the [AI Scientists](05-applications.qmd#sec:ai-scientists) overview, the [Hypothesis Generation](05-applications.qmd#sec:hypothesis), and the [LLMs as Optimizers](05-applications.qmd#sec:optimizers) sections, and helped in reviewing the entire manuscript.

A.M. was the main contributor to the [Introduction](01-introduction.qmd) and [The Shape and Structure of Chemical Data](02-data_taxonomy.qmd) sections, and the main contributor to the [Knowledge Gathering](05-applications.qmd#sec:information_gathering) and [Reporting](05-applications.qmd#sec:reporting) sections within the applications section, with minor contributions to the [Building Principles of GPMs](03-architectures.qmd) and the [Safety](06-safety.qmd#sec:safety) sections. Has drafted the initial outline of the article. Reviewed the [Building Principles of GPMs](03-architectures.qmd) sections, the [Safety](06-safety.qmd#sec:safety) section, the [Hypothesis Generation](05-applications.qmd#sec:hypothesis), the [Data Analysis](05-applications.qmd#sec:data_analysis) sections and contributed to the review of the [LLMs as Optimizers](05-applications.qmd#sec:optimizers) section.

M.S.-W. was the main contributor to the [Evaluations](04-evals.qmd), [Education](06-safety.qmd#sec:education) and [Data Analysis](05-applications.qmd#sec:data_analysis) section. M.S.-W. also reviewed the [The Shape and Structure of Chemical Data](02-data_taxonomy.qmd), [Hypothesis Generation](05-applications.qmd#sec:hypothesis), [Experiment Execution](05-applications.qmd#sec:experiment_execution), [Reporting](05-applications.qmd#sec:reporting) and [Safety](06-safety.qmd#sec:safety) section. Unified all figures. Kept track of upcoming deadlines.

M. S. was the primary contributor to the writing of [Experiment Planning](05-applications.qmd#sec:planning) section and related figure. And also helped in reviewing [Knowledge Gathering](05-applications.qmd#sec:information_gathering), [Property Prediction](05-applications.qmd#sec:prediction), and [LLMs as Optimizers](05-applications.qmd#sec:optimizers) sections.

G.P. was the main contributor to [Model Level Adaptation](03-architectures.qmd#sec:model_adaptation) section, including its writing and table. G.P. additionally reviewed the [The Shape and Structure of Chemical Data](02-data_taxonomy.qmd), [Data Analysis](05-applications.qmd#sec:data_analysis), [Reporting](05-applications.qmd#sec:reporting) and [Molecular and Material Generation](05-applications.qmd#sec:mol_generation) sections.

A.A.A. was the main contributor to the [Experiment Execution](05-applications.qmd#sec:experiment_execution) section, including its figure, and a minor contributor to the post-training subsection. A.A.A. reviewed the [Introduction](01-introduction.qmd), [Experiment Planning](05-applications.qmd#sec:planning), [Molecular and Material Generation](05-applications.qmd#sec:mol_generation) and [Education](06-safety.qmd#sec:education) sections, edited [The Shape and Structure of Chemical Data](02-data_taxonomy.qmd) and [Building Principles of GPMs](03-architectures.qmd) sections, created the glossary, and ensured that most references are accessible via a DOI.

K.M.J. initiated and led the project. K.M.J. edited all sections. 

## Conflicts of Interest
K.M.J.\ has been a paid contractor for OpenAI as part of the Red-Teaming Network.

---

## Table of Contents

This book covers the following topics:

1. [Introduction](01-introduction.qmd)
2. [Data Taxonomy](02-data_taxonomy.qmd)
3. [Architectures](03-architectures.qmd)
4. [Evaluations](04-evals.qmd)
5. [Applications](05-applications.qmd)
6. [Safety](06-safety.qmd)
7. [Conclusions and Outlook](07-outlook_conclusions.qmd)
"""
    
    # Clean up any remaining citation formatting issues in the index content
    index_content = clean_citation_formatting_in_markdown(index_content)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(index_content)

def create_quarto_config(output_dir):
    """Create the _quarto.yml configuration file."""
    config = {
        'project': {
            'type': 'book',
            'title': 'General Purpose Models for the Chemical Sciences'
        },
        'book': {
            'title': 'General Purpose Models for the Chemical Sciences',
            'author': 'Nawaf Alampara, Anagha Aneesh, Martiño Ríos-García, Adrian Mirza, Mara Schilling-Wilhelmi, Meiling Sun, Gordan Prastalo, Ali Asghar Aghajani, Kevin Maik Jablonka',
            'date': 'today',
            'chapters': [
                'index.qmd',
                '01-introduction.qmd',
                '02-data_taxonomy.qmd',
                '03-architectures.qmd',
                '04-evals.qmd',
                '05-applications.qmd',
                '06-safety.qmd',
                '07-outlook_conclusions.qmd'
            ],
        },
        'bibliography': 'references.bib',
        'format': {
            'html': {
                'theme': 'cosmo',
                'css': 'styles.css',
                'toc': True,
                'toc-depth': 3,
                'number-sections': True,
                'highlight-style': 'github'
            }
        },
        'execute': {
            'freeze': 'auto'
        }
    }
    
    config_path = output_dir / '_quarto.yml'
    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)
    
    print(f"Created Quarto configuration at {config_path}")

def extract_zip_file(zip_path, extract_to):
    """
    Extract a zip file to a specified directory.
    
    Args:
        zip_path: Path to the zip file
        extract_to: Directory to extract files to
    """
    zip_path = Path(zip_path)
    extract_to = Path(extract_to)
    
    if not zip_path.exists():
        print(f"Error: Zip file {zip_path} not found")
        return False
    
    print(f"Extracting {zip_path} to {extract_to}")
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        print(f"Successfully extracted {zip_path}")
        return True
    except zipfile.BadZipFile:
        print(f"Error: {zip_path} is not a valid zip file")
        return False
    except Exception as e:
        print(f"Error extracting {zip_path}: {e}")
        return False

def convert_pdf_images_to_png(media_dir):
    """
    Convert PDF images to PNG format for web display.
    
    Args:
        media_dir: Directory containing extracted media files
    """
    media_path = Path(media_dir)
    if not media_path.exists():
        return
    
    print(f"Converting PDF images to PNG in {media_dir}")
    
    # Find all PDF files in the media directory
    pdf_files = list(media_path.rglob("*.pdf"))
    
    if not pdf_files:
        print("No PDF files found in media directory")
        return
    
    converted_count = 0
    
    for pdf_file in pdf_files:
        try:
            # Create PNG filename
            png_file = pdf_file.with_suffix('.png')
            
            # Convert PDF to PNG using pdftoppm (part of poppler-utils)
            # Try pdftoppm first (usually better quality)
            convert_cmd = [
                'pdftoppm', 
                '-png', 
                '-singlefile', 
                '-r', '300',  # 300 DPI for good quality
                str(pdf_file), 
                str(png_file.with_suffix(''))  # pdftoppm adds .png automatically
            ]
            
            result = subprocess.run(convert_cmd, capture_output=True, text=True, check=False)
            
            if result.returncode == 0:
                print(f"Converted {pdf_file.name} to PNG")
                converted_count += 1
            else:
                # Try with ImageMagick convert as fallback
                convert_cmd_alt = [
                    'convert', 
                    '-density', '300',
                    str(pdf_file), 
                    str(png_file)
                ]
                
                result_alt = subprocess.run(convert_cmd_alt, capture_output=True, text=True, check=False)
                
                if result_alt.returncode == 0:
                    print(f"Converted {pdf_file.name} to PNG (using ImageMagick)")
                    converted_count += 1
                else:
                    print(f"Warning: Could not convert {pdf_file.name} to PNG")
                    print(f"pdftoppm error: {result.stderr}")
                    print(f"ImageMagick error: {result_alt.stderr}")
                    
        except Exception as e:
            print(f"Error converting {pdf_file.name}: {e}")
    
    print(f"Successfully converted {converted_count} PDF images to PNG")

def update_image_references_in_markdown(file_path, media_dir="media"):
    """
    Update image references in markdown files to use PNG instead of PDF and correct media paths.
    
    Args:
        file_path: Path to the markdown file to update
        media_dir: The media directory name (default: "media")
    """
    if not file_path.exists():
        return
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace PDF image references with PNG
    # Handle both ![alt](path.pdf) and ![alt](path.pdf "title") formats
    content = re.sub(r'!\[([^\]]*)\]\(([^)]+)\.pdf(\s+"[^"]*")?\)', r'![\1](\2.png\3)', content)
    
    # Handle HTML img tags with PDF sources
    content = re.sub(r'<img([^>]*)\ssrc="([^"]+)\.pdf"', r'<img\1 src="\2.png"', content)
    
    # Handle pandoc-generated data-original-image-src attributes with PDF
    content = re.sub(r'data-original-image-src="([^"]+)\.pdf"', r'data-original-image-src="\1.png"', content)
    
    # Handle markdown reference-style images
    content = re.sub(r'(\[[^\]]*\]:\s*)([^\s]+)\.pdf', r'\1\2.png', content)
    
    # Fix image paths to include media directory prefix
    # Update paths that start with "figures/" to "media/figures/"
    content = re.sub(r'src="figures/', f'src="{media_dir}/figures/', content)
    content = re.sub(r'!\[([^\]]*)\]\(figures/', rf'![\1]({media_dir}/figures/', content)
    
    # Convert pandoc placeholder spans to proper img tags
    # This pattern matches: <span class="image placeholder" data-original-image-src="path.png" ...></span>
    def convert_placeholder_to_img(match):
        full_match = match.group(0)
        src_match = re.search(r'data-original-image-src="([^"]+)"', full_match)
        width_match = re.search(r'width="([^"]+)"', full_match)
        
        if src_match:
            src = src_match.group(1)
            width = width_match.group(1) if width_match else "100%"
            return f'<img src="{src}" width="{width}" />'
        return full_match
    
    content = re.sub(r'<span class="image placeholder"[^>]*data-original-image-src="[^"]*"[^>]*></span>', 
                     convert_placeholder_to_img, content)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

def clean_citation_formatting_in_markdown(content):
    """
    Clean up citation formatting in markdown content to ensure proper Quarto citation syntax.
    This function fixes any remaining issues with citation formatting after conversion.
    """
    # Fix backslashes before @ symbols in citations
    content = re.sub(r'\\@', '@', content)
    
    # Fix the specific pattern: [@key1; \@key2; \@key3] -> [@key1; @key2; @key3]
    # This is a more comprehensive fix for the issue
    def fix_citation_block(match):
        citation_content = match.group(1)
        # Remove all backslashes before @ symbols
        citation_content = re.sub(r'\\@', '@', citation_content)
        return f'[{citation_content}]'
    
    # Apply the fix to all citation blocks
    content = re.sub(r'\[([^]]*@[^]]*)\]', fix_citation_block, content)
    
    # Also handle standalone citations that might have been escaped
    content = re.sub(r'\\@(\w+)', r'@\1', content)
    
    return content

def main():
    parser = argparse.ArgumentParser(description='Convert LaTeX document to Quarto book')
    parser.add_argument('--input-dir', default='.', help='Input directory containing LaTeX files')
    parser.add_argument('--output-dir', default='../quarto_book', help='Output directory for Quarto book')
    parser.add_argument('--media-dir', default='media', help='Directory name for extracted media')
    parser.add_argument('--zip-file', default='general_purpose_models_chemrev.zip', 
                       help='Zip file containing LaTeX source (will be extracted if provided)')
    parser.add_argument('--extract-to', default='extracted_latex', 
                       help='Directory to extract zip file to')
    
    args = parser.parse_args()
    
    # Handle zip file extraction if provided
    if args.zip_file and Path(args.zip_file).exists():
        extract_dir = Path(args.extract_to)
        if extract_zip_file(args.zip_file, extract_dir):
            # Update input directory to the extracted content
            # Look for the main LaTeX files in the extracted directory
            potential_dirs = [
                extract_dir,
                extract_dir / 'latex_source',
                extract_dir / 'src',
                extract_dir / 'main'
            ]
            
            for potential_dir in potential_dirs:
                if potential_dir.exists() and (potential_dir / 'main.tex').exists():
                    args.input_dir = str(potential_dir)
                    print(f"Using extracted directory: {args.input_dir}")
                    break
            else:
                # If no main.tex found in obvious places, use the extract directory
                args.input_dir = str(extract_dir)
                print(f"Using extracted directory: {args.input_dir}")
        else:
            print(f"Failed to extract {args.zip_file}, using input directory: {args.input_dir}")
    elif args.zip_file:
        print(f"Zip file {args.zip_file} not found, using input directory: {args.input_dir}")
    
    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    media_dir = args.media_dir
    
    # Create output directory
    output_dir.mkdir(exist_ok=True)
    
    # Copy and clean bibliography file early (needed for citations)
    bib_file = input_dir / 'references.bib'
    if bib_file.exists():
        # Read, clean, and write the bibliography file
        with open(bib_file, 'r', encoding='utf-8') as f:
            bib_content = f.read()
        
        cleaned_bib_content = clean_bibliography_content(bib_content)
        
        with open(output_dir / 'references.bib', 'w', encoding='utf-8') as f:
            f.write(cleaned_bib_content)
        
        print(f"Copied and cleaned bibliography to {output_dir / 'references.bib'}")
    else:
        print("Warning: No references.bib file found")
    
    # Section mapping (order matters for the book)
    sections = [
        ('introduction.tex', '01-introduction.qmd'),
        ('data_taxonomy.tex', '02-data_taxonomy.qmd'),
        ('architectures.tex', '03-architectures.qmd'),
        ('evals.tex', '04-evals.qmd'),
        ('applications.tex', '05-applications.qmd'),
        ('safety.tex', '06-safety.qmd'),
        ('outlook_conclusions.tex', '07-outlook_conclusions.qmd')
    ]
    
    # Create media directory in output
    media_output_dir = output_dir / media_dir
    
    # Convert each section
    sections_dir = input_dir / 'sections'
    if sections_dir.exists():
        for section_file, output_file in sections:
            section_path = sections_dir / section_file
            output_path = output_dir / output_file
            
            if section_path.exists():
                convert_section_to_markdown(section_path, output_path, media_output_dir)
            else:
                print(f"Warning: Section file {section_path} not found")
    
    # Create index page
    main_tex_path = input_dir / 'main.tex'
    index_path = output_dir / 'index.qmd'
    if main_tex_path.exists():
        create_index_page(main_tex_path, index_path, media_output_dir)
    
    # Copy media directory if it exists
    media_source = input_dir / 'media'
    if media_source.exists():
        if media_output_dir.exists():
            shutil.rmtree(media_output_dir)
        shutil.copytree(media_source, media_output_dir)
        print(f"Copied media directory to {media_output_dir}")
    
    # Copy figures directory if it exists
    figures_source = input_dir / 'figures'
    if figures_source.exists():
        figures_output = media_output_dir / 'figures'
        if figures_output.exists():
            shutil.rmtree(figures_output)
        shutil.copytree(figures_source, figures_output)
        print(f"Copied figures directory to {figures_output}")
    
    # Convert PDF images to PNG for web display
    convert_pdf_images_to_png(media_output_dir)
    
    # Update image references in all markdown files
    for qmd_file in output_dir.glob('*.qmd'):
        update_image_references_in_markdown(qmd_file, media_dir)
    
    # Final cleanup: fix any remaining citation formatting issues in all markdown files
    print("Performing final citation cleanup...")
    for qmd_file in output_dir.glob('*.qmd'):
        with open(qmd_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        cleaned_content = clean_citation_formatting_in_markdown(content)
        
        with open(qmd_file, 'w', encoding='utf-8') as f:
            f.write(cleaned_content)
    
    # Create Quarto configuration
    create_quarto_config(output_dir)
    
    # Create a basic CSS file
    css_content = """
/* Custom styles for the chemistry book */
body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.quarto-title-block {
    margin-bottom: 2rem;
}

/* Chemistry-specific styling */
.chem-formula {
    font-family: 'Times New Roman', serif;
}

/* Table styling */
table {
    margin: 1rem 0;
}

/* Figure captions */
.figure-caption {
    font-style: italic;
    margin-top: 0.5rem;
}

/* Code blocks */
pre {
    background-color: #f8f9fa;
    padding: 1rem;
    border-radius: 0.375rem;
}
"""
    
    with open(output_dir / 'styles.css', 'w', encoding='utf-8') as f:
        f.write(css_content)
    
    # Convert PDF images to PNG
    convert_pdf_images_to_png(media_output_dir)
    
    # Update image references in all markdown files
    for section_file, output_file in sections:
        output_path = output_dir / output_file
        update_image_references_in_markdown(output_path, media_dir)
    
    # Update index.qmd references
    update_image_references_in_markdown(index_path, media_dir)
    
    print(f"\nConversion complete! Quarto book created in {output_dir}")
    print(f"To build the book, run: cd {output_dir} && quarto render")
    print(f"To preview the book, run: cd {output_dir} && quarto preview")
    print(f"\nNote: If you encounter issues with PDF images not displaying:")
    print(f"1. Ensure you have either 'pdftoppm' (from poppler-utils) or 'convert' (from ImageMagick) installed")
    print(f"2. On macOS: brew install poppler or brew install imagemagick")
    print(f"3. On Ubuntu/Debian: sudo apt-get install poppler-utils or sudo apt-get install imagemagick")
    print(f"4. PDF images have been automatically converted to PNG format for web display")

if __name__ == '__main__':
    main()

