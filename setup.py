from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __version__ variable in abarhailwater/__init__.py
from abarhailwater import __version__ as version

setup(
	name="abarhailwater",
	version=version,
	description="All Abar Hail Water Customizations",
	author="Kossivi",
	author_email="dodziamouzou@gmail.com",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
