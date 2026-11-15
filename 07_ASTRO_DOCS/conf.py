# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'ASTROVITAL AI : VITALX CORE (RECREATED V1)'
copyright = '2026, Team VITALX CORE (NASA Space Apps Challenge 2026)'
author = 'Gourgopal Mohapatra (Team VITALX CORE)'
release = '1.0.0-TRL7-OPERATIONAL'
version = '1.0.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.mathjax',
    'sphinx.ext.viewcode',
    'sphinx.ext.napoleon',
    'sphinx.ext.todo',
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']
master_doc = '00_MASTER_ASTRO_DOCS_INDEX'

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'alabaster'
html_static_path = ['_static']

html_theme_options = {
    'description': 'Autonomous Bio-Astronautic Clinical Decision Support Architecture (RTCA DO-178C DAL C)',
    'github_user': 'GOURGOPAL618',
    'github_repo': 'ASTROVITAL_AI_VITALX_CORE_RECREATED',
    'page_width': '1200px',
    'sidebar_width': '300px',
}
