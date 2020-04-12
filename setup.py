"""Setup skyq_remote package."""
from setuptools import setup, find_packages

from pyskyqremote.version import __version__ as version

setup(
    name='pyskyqremote',
    version=version,
    description='Library for Sky Q Remote',
    long_description='Python module for accessing SkyQ box and EPG, and sending commands',
    url='https://github.com/RogerSelwyn/skyq_remote',
    maintainer='Roger Selwyn',
    license='MIT',
    packages=find_packages(),
    install_requires=['requests', 'ws4py==0.5.1', 'xmltodict==0.12.0'],
    keywords='SKYQ Remote',
    include_package_data=True,
    zip_safe=False
)
