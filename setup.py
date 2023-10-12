#!/usr/bin/env python3

from setuptools import setup

if __name__ == '__main__':
    import sys

    if len(sys.argv) == 1:
        sys.argv.append('install')

with open('README.md', 'r') as f:
    long_description = f.read()

setup(
    name='tremolo-login',
    version='1.0.0',
    license='MIT',
    author='nggit',
    author_email='contact@anggit.com',
    description=(
        'tremolo-login is basically an extension of tremolo-session.'),
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/nggit/tremolo-login',
    packages=['tremolo_login'],
    install_requires=['tremolo_session'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Topic :: Internet :: WWW/HTTP :: HTTP Servers',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
    ],
)
