#!/usr/bin/env python3
"""
Script to convert longtable to simple table and then to markdown using pandoc.
"""

import re
import subprocess
import sys
from pathlib import Path


def convert_longtable_to_simple_table(input_file, output_file):
    """
    Convert a longtable to a simple tabular environment.
    
    Args:
        input_file (str): Path to the input LaTeX file containing longtable
        output_file (str): Path to the output LaTeX file with simple table
    """
    
    # Read the input file
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix specific formatting issues before general conversion
    
    # 1. Handle SMILES makecell - convert to simpler format
    smiles_pattern = r'\\footnotesize \\makecell\[tl\]\{%\s*\\smi\{([^}]+)\}\\\\.*?\\smi\{([^}]+)\}\\\\.*?\\emph\{etc\.\}\s*\}'
    smiles_replacement = r'\\footnotesize \\texttt{\1}, \\texttt{\2}, \\emph{etc.}'
    content = re.sub(smiles_pattern, smiles_replacement, content, flags=re.DOTALL)
    
    # 2. Handle SELFIES - join fragmented texttt commands into one
    selfies_pattern = r'\\footnotesize \\texttt\{([^}]+)\}\s*\\texttt\{([^}]+)\}\s*\\texttt\{([^}]+)\}\s*\\texttt\{([^}]+)\}'
    selfies_replacement = r'\\footnotesize \\texttt{\1\2\3\4}'
    content = re.sub(selfies_pattern, selfies_replacement, content)
    
    # 3. Handle InChI - join fragmented texttt commands into one
    inchi_pattern = r'\\footnotesize \\texttt\{(InChI=[^}]+)\}\s*\\texttt\{([^}]+)\}\s*\\texttt\{([^}]+)\}'
    inchi_replacement = r'\\footnotesize \\texttt{\1\2\3}'
    content = re.sub(inchi_pattern, inchi_replacement, content)
    
    # 4. Handle cellimage commands - convert to simple text placeholders
    content = re.sub(r'\\cellimage\{([^}]+)\}', r'[Image: \1]', content)
    
    # 5. Handle smi commands that might remain
    content = re.sub(r'\\smi\{([^}]+)\}', r'\\texttt{\1}', content)
    
    # 6. Clean up any remaining makecell commands
    content = re.sub(r'\\makecell\[tl\]\{([^}]+)\}', r'\1', content)
    
    # Replace longtable with tabular
    content = re.sub(r'\\begin\{longtable\}', r'\\begin{tabular}', content)
    content = re.sub(r'\\end\{longtable\}', r'\\end{tabular}', content)
    
    # Remove longtable-specific commands
    # Remove caption and label from inside the table
    content = re.sub(r'\\caption\{.*?\}.*?\\label\{.*?\}.*?\\\\', '', content, flags=re.DOTALL)
    
    # Remove header continuation commands
    content = re.sub(r'\\endfirsthead.*?\\endhead', '', content, flags=re.DOTALL)
    content = re.sub(r'\\endfoot.*?\\endlastfoot', '', content, flags=re.DOTALL)
    
    # Remove multicolumn continuation text
    content = re.sub(r'\\multicolumn\{4\}\{c\}.*?\\\\', '', content, flags=re.DOTALL)
    content = re.sub(r'\\multicolumn\{4\}\{r\}.*?\\\\', '', content, flags=re.DOTALL)
    
    # Clean up extra spacing and line breaks
    content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
    content = re.sub(r'\\\\.*?%[^\n]*\n', r'\\\\ \n', content)  # Clean up comments after line breaks
    
    # Write the converted content
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Converted longtable to simple table: {output_file}")


def convert_latex_to_markdown_with_pandoc(input_file, output_file):
    """
    Use pandoc to convert LaTeX table to markdown.
    
    Args:
        input_file (str): Path to the input LaTeX file
        output_file (str): Path to the output markdown file
    """
    
    try:
        # Run pandoc command
        cmd = [
            'pandoc',
            '-f', 'latex',
            '-t', 'markdown',
            '--wrap=none',  # Don't wrap lines
            input_file,
            '-o', output_file
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        print(f"Successfully converted to markdown: {output_file}")
        
        # Post-process the markdown to fix remaining issues
        post_process_markdown(output_file)
        
    except subprocess.CalledProcessError as e:
        print(f"Error running pandoc: {e}")
        print(f"STDOUT: {e.stdout}")
        print(f"STDERR: {e.stderr}")
        sys.exit(1)
    except FileNotFoundError:
        print("Error: pandoc not found. Please install pandoc first.")
        print("On macOS: brew install pandoc")
        print("On Ubuntu/Debian: sudo apt-get install pandoc")
        sys.exit(1)


def post_process_markdown(markdown_file):
    """
    Clean up the markdown output to fix formatting issues.
    
    Args:
        markdown_file (str): Path to the markdown file to process
    """
    
    with open(markdown_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix acronym formatting - convert [text]{acronym-label="..."} to just text
    content = re.sub(r'\[([^\]]+)\]\{acronym-label="[^"]+"\s*acronym-form="[^"]+"\}', r'\1', content)
    
    # Fix citation formatting - convert [@citation] to (citation)
    content = re.sub(r'\[@([^\]]+)\]', r'(\1)', content)
    
    # Fix missing "2" in IUPAC name (this might be a pandoc issue)
    content = re.sub(r'-acetyloxybenzoic acid', r'2-acetyloxybenzoic acid', content)
    
    # Fix percentage symbol
    content = re.sub(r'\\%', r'100%', content)
    
    # Join fragmented code examples that might have been split by pandoc
    # Fix SELFIES - join multiple backticks into one
    content = re.sub(r'`\[C\]\[C\]\[=Branch1\]\[C\]\[=O\]\[O\]`\s*`\[C\]\[=C\]\[C\]\[=C\]\[C\]\[=C\]`\s*`\[Ring1\]\[=Branch1\]\[C\]`\s*`\[=Branch1\]\[C\]\[=O\]\[O\]`', 
                     r'`[C][C][=Branch1][C][=O][O][C][=C][C][=C][C][=C][Ring1][=Branch1][C][=Branch1][C][=O][O]`', content)
    
    # Fix InChI - join multiple backticks into one
    content = re.sub(r'`InChI=1S/C9H8O4/c1-6\(10\)13`\s*`-8-5-3-2-4-7\(8\)9\(11\)12/`\s*`h2-5H,1H3,\(H,11,12\)`', 
                     r'`InChI=1S/C9H8O4/c1-6(10)13-8-5-3-2-4-7(8)9(11)12/h2-5H,1H3,(H,11,12)`', content)
    
    # Clean up empty cells and formatting - fix SMILES examples
    content = re.sub(r'\s+\n\s+\n\s+\*etc\.\*\s+', r' `CC(=O)OC1=CC=CC=C1C(=O)O`, `O=C(O)c1ccccc1OC(C)=O`, *etc.*', content)
    
    # Make sure image placeholders are clear and italicized
    content = re.sub(r'\[Image: ([^\]]+)\]', r'*[Image: \1]*', content)
    
    # Fix missing representation names
    content = re.sub(r'^\s+\(Xiao_2023\)', r'  SLICES (Xiao_2023)', content, flags=re.MULTILINE)
    content = re.sub(r'^\s+\(alampara2024mattext\)', r'  Local-Env (alampara2024mattext)', content, flags=re.MULTILINE)
    
    # Fix rows where images should appear but are missing
    content = re.sub(r'(Graphs\s+.*?implicit\.\s+)\n', r'\1*[Image: figures/Aspirin.png]*\n', content)
    content = re.sub(r'(Multimodal\s+.*?included\.\s+)\n', r'\1*[Image: figures/60031761.jpeg]*\n', content)
    
    # Clean up extra spaces and improve readability
    content = re.sub(r'\s+\n', '\n', content)
    
    with open(markdown_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Post-processed markdown file: {markdown_file}")


def main():
    """Main function to orchestrate the conversion process."""
    
    # Define file paths
    input_file = "/Users/martino/Nueva_Carpeta/GPMs-book/convert_book/extracted_latex/extras/representation_table.tex"
    simple_table_file = "/Users/martino/Nueva_Carpeta/GPMs-book/convert_book/simple_table.tex"
    markdown_file = "/Users/martino/Nueva_Carpeta/GPMs-book/convert_book/new_table.md"
    
    # Check if input file exists
    if not Path(input_file).exists():
        print(f"Error: Input file not found: {input_file}")
        sys.exit(1)
    
    # Step 1: Convert longtable to simple table
    print("Step 1: Converting longtable to simple table...")
    convert_longtable_to_simple_table(input_file, simple_table_file)
    
    # Step 2: Convert LaTeX table to markdown using pandoc
    print("Step 2: Converting LaTeX table to markdown using pandoc...")
    convert_latex_to_markdown_with_pandoc(simple_table_file, markdown_file)
    
    print("\nConversion complete!")
    print(f"Simple table saved as: {simple_table_file}")
    print(f"Markdown table saved as: {markdown_file}")


if __name__ == "__main__":
    main()
