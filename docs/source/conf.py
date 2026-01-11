# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import sys
from pathlib import Path

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'qt-node-editor'
copyright = '2026, Andrey Makarov'  # noqa: A001
author = 'Andrey Makarov'
release = '0.1.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",  # https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html
    # "sphinx.ext.todo",
    # "sphinx.ext.coverage",  # does not report if undocumented members are included
                            # with :undoc-members: directive in apidoc output
    "myst_parser",  # requires myst-parser package for Markdown support
    # "sphinx_autodoc_typehints",  # https://github.com/tox-dev/sphinx-autodoc-typehints
]

project_root = Path(__file__).parents[2]
sys.path.insert(0, str(project_root / "src"))  # package dir for autodoc
sys.path.insert(0, str(project_root / ".venv/Lib/site-packages"))  # deps
autodoc_member_order = "bysource"
autoclass_content = "both"  # Combine class and __init__ docstrings (default: class)
coverage_show_missing_items = True

templates_path = ['_templates']
exclude_patterns = []


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'  # alabaster, ...
html_static_path = ['_static']
