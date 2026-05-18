from setuptools import setup, find_packages

setup(
    name="pdf_gui",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "PyQt5>=5.15",
        "PyYAML>=6.0",
    ],
    entry_points={
        "console_scripts": [
            "pdf-gui=pdf_gui.main:main",
        ],
    },
    python_requires=">=3.9",
)
