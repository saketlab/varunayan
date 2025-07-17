import os
import sys
from typing import List, Dict

sys.path.insert(0, os.path.abspath(".."))

project = "Varunayan"
copyright = "2025, Atharva Jagtap and Saket Choudhary"
author = "Atharva Jagtap and Saket Choudhary"
release = "0.1.0"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.viewcode",
    "sphinx.ext.napoleon",
    "sphinx.ext.intersphinx",
    "myst_nb",
    "autoapi.extension",
    "sphinx_copybutton",
    "sphinx_design",
    "sphinx_togglebutton",
    "sphinx_tabs.tabs",
]

# AutoAPI configuration
autoapi_dirs = ["../varunayan"]
autoapi_type = "python"
autoapi_generate_api_docs = True

# Napoleon settings
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = False
napoleon_include_private_with_doc = False

# Intersphinx mapping
intersphinx_mapping = {
    "python": ("https://docs.python.org/3/", None),
    "numpy": ("https://numpy.org/doc/stable/", None),
    "pandas": ("https://pandas.pydata.org/docs/", None),
    "xarray": ("https://xarray.pydata.org/en/stable/", None),
}

# MyST configuration
myst_enable_extensions = [
    "amsmath",
    "colon_fence",
    "deflist",
    "dollarmath",
    "fieldlist",
    "html_admonition",
    "html_image",
    "linkify",
    "replacements",
    "smartquotes",
    "strikethrough",
    "substitution",
    "tasklist",
]

# MyST-NB configuration
nb_execution_mode = "off"
nb_execution_timeout = 60
nb_execution_excludepatterns: List[str] = []
nb_kernel_rgx_aliases: Dict[str, str] = {}
nb_output_stderr = "show"
nb_render_priority = {
    "html": [
        "application/vnd.jupyter.widget-view+json",
        "application/javascript",
        "text/html",
        "image/svg+xml",
        "image/png",
        "image/jpeg",
        "text/markdown",
        "text/latex",
        "text/plain",
    ]
}

import shutil
import os

# Notebook source directory
nb_source_dir = "../notebooks"
# Copy notebooks to docs directory for processing

if os.path.exists("../notebooks"):
    # Copy notebooks to tutorials directory
    notebook_files = [
        "Demo.ipynb",
        "India_temp_change.ipynb",
    ]
    for nb in notebook_files:
        src = f"../notebooks/{nb}"
        dst = f"tutorials/{nb}"
        if os.path.exists(src):
            shutil.copy2(src, dst)

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store", "*.rst.bak"]

# Source file extensions
source_suffix = {
    ".rst": None,
    ".md": None,
    ".ipynb": None,
}

# Master document
master_doc = "index"

# Theme configuration
html_theme = "sphinx_book_theme"
html_static_path = ["_static"]
html_title = f"{project} {release}"
html_short_title = project

# Sphinx Book Theme configuration
html_theme_options = {
    "repository_url": "https://github.com/saketlab/varunayan",
    "repository_branch": "main",
    "path_to_docs": "docs",
    "use_repository_button": True,
    "use_edit_page_button": True,
    "use_issues_button": True,
    "use_download_button": True,
    "use_sidenotes": True,
    "show_toc_level": 2,
    "navigation_with_keys": True,
    "home_page_in_toc": True,
    "extra_footer": "<p>Built by the Varunayan team</p>",
    "analytics": {
        "google_analytics_id": "",  # Add your GA ID here if needed
    },
    "search_bar_text": "Search the documentation...",
    "logo": {
        "image_light": "_static/varunayan_logo.png",
        "image_dark": "_static/varunayan_logo.png",
    },
    "theme_switcher_button": False,  # Disable theme switcher
    "show_navbar_depth": 1,
}

# Copy button configuration
copybutton_prompt_text = r">>> |\.\.\. |\$ |In \[\d*\]: | {2,5}\.\.\.: | {5,8}: "
copybutton_prompt_is_regexp = True
copybutton_line_continuation_character = "\\"

# Search configuration
html_search_language = "en"
html_search_options = {
    "type": "default",
    "scorer": "query_terms",
    "word_boundaries": True,
}

# Additional HTML options
html_favicon = "_static/favicon.ico"
html_logo = "_static/varunayan_logo.png"
html_css_files = [
    "custom.css",
]

html_js_files = [
    "custom.js",
]

# Social cards (for sharing)
html_baseurl = "https://saketlab.github.io/varunayan/"
html_context = {
    "display_github": True,
    "github_user": "saketlab",
    "github_repo": "varunayan",
    "github_version": "main",
    "conf_py_path": "/docs/",
}
