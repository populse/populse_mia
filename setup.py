"""Building, distributing, and installing modules using the Distutils"""

import os

from setuptools import find_packages, setup

# Select modules to include in distribution
modules = find_packages()
print("\nmodules found: ", modules)

# Additional script files to include in distribution
scripts = []

# Data files to include in distribution
pkgdata = {
    # format is:
    # <python module>: <file extensions list>
    # e.g:
    "populse_mia.sources_images": ["*.png", "*.jpeg", "*.jpg"]
}

# Read the info.py file in populse_mia module
release_info = {}
root_dir = os.path.join(os.path.dirname(__file__))
with open(os.path.join(root_dir, "populse_mia", "info.py")) as f:
    code = f.read()
    exec(code, release_info)

# Build the setup
setup(
    name=release_info["NAME"],
    description=release_info["DESCRIPTION"],
    long_description=release_info["LONG_DESCRIPTION"],
    license=release_info["LICENSE"],
    classifiers=release_info["CLASSIFIERS"],
    author=release_info["AUTHOR"],
    author_email=release_info["AUTHOR_EMAIL"],
    version=release_info["VERSION"],
    url=release_info["URL"],
    packages=modules,
    package_data=pkgdata,
    platforms=release_info["PLATFORMS"],
    install_requires=release_info["REQUIRES"],
    extras_require=release_info["EXTRA_REQUIRES"],
    scripts=scripts,
)
