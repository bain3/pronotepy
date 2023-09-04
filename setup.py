import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pronotepy",
    version="2.12.0",
    description='A wrapper for the pronote "API"',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://www.github.com/bain3/pronotepy",
    author="bain",
    license="MIT",
    packages=setuptools.find_packages(),
    zip_safe=False,
    python_requires=">=3.7",
    install_requires=[
        "beautifulsoup4>=4.8.2",
        "pycryptodome>=3.9.4",
        "requests>=2.22.0",
        "autoslot>=2022.12.1",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    package_data={"pronotepy": ["py.typed"]},
)
