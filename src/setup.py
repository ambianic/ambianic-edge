"""Setup for the Ambianic Edge package."""
import setuptools

with open("../README.md", "r") as fh:
    long_description = fh.read()

version="0.11.4"

setuptools.setup(
    name="ambianic",
    version=version,
    author="Ivelin Ivanov",
    author_email="ivelin.ivanov@ambianic.ai",
    description="Edge component of the AI platform "
                "for home and business automation",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://ambianic.ai",
    license="Apache Software License 2.0",
    packages=setuptools.find_packages(),
    python_requires=">=3.6",
    install_requires=[],
    classifiers=[
        'Development Status :: Alpha ' + version,
        "Programming Language :: Python :: 3",
        "OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        'TOPIC :: HOME AUTOMATION',
        'TOPIC :: SCIENTIFIC/ENGINEERING :: ARTIFICIAL INTELLIGENCE'
        'TOPIC :: SOFTWARE DEVELOPMENT :: EMBEDDED SYSTEMS',
        'Intended Audience :: Developers',
    ],
)
