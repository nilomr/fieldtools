from setuptools import setup, find_packages
import os
import sys

_here = os.path.abspath(os.path.dirname(__file__))

version = {}
with open(os.path.join(_here, 'fieldtools', 'version.py')) as f:
    exec(f.read(), version)

setup(
    name='fieldtools',
    version=version['__version__'],
    description=('Command-line tools to help with bioacoustics fieldwork'),
    author='Nilo M. Recalde',
    url='https://github.com/nilomr/fieldtools',
    license='MIT',
    packages=find_packages(),
    include_package_data=True,
    classifiers=[
        'Intended Audience :: Science/Research',
        'Programming Language :: Python :: 3.8'],
)
