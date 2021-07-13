import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(name='pronotepy',
                 version='1.5.0',
                 description='A wrapper for the pronote "API"',
                 url='http://www.github.com/bain3/pronotepy',
                 author='bain',
                 license='MIT',
                 packages=setuptools.find_packages(),
                 zip_safe=False,
                 python_requires='>=3.6',
                 install_requires=['beautifulsoup4>=4.8.2',
                                   'pycryptodome>=3.9.4',
                                   'requests>=2.22.0',
                                   ],
                 classifiers=[
                     "Programming Language :: Python :: 3",
                     "License :: OSI Approved :: MIT License",
                     "Operating System :: OS Independent",
                 ])
