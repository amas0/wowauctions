from setuptools import setup, find_packages

setup(name='wowauctions',
      version='0.1',
      packages=find_packages(),
      python_requires='>=3.9',
      install_requires=['python-wowapi'])