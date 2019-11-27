import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="nwbindexer",
    version="0.1.0",
    author="Jeff Teeters",
    author_email="jteeters@berkeley.edu",
    description="Two tools for searching NWB files",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jeffteeters/nwbindexer",
    # packages=setuptools.find_packages(),
    packages = ["nwbindexer", "nwbindexer.lib", "nwbindexer.test"],
    entry_points={
        'console_scripts': [
            'search_nwb = nwbindexer.search_nwb:main',
            'build_index = nwbindexer.build_index:main',
            'query_index = nwbindexer.query_index:main',
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        # "License :: OSI Approved :: MIT License", # license is UC Berkeley license, see file license.txt
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
)

