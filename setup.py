import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pythoneer",
    version="0.0.1",
    author="Vadim Gubergrits",
    author_email="vadim.gubergrits@gmail.com",
    description="Python code generation tool",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/vadimgu/pythoneer",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    entry_points={
        "console_scripts": [
            "pythoneer=pythoneer.__main__:main",
        ],
    },
    install_requires=[
        "astor",
    ],
)