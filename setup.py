from setuptools import setup, find_packages
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="mljar-supervised",
    version="0.1.0",
    description="Automated Machine Learning for Humans",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jianzhnie/AutoTabular",
    author="MLJAR, Inc.",
    author_email="jianzhnie@gmail.com",
    license="MIT",
    packages=find_packages(exclude=["*.tests", "*.tests.*", "tests.*", "tests", "autobular"]),
    install_requires=open("requirements.txt").readlines(),
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
    keywords=[
        "automated machine learning",
        "automl",
        "machine learning",
        "data science",
        "data mining",
        "mljar"
    ],
)
