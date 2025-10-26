"""
Setup file for pptx-bible-verses package.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the contents of README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8')

setup(
    name="pptx-bible-verses",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="Create beautiful PowerPoint presentations from Bible verses in JSON format",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/MervinPraison/ppt-package",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Religion",
        "Topic :: Office/Business :: Office Suites",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.7",
    install_requires=[
        "python-pptx>=0.6.21",
    ],
    entry_points={
        "console_scripts": [
            "pptx-bible-verses=pptx_bible_verses.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["examples/*.json"],
    },
    keywords="powerpoint pptx bible verses presentation generator",
    project_urls={
        "Bug Reports": "https://github.com/MervinPraison/ppt-package/issues",
        "Source": "https://github.com/MervinPraison/ppt-package",
    },
)
