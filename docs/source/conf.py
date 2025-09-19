# -- Path setup --------------------------------------------------------------

import os
import sys

sys.path.insert(0, os.path.abspath("../.."))


# -- Project information -----------------------------------------------------

project = "pronotepy"
copyright = "2022, bain, Xiloe"
author = "bain, Xiloe"


# -- General configuration ---------------------------------------------------

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.intersphinx",
]

master_doc = "index"

html_theme = "furo"

# -- API Doc ------------------------------------------------------------------

intersphinx_mapping = {"python": ("https://docs.python.org/3", None)}

autodoc_member_order = "groupwise"
autodoc_default_options = {
    'members': True,
    'exclude-members': '__init__, __new__',
}
autodoc_class_signature = "separated"
