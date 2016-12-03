from setuptools import setup
from Cython.Build import cythonize
import numpy

setup(
    name='maze',
    ext_modules=cythonize(
        'maze.pyx',
        language_level=3,
        include_dirs=[numpy.get_include()],
        language="c++"
    ),
    include_dirs=[numpy.get_include()],
    install_requires=[
        'Cython',
        'NumPy',
    ],
)
