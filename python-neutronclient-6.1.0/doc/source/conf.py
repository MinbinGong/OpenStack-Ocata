# -*- coding: utf-8 -*-
#

project = 'python-neutronclient'

# -- General configuration ---------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom ones.
extensions = ['sphinx.ext.autodoc',
              'oslosphinx',
              'reno.sphinxext',
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# The suffix of source filenames.
source_suffix = '.rst'

# The main toctree document.
main_doc = 'index'

# General information about the project.
copyright = u'OpenStack Foundation'

# If true, '()' will be appended to :func: etc. cross-reference text.
add_function_parentheses = True

# If true, the current module name will be prepended to all description
# unit titles (such as .. function::).
add_module_names = True

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = 'sphinx'

# -- Options for HTML output ---------------------------------------------

# The theme to use for HTML and HTML Help pages.  Major themes that come with
# Sphinx are currently 'default' and 'sphinxdoc'.
# html_theme = 'nature'

# Output file base name for HTML help builder.
htmlhelp_basename = '%sdoc' % project


# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title, author,
#  documentclass [howto/manual]).
latex_documents = [
  ('index',
    '%s.tex' % project,
    u'%s Documentation' % project,
    u'OpenStack Foundation', 'manual'),
]
