from setuptools import setup, find_packages

setup(
    name="realestate-scraper",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        'flask',
        'flask-sqlalchemy',
        'apscheduler',
        'beautifulsoup4',
        'requests',
        'pandas',
        'python-dotenv',
        'aiohttp',
        'selenium',
        'gunicorn'
    ],
)
