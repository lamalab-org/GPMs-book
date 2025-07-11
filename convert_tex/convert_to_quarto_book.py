#!/usr/bin/env python3
"""
LaTeX to Quarto Book Converter

This script converts a LaTeX document with multiple sections into a Quarto book
with each section as a separate webpage.
"""

import re
import os
import tempfile
import subprocess
import re
import shutil
from pathlib import Path
import tempfile
import argparse
import yaml
import zipfile
from pathlib import Path


def split_applications_file(applications_path, output_dir):
    """
    Split the applications.tex file into two parts:
    1. applications_part1.tex - content before "Accelerating Applications"
    2. applications_part2.tex - content from "Accelerating Applications" onwards
    """
    with open(applications_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Find the split point
    split_pattern = r"\\section\{Accelerating Applications\}"
    match = re.search(split_pattern, content)

    if not match:
        print(
            "Warning: Could not find 'Accelerating Applications' section. Using original file."
        )
        # If we can't find the split point, just copy the original file
        shutil.copy(applications_path, output_dir / "applications_part1.tex")
        # Create empty part2 file
        with open(output_dir / "applications_part2.tex", "w", encoding="utf-8") as f:
            f.write("\\section{Accelerating Applications}\n% No content found\n")
        return

    # Split the content
    split_pos = match.start()

    # Part 1: Everything before "Accelerating Applications"
    part1_content = content[:split_pos].rstrip()

    # Part 2: Everything from "Accelerating Applications" onwards
    part2_content = content[split_pos:]

    # Write the split files
    with open(output_dir / "applications_part1.tex", "w", encoding="utf-8") as f:
        f.write(part1_content)

    with open(output_dir / "applications_part2.tex", "w", encoding="utf-8") as f:
        f.write(part2_content)

    print(f"Split applications.tex into two parts:")
    print(f"  - Part 1: {len(part1_content)} characters")
    print(f"  - Part 2: {len(part2_content)} characters")


def clean_bibliography_content(content):
    """
    Clean bibliography content by fixing problematic Unicode characters.
    """
    # Fix problematic Unicode characters
    content = content.replace(
        "‑", "-"
    )  # Replace non-breaking hyphen with regular hyphen
    content = content.replace("–", "-")  # Replace en-dash with hyphen
    content = content.replace("—", "-")  # Replace em-dash with hyphen
    content = content.replace(
        """, "'")  # Replace smart quote
    content = content.replace(""",
        "'",
    )  # Replace smart quote
    content = content.replace('"', '"')  # Replace smart quote
    content = content.replace('"', '"')  # Replace smart quote
    content = content.replace("…", "...")  # Replace ellipsis
    content = content.replace("×", "x")  # Replace multiplication sign
    content = content.replace("°", "deg")  # Replace degree symbol
    content = content.replace("±", "+/-")  # Replace plus-minus
    content = content.replace("α", "alpha")  # Replace Greek alpha
    content = content.replace("β", "beta")  # Replace Greek beta
    content = content.replace("γ", "gamma")  # Replace Greek gamma
    content = content.replace("δ", "delta")  # Replace Greek delta
    content = content.replace("ε", "epsilon")  # Replace Greek epsilon
    content = content.replace("θ", "theta")  # Replace Greek theta
    content = content.replace("λ", "lambda")  # Replace Greek lambda
    content = content.replace("μ", "mu")  # Replace Greek mu
    content = content.replace("π", "pi")  # Replace Greek pi
    content = content.replace("σ", "sigma")  # Replace Greek sigma
    content = content.replace("τ", "tau")  # Replace Greek tau
    content = content.replace("φ", "phi")  # Replace Greek phi
    content = content.replace("χ", "chi")  # Replace Greek chi
    content = content.replace("ψ", "psi")  # Replace Greek psi
    content = content.replace("ω", "omega")  # Replace Greek omega

    # Fix other problematic characters
    content = content.replace("\u2009", " ")  # Replace thin space
    content = content.replace("\u202f", " ")  # Replace narrow no-break space
    content = content.replace("\u2011", "-")  # Replace non-breaking hyphen
    content = content.replace("\u2012", "-")  # Replace figure dash
    content = content.replace("\u2013", "-")  # Replace en dash
    content = content.replace("\u2014", "-")  # Replace em dash
    content = content.replace("\u2015", "-")  # Replace horizontal bar
    content = content.replace("\u2212", "-")  # Replace minus sign

    return content


def fix_heading_levels(content):
    """
    Fix skipped heading levels in markdown content.

    This function ensures that heading levels are sequential (no skipped levels).
    For example, if we have h1 -> h4, it converts h4 to h3.
    It also handles cases where headings go back to a higher level.
    """
    lines = content.split("\n")
    result_lines = []

    # Track the current heading level context (the last heading level we've seen)
    current_level = 0

    for line in lines:
        # Check if this line is a heading
        if line.strip().startswith("#") and not line.strip().startswith("```"):
            # Count the number of '#' characters
            hash_count = 0
            for char in line:
                if char == "#":
                    hash_count += 1
                else:
                    break

            # Skip if this looks like a comment (more than 6 #'s usually indicates a comment)
            if hash_count > 6:
                result_lines.append(line)
                continue

            # Determine the appropriate level based on context
            if hash_count == 1:
                # H1 headings reset the context
                current_level = 1
                adjusted_line = line
            else:
                # For other headings, ensure they don't skip levels
                if hash_count <= current_level + 1:
                    # This heading is at an appropriate level or going back up
                    adjusted_line = line
                    current_level = hash_count
                else:
                    # This heading is too deep, adjust it to the max allowed level
                    max_allowed_level = current_level + 1
                    adjusted_hash_count = max_allowed_level
                    # Replace the heading hashes
                    content_part = line[hash_count:].rstrip()
                    adjusted_line = "#" * adjusted_hash_count + content_part
                    current_level = adjusted_hash_count

            result_lines.append(adjusted_line)
        else:
            result_lines.append(line)

    return "\n".join(result_lines)


def clean_latex_content(content):
    """
    Clean LaTeX content by removing/modifying problematic commands for pandoc conversion.
    """
    # Remove \usepackage commands
    content = re.sub(
        r"\\usepackage(?:\[.*?\])?\{.*?\}", "", content, flags=re.MULTILINE
    )

    # Remove \input commands for preamble, authors, etc. but keep section inputs
    # Note: section inputs are now handled by resolve_input_commands before this function
    content = re.sub(r"\\input\{(?!sections/).*?\}", "", content)

    # Remove document class
    content = re.sub(r"\\documentclass(?:\[.*?\])?\{.*?\}", "", content)

    # Remove \begin{document} and \end{document}
    content = re.sub(r"\\begin\{document\}", "", content)
    content = re.sub(r"\\end\{document\}", "", content)

    # Remove \maketitle
    content = re.sub(r"\\maketitle", "", content)

    # Remove \clearpage
    content = re.sub(r"\\clearpage", "", content)

    # Remove \tableofcontents
    content = re.sub(r"\\tableofcontents", "", content)

    # Remove bibliography commands (will be handled by pandoc)
    content = re.sub(r"\\printbibliography", "", content)

    # Remove glossary commands
    content = re.sub(r"\\glsaddall", "", content)
    content = re.sub(r"\\printnoidxglossary.*", "", content)

    # Remove \title commands (will be handled in YAML frontmatter)
    content = re.sub(r"\\title\{.*?\}", "", content, flags=re.DOTALL)

    # Convert \section* to \section (pandoc handles this better)
    content = re.sub(r"\\section\*", r"\\section", content)

    # Convert custom \modelname command to \texttt before pandoc processes it
    # \modelname{text} -> \texttt{text}
    content = re.sub(r"\\modelname\{([^}]+)\}", r"\\texttt{\1}", content)

    # Convert \ce{} chemical equation commands to plain text (keep only the content)
    content = re.sub(r"\\ce\{([^}]+)\}", r"\1", content)

    # Clean up citation issues before conversion
    # Fix citation issues - remove double commas and trailing/leading commas
    content = re.sub(
        r"\\(cite|textcite|autocite|parencite|citet|citep)\{([^}]*),\s*,\s*([^}]*)\}",
        r"\\\1{\2,\3}",
        content,
    )
    content = re.sub(
        r"\\(cite|textcite|autocite|parencite|citet|citep)\{,\s*([^}]*)\}",
        r"\\\1{\2}",
        content,
    )
    content = re.sub(
        r"\\(cite|textcite|autocite|parencite|citet|citep)\{([^}]*),\s*\}",
        r"\\\1{\2}",
        content,
    )
    content = re.sub(
        r"\\(cite|textcite|autocite|parencite|citet|citep)\{([^}]*),\s*,\s*\}",
        r"\\\1{\2}",
        content,
    )

    # Fix problematic Unicode characters
    content = content.replace("‑", "-")  # Replace en-dash with hyphen
    content = content.replace("–", "-")  # Replace em-dash with hyphen
    content = content.replace("—", "-")  # Replace em-dash with hyphen
    content = content.replace(
        """, "'")  # Replace smart quote
    content = content.replace(""",
        "'",
    )  # Replace smart quote
    content = content.replace('"', '"')  # Replace smart quote
    content = content.replace('"', '"')  # Replace smart quote

    # Remove empty lines (more than 2 consecutive)
    content = re.sub(r"\n\s*\n\s*\n", "\n\n", content)

    return content.strip()


def extract_title_from_section(content):
    """Extract the title from a section file."""
    match = re.search(r"\\section\{(.*?)\}", content)
    if match:
        # Clean LaTeX commands from title
        title = match.group(1)
        title = re.sub(
            r"\\.*?\{(.*?)\}", r"\1", title
        )  # Remove LaTeX commands but keep content
        title = re.sub(r"\\.*?\s", "", title)  # Remove standalone LaTeX commands
        return title.strip()
    return "Untitled"


def create_section_frontmatter():
    """Create YAML frontmatter for a section."""
    return f"""---
format:
  html:
    toc: true
    smooth-scroll: true
    anchor-sections: true
    other-links:
    - text: Visit our website
      href: https://lamalab.org/
      icon: globe
    - text: Follow us on X (Twitter)
      href: https://x.com/jablonkagroup
      icon: twitter-x
    - text: We are hiring!
      href: https://forms.fillout.com/t/eoGA7AhnAKus
      icon: person-badge
    - text: Contact us
      href: mailto:contact@lamalab.org
      icon: mailbox
acronyms:
  insert_loa: false 
  insert_links: false  
  fromfile: ./acronyms.yml
---

"""


def convert_citations_to_markdown(content):
    """Convert LaTeX citations to markdown format that Quarto can process."""

    # Function to clean citation keys
    def clean_citation_keys(keys_str):
        """Clean and format citation keys."""
        keys = [k.strip() for k in keys_str.split(",")]
        # Remove empty keys and clean up problematic characters
        cleaned_keys = []
        for key in keys:
            if key and not key.isspace():
                # Remove any trailing/leading commas or spaces
                key = key.strip(" ,")
                if key:
                    cleaned_keys.append(key)
        return cleaned_keys

    # Convert \cite{} to [@key]
    def replace_cite(match):
        keys = clean_citation_keys(match.group(1))
        if keys:
            return "[@" + "; @".join(keys) + "]"
        return ""

    # Convert \textcite{} to @key (for single citations) or [@key1; @key2] for multiple
    def replace_textcite(match):
        keys = clean_citation_keys(match.group(1))
        if not keys:
            return ""
        if len(keys) == 1:
            return f"@{keys[0]}"
        else:
            return "[@" + "; @".join(keys) + "]"

    # Apply replacements
    content = re.sub(r"\\cite\{([^}]+)\}", replace_cite, content)
    content = re.sub(r"\\textcite\{([^}]+)\}", replace_textcite, content)
    content = re.sub(r"\\autocite\{([^}]+)\}", replace_cite, content)
    content = re.sub(r"\\parencite\{([^}]+)\}", replace_cite, content)
    content = re.sub(r"\\citet\{([^}]+)\}", replace_textcite, content)
    content = re.sub(r"\\citep\{([^}]+)\}", replace_cite, content)

    # Handle any remaining malformed citations (like those with extra commas)
    content = re.sub(r"\[@([^]]*),\s*,\s*([^]]*)\]", r"[@\1; @\2]", content)
    content = re.sub(r"\[@,\s*([^]]*)\]", r"[@\1]", content)
    content = re.sub(r"\[@([^]]*),\s*\]", r"[@\1]", content)

    # Fix any remaining cases where backslashes got added before @ symbols
    content = re.sub(r"\\@", "@", content)

    # Additional cleanup for the specific issue: fix \@key patterns inside citation brackets
    # This handles cases like [@key1; \@key2; \@key3] -> [@key1; @key2; @key3]
    content = re.sub(r"(\[@[^]]*?)\\@", r"\1@", content)

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
                with open(input_path, "r", encoding="utf-8") as f:
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
    content = re.sub(r"\\input\{([^}]+)\}", replace_input, content)

    return content


def convert_section_to_markdown(
    section_path, output_path, extract_media_dir, base_dir=None
):
    """Convert a single section LaTeX file to markdown."""
    print(f"Converting {section_path} to {output_path}")

    # Read and clean the section content
    with open(section_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Determine the correct base directory for resolving \input{} commands
    if base_dir is None:
        base_dir = section_path.parent.parent

    # Resolve any \input{} commands in the content
    content = resolve_input_commands(content, base_dir)

    # Extract title for frontmatter
    title = extract_title_from_section(content)

    # Clean the content
    cleaned_content = clean_latex_content(content)

    # Convert citations to markdown format
    cleaned_content = convert_citations_to_markdown(cleaned_content)

    # Create temporary file with cleaned content
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".tex", delete=False, encoding="utf-8"
    ) as temp_file:
        temp_file.write(cleaned_content)
        temp_file_path = temp_file.name

    try:
        # Convert with pandoc (without --citeproc since Quarto will handle citations)
        pandoc_cmd = [
            "pandoc",
            temp_file_path,
            "-s",
            "--from=latex",
            "--to=markdown+yaml_metadata_block+raw_tex",
            f"--extract-media={extract_media_dir}",
            "-o",
            output_path,
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
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(basic_content)
            return

        # Only proceed if output file was created
        if not output_path.exists():
            print(f"Error: Output file {output_path} was not created")
            return

        # Read the converted content and add proper frontmatter
        with open(output_path, "r", encoding="utf-8") as f:
            markdown_content = f.read()

        # Remove any existing frontmatter and add our own
        if markdown_content.startswith("---"):
            # Find the end of existing frontmatter
            lines = markdown_content.split("\n")
            frontmatter_end = -1
            for i, line in enumerate(lines[1:], 1):
                if line.strip() == "---":
                    frontmatter_end = i
                    break
            if frontmatter_end > 0:
                markdown_content = "\n".join(lines[frontmatter_end + 1 :])

        # Add our frontmatter
        final_content = create_section_frontmatter() + markdown_content

        # Clean up any remaining citation formatting issues
        final_content = clean_citation_formatting_in_markdown(final_content)

        # Fix heading levels to ensure no levels are skipped
        final_content = fix_heading_levels(final_content)
        
        # Convert LaTeX acronyms to glossary shortcodes
        final_content = convert_latex_acronyms_to_glossary_shortcodes(final_content)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(final_content)

        # Update image references to use PNG instead of PDF
        update_image_references_in_markdown(output_path, "media")

    finally:
        # Clean up temporary file
        os.unlink(temp_file_path)


def create_index_page(main_tex_path, output_path, extract_media_dir):
    """Create the index page from main.tex."""
    print(f"Creating index page from {main_tex_path}")

    with open(main_tex_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Extract title
    title_match = re.search(r"\\title\{\\textsf\{(.*?)\}\}", content)
    if not title_match:
        title_match = re.search(r"\\title\{(.*?)\}", content, re.DOTALL)

    title = "General Purpose Models for the Chemical Sciences"
    if title_match:
        title = title_match.group(1)
        title = re.sub(r"\\.*?\{(.*?)\}", r"\1", title)
        title = re.sub(r"\\.*?\s", "", title)
        title = title.strip()

    # Extract abstract
    abstract_match = re.search(
        r"\\begin\{abstract\}(.*?)\\end\{abstract\}", content, re.DOTALL
    )
    abstract = ""
    if abstract_match:
        abstract = abstract_match.group(1).strip()
        abstract = re.sub(r"\\noindent\s*", "", abstract)
        abstract = clean_latex_content(abstract)

    # Create index content
    index_content = (
        create_section_frontmatter()
        + f"""
# {title} {{.unnumbered}}

## Abstract

{abstract}

## Acknowledgments

This work was supported by the Carl-Zeiss Foundation. 

A.A. acknowledges financial support for this research by the Fulbright U.S. Student Program, which is sponsored by the U.S. Department of State and the German-American Fulbright Commission. Its contents are solely the responsibility of the author and do not necessarily represent the official views of the Fulbright Program, the Government of the United States, or the German-American Fulbright Commission. 
 
M. S.-W. was supported by Intel and Merck via the AWASES research center. 

A.M.'s work was funded by the SOL-AI project, funded as part of the Helmholtz Foundation Model Initiative of the Helmholtz Association. 

G.P.'s work was supported by the HPC Gateway measure of the Helmholtz Association.

K.M.J. is part of the NFDI consortium FAIRmat funded by the Deutsche Forschungsgemeinschaft (DFG, German Research Foundation) - project 460197019.

We thank Mimi Lavin and Maximilian Greiner for their feedback on a draft of this article.

## Author contributions

N. A. was the lead contributor for the [Building Principles of GPMs](03-architectures.qmd) section. Including its writing and figures (excluding the [Model Level Adaptation](03-architectures.qmd#sec:model_adaptation) subsection). N. A. also reviewed the [Introduction](01-introduction.qmd), [The Shape and Structure of Chemical Data](02-data_taxonomy.qmd), [Evaluations](04-evals.qmd), [Implications of GPMs: Education, Safety, and Ethics](07-safety.qmd), and [Property Prediction](05-applications.qmd#sec:prediction) and [Molecular and Material Generation](05-applications.qmd#sec:mol_generation) sections.

A. A. was the primary contributor to the writing of the [Property Prediction](05-applications.qmd#sec:prediction), [Molecular and Material Generation](05-applications.qmd#sec:mol_generation), [Safety](07-safety.qmd#sec:safety), and [Ethics](07-safety.qmd#sec:ethics) sections, conceptualized the outline for safety and ethics sections, designed and created all figures/schematics/plots in sections with primary contribution, was one of the contributors to the [AI Scientists](05-applications.qmd#sec:ai-scientists) overview, edited [Introduction](01-introduction.qmd), [Evaluations](04-evals.qmd), [Building Principles of GPMs](03-architectures.qmd), [Knowledge Gathering](05-applications.qmd#sec:information_gathering), [Experiment Execution](05-applications.qmd#sec:experiment_execution), and [Education](07-safety.qmd#sec:education) sections.

M.R.-G. was the primary contributor to the [AI Scientists](05-applications.qmd#sec:ai-scientists) overview, the [Hypothesis Generation](05-applications.qmd#sec:hypothesis), and the [LLMs as Optimizers](05-applications.qmd#sec:optimizers) sections, and helped in reviewing the entire manuscript.

A.M. was the main contributor to the [Introduction](01-introduction.qmd) and [The Shape and Structure of Chemical Data](02-data_taxonomy.qmd) sections, and the main contributor to the [Knowledge Gathering](05-applications.qmd#sec:information_gathering) and [Reporting](05-applications.qmd#sec:reporting) sections within the applications section, with minor contributions to the [Building Principles of GPMs](03-architectures.qmd) and the [Safety](07-safety.qmd#sec:safety) sections. Has drafted the initial outline of the article. Reviewed the [Building Principles of GPMs](03-architectures.qmd) sections, the [Safety](07-safety.qmd#sec:safety) section, the [Hypothesis Generation](05-applications.qmd#sec:hypothesis), the [Data Analysis](05-applications.qmd#sec:data_analysis) sections and contributed to the review of the [LLMs as Optimizers](05-applications.qmd#sec:optimizers) section.

M.S.-W. was the main contributor to the [Evaluations](04-evals.qmd), [Education](07-safety.qmd#sec:education) and [Data Analysis](05-applications.qmd#sec:data_analysis) section. M.S.-W. also reviewed the [The Shape and Structure of Chemical Data](02-data_taxonomy.qmd), [Hypothesis Generation](05-applications.qmd#sec:hypothesis), [Experiment Execution](05-applications.qmd#sec:experiment_execution), [Reporting](05-applications.qmd#sec:reporting) and [Safety](07-safety.qmd#sec:safety) section. Unified all figures. Kept track of upcoming deadlines.

A.A.A. was the main contributor to the [Experiment Execution](05-applications.qmd#sec:experiment_execution) section, including its figure, and a minor contributor to the post-training subsection. A.A.A. reviewed the [Introduction](01-introduction.qmd), [Experiment Planning](05-applications.qmd#sec:planning), [Molecular and Material Generation](05-applications.qmd#sec:mol_generation) and [Education](07-safety.qmd#sec:education) sections, edited [The Shape and Structure of Chemical Data](02-data_taxonomy.qmd) and [Building Principles of GPMs](03-architectures.qmd) sections, created the glossary, and ensured that most references are accessible via a DOI.

M. S. was the primary contributor to the writing of [Experiment Planning](05-applications.qmd#sec:planning) section and related figure. And also helped in reviewing [Knowledge Gathering](05-applications.qmd#sec:information_gathering), [Property Prediction](05-applications.qmd#sec:prediction), and [LLMs as Optimizers](05-applications.qmd#sec:optimizers) sections.

G.P. was the main contributor to [Model Level Adaptation](03-architectures.qmd#sec:model_adaptation) section, including its writing and table. G.P. additionally reviewed the [The Shape and Structure of Chemical Data](02-data_taxonomy.qmd), [Data Analysis](05-applications.qmd#sec:data_analysis), [Reporting](05-applications.qmd#sec:reporting) and [Molecular and Material Generation](05-applications.qmd#sec:mol_generation) sections.

K.M.J. initiated and led the project. K.M.J. edited all sections. 

## Conflicts of Interest

K.M.J. has been a paid contractor for OpenAI as part of the Red-Teaming Network.

## Citation

If you find this work useful, please cite it using:

```bibtex
@article{{alampara2025general,
  title   = {{General purpose models for the chemical sciences}},
  author  = {{Nawaf Alampara and Anagha Aneesh and Martiño Ríos-García and Adrian Mirza and Mara Schilling-Wilhelmi and Ali Asghar Aghajani and Meiling Sun and Gordan Prastalo and Kevin Maik Jablonka}},
  year    = {{2025}},
  journal = {{arXiv preprint arXiv: 2507.07456}}
}}
```

---

## Table of Contents

This book covers the following topics:

1. [Introduction](01-introduction.qmd)
2. [The Shape and Structure of Chemical Data](02-data_taxonomy.qmd)
3. [Building Principles of GPMs](03-architectures.qmd)
4. [Evaluations](04-evals.qmd)
5. [Applications](05-applications.qmd)
6. [Accelerating Applications](06-accelerating_applications.qmd)
7. [Implications of GPMs: Education, Safety, and Ethics](07-safety.qmd)
8. [Outlook and Conclusions](08-outlook_conclusions.qmd)
-  [References](09-references.qmd)
"""
    )

    # Clean up any remaining citation formatting issues in the index content
    index_content = clean_citation_formatting_in_markdown(index_content)

    # Fix heading levels to ensure no levels are skipped
    index_content = fix_heading_levels(index_content)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(index_content)

def convert_acronyms_to_yaml(input_file, output_file):
    """
    Convert acronyms from LaTeX glossaries package format to YAML format for the glossary extension.
    
    This function creates a glossary file in YAML format suitable for the acronyms extension.
    The format for the file will be:
    ---
    acronyms:
      keys:
      - key: ppo
        shortname: PPO
        longname: proximal policy optimization
      - shortname: RL # key defaults to shortname
        longname: reinforcement learning
    ---
    
    Args:
        input_file: Path to the input .tex file containing LaTeX acronyms
        output_file: Path to the output .yml file where converted acronyms will be saved
    """
    import re
    
    acronyms_list = []
    processed_keys = set()
    # Special cases that need custom handling
    special_cases = {
        'chidl': {'shortname': '$\\chi$DL', 'longname': 'chemical description language'}
    }

    # Read the input file
    with open(input_file, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Extract acronyms with the optional long parameter
    long_pattern = r'\\newacronym\[long=(.*?)\]\{(.*?)\}\{(.*?)\}\{.*?\}'
    for match in re.finditer(long_pattern, content):
        longname, key, shortname = match.groups()
        
        # Check if this is a special case
        if key in special_cases:
            shortname = special_cases[key]['shortname']
            longname = special_cases[key]['longname']
        
        # Store the acronym information in the list
        acronyms_list.append({
            'key': key,
            'shortname': shortname,
            'longname': longname
        })
        processed_keys.add(key)
    
    # Extract basic acronyms without the optional parameter
    basic_pattern = r'\\newacronym\{(.*?)\}\{(.*?)\}\{(.*?)\}'
    for match in re.finditer(basic_pattern, content):
        key, shortname, longname = match.groups()
        # Skip acronyms that were already processed with the long parameter
        if key not in processed_keys:
            # Check if this is a special case
            if key in special_cases:
                shortname = special_cases[key]['shortname']
                longname = special_cases[key]['longname']
                
            # Check if longname contains a backslash (likely referring to glossary)
            if '\\' in longname:
                # Try to find the corresponding long parameter version
                long_match = re.search(fr'\\newacronym\[long=(.*?)\]\{{{key}\}}', content)
                if long_match:
                    # Use the long parameter value instead
                    longname = long_match.group(1)
                elif '(' in longname and 'See glossary' in longname:
                    # Extract just the first part before the reference to glossary
                    longname = longname.split('(')[0].strip()
            
            # Store the acronym information in the list
            acronyms_list.append({
                'key': key,
                'shortname': shortname,
                'longname': longname
            })
            processed_keys.add(key)
    
    # Sort the list alphabetically by key
    acronyms_list.sort(key=lambda x: x['key'])
    
    # Create the YAML content in the new format with delimiting dashes
    yaml_content = "---\n"
    yaml_content += "acronyms:\n"
    yaml_content += "  keys:\n"
    
    for entry in acronyms_list:
        key = entry['key']
        shortname = entry['shortname']
        longname = entry['longname']
        
        # Format each entry according to the new structure
        yaml_content += f"  - key: {key}\n"
        yaml_content += f"    shortname: {shortname}\n"
        yaml_content += f"    longname: {longname}\n"
    
    # Add closing delimiter
    yaml_content += "---\n"
    
    # Write the formatted YAML content to the output file
    with open(output_file, 'w', encoding='utf-8') as file:
        file.write(yaml_content)
    
    print(f"Converted {len(acronyms_list)} acronyms from LaTeX to YAML format in the new structure")
    print(f"Output saved to {output_file}")

def create_quarto_config(output_dir):
    """Create the _quarto.yml configuration file."""
    config = {
        "project": {
            "type": "book",
            "output-dir": "../docs",
            "title": "General Purpose Models for the Chemical Sciences",
        },
        "book": {
            "title": "General Purpose Models for the Chemical Sciences",
            "author": "Nawaf Alampara, Anagha Aneesh, Martiño Ríos-García, Adrian Mirza, Mara Schilling-Wilhelmi, Ali Asghar Aghajani, Meiling Sun, Gordan Prastalo, Kevin Maik Jablonka",
            "date": "today",
            "page-footer": {
                "left": (
                    '<img src="https://raw.githubusercontent.com/lamalab-org/'
                    'lamalab.github.io/main/static/png-file.png" '
                    'alt="Lab for AI in Materials Science logo" '
                    'style="height:3rem;vertical-align:middle;'
                    'margin-right:0.4rem;">'
                ),
                "right": "Copyright © 2025 Lab for AI in Materials Science",
            },
            "chapters": [
                "index.qmd",
                "01-introduction.qmd",
                "02-data_taxonomy.qmd",
                "03-architectures.qmd",
                "04-evals.qmd",
                "05-applications.qmd",
                "06-accelerating_applications.qmd",
                "07-safety.qmd",
                "08-outlook_conclusions.qmd",
                "09-references.qmd",
            ],
        },
        "bibliography": "references.bib",
        "format": {
            "html": {
                "theme": "cosmo",
                "css": "styles.css",
                "toc": True,
                "toc-depth": 5,
                "number-sections": True,
                "highlight-style": "github",
                "code-link": True,
                "toc-title": "On this page",
                "code-overflow": "wrap",
            }
        },
        "execute": {"freeze": "auto"},
        "filters": [
            "acronyms",
        ]
    }

    config_path = output_dir / "_quarto.yml"
    with open(config_path, "w", encoding="utf-8") as f:
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
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
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
            png_file = pdf_file.with_suffix(".png")

            # Convert PDF to PNG using pdftoppm (part of poppler-utils)
            # Try pdftoppm first (usually better quality)
            convert_cmd = [
                "pdftoppm",
                "-png",
                "-singlefile",
                "-r",
                "300",  # 300 DPI for good quality
                str(pdf_file),
                str(png_file.with_suffix("")),  # pdftoppm adds .png automatically
            ]

            result = subprocess.run(
                convert_cmd, capture_output=True, text=True, check=False
            )

            if result.returncode == 0:
                print(f"Converted {pdf_file.name} to PNG")
                converted_count += 1
            else:
                # Try with ImageMagick convert as fallback
                convert_cmd_alt = [
                    "convert",
                    "-density",
                    "300",
                    str(pdf_file),
                    str(png_file),
                ]

                result_alt = subprocess.run(
                    convert_cmd_alt, capture_output=True, text=True, check=False
                )

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
    Ensures all images have width="100%".

    Args:
        file_path: Path to the markdown file to update
        media_dir: The media directory name (default: "media")
    """
    if not file_path.exists():
        return

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Replace PDF image references with PNG and add width attributes
    # Handle both ![alt](path.pdf) and ![alt](path.pdf "title") formats
    # Convert to HTML img tags with width="100%"
    def replace_markdown_image_pdf(match):
        alt_text = match.group(1)
        image_path = match.group(2)
        title = match.group(3) if match.group(3) else ""
        if title.strip():
            title_clean = title.strip(' "')
            title_attr = f' title="{title_clean}"'
        else:
            title_attr = ""
        return (
            f'<img src="{image_path}.png" alt="{alt_text}" width="100%"{title_attr} />'
        )

    content = re.sub(
        r'!\[([^\]]*)\]\(([^)]+)\.pdf(\s+"[^"]*")?\)',
        replace_markdown_image_pdf,
        content,
    )

    # Handle regular PNG/JPG markdown images and convert to HTML with width="100%"
    def replace_markdown_image_regular(match):
        alt_text = match.group(1)
        image_path = match.group(2)
        title = match.group(3) if match.group(3) else ""
        if title.strip():
            title_clean = title.strip(' "')
            title_attr = f' title="{title_clean}"'
        else:
            title_attr = ""
        return f'<img src="{image_path}" alt="{alt_text}" width="100%"{title_attr} />'

    content = re.sub(
        r'!\[([^\]]*)\]\(([^)]+\.(?:png|jpg|jpeg|gif|svg))(\s+"[^"]*")?\)',
        replace_markdown_image_regular,
        content,
    )

    # Handle HTML img tags with PDF sources and ensure width="100%"
    def replace_html_img_pdf(match):
        other_attrs = match.group(1)
        image_path = match.group(2)
        # Remove existing width attributes from other_attrs
        other_attrs = re.sub(r'\s*width="[^"]*"', "", other_attrs)
        return f'<img{other_attrs} src="{image_path}.png" width="100%"'

    content = re.sub(r'<img([^>]*)\ssrc="([^"]+)\.pdf"', replace_html_img_pdf, content)

    # Handle existing HTML img tags and ensure they have width="100%"
    def ensure_img_width(match):
        pre_src = match.group(1)
        src = match.group(2)
        post_src = match.group(3)

        # Remove existing width attributes
        pre_src = re.sub(r'\s*width="[^"]*"', "", pre_src)
        post_src = re.sub(r'\s*width="[^"]*"', "", post_src)

        # Add width="100%" before the closing tag
        return f'<img{pre_src} src="{src}"{post_src} width="100%"'

    content = re.sub(r'<img([^>]*)\ssrc="([^"]+)"([^>]*)', ensure_img_width, content)

    # Handle pandoc-generated data-original-image-src attributes with PDF
    content = re.sub(
        r'data-original-image-src="([^"]+)\.pdf"',
        r'data-original-image-src="\1.png"',
        content,
    )

    # Handle markdown reference-style images
    content = re.sub(r"(\[[^\]]*\]:\s*)([^\s]+)\.pdf", r"\1\2.png", content)

    # Fix image paths to include media directory prefix
    # Update paths that start with "figures/" to "media/figures/"
    content = re.sub(r'src="figures/', f'src="{media_dir}/figures/', content)
    content = re.sub(
        r"!\[([^\]]*)\]\(figures/", rf"![\1]({media_dir}/figures/", content
    )

    # Convert pandoc placeholder spans to proper img tags with width="100%"
    # This pattern matches: <span class="image placeholder" data-original-image-src="path.png" ...></span>
    def convert_placeholder_to_img(match):
        full_match = match.group(0)
        src_match = re.search(r'data-original-image-src="([^"]+)"', full_match)
        alt_match = re.search(r'alt="([^"]*)"', full_match)

        if src_match:
            src = src_match.group(1)
            alt = alt_match.group(1) if alt_match else ""
            return f'<img src="{src}" alt="{alt}" width="100%" />'
        return full_match

    content = re.sub(
        r'<span class="image placeholder"[^>]*data-original-image-src="[^"]*"[^>]*></span>',
        convert_placeholder_to_img,
        content,
    )

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)


def clean_citation_formatting_in_markdown(content):
    """
    Clean up citation formatting in markdown content to ensure proper Quarto citation syntax.
    This function fixes any remaining issues with citation formatting after conversion.
    """
    # Fix backslashes before @ symbols in citations
    content = re.sub(r"\\@", "@", content)

    # Fix the specific pattern: [@key1; \@key2; \@key3] -> [@key1; @key2; @key3]
    # This is a more comprehensive fix for the issue
    def fix_citation_block(match):
        citation_content = match.group(1)
        # Remove all backslashes before @ symbols
        citation_content = re.sub(r"\\@", "@", citation_content)
        return f"[{citation_content}]"

    # Apply the fix to all citation blocks
    content = re.sub(r"\[([^]]*@[^]]*)\]", fix_citation_block, content)

    # Also handle standalone citations that might have been escaped
    content = re.sub(r"\\@(\w+)", r"@\1", content)

    return content


def replace_boxes_with_images(
    file_path, eq_images_dir="../docs/eq_images", media_dir="media"
):
    """
    Replace tcolorbox equations and promptbox blocks with images.

    Args:
        file_path: Path to the markdown file to update
        eq_images_dir: Directory containing equation images
        media_dir: The media directory name in output
    """
    if not file_path.exists():
        print(f"Warning: File {file_path} does not exist")
        return

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Define image mappings based on labels - extract label from eq:label or box: label format
    image_mappings = {
        "eq:nexttoken": "nexttoken.png",
        "eq:infonce": "infonce.png",
        "eq:rl_objective": "rl_objective.png",
        "eq:cot_prompting": "cot_prompting.png",
        "box:cot_prompting": "cot_prompting.png",
        "box: cot_prompting": "cot_prompting.png",
        # Add any other mappings here as needed
        "nexttoken": "nexttoken.png",
        "infonce": "infonce.png",
        "rl_objective": "rl_objective.png",
        "cot_prompting": "cot_prompting.png",
    }

    # Pattern to match tcolorbox sections with equations
    # This pattern matches the entire tcolorbox block from ::::: tcolorbox to :::::
    tcolorbox_pattern = r"::::: tcolorbox\s*\n(.*?)\n:::::"

    # Pattern to match promptbox sections
    # This pattern matches the entire promptbox block from ::: promptbox to :::
    promptbox_pattern = r"::: promptbox\s*\n(.*?)\n:::"

    def replace_box_block(match, box_type="tcolorbox"):
        block_content = match.group(1)

        # Check for specific cases first - such as RL framework
        if box_type == "tcolorbox" and (
            "Reinforcement Learning Framework" in block_content
            or "rl_objective" in block_content
        ):
            # This is the RL framework box
            img_tag = f'<img src="{media_dir}/eq_images/rl_objective.png" width="100%" alt="Reinforcement Learning Framework" />'
            print(f"Replacing RL framework tcolorbox with rl_objective.png image")
            return img_tag

        # Extract the label from the block - try different patterns
        label = None

        # Pattern 1: []{#eq:label label="eq:label"} or []{#box:label label="box:label"}
        label_match = re.search(r'\[]\{#([^}]+)\s+label="([^"]+)"\}', block_content)
        if label_match:
            label = label_match.group(2)  # Use the label value

        # Pattern 2: label="eq:label" or label="box:label"
        if not label:
            label_match = re.search(r'label="([^"]+)"', block_content)
            if label_match:
                label = label_match.group(1)

        # Pattern 3: #eq:label or #box:label
        if not label:
            if box_type == "tcolorbox":
                label_match = re.search(r"#(eq:[^\s}]+)", block_content)
                if not label_match:
                    # Also check for \label{eq:label} inside equation environments
                    equation_label_match = re.search(
                        r"\\begin\{equation\}.*?\\label\{(eq:[^\}]+)\}",
                        block_content,
                        re.DOTALL,
                    )
                    if equation_label_match:
                        label = equation_label_match.group(1)
            else:  # promptbox
                label_match = re.search(r"#(box:[^\s}]+)", block_content)
            if label_match:
                label = label_match.group(1)

        # Pattern 4: \label{eq:label} or \label{box:label}
        if not label:
            # We need to check for all \label commands, as the main block might have a different label
            # than the equation or content inside it
            label_matches = re.findall(r"\\label\{([^}]+)\}", block_content)
            if label_matches:
                # Check if any of the labels have our target patterns
                for potential_label in label_matches:
                    if "eq:" in potential_label or "box:" in potential_label:
                        # Prioritize equation or box labels over others
                        label = potential_label
                        break

                # If no specialized label found, use the first one
                if not label and label_matches:
                    label = label_matches[0]

        if not label:
            # If no label found, try to identify which content type it is
            if box_type == "tcolorbox":
                if "nexttoken" in block_content.lower():
                    label = "eq:nexttoken"
                elif "infonce" in block_content.lower():
                    label = "eq:infonce"
                elif (
                    "rl_objective" in block_content.lower()
                    or "rl objective" in block_content.lower()
                    or "eq:rl_objective" in block_content.lower()
                ):
                    label = "eq:rl_objective"
                elif (
                    "cot_prompting" in block_content.lower()
                    or "cot prompting" in block_content.lower()
                ):
                    label = "eq:cot_prompting"
            else:  # promptbox
                if (
                    "cot_prompting" in block_content.lower()
                    or "cot prompting" in block_content.lower()
                ):
                    label = "box: cot_prompting"

            if not label:
                # If still no match, print the content for debugging and return original block
                print(
                    f"Warning: No label found in {box_type} block and couldn't infer type"
                )
                print(
                    f"Block content preview: {block_content[:200]}..."
                )  # Print first 200 chars for debugging
                return match.group(0)

        # Remove prefix if it exists to check the mapping
        clean_label = label
        if label.startswith("eq:"):
            clean_label = label.replace("eq:", "")
        elif label.startswith("box:"):
            clean_label = label.replace("box:", "")
        elif label.startswith("box: "):
            clean_label = label.replace("box: ", "")

        # First try with the full label
        image_filename = None
        if label in image_mappings:
            image_filename = image_mappings[label]
        # Then try with the clean label (without prefix)
        elif clean_label in image_mappings:
            image_filename = image_mappings[clean_label]

        if image_filename:
            # Create HTML img tag with width="100%"
            img_tag = f'<img src="{media_dir}/eq_images/{image_filename}" width="100%" alt="{box_type.capitalize()}: {label}" />'

            # Extract any descriptive text that comes after the equation or prompt
            description = ""

            if box_type == "tcolorbox":
                # For equations, extract text after the math block
                math_end_pattern = (
                    r"(\$\$.*?\$\$|\\\[.*?\\\]|\\begin\{equation\}.*?\\end\{equation\})"
                )
                math_match = re.search(math_end_pattern, block_content, re.DOTALL)

                if math_match:
                    # Get everything after the math block
                    after_math = block_content[math_match.end() :].strip()

                    # Remove any closing LaTeX environments
                    after_math = re.sub(r":::\s*::::", "", after_math)
                    after_math = re.sub(r":::", "", after_math)
                    after_math = after_math.strip()

                    if after_math and not after_math.startswith(":::"):
                        description = f"\n\n{after_math}"

            print(f"Replacing {box_type} {label} with image {image_filename}")
            return f"{img_tag}{description}"
        else:
            # If no corresponding image, return original block but warn
            print(
                f"Warning: No image mapping found for label '{label}'. Available mappings: {list(image_mappings.keys())}"
            )
            return match.group(0)

    # Apply the replacement for tcolorbox equations
    original_content = content
    replace_tcolorbox = lambda match: replace_box_block(match, "tcolorbox")
    content = re.sub(tcolorbox_pattern, replace_tcolorbox, content, flags=re.DOTALL)

    # Apply the replacement for promptbox blocks
    replace_promptbox = lambda match: replace_box_block(match, "promptbox")
    content = re.sub(promptbox_pattern, replace_promptbox, content, flags=re.DOTALL)

    # Check if any replacements were made
    if content != original_content:
        print(f"Replaced boxes with images in {file_path}")

    # Write the updated content back to the file
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"Processed box replacements in {file_path}")


def copy_equation_images_to_media(eq_images_source, output_media_dir):
    """
    Copy equation images from source directory to the media directory.

    Args:
        eq_images_source: Source directory containing equation images
        output_media_dir: Output media directory
    """
    eq_images_source = Path(eq_images_source)
    output_media_dir = Path(output_media_dir)

    if not eq_images_source.exists():
        print(
            f"Warning: Equation images source directory {eq_images_source} does not exist"
        )
        return

    # Create eq_images subdirectory in media
    eq_images_dest = output_media_dir / "eq_images"
    eq_images_dest.mkdir(parents=True, exist_ok=True)

    # Copy all PNG files from source to destination
    png_files = list(eq_images_source.glob("*.png"))

    if not png_files:
        print(f"Warning: No PNG files found in {eq_images_source}")
        print(f"Looking for any image files instead...")
        png_files = (
            list(eq_images_source.glob("*.jpg"))
            + list(eq_images_source.glob("*.jpeg"))
            + list(eq_images_source.glob("*.gif"))
        )

    copied_count = 0
    for png_file in png_files:
        dest_file = eq_images_dest / png_file.name
        shutil.copy2(png_file, dest_file)
        copied_count += 1
        print(f"Copied equation image: {png_file.name}")

    print(f"Copied {copied_count} equation images to {eq_images_dest}")

    # Verify the expected equation images exist
    expected_images = [
        "nexttoken.png",
        "infonce.png",
        "rl_objective.png",
        "cot_prompting.png",
    ]
    missing_images = []

    for img in expected_images:
        if not (eq_images_dest / img).exists():
            missing_images.append(img)

    if missing_images:
        print(
            f"Warning: The following expected equation images are missing: {missing_images}"
        )
        print(f"Make sure these images exist in {eq_images_source}")
    else:
        print(f"All expected equation images were successfully copied.")


def enforce_image_width_100_percent(file_path):
    """
    Comprehensive function to ensure all images in a markdown file have width="100%".
    This function handles various image formats and ensures consistent width settings.

    Args:
        file_path: Path to the markdown file to update
    """
    if not file_path.exists():
        print(f"Warning: File {file_path} does not exist")
        return

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Convert any remaining markdown images to HTML with width="100%"
    def convert_remaining_markdown_images(match):
        alt_text = match.group(1)
        image_src = match.group(2)
        return f'<img src="{image_src}" alt="{alt_text}" width="100%" />'

    # Convert all remaining markdown images to HTML
    content = re.sub(
        r"!\[([^\]]*)\]\(([^)]+)\)", convert_remaining_markdown_images, content
    )

    # Ensure all HTML img tags have width="100%" and fix any missing width attributes
    def ensure_width_attribute(match):
        img_tag = match.group(1)
        closing = match.group(2)

        # Check if width attribute already exists
        if "width=" in img_tag:
            # Update existing width to 100%
            img_tag = re.sub(r'width="[^"]*"', 'width="100%"', img_tag)
            img_tag = re.sub(r"width='[^']*'", 'width="100%"', img_tag)
        else:
            # Add width attribute
            img_tag = img_tag + ' width="100%"'

        return img_tag + closing

    content = re.sub(r"(<img[^>]*)(>)", ensure_width_attribute, content)

    # Handle any figure environments that might contain images
    def process_figure_images(match):
        figure_content = match.group(1)
        # Apply width="100%" to any img tags within figures
        figure_content = re.sub(
            r"(<img[^>]*)(>)", ensure_width_attribute, figure_content
        )
        return f"<figure>{figure_content}</figure>"

    content = re.sub(
        r"<figure>(.*?)</figure>", process_figure_images, content, flags=re.DOTALL
    )

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)


def convert_latex_acronyms_to_glossary_shortcodes(content):
    """
    Convert various acronym formats to acronym shortcodes in the format {{{< acr acronym_key >}}}.
    Handles:
    1. LaTeX acronyms: [text]{acronym-label="label" acronym-form="form"}
    2. HTML spans: <span data-acronym-label="label" data-acronym-form="form">text</span>
    3. Simple LaTeX format: [text]{acronym-label="label"}
    4. Special cases with backticks and hyphens
    5. Plural forms by adding "s" after the command when needed
    """
    import re

    def replace_acronym(match, pattern_type):
        if pattern_type == 'latex':
            displayed_text = match.group(1)
            label = match.group(2)
            # Remove any form specifier from the label
            label = label.split('+')[0] if '+' in label else label

            # Detect and preserve backticks around the displayed text
            backtick_prefix = ''
            backtick_suffix = ''
            if displayed_text.startswith('`') and displayed_text.endswith('`'):
                backtick_prefix = '`'
                backtick_suffix = '`'
                displayed_text = displayed_text[1:-1]
            elif displayed_text.startswith('`'):
                backtick_prefix = '`'
                displayed_text = displayed_text[1:]
            elif displayed_text.endswith('`'):
                backtick_suffix = '`'
                displayed_text = displayed_text[:-1]
                
            # Check if the displayed text is plural form of the label
            is_plural = False
            if displayed_text.lower().endswith('s') and not label.lower().endswith('s'):
                # Check if the text without the 's' matches the label
                stripped_text = displayed_text[:-1]
                if stripped_text.lower() == label.lower():
                    is_plural = True

            # Handle hyphenated compound words like "ai-Scientist"
            # Only replace the part before the hyphen if it matches the label
            if '-' in displayed_text and displayed_text.lower().startswith(label.lower()):
                pre_hyphen, post_hyphen = displayed_text.split('-', 1)
                plural_suffix = 's' if is_plural else ''
                # Only replace the pre_hyphen part
                if pre_hyphen.lower() != label.lower():
                    acr_cmd = "\\acr[" + pre_hyphen + "]{" + label + "}"
                else:
                    acr_cmd = "\\acr{" + label + "}"
                return backtick_prefix + acr_cmd + plural_suffix + backtick_suffix + "-" + post_hyphen
            # For multi-word terms or terms that don't match their labels exactly (excluding plural case)
            elif ' ' in displayed_text or (displayed_text.lower() != label.lower() and not is_plural):
                acr_cmd = "\\acr[" + displayed_text + "]{" + label + "}"
                return backtick_prefix + acr_cmd + backtick_suffix
            else:
                # For single-word terms where display matches label (or is plural form)
                plural_suffix = 's' if is_plural else ''
                acr_cmd = "\\acr{" + label + "}"
                return backtick_prefix + acr_cmd + plural_suffix + backtick_suffix
        elif pattern_type == 'span':
            label = match.group(1)
            displayed_text = match.group(2)
            label = label.split('+')[0] if '+' in label else label
            
            # Check for plural form
            is_plural = False
            if displayed_text.lower().endswith('s') and not label.lower().endswith('s'):
                stripped_text = displayed_text[:-1]
                if stripped_text.lower() == label.lower():
                    is_plural = True
                    
            if displayed_text.lower() != label.lower() and not is_plural:
                return "\\acr[" + displayed_text + "]{" + label + "}"
            else:
                plural_suffix = 's' if is_plural else ''
                return "\\acr{" + label + "}" + plural_suffix

    # Pattern 1: LaTeX acronym format [text]{acronym-label="label" acronym-form="..."}
    # Only match if the [text] is not immediately followed by a citation (e.g. [@foo])
    pattern_latex = r'(?<!\\)\[(.+?)\]\{acronym-label="(.*?)"[^}]*\}'
    content = re.sub(pattern_latex, lambda m: replace_acronym(m, 'latex'), content)

    # Pattern 2: HTML span format <span data-acronym-label="label" data-acronym-form="...">text</span>
    pattern_span = r'<span data-acronym-label="(.*?)"[^>]*>(.*?)</span>'
    content = re.sub(pattern_span, lambda m: replace_acronym(m, 'span'), content)

    # Pattern 3: Simple LaTeX format [text]{acronym-label="label"}
    pattern_simple = r'(?<!\\)\[(.+?)\]\{acronym-label="(.*?)"\}'
    content = re.sub(pattern_simple, lambda m: replace_acronym(m, 'latex'), content)

    return content

def copy_extensions_dir(src_dir, dest_dir):
    """
    Copy the _extensions directory (with all subfolders and files) to the output directory.
    """
    src_path = Path(src_dir)
    dest_path = Path(dest_dir)
    if not src_path.exists():
        print(f"Warning: Extensions source directory {src_path} does not exist")
        return
    if dest_path.exists():
        shutil.rmtree(dest_path)
    shutil.copytree(src_path, dest_path)
    print(f"Copied extensions from {src_path} to {dest_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Convert LaTeX document to Quarto book"
    )
    parser.add_argument(
        "--input-dir", default=".", help="Input directory containing LaTeX files"
    )
    parser.add_argument(
        "--output-dir",
        default="../quarto_book",
        help="Output directory for Quarto book",
    )
    parser.add_argument(
        "--media-dir", default="media", help="Directory name for extracted media"
    )
    parser.add_argument(
        "--zip-file",
        default="general_purpose_models_chemrev.zip",
        help="Zip file containing LaTeX source (will be extracted if provided)",
    )
    parser.add_argument(
        "--extract-to",
        default="extracted_latex",
        help="Directory to extract zip file to",
    )

    args = parser.parse_args()

    # Handle zip file extraction if provided
    if args.zip_file and Path(args.zip_file).exists():
        extract_dir = Path(args.extract_to)
        if extract_zip_file(args.zip_file, extract_dir):
            # Update input directory to the extracted content
            # Look for the main LaTeX files in the extracted directory
            potential_dirs = [
                extract_dir,
                extract_dir / "latex_source",
                extract_dir / "src",
                extract_dir / "main",
            ]

            for potential_dir in potential_dirs:
                if potential_dir.exists() and (potential_dir / "main.tex").exists():
                    args.input_dir = str(potential_dir)
                    print(f"Using extracted directory: {args.input_dir}")
                    break
            else:
                # If no main.tex found in obvious places, use the extract directory
                args.input_dir = str(extract_dir)
                print(f"Using extracted directory: {args.input_dir}")
        else:
            print(
                f"Failed to extract {args.zip_file}, using input directory: {args.input_dir}"
            )
    elif args.zip_file:
        print(
            f"Zip file {args.zip_file} not found, using input directory: {args.input_dir}"
        )

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    media_dir = args.media_dir

    # Create output directory
    output_dir.mkdir(exist_ok=True)

    # Copy and clean bibliography file early (needed for citations)
    bib_file = input_dir / "references.bib"
    if bib_file.exists():
        # Read, clean, and write the bibliography file
        with open(bib_file, "r", encoding="utf-8") as f:
            bib_content = f.read()

        cleaned_bib_content = clean_bibliography_content(bib_content)

        with open(output_dir / "references.bib", "w", encoding="utf-8") as f:
            f.write(cleaned_bib_content)

        print(f"Copied and cleaned bibliography to {output_dir / 'references.bib'}")
    else:
        print("Warning: No references.bib file found")

    # Split the applications.tex file into two parts
    sections_dir = input_dir / "sections"
    if sections_dir.exists():
        applications_file = sections_dir / "applications.tex"
        if applications_file.exists():
            # Create temporary directory for split files
            temp_dir = output_dir / "temp_sections"
            temp_dir.mkdir(exist_ok=True)

            # Split the applications file
            split_applications_file(applications_file, temp_dir)

            print("Successfully split applications.tex into two parts")
        else:
            print("Warning: applications.tex not found")

    # Section mapping (order matters for the book)
    sections = [
        ("introduction.tex", "01-introduction.qmd"),
        ("data_taxonomy.tex", "02-data_taxonomy.qmd"),
        ("architectures.tex", "03-architectures.qmd"),
        ("evals.tex", "04-evals.qmd"),
        ("applications_part1.tex", "05-applications.qmd"),
        ("applications_part2.tex", "06-accelerating_applications.qmd"),
        ("safety.tex", "07-safety.qmd"),
        ("outlook_conclusions.tex", "08-outlook_conclusions.qmd"),
    ]

    # Create media directory in output
    media_output_dir = output_dir / media_dir

    # Convert each section
    sections_dir = input_dir / "sections"
    temp_sections_dir = output_dir / "temp_sections"

    if sections_dir.exists():
        for section_file, output_file in sections:
            # Check if this is a split file (look in temp directory first)
            if (
                section_file.startswith("applications_part")
                and temp_sections_dir.exists()
            ):
                section_path = temp_sections_dir / section_file
                # For split files, use the original input_dir as base_dir for resolving \input{} commands
                base_dir = input_dir
            else:
                section_path = sections_dir / section_file
                base_dir = None  # Will use default (section_path.parent.parent)

            output_path = output_dir / output_file

            if section_path.exists():
                convert_section_to_markdown(
                    section_path, output_path, media_output_dir, base_dir
                )
            else:
                print(f"Warning: Section file {section_path} not found")

    # Create index page
    main_tex_path = input_dir / "main.tex"
    index_path = output_dir / "index.qmd"
    if main_tex_path.exists():
        create_index_page(main_tex_path, index_path, media_output_dir)

    # Create references page
    references_path = output_dir / "09-references.qmd"
    references_content = create_section_frontmatter() + """
# References {.unnumbered}

::: {#refs}
:::"""

    with open(references_path, "w", encoding="utf-8") as f:
        f.write(references_content)
    print(f"Created references page at {references_path}")

    # Copy media directory if it exists
    media_source = input_dir / "media"
    if media_source.exists():
        if media_output_dir.exists():
            shutil.rmtree(media_output_dir)
        shutil.copytree(media_source, media_output_dir)
        print(f"Copied media directory to {media_output_dir}")

    # Copy figures directory if it exists
    figures_source = input_dir / "figures"
    if figures_source.exists():
        figures_output = media_output_dir / "figures"
        if figures_output.exists():
            shutil.rmtree(figures_output)
        shutil.copytree(figures_source, figures_output)
        print(f"Copied figures directory to {figures_output}")

    # Convert PDF images to PNG for web display
    convert_pdf_images_to_png(media_output_dir)

    # Copy equation images to media directory
    # First try relative to input_dir.parent, then relative to workspace root
    eq_images_source = input_dir.parent / "docs" / "eq_images"
    eq_images_found = eq_images_source.exists()

    if not eq_images_found:
        # Try from workspace root (go up until we find docs directory)
        current_path = input_dir
        while current_path.parent != current_path:  # Stop at filesystem root
            potential_docs = current_path / "docs" / "eq_images"
            if potential_docs.exists():
                eq_images_source = potential_docs
                eq_images_found = True
                break
            current_path = current_path.parent

    # Try looking for the directory directly in the project root
    if not eq_images_found:
        project_root = Path(__file__).parent.parent
        potential_docs = project_root / "docs" / "eq_images"
        if potential_docs.exists():
            eq_images_source = potential_docs
            eq_images_found = True

    # Try explicit path as a last resort
    if not eq_images_found:
        # Try an absolute path as a last resort
        absolute_docs = Path("/Users/martino/Nueva_Carpeta/GPMs-book/docs/eq_images")
        if absolute_docs.exists():
            eq_images_source = absolute_docs
            eq_images_found = True

    if eq_images_found:
        print(f"Found equation images directory: {eq_images_source}")
        copy_equation_images_to_media(eq_images_source, media_output_dir)
    else:
        print(
            f"WARNING: Could not find equation images directory. Please ensure it exists at 'docs/eq_images' relative to the project root."
        )
        print(f"Searched locations: ")
        print(f"  - {input_dir.parent / 'docs' / 'eq_images'}")
        print(f"  - Various parent directories containing 'docs/eq_images'")
        print(f"  - {Path(__file__).parent.parent / 'docs' / 'eq_images'}")

    # Update image references in all markdown files
    for qmd_file in output_dir.glob("*.qmd"):
        update_image_references_in_markdown(qmd_file, media_dir)

    # Final cleanup: fix any remaining citation formatting issues in all markdown files
    print("Performing final citation cleanup...")
    for qmd_file in output_dir.glob("*.qmd"):
        with open(qmd_file, "r", encoding="utf-8") as f:
            content = f.read()

        cleaned_content = clean_citation_formatting_in_markdown(content)

        with open(qmd_file, "w", encoding="utf-8") as f:
            f.write(cleaned_content)

    # Final heading level fix: ensure all markdown files have proper heading levels
    print("Performing final heading level fix...")
    for qmd_file in output_dir.glob("*.qmd"):
        with open(qmd_file, "r", encoding="utf-8") as f:
            content = f.read()

        fixed_content = fix_heading_levels(content)

        with open(qmd_file, "w", encoding="utf-8") as f:
            f.write(fixed_content)

    # Replace tcolorbox equations and promptbox blocks with images
    print("Replacing boxes with images...")
    for qmd_file in output_dir.glob("*.qmd"):
        replace_boxes_with_images(qmd_file, eq_images_source, media_dir)

    # Final image width enforcement: ensure all images have width="100%"
    print("Enforcing 100% width on all images...")
    for qmd_file in output_dir.glob("*.qmd"):
        enforce_image_width_100_percent(qmd_file)

    # Copy _extensions directory to output directory
    extensions_source = Path(__file__).parent / "_extensions"
    if extensions_source.exists():
        extensions_output = output_dir / "_extensions"
        copy_extensions_dir(extensions_source, extensions_output)
        print(f"Copied _extensions directory to {extensions_output}")
    else:
        print(f"Warning: _extensions directory not found at {extensions_source}")


    # Create Quarto configuration
    create_quarto_config(output_dir)

    # Convert acronyms from LaTeX to YAML format
    acronyms_tex_path = input_dir / 'acronyms.tex'
    if acronyms_tex_path.exists():
        acronyms_yml_path = output_dir / 'acronyms.yml'
        convert_acronyms_to_yaml(acronyms_tex_path, acronyms_yml_path)
        print(f"Converted LaTeX acronyms to YAML format at {acronyms_yml_path}")
    else:
        print("Warning: acronyms.tex file not found")

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

    with open(output_dir / "styles.css", "w", encoding="utf-8") as f:
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
    print(
        f"1. Ensure you have either 'pdftoppm' (from poppler-utils) or 'convert' (from ImageMagick) installed"
       )
    print(f"2. On macOS: brew install poppler or brew install imagemagick")
    print(
        f"3. On Ubuntu/Debian: sudo apt-get install poppler-utils or sudo apt-get install imagemagick"
    )
    print(
        f"4. PDF images have been automatically converted to PNG format for web display"
    )
    print(f"5. All images have been set to width='100%' for consistent display")


if __name__ == "__main__":
    main()
