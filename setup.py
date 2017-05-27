from setuptools import setup, find_packages
from os import path

here = path.abspath(path.dirname(__file__))

setup(
    name='minIRC_Server',
    version='0.1dev',
    packages=find_packages(exclude=['contrib', 'docs', 'tests*']),
    url='https://github.com/mikelane/minIRC_Server',
    license='MIT',
    author='Michael Lane',
    author_email='mikelane@gmail.com',
    description='A minimal IRC Server for CS594 - Internetworking Protocols',

    # https://packaging.python.org/distributing/#classifiers
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 3 - Alpha',

        # Indicate who your project is intended for
        'Intended Audience :: Students',
        'Topic :: Education :: Networking',

        # License should match License above
        'License :: OSI Approved :: MIT License',

        'Programming Language :: Python :: 3.6'
    ],
    
    keywords='',
    install_requires=[
        'nose'
    ],
    setup_requires=[
        'nose'
    ]
)
