# Minimal makefile for Sphinx documentation
# make html → fast incremental build
# make freshhtml → force full re-read, good after __all__ changes
# make cleanhtml → nuclear option, start from scratch

# You can set these variables from the command line.
SPHINXOPTS    =
# SPHINXBUILD   = python -m sphinx.cmd.build
SPHINXBUILD   = python -m sphinx
SOURCEDIR     = source
BUILDDIR      = .

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: help freshhtml cleanhtml Makefile

# Full rebuild ignoring cached environment (keeps _autosummary and build files)
freshhtml:
	@$(SPHINXBUILD) -b html -E "$(SOURCEDIR)" "$(BUILDDIR)/html" $(SPHINXOPTS) $(O)

# Full clean rebuild: removes doctrees, html output and _autosummary stubs
cleanhtml:
	rm -rf "$(BUILDDIR)/html" "$(BUILDDIR)/doctrees" "$(SOURCEDIR)/_autosummary"
	@$(SPHINXBUILD) -M html "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
