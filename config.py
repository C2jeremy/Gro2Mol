# -*- coding: utf-8 -*-
"""
配置文件
定义转换工具的各种配置选项
"""

import os
from pathlib import Path

# 项目信息
PROJECT_NAME = "gro2mol2lmp"
VERSION = "1.0.0"
DESCRIPTION = "GROMACS to LAMMPS converter via moltemplate"

# 默认配置
DEFAULT_CONFIG = {
    # 输出设置
    'output_dir': 'output',
    'output_name': 'system',
    
    # 力场设置
    'default_force_field': 'gaff2',
    'force_field_search_paths': [
        '/usr/local/share/moltemplate/forcefields',
        '~/.moltemplate/forcefields',
        './forcefields'
    ],
    
    # 文件格式设置
    'coordinate_precision': 6,
    'parameter_precision': 6,
    
    # 转换选项
    'auto_detect_molecules': True,
    'validate_force_field': True,
    'generate_run_scripts': True,
    
    # 日志设置
    'log_level': 'INFO',
    'log_format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'log_date_format': '%Y-%m-%d %H:%M:%S'
}

# 支持的文件格式
SUPPORTED_FORMATS = {
    'topology': ['.top'],
    'include': ['.itp'],
    'coordinate': ['.gro', '.pdb'],
    'output': ['.lt', '.data', '.in']
}

# GROMACS函数类型映射到LAMMPS
FUNCTION_TYPE_MAPPING = {
    # 键函数类型
    'bond_functions': {
        1: 'harmonic',      # 谐振子
        2: 'morse',         # Morse势
        3: 'cubic',         # 三次
        4: 'fene',          # FENE
        6: 'harmonic',      # 约束（作为谐振子处理）
    },
    
    # 角度函数类型
    'angle_functions': {
        1: 'harmonic',      # 谐振子
        2: 'cosine',        # 余弦
        5: 'quartic',       # 四次
    },
    
    # 二面角函数类型
    'dihedral_functions': {
        1: 'harmonic',      # 谐振子
        2: 'harmonic',      # 改进二面角
        3: 'fourier',       # Fourier级数
        4: 'fourier',       # 周期improper
        9: 'fourier',       # 多重二面角
    }
}

# 原子类型映射
ATOM_TYPE_MAPPINGS = {
    'gaff_to_lammps': {
        # GAFF原子类型到LAMMPS类型的映射
        'c3': 'C3',
        'hc': 'HC',
        'oh': 'OH',
        'ho': 'HO',
        'os': 'OS',
        'n3': 'N3',
        'hn': 'HN',
        # 更多映射可以在这里添加
    },
    
    'opls_to_lammps': {
        # OPLS原子类型到LAMMPS类型的映射
        'CT': 'CT',
        'HC': 'HC',
        'OH': 'OH',
        'HO': 'HO',
        # 更多映射可以在这里添加
    }
}

# 单位转换
UNIT_CONVERSIONS = {
    # 长度单位 (GROMACS nm -> LAMMPS Angstrom)
    'length': 10.0,
    
    # 能量单位 (GROMACS kJ/mol -> LAMMPS kcal/mol)
    'energy': 0.239006,
    
    # 力常数单位转换
    'bond_force': 0.239006 * 100,  # kJ/mol/nm² -> kcal/mol/Å²
    'angle_force': 0.239006,       # kJ/mol/rad² -> kcal/mol/rad²
    
    # LJ参数单位转换
    'sigma': 10.0,      # nm -> Angstrom
    'epsilon': 0.239006, # kJ/mol -> kcal/mol
    
    # 质量单位 (GROMACS和LAMMPS都是amu，无需转换)
    'mass': 1.0,
    
    # 电荷单位 (都是基本电荷，无需转换)
    'charge': 1.0,
    
    # 角度单位 (度到弧度的转换)
    'angle_degree_to_radian': 3.14159265359 / 180.0,
}

# moltemplate模板
MOLTEMPLATE_TEMPLATES = {
    'file_header': '''# Moltemplate文件: {filename}
# 由 GROMACS 到 LAMMPS 转换工具生成
# 生成时间: {timestamp}
# 力场类型: {force_field_type}

''',
    
    'molecule_header': '''{molecule_name} {{

''',
    
    'molecule_footer': '''
}}

''',
    
    'system_header': '''# 系统定义文件
# 包含所有分子类型和系统组成

''',
}

# 错误消息
ERROR_MESSAGES = {
    'file_not_found': "找不到文件: {filename}",
    'unsupported_format': "不支持的文件格式: {format}",
    'force_field_not_found': "找不到力场: {force_field}",
    'moltemplate_not_found': "未找到moltemplate，请确保已安装",
    'parsing_error': "解析文件时出错: {error}",
    'conversion_error': "转换过程中出错: {error}",
}

# 警告消息
WARNING_MESSAGES = {
    'missing_parameters': "缺少力场参数: {parameters}",
    'unknown_atom_type': "未知原子类型: {atom_type}",
    'force_field_mismatch': "力场不匹配: {details}",
}

# 环境变量
ENV_VARS = {
    'MOLTEMPLATE_PATH': 'MOLTEMPLATE_PATH',
    'LAMMPS_POTENTIAL_PATH': 'LAMMPS_POTENTIAL_PATH',
    'GROMACS_DATA_PATH': 'GROMACS_DATA_PATH',
}


def get_config():
    """获取配置"""
    config = DEFAULT_CONFIG.copy()
    
    # 从环境变量更新配置
    if 'GRO2LAMMPS_OUTPUT_DIR' in os.environ:
        config['output_dir'] = os.environ['GRO2LAMMPS_OUTPUT_DIR']
    
    if 'GRO2LAMMPS_FORCE_FIELD' in os.environ:
        config['default_force_field'] = os.environ['GRO2LAMMPS_FORCE_FIELD']
    
    return config


def get_moltemplate_paths():
    """获取moltemplate路径"""
    paths = []
    
    # 从环境变量获取
    if ENV_VARS['MOLTEMPLATE_PATH'] in os.environ:
        paths.extend(os.environ[ENV_VARS['MOLTEMPLATE_PATH']].split(':'))
    
    # 添加默认路径
    default_paths = DEFAULT_CONFIG['force_field_search_paths']
    for path in default_paths:
        expanded_path = Path(path).expanduser()
        if expanded_path.exists():
            paths.append(str(expanded_path))
    
    return paths


def validate_config(config):
    """验证配置"""
    errors = []
    
    # 检查输出目录权限
    output_dir = Path(config['output_dir'])
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        errors.append(f"无法创建输出目录: {output_dir}")
    
    # 检查力场
    if config['default_force_field'] not in ['gaff', 'gaff2', 'opls', 'amber', 'charmm']:
        errors.append(f"不支持的默认力场: {config['default_force_field']}")
    
    return errors 