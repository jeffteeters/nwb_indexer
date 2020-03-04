import setuptools

with open("README.rst", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="nwbindexer",
    version="0.1.2",
    author="Jeff Teeters",
    author_email="jeff@teeters.us",
    description="Two tools for searching NWB files",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jeffteeters/nwbindexer",
    # packages=setuptools.find_packages(),
    packages = ["nwbindexer", "nwbindexer.lib", "nwbindexer.test"],
    package_data={
        'nwbindexer.test': ['*.nwb'],
    },
    entry_points={
        'console_scripts': [
            'search_nwb = nwbindexer.search_nwb:main',
            'build_nwbindex = nwbindexer.build_index:main',
            'query_nwbindex = nwbindexer.query_index:main',
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        # "License :: OSI Approved :: MIT License", # license is UC Berkeley license, see file license.txt
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
    install_requires=["parsimonious>=0.8.1","h5py>=2.9","numpy"]
)

