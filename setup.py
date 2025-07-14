"""Скрипт встановлення для crypto_bot_project."""

from setuptools import find_packages, setup


setup(
    name="crypto_bot_project",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "google-generativeai>=0.3.0",
        "python-dotenv>=1.0.0",
    ],
    entry_points={
        "console_scripts": [
            "crypto-bot=run:main",
        ],
    },
    author="Ukrainian",
    author_email="CEHA.UA@gmail.com",
    description="Система управління завданнями для Crypto Bot Project",
    keywords="crypto, bot, task, management",
    python_requires=">=3.8",
)
