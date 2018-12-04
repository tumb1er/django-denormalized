import os
import re
import subprocess
from pathlib import Path

from setuptools import setup

with open('README.md') as f:
    long_description = f.read()

version_re = re.compile('^Version: (.+)$', re.M)
package_name = 'django_denormalized'


def get_version():
    """
    Reads version from git status or PKG-INFO

    https://gist.github.com/pwithnall/7bc5f320b3bdf418265a
    """
    d: Path = Path(__file__).parent.absolute()
    git_dir = d.joinpath('.git')
    if git_dir.is_dir():
        # Get the version using "git describe".
        cmd = 'git describe --tags --match [0-9]*'.split()
        try:
            version = subprocess.check_output(cmd).decode().strip()
        except subprocess.CalledProcessError:
            return None

        # PEP 386 compatibility
        if '-' in version:
            version = '.post'.join(version.split('-')[:2])

        # Don't declare a version "dirty" merely because a time stamp has
        # changed. If it is dirty, append a ".dev1" suffix to indicate a
        # development revision after the release.
        with open(os.devnull, 'w') as fd_devnull:
            subprocess.call(['git', 'status'],
                            stdout=fd_devnull, stderr=fd_devnull)

        cmd = 'git diff-index --name-only HEAD'.split()
        try:
            dirty = subprocess.check_output(cmd).decode().strip()
        except subprocess.CalledProcessError:
            return None

        if dirty != '':
            version += '.dev1'
    else:
        # Extract the version from the PKG-INFO file.
        with open(str(d.joinpath(f'{package_name}.egg-info/PKG-INFO'))) as v:
            version = version_re.search(v.read()).group(1)

    return version


setup(
    name=package_name,
    version=get_version(),
    packages=['denormalized'],
    url='https://github.com/just-work/django-denormalized',
    long_description=long_description,
    long_description_content_type='text/markdown',
    license='Beer License',
    author='Sergey Tikhonov',
    author_email='zimbler@gmail.com',
    description='Utils for maintaining denormalized '
                'aggregates for Django models',
    install_requires=['Django']
)
