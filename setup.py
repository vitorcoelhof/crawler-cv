from setuptools import setup, find_packages

setup(
    name="cv-crawler",
    version="0.1.0",
    description="Match your resume against remote job opportunities",
    author="Vitor",
    python_requires=">=3.9",
    packages=find_packages(),
    install_requires=[
        "beautifulsoup4==4.12.2",
        "playwright==1.40.0",
        "pdfplumber==0.10.3",
        "requests==2.31.0",
        "groq==0.4.1",
        "sentence-transformers==2.2.2",
        "scikit-learn==1.3.2",
        "jinja2==3.1.2",
        "click==8.1.7",
        "python-dotenv==1.0.0",
        "rich==13.7.0",
    ],
    entry_points={
        "console_scripts": [
            "cv-crawler=src.cli:main",
        ],
    },
    include_package_data=True,
)
