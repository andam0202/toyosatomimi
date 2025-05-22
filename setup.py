from setuptools import setup, find_packages

setup(
    name="voice-separator",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "torch>=1.9.0",
        "numpy>=1.20.0",
        "scipy>=1.7.0",
        "librosa>=0.8.1",
        "soundfile>=0.10.3.post1",
        "pydub>=0.25.1",
        "demucs>=4.0.0",
        "pyannote-audio>=2.1.1",
    ],
    extras_require={
        "dev": [
            "pytest",
            "pytest-cov",
        ],
    },
    author="Your Name",
    author_email="your.email@example.com",
    description="A tool for separating voices in audio files",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/voice-separator",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
)
