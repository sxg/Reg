"""
CLI for 4D image registration of .mat files using the FMRIB Software Library (FSL)
"""

from setuptools import setup

setup(
    name="reg",
    version="0.1.0",
    py_modules=["reg"],
    install_requires=[
        "Click",
        "numpy",
        "scipy",
        "hdf5storage",
        "nibabel"
    ],
    entry_points="""
        [console_scripts]
        reg=reg:cli
    """,
)
