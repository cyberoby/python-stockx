from setuptools import find_packages, setup

with open('README.md', 'r') as f:
    long_description = f.read()

setup(
    name='python-stockx',
    version='0.1.0',
    package_dir={'': 'stockx'},
    packages=find_packages(where='stockx'),
    description='An async Python SDK for interacting with the StockX API',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Roberto Scifo',
    author_email='roberto@naha.it',
    url='https://github.com/RobertoScifo/python-stockx',
    license='MIT',
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.12',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.12',
    install_requires=['aiohttp>=3.9.5'],
    extras_require={
        'test': [
            'pytest>=8.3.4',
            'pytest-asyncio>=0.24.0',
            'pytest-cov>=6.0.0',
            'pytest-mock>=3.14.0',
        ],
    },
)

