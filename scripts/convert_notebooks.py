#!/usr/bin/env python3
import os
import sys
import subprocess
import json
from pathlib import Path
from typing import List, Dict, Tuple


def find_notebooks(notebooks_dir: str = "notebooks") -> List[Path]:
    notebooks_path = Path(notebooks_dir)
    if not notebooks_path.exists():
        print(f"Warning: {notebooks_dir} directory not found")
        return []
    
    notebook_files = list(notebooks_path.glob("*.ipynb"))
    print(f"Found {len(notebook_files)} notebook(s): {[nb.name for nb in notebook_files]}")
    return notebook_files


def get_notebook_title(notebook_path: Path) -> str:
    try:
        with open(notebook_path, 'r', encoding='utf-8') as f:
            notebook_data = json.load(f)
        
        metadata = notebook_data.get('metadata', {})
        title = metadata.get('title', '')
        
        if not title:
            cells = notebook_data.get('cells', [])
            for cell in cells:
                if cell.get('cell_type') == 'markdown':
                    source = ''.join(cell.get('source', []))
                    lines = source.strip().split('\n')
                    for line in lines:
                        if line.startswith('# '):
                            title = line[2:].strip()
                            break
                    if title:
                        break
        
        if not title:
            title = notebook_path.stem.replace('_', ' ').replace('-', ' ').title()
        
        return title
    except Exception as e:
        print(f"Warning: Could not extract title from {notebook_path}: {e}")
        return notebook_path.stem.replace('_', ' ').replace('-', ' ').title()


def convert_notebook(notebook_path: Path, output_dir: str = "docs/tutorials") -> Tuple[bool, str]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    output_name = notebook_path.stem.lower().replace(' ', '_').replace('-', '_')
    
    try:
        cmd = [
            'jupyter', 'nbconvert',
            '--to', 'markdown',
            str(notebook_path),
            '--output-dir', str(output_path),
            '--output', output_name
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        markdown_file = output_path / f"{output_name}.md"
        
        print(f"Converted {notebook_path.name} -> {markdown_file}")
        return True, str(markdown_file)
        
    except subprocess.CalledProcessError as e:
        print(f"Failed to convert {notebook_path.name}: {e.stderr}")
        return False, ""
    except Exception as e:
        print(f"Error converting {notebook_path.name}: {e}")
        return False, ""


def update_tutorials_index(converted_notebooks: List[Tuple[str, str]], notebook_files: List[Path], output_dir: str = "docs/tutorials"):
    index_path = Path(output_dir) / "index.md"
    
    content = """# Tutorials

These vignettes demonstrate usage of Varunayan for different use cases.

## Available Tutorials

```{toctree}
:maxdepth: 1
:hidden:

"""
    
    converted_notebooks_sorted = sorted(converted_notebooks, key=lambda x: Path(x[1]).stem)
    
    toctree_entries = []
    for title, markdown_file in converted_notebooks_sorted:
        rel_path = Path(markdown_file).stem
        toctree_entries.append(rel_path)
    
    markdown_stems = {Path(md_file).stem for _, md_file in converted_notebooks}
    notebook_entries = []
    for notebook_path in sorted(notebook_files, key=lambda x: x.stem):
        notebook_stem = notebook_path.stem.lower().replace(' ', '_').replace('-', '_')
        if notebook_stem not in markdown_stems:
            notebook_entries.append(notebook_path.name)
    
    for entry in toctree_entries + notebook_entries:
        content += f"{entry}\n"
    
    content += "```\n\n"
    
    for title, markdown_file in converted_notebooks_sorted:
        rel_path = Path(markdown_file).name
        content += f"- [{title}]({rel_path})\n"
    
    
    try:
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated tutorials index: {index_path}")
    except Exception as e:
        print(f"Warning: Could not update tutorials index: {e}")




def main():
    print("Starting automatic notebook conversion...")
    
    notebooks = find_notebooks()
    if not notebooks:
        print("No notebooks found to convert.")
        return
    
    converted_notebooks = []
    success_count = 0
    
    for notebook_path in notebooks:
        title = get_notebook_title(notebook_path)
        success, markdown_file = convert_notebook(notebook_path)
        
        if success:
            converted_notebooks.append((title, markdown_file))
            success_count += 1
    
    if converted_notebooks:
        update_tutorials_index(converted_notebooks, notebooks)
    
    print(f"Conversion complete! {success_count}/{len(notebooks)} notebooks converted successfully.")
    
    if success_count < len(notebooks):
        print("Some notebooks failed to convert. Check the error messages above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
