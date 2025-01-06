import os
import sys
sys.path.insert(0, os.path.abspath('../'))
sys.path.insert(0, os.path.abspath('../spike'))

autodoc_preserve_defaults = True

project = 'spike'
copyright = '2024, Ava Polzin'
author = 'Ava Polzin'
root_doc = 'index'

release = '0.5'

extensions = [
	'sphinx_rtd_theme',
	'sphinx.ext.autodoc',
	'sphinx.ext.napoleon'
]

templates_path = ['_templates']
exclude_patterns = ['_build', '.DS_STORE']

html_theme = 'sphinx_rtd_theme'

html_static_path = []