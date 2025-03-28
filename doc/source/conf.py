# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'ricco'
copyright = '2024, wangyukang'
author = 'wangyukang'

release = '1.6.1'
# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
  'sphinx.ext.autodoc',
  'sphinx.ext.napoleon',
  'sphinx.ext.graphviz',
  # 'sphinxcontrib.redoc',
  'autodocsumm',
  'sphinx_copybutton',
  'sphinx.ext.intersphinx',
  'sphinx_rtd_theme',
]

templates_path = ['_templates']

language = 'zh_CN'

exclude_patterns = []

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']

autodoc_default_options = {
  'show-inheritance': True,
  'members': True,
  'undoc-members': True,
  'autosummary': True,
}
