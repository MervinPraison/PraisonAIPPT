"""
Setup file for PraisonAI PPT package.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the contents of README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8')

setup(
    name="praisonaippt",
    version="1.2.0",
    author="MervinPraison",
    description="PraisonAI PPT - Create beautiful PowerPoint presentations from Bible verses in JSON format",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/MervinPraison/PraisonAIPPT",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Religion",
        "Topic :: Office/Business :: Office Suites",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.7",
    install_requires=[
        "python-pptx>=0.6.21",
        "PyYAML>=6.0",
    ],
    extras_require={
        'pdf-aspose': ['aspose.slides>=24.0.0'],
        'pdf-all': ['aspose.slides>=24.0.0', 'psutil>=5.9.0', 'tqdm>=4.64.0'],
    },
    entry_points={
        "console_scripts": [
            "praisonaippt=praisonaippt.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["examples/*.json"],
    },
    keywords="powerpoint pptx bible verses presentation generator praisonai",
    project_urls={
        "Bug Reports": "https://github.com/MervinPraison/PraisonAIPPT/issues",
        "Source": "https://github.com/MervinPraison/PraisonAIPPT",
    },
)
