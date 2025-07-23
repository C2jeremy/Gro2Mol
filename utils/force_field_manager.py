# -*- coding: utf-8 -*-
"""
力场管理器
处理不同类型的力场（通用和自定义）
"""

from typing import Dict, List, Optional
from pathlib import Path

class ForceFieldManager:
    """力场管理器"""
    
    # 支持的通用力场
    STANDARD_FORCE_FIELDS = {
        'gaff2': {
            'name': 'gaff2',
            'file': 'force_fields/gaff2.lt',
            'description': 'General Amber Force Field 2'
        },
        'gaff': {
            'name': 'gaff',
            'file': 'force_fields/gaff.lt',
            'description': 'General Amber Force Field'
        },
        'opls': {
            'name': 'opls',
            'file': 'force_fields/oplsaa.lt',
            'description': 'OPLS-AA Force Field'
        },
        'lopls': {
            'name': 'lopls',
            'file': 'force_fields/loplsaa.lt',
            'description': 'LOPLS-AA Force Field'
        },
        'compass': {
            'name': 'compass',
            'file': 'force_fields/compass_published.lt',
            'description': 'COMPASS Force Field'
        }
    }
    
    def __init__(self, logger):
        self.logger = logger
    
    def process_force_field(self, system_data: Dict, force_field: Optional[str] = None,
                           custom_ff: bool = False) -> Dict:
        """处理力场信息"""
        
        if custom_ff:
            # 使用自定义力场
            return self._process_custom_force_field(system_data)
        else:
            # 使用标准力场
            return self._process_standard_force_field(force_field)
    
    def _process_standard_force_field(self, force_field: Optional[str]) -> Dict:
        """处理标准力场"""
        
        # 如果未指定力场，默认使用GAFF2
        if force_field is None:
            force_field = 'gaff2'
        
        # 转换为小写
        force_field = force_field.lower()
        
        # 检查是否支持该力场
        if force_field not in self.STANDARD_FORCE_FIELDS:
            available_ff = ', '.join(self.STANDARD_FORCE_FIELDS.keys())
            raise ValueError(f"不支持的力场: {force_field}. 可用的力场: {available_ff}")
        
        ff_info = self.STANDARD_FORCE_FIELDS[force_field]
        
        self.logger.info(f"使用标准力场: {ff_info['description']}")
        
        return {
            'type': 'standard',
            'name': ff_info['name'],
            'file': ff_info['file'],
            'description': ff_info['description']
        }
    
    def _process_custom_force_field(self, system_data: Dict) -> Dict:
        """处理自定义力场"""
        
        self.logger.info("使用自定义力场模式")
        
        # 提取力场参数
        force_field_data = {
            'type': 'custom',
            'name': 'custom',
            'atom_types': {},
            'bond_types': {},
            'angle_types': {},
            'dihedral_types': {}
        }
        
        # 首先从全局力场参数中收集
        if 'global_force_field' in system_data:
            global_ff = system_data['global_force_field']
            for ff_type in ['atom_types', 'bond_types', 'angle_types', 'dihedral_types']:
                if ff_type in global_ff:
                    force_field_data[ff_type].update(global_ff[ff_type])
        
        # 然后从各分子中收集力场参数（如果有的话）
        for mol_name, mol_data in system_data['molecules'].items():
            
            # 合并原子类型
            if 'atom_types' in mol_data:
                force_field_data['atom_types'].update(mol_data['atom_types'])
            
            # 合并键类型
            if 'bond_types' in mol_data:
                force_field_data['bond_types'].update(mol_data['bond_types'])
            
            # 合并角度类型
            if 'angle_types' in mol_data:
                force_field_data['angle_types'].update(mol_data['angle_types'])
            
            # 合并二面角类型
            if 'dihedral_types' in mol_data:
                force_field_data['dihedral_types'].update(mol_data['dihedral_types'])
            
            # 从分子的全局力场中收集（新增）
            if 'global_force_field' in mol_data:
                mol_global_ff = mol_data['global_force_field']
                for ff_type in ['atom_types', 'bond_types', 'angle_types', 'dihedral_types']:
                    if ff_type in mol_global_ff:
                        force_field_data[ff_type].update(mol_global_ff[ff_type])
        
        # 统计力场参数
        n_atom_types = len(force_field_data['atom_types'])
        n_bond_types = len(force_field_data['bond_types'])
        n_angle_types = len(force_field_data['angle_types'])
        n_dihedral_types = len(force_field_data['dihedral_types'])
        
        self.logger.info(f"自定义力场参数统计:")
        self.logger.info(f"  原子类型: {n_atom_types}")
        self.logger.info(f"  键类型: {n_bond_types}")
        self.logger.info(f"  角度类型: {n_angle_types}")
        self.logger.info(f"  二面角类型: {n_dihedral_types}")
        
        return force_field_data
    
    def validate_force_field_compatibility(self, system_data: Dict, 
                                         force_field_data: Dict) -> bool:
        """验证力场与系统的兼容性"""
        
        # 检查是否所有原子类型都有对应的力场参数
        missing_types = []
        
        for mol_name, mol_data in system_data['molecules'].items():
            if 'atoms' in mol_data:
                for atom in mol_data['atoms']:
                    atom_type = atom['type']
                    if force_field_data['type'] == 'custom':
                        if atom_type not in force_field_data['atom_types']:
                            missing_types.append(atom_type)
        
        if missing_types:
            unique_missing = list(set(missing_types))
            self.logger.warning(f"缺少以下原子类型的力场参数: {unique_missing}")
            return False
        
        self.logger.info("力场兼容性检查通过")
        return True
    
    def get_atom_type_mapping(self, system_data: Dict, force_field_data: Dict) -> Dict[str, str]:
        """获取原子类型映射"""
        
        mapping = {}
        
        if force_field_data['type'] == 'standard':
            # 对于标准力场，需要将GROMACS原子类型映射到力场原子类型
            # 这里提供一个基本的映射策略
            for mol_name, mol_data in system_data['molecules'].items():
                if 'atoms' in mol_data:
                    for atom in mol_data['atoms']:
                        gromacs_type = atom['type']
                        # 简单映射策略：保持相同名称或进行基本转换
                        lammps_type = self._convert_atom_type_name(gromacs_type, force_field_data['name'])
                        mapping[gromacs_type] = lammps_type
        
        else:
            # 对于自定义力场，直接使用原有类型名
            for mol_name, mol_data in system_data['molecules'].items():
                if 'atoms' in mol_data:
                    for atom in mol_data['atoms']:
                        atom_type = atom['type']
                        mapping[atom_type] = atom_type
        
        return mapping
    
    def _convert_atom_type_name(self, gromacs_type: str, force_field_name: str) -> str:
        """转换原子类型名称"""
        
        # 基本的原子类型名称转换
        # 这里可以根据具体力场进行更复杂的映射
        
        if force_field_name in ['gaff', 'gaff2']:
            # GAFF原子类型通常是小写
            return gromacs_type.lower()
        
        elif force_field_name == 'opls':
            # OPLS原子类型映射
            opls_mapping = {
                'CT': 'CT',  # 碳原子
                'HC': 'HC',  # 氢原子
                'OH': 'OH',  # 羟基氧
                'HO': 'HO',  # 羟基氢
                # 添加更多映射...
            }
            return opls_mapping.get(gromacs_type, gromacs_type)
        
        else:
            # 默认保持原名
            return gromacs_type
    
    def generate_force_field_info(self, output_dir: Path, force_field_data: Dict):
        """生成力场信息文件"""
        
        info_file = output_dir / "force_field_info.txt"
        
        with open(info_file, 'w') as f:
            f.write("力场信息\n")
            f.write("=" * 50 + "\n\n")
            
            f.write(f"力场类型: {force_field_data['type']}\n")
            f.write(f"力场名称: {force_field_data['name']}\n")
            
            if force_field_data['type'] == 'standard':
                f.write(f"力场文件: {force_field_data['file']}\n")
                f.write(f"描述: {force_field_data['description']}\n")
            
            elif force_field_data['type'] == 'custom':
                f.write("\n自定义力场参数统计:\n")
                f.write(f"  原子类型数量: {len(force_field_data['atom_types'])}\n")
                f.write(f"  键类型数量: {len(force_field_data['bond_types'])}\n")
                f.write(f"  角度类型数量: {len(force_field_data['angle_types'])}\n")
                f.write(f"  二面角类型数量: {len(force_field_data['dihedral_types'])}\n")
                
                # 列出所有原子类型
                if force_field_data['atom_types']:
                    f.write("\n原子类型列表:\n")
                    for atom_type, data in force_field_data['atom_types'].items():
                        mass = data.get('mass', 'N/A')
                        f.write(f"  {atom_type}: 质量={mass}\n")
        
        self.logger.info(f"生成力场信息文件: {info_file}") 