# -*- coding: utf-8 -*-
"""
GROMACS to LAMMPS converter via moltemplate
将GROMACS工程文件转换为LAMMPS工程文件的工具包

作者: 陈佳钰
日期: 2025-07-24
"""

from .config import PROJECT_NAME, VERSION, DESCRIPTION

__version__ = VERSION
__title__ = PROJECT_NAME
__description__ = DESCRIPTION

# 导出主要接口
from .main import main

__all__ = ['main', '__version__', '__title__', '__description__'] 