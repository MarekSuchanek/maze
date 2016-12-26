import glob
from setuptools import setup, find_packages
from Cython.Build import cythonize
import numpy

with open('README.md') as f:
    long_description = ''.join(f.readlines())

setup(
    name='maze',
    version=0.4,
    keywords='maze analysis matrix cython',
    description='Simple python maze analyzer for finding shortest path',
    long_description=long_description,
    author='Marek Suchánek',
    author_email='suchama4@fit.cvut.cz',
    license='MIT',
    packages=find_packages(),
    package_data={
        'maze': [
            'static/*.cfg',
            'static/*.json',
            'static/ui/*.ui',
            'static/pics/*.svg',
            'static/pics/README.md',
            'static/pics/arrows/*.svg',
            'static/pics/lines/*.svg',
        ]
    },
    ext_modules=cythonize(
        glob.glob('maze/*.pyx'),
        language_level=3,
        include_dirs=[numpy.get_include()],
        language="c++"
    ),
    include_dirs=[numpy.get_include()],
    install_requires=[
        'Cython>=0.25.1',
        'numpy>=1.11.2',
        'py>=1.4.31',
        'PyQt5>=5.7',
        'bresenham>=0.1',
        'quamash>=0.5.5'
    ],
    setup_requires=[
        'pytest-runner'
    ],
    tests_require=[
        'pytest',
    ],
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Topic :: Scientific/Engineering :: Mathematics',
    ],
)
