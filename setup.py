"""Setup skyq_remote package."""
from setuptools import setup, find_namespace_packages

from pyskyqremote.version import __version__ as version

from os import path
this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='pyskyqremote',
    version=version,
    author='Roger Selwyn',
    author_email='roger.selwyn@nomail.com',
    description='Library for Sky Q Remote',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/RogerSelwyn/skyq_remote',
    license='MIT',
    packages=find_namespace_packages(exclude=['tests','manage']),
    install_requires=['requests>=2.24.0', 'websocket-client>=0.56.0', 'xmltodict>=0.12.0', 'pycountry>=20.7.3'],
    keywords='SKYQ Remote',
    include_package_data=True,
    zip_safe=False,
    python_requires='>=3.7'	
)
