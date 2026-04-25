from setuptools import find_namespace_packages, setup


def parse_requirements(filename):
    """Load requirements from a pip requirements file."""
    with open(filename, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip() and not line.startswith("#")]


with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="documentdb-functional-tests",
    version="0.1.0",
    author="DocumentDB Contributors",
    description="End-to-end functional testing framework for DocumentDB",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/documentdb/functional-tests",
    packages=find_namespace_packages(exclude=["docs", "docs.*"]),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.9",
    install_requires=parse_requirements("requirements.txt"),
    entry_points={
        "console_scripts": [
            "docdb-analyze=documentdb_tests.compatibility.result_analyzer.cli:main",
        ],
    },
)
