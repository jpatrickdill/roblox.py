# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys

sys.path.insert(0, os.path.abspath('../..'))

# -- Project information -----------------------------------------------------

project = 'roblox.py'
copyright = '2020, Patrick Dill'
author = 'Patrick Dill'

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.coverage",
    "sphinx.ext.napoleon",
    "sphinx_autodoc_typehints",
    "sphinxcontrib_trio",
    "sphinxcontrib_autodoc_filterparams"
]

autodoc_default_options = {
    "autodoc-member-order": "bysource",
    "member-order": "bysource"
}

always_document_param_types = True
typehints_document_rtype = False


def sphinxcontrib_autodoc_filterparams(fun, param):
    return param not in ("state", "data", "gen", "opts", "group")


# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.

html_theme = "sphinx_material"

html_theme_options = {
    "nav_title": "roblox.py",
    "color_primary": "red",
    "color_accent": "light-red",

    "repo_url": "https://github.com/jpatrickdill/roblox.py/",
    "repo_name": "roblox.py",
    "logo_icon": '',
    "master_doc": False,

    "nav_links": [
        {"href": "index", "internal": True, "title": "roblox.py"}
    ],

    "globaltoc_depth": 1
}

html_sidebars = {
    "**": ["logo-text.html", "localtoc.html", "globaltoc.html", "searchbox.html"]
}

html_experimental_html5_writer = True

html_logo = "_static/logos/icon.png"

rst_prolog = """
.. |coro| replace:: This function is a |coroutine_link|_.
.. |coroutine_link| replace:: coroutine
.. _coroutine_link: https://docs.python.org/3/library/asyncio-task.html#coroutine

.. |asyncgen| replace:: This function is an :ref:`async generator<asyncgen>`.
.. |asyncprop| replace:: This function is an :ref:`async property<asyncprop>`.
"""

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']
html_css_files = [
    "custom.css"
]
