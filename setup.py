#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
import os
from pathlib import Path

# 读取版本信息
def get_version():
    """从config.py读取版本信息"""
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from config import VERSION
    return VERSION

# 读取README文件
def get_long_description():
    """读取README文件作为长描述"""
    readme_path = Path(__file__).parent / "README.md"
    if readme_path.exists():
        with open(readme_path, "r", encoding="utf-8") as f:
            return f.read()
    return ""

# 读取依赖
def get_requirements():
    """读取requirements.txt文件"""
    requirements_path = Path(__file__).parent / "requirements.txt"
    requirements = []
    if requirements_path.exists():
        with open(requirements_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                # 忽略注释和空行
                if line and not line.startswith("#"):
                    # 忽略开发依赖注释行
                    if not any(dev_marker in line for dev_marker in ["# 用于", "# 代码", "# 安装方法"]):
                        requirements.append(line)
    return requirements

setup(
    name="gro2mol2lmp",
    version=get_version(),
    author="gro2mol2lmp developer",
    author_email="developer@example.com",
    description="GROMACS to LAMMPS converter via moltemplate",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/gro2mol2lmp",  # 请替换为实际的项目URL
    py_modules=[
        'main', 'config', 'gro2mol2lmp_cli', '__init__'
    ],
    packages=find_packages(include=['parsers*', 'generators*', 'utils*', 'force_fields*']),
    include_package_data=True,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Chemistry",
        "Topic :: Scientific/Engineering :: Physics",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    install_requires=get_requirements(),
    entry_points={
        "console_scripts": [
            "gro2mol2lmp=gro2mol2lmp_cli:main",
            "gro2lammps=gro2mol2lmp_cli:main",  # 提供一个更短的别名
        ],
    },
    keywords="gromacs lammps moltemplate molecular-dynamics simulation",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/gro2mol2lmp/issues",
        "Source": "https://github.com/yourusername/gro2mol2lmp",
        "Documentation": "https://github.com/yourusername/gro2mol2lmp/docs",
    },
) 