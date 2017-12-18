from setuptools import setup, find_packages

setup_requires = [
    ]

install_requires = [
    ]

dependency_links = [
    ]
desc = """\
this is Python package for control Codrone
"""

setup(
    name='CoDrone',
    version='0.2',
    description='Python package for CoDrone',
    url='https://github.com/RobolinkInc/CoDrone-python.git',
    author='robolink',
    author_email='whoseop@robolink.com',
    packages=["CoDrone"],
    include_package_data=True,
    install_requires=install_requires,
    setup_requires=setup_requires,
    dependency_links=dependency_links,
    # scripts=['manage.py'],
    python_requires='>=3',
    )
