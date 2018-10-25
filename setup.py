"""
CLI for 4D image registration of .mat files using the FMRIB Software Library (FSL)
"""

from setuptools import setup

setup(
    name="reg",
    version="0.1",
    py_modules=["reg"],
    install_requires=[
        "Click",
    ],
    entry_points="""
        [console_scripts]
        reg=reg:cli
    """,
)
