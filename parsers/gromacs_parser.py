# -*- coding: utf-8 -*-
"""
GROMACS文件解析器
解析.top, .itp, .gro, .pdb文件
"""

import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass

@dataclass
class Atom:
    """原子数据结构"""
    index: int
    name: str
    residue_name: str
    residue_number: int
    x: float
    y: float
    z: float
    atom_type: str = ""
    charge: float = 0.0
    mass: float = 0.0

@dataclass
class Bond:
    """键数据结构"""
    atom1: int
    atom2: int
    bond_type: str = ""
    parameters: List[float] = None

@dataclass
class Angle:
    """角度数据结构"""
    atom1: int
    atom2: int
    atom3: int
    angle_type: str = ""
    parameters: List[float] = None

@dataclass
class Dihedral:
    """二面角数据结构"""
    atom1: int
    atom2: int
    atom3: int
    atom4: int
    dihedral_type: str = ""
    parameters: List[float] = None

@dataclass
class Molecule:
    """分子数据结构"""
    name: str
    atoms: List[Atom]
    bonds: List[Bond]
    angles: List[Angle]
    dihedrals: List[Dihedral]
    atom_types: Dict[str, Dict] = None
    bond_types: Dict[str, Dict] = None
    angle_types: Dict[str, Dict] = None
    dihedral_types: Dict[str, Dict] = None

class GromacsParser:
    """GROMACS文件解析器"""
    
    def __init__(self, logger):
        self.logger = logger
        self.molecules = {}
        self.system_composition = []
        
    def parse_system(self, top_file: str, coord_file: str, 
                    itp_files: Optional[List[str]] = None) -> Dict:
        """解析完整的GROMACS系统"""
        system_data = {
            'molecules': {},
            'system_composition': [],
            'box_vectors': None,
            'coordinates': [],
            'global_force_field': {
                'atom_types': {},
                'bond_types': {},
                'angle_types': {},
                'dihedral_types': {}
            }
        }
        
        # 解析拓扑文件
        self.logger.info(f"解析拓扑文件: {top_file}")
        top_data = self._parse_topology_file(top_file)
        
        # 解析ITP文件
        if itp_files:
            for itp_file in itp_files:
                self.logger.info(f"解析ITP文件: {itp_file}")
                itp_data = self._parse_itp_file(itp_file)
                # 合并ITP数据到系统中
                self._merge_itp_data(system_data, itp_data)
        
        # 解析坐标文件
        self.logger.info(f"解析坐标文件: {coord_file}")
        coord_data = self._parse_coordinate_file(coord_file)
        
        # 合并拓扑数据
        if 'molecules' in top_data:
            system_data['molecules'].update(top_data['molecules'])
        if 'system_composition' in top_data:
            system_data['system_composition'] = top_data['system_composition']
        if 'system_name' in top_data:
            system_data['system_name'] = top_data['system_name']
        
        # 合并全局力场数据
        if 'global_force_field' in top_data:
            for ff_type in ['atom_types', 'bond_types', 'angle_types', 'dihedral_types']:
                if ff_type in top_data['global_force_field']:
                    system_data['global_force_field'][ff_type].update(
                        top_data['global_force_field'][ff_type]
                    )
        
        # 合并坐标数据
        if 'coordinates' in coord_data:
            system_data['coordinates'] = coord_data['coordinates']
        if 'box_vectors' in coord_data:
            system_data['box_vectors'] = coord_data['box_vectors']
        if 'title' in coord_data:
            system_data['title'] = coord_data['title']
        
        return system_data
    
    def parse_itp_only(self, itp_files: List[str]) -> Dict:
        """仅解析ITP文件（用于标准力场模式）"""
        
        system_data = {
            'molecules': {},
            'global_force_field': {
                'atom_types': {},
                'bond_types': {},
                'angle_types': {},
                'dihedral_types': {}
            }
        }
        
        # 解析每个ITP文件
        for itp_file in itp_files:
            self.logger.info(f"解析ITP文件: {itp_file}")
            itp_data = self._parse_itp_file(itp_file)
            
            # 合并分子数据
            system_data['molecules'].update(itp_data.get('molecules', {}))
            
            # 合并全局力场数据
            if 'global_force_field' in itp_data:
                for ff_type in ['atom_types', 'bond_types', 'angle_types', 'dihedral_types']:
                    if ff_type in itp_data['global_force_field']:
                        system_data['global_force_field'][ff_type].update(
                            itp_data['global_force_field'][ff_type]
                        )
        
        # 为单分子模式添加虚拟坐标（如果没有坐标信息）
        self._add_dummy_coordinates(system_data)
        
        self.logger.info(f"解析完成，发现 {len(system_data['molecules'])} 个分子类型")
        return system_data
    
    def _add_dummy_coordinates(self, system_data: Dict):
        """为没有坐标的原子添加虚拟坐标"""
        
        for mol_name, mol_data in system_data['molecules'].items():
            if 'atoms' in mol_data:
                for i, atom in enumerate(mol_data['atoms']):
                    if 'x' not in atom:
                        # 添加简单的线性排列坐标
                        atom['x'] = i * 0.15  # 1.5 Angstrom spacing
                        atom['y'] = 0.0
                        atom['z'] = 0.0
    
    def _parse_topology_file(self, top_file: str) -> Dict:
        """解析.top文件"""
        data = {'molecules': {}, 'system_composition': [], 'global_force_field': {
            'atom_types': {},
            'bond_types': {},
            'angle_types': {},
            'dihedral_types': {}
        }}
        
        with open(top_file, 'r') as f:
            content = f.read()
        
        # 移除注释
        content = self._remove_comments(content)
        
        # 解析各个section
        sections = self._split_into_sections(content)
        
        for section_name, section_content in sections.items():
            if section_name == 'system':
                data['system_name'] = section_content.strip()
            elif section_name == 'molecules':
                data['system_composition'] = self._parse_molecules_section(section_content)
            elif section_name == 'moleculetype':
                # 如果top文件中定义了分子类型
                mol_data = self._parse_moleculetype_section(section_content)
                if mol_data:
                    data['molecules'][mol_data['name']] = mol_data
            elif section_name == 'atomtypes':
                data['global_force_field']['atom_types'].update(self._parse_atomtypes_section(section_content))
            elif section_name == 'bondtypes':
                data['global_force_field']['bond_types'].update(self._parse_bondtypes_section(section_content))
            elif section_name == 'angletypes':
                data['global_force_field']['angle_types'].update(self._parse_angletypes_section(section_content))
            elif section_name == 'dihedraltypes':
                data['global_force_field']['dihedral_types'].update(self._parse_dihedraltypes_section(section_content))
        
        return data
    
    def _parse_itp_file(self, itp_file: str) -> Dict:
        """解析.itp文件，支持多个分子类型"""
        with open(itp_file, 'r') as f:
            content = f.read()
        
        content = self._remove_comments(content)
        
        # 将内容按分子类型分组
        molecules_data = self._parse_multiple_molecules(content)
        
        return molecules_data
    
    def _parse_multiple_molecules(self, content: str) -> Dict:
        """解析包含多个分子类型的内容"""
        lines = content.split('\n')
        
        # 全局力场参数（在任何分子定义之前）
        global_force_field = {
            'atom_types': {},
            'bond_types': {},
            'angle_types': {},
            'dihedral_types': {}
        }
        
        molecules = {}
        current_molecule = None
        current_section = None
        section_content = []
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # 跳过空行
            if not line:
                i += 1
                continue
            
            # 检查是否是section标题
            if line.startswith('[') and line.endswith(']'):
                # 保存前一个section的内容
                if current_section and section_content:
                    self._process_section(current_molecule, current_section, 
                                        '\n'.join(section_content), molecules, global_force_field)
                
                # 开始新的section
                current_section = line[1:-1].strip()
                section_content = []
                
                # 如果是moleculetype，创建新的分子
                if current_section == 'moleculetype':
                    # 读取下一行获取分子名称
                    i += 1
                    while i < len(lines) and not lines[i].strip():
                        i += 1
                    if i < len(lines):
                        mol_line = lines[i].strip()
                        parts = mol_line.split()
                        if parts:
                            mol_name = parts[0]
                            nrexcl = int(parts[1]) if len(parts) > 1 else 1
                            current_molecule = mol_name
                            molecules[mol_name] = {
                                'name': mol_name,
                                'nrexcl': nrexcl,
                                'atoms': [],
                                'bonds': [],
                                'angles': [],
                                'dihedrals': []
                            }
                i += 1
                continue
            
            # 收集section内容
            if current_section:
                section_content.append(line)
            
            i += 1
        
        # 处理最后一个section
        if current_section and section_content:
            self._process_section(current_molecule, current_section, 
                                '\n'.join(section_content), molecules, global_force_field)
        
        # 为每个分子添加全局力场参数的引用
        for mol_name in molecules:
            molecules[mol_name]['global_force_field'] = global_force_field
        
        # 返回包含多个分子和全局力场的数据
        result = {
            'molecules': molecules,
            'global_force_field': global_force_field
        }
        
        return result
    
    def _process_section(self, current_molecule: str, section_name: str, 
                        content: str, molecules: Dict, global_force_field: Dict):
        """处理单个section的内容"""
        
        if section_name == 'atoms' and current_molecule:
            molecules[current_molecule]['atoms'] = self._parse_atoms_section(content)
        elif section_name == 'bonds' and current_molecule:
            molecules[current_molecule]['bonds'] = self._parse_bonds_section(content)
            # 从具体的bonds中提取bond types
            self._extract_bond_types_from_bonds(molecules[current_molecule], global_force_field)
        elif section_name == 'angles' and current_molecule:
            molecules[current_molecule]['angles'] = self._parse_angles_section(content)
            # 从具体的angles中提取angle types
            self._extract_angle_types_from_angles(molecules[current_molecule], global_force_field)
        elif section_name == 'dihedrals' and current_molecule:
            molecules[current_molecule]['dihedrals'] = self._parse_dihedrals_section(content)
            # 从具体的dihedrals中提取dihedral types
            self._extract_dihedral_types_from_dihedrals(molecules[current_molecule], global_force_field)
        elif section_name == 'atomtypes':
            global_force_field['atom_types'].update(self._parse_atomtypes_section(content))
        elif section_name == 'bondtypes':
            global_force_field['bond_types'].update(self._parse_bondtypes_section(content))
        elif section_name == 'angletypes':
            global_force_field['angle_types'].update(self._parse_angletypes_section(content))
        elif section_name == 'dihedraltypes':
            global_force_field['dihedral_types'].update(self._parse_dihedraltypes_section(content))
    
    def _parse_coordinate_file(self, coord_file: str) -> Dict:
        """解析坐标文件(.gro或.pdb)"""
        file_ext = Path(coord_file).suffix.lower()
        
        if file_ext == '.gro':
            return self._parse_gro_file(coord_file)
        elif file_ext == '.pdb':
            return self._parse_pdb_file(coord_file)
        else:
            raise ValueError(f"不支持的坐标文件格式: {file_ext}")
    
    def _parse_gro_file(self, gro_file: str) -> Dict:
        """解析.gro文件"""
        coordinates = []
        
        with open(gro_file, 'r') as f:
            lines = f.readlines()
        
        # 第一行是标题
        title = lines[0].strip()
        
        # 第二行是原子数
        n_atoms = int(lines[1].strip())
        
        # 解析原子坐标
        for i in range(2, 2 + n_atoms):
            line = lines[i]
            
            # GRO格式解析
            res_num = int(line[0:5])
            res_name = line[5:10].strip()
            atom_name = line[10:15].strip()
            atom_num = int(line[15:20])
            x = float(line[20:28]) * 10  # nm to Angstrom
            y = float(line[28:36]) * 10
            z = float(line[36:44]) * 10
            
            atom = Atom(
                index=atom_num,
                name=atom_name,
                residue_name=res_name,
                residue_number=res_num,
                x=x, y=y, z=z
            )
            coordinates.append(atom)
        
        # 最后一行是盒子向量
        box_line = lines[2 + n_atoms].strip().split()
        box_vectors = [float(x) * 10 for x in box_line]  # nm to Angstrom
        
        return {
            'coordinates': coordinates,
            'box_vectors': box_vectors,
            'title': title
        }
    
    def _parse_pdb_file(self, pdb_file: str) -> Dict:
        """解析.pdb文件"""
        coordinates = []
        box_vectors = None
        
        with open(pdb_file, 'r') as f:
            for line in f:
                if line.startswith('ATOM') or line.startswith('HETATM'):
                    atom_num = int(line[6:11])
                    atom_name = line[12:16].strip()
                    res_name = line[17:20].strip()
                    res_num = int(line[22:26])
                    x = float(line[30:38])
                    y = float(line[38:46])
                    z = float(line[46:54])
                    
                    atom = Atom(
                        index=atom_num,
                        name=atom_name,
                        residue_name=res_name,
                        residue_number=res_num,
                        x=x, y=y, z=z
                    )
                    coordinates.append(atom)
                
                elif line.startswith('CRYST1'):
                    # 提取晶胞参数
                    a = float(line[6:15])
                    b = float(line[15:24])
                    c = float(line[24:33])
                    box_vectors = [a, b, c]
        
        return {
            'coordinates': coordinates,
            'box_vectors': box_vectors
        }
    
    def _remove_comments(self, content: str) -> str:
        """移除GROMACS文件中的注释"""
        lines = content.split('\n')
        clean_lines = []
        
        for line in lines:
            # 移除;后面的注释
            comment_pos = line.find(';')
            if comment_pos != -1:
                line = line[:comment_pos]
            
            # 保留非空行
            if line.strip():
                clean_lines.append(line)
        
        return '\n'.join(clean_lines)
    
    def _split_into_sections(self, content: str) -> Dict[str, str]:
        """将内容分割成各个section"""
        sections = {}
        current_section = None
        current_content = []
        
        for line in content.split('\n'):
            line = line.strip()
            if line.startswith('[') and line.endswith(']'):
                # 保存前一个section
                if current_section:
                    sections[current_section] = '\n'.join(current_content)
                
                # 开始新的section
                current_section = line[1:-1].strip()
                current_content = []
            elif current_section:
                current_content.append(line)
        
        # 保存最后一个section
        if current_section:
            sections[current_section] = '\n'.join(current_content)
        
        return sections
    
    def _parse_molecules_section(self, content: str) -> List[Tuple[str, int]]:
        """解析molecules section"""
        molecules = []
        for line in content.split('\n'):
            line = line.strip()
            if line:
                parts = line.split()
                if len(parts) >= 2:
                    mol_name = parts[0]
                    mol_count = int(parts[1])
                    molecules.append((mol_name, mol_count))
        return molecules
    
    def _parse_moleculetype_section(self, content: str) -> Dict:
        """解析moleculetype section"""
        lines = content.strip().split('\n')
        if lines:
            parts = lines[0].split()
            if len(parts) >= 2:
                return {
                    'name': parts[0],
                    'nrexcl': int(parts[1])
                }
        return {}
    
    def _parse_atoms_section(self, content: str) -> List[Dict]:
        """解析atoms section"""
        atoms = []
        for line in content.split('\n'):
            line = line.strip()
            if line:
                parts = line.split()
                if len(parts) >= 6:
                    atom_name = parts[4]
                    # 如果原子名只是通用名称（如"C", "H"），添加索引号
                    if atom_name in ['C', 'H', 'N', 'O', 'S', 'P'] or atom_name == parts[1]:
                        atom_name = f"{atom_name}{parts[0]}"
                    
                    atom = {
                        'index': int(parts[0]),
                        'type': parts[1],
                        'residue_number': int(parts[2]),
                        'residue_name': parts[3],
                        'name': parts[4],  # 原始名称
                        'atom_name': atom_name,  # 生成的唯一名称
                        'charge_group': int(parts[5]),
                        'charge': float(parts[6]) if len(parts) > 6 else 0.0,
                        'mass': float(parts[7]) if len(parts) > 7 else 0.0
                    }
                    atoms.append(atom)
        return atoms
    
    def _parse_bonds_section(self, content: str) -> List[Dict]:
        """解析bonds section"""
        bonds = []
        for line in content.split('\n'):
            line = line.strip()
            if line:
                parts = line.split()
                if len(parts) >= 3:
                    bond = {
                        'atom1': int(parts[0]),
                        'atom2': int(parts[1]),
                        'function_type': int(parts[2]),
                        'parameters': [float(x) for x in parts[3:]]
                    }
                    bonds.append(bond)
        return bonds
    
    def _parse_angles_section(self, content: str) -> List[Dict]:
        """解析angles section"""
        angles = []
        for line in content.split('\n'):
            line = line.strip()
            if line:
                parts = line.split()
                if len(parts) >= 4:
                    angle = {
                        'atom1': int(parts[0]),
                        'atom2': int(parts[1]),
                        'atom3': int(parts[2]),
                        'function_type': int(parts[3]),
                        'parameters': [float(x) for x in parts[4:]]
                    }
                    angles.append(angle)
        return angles
    
    def _parse_dihedrals_section(self, content: str) -> List[Dict]:
        """解析dihedrals section"""
        dihedrals = []
        for line in content.split('\n'):
            line = line.strip()
            if line:
                parts = line.split()
                if len(parts) >= 5:
                    dihedral = {
                        'atom1': int(parts[0]),
                        'atom2': int(parts[1]),
                        'atom3': int(parts[2]),
                        'atom4': int(parts[3]),
                        'function_type': int(parts[4]),
                        'parameters': [float(x) for x in parts[5:]]
                    }
                    dihedrals.append(dihedral)
        return dihedrals
    
    def _parse_atomtypes_section(self, content: str) -> Dict:
        """解析atomtypes section"""
        atom_types = {}
        for line in content.split('\n'):
            line = line.strip()
            if line:
                parts = line.split()
                if len(parts) >= 6:
                    atom_type = {
                        'name': parts[0],
                        'atomic_number': int(parts[1]) if parts[1].isdigit() else 0,
                        'mass': float(parts[2]),
                        'charge': float(parts[3]),
                        'particle_type': parts[4],
                        'sigma': float(parts[5]),
                        'epsilon': float(parts[6]) if len(parts) > 6 else 0.0
                    }
                    atom_types[parts[0]] = atom_type
        return atom_types
    
    def _parse_bondtypes_section(self, content: str) -> Dict:
        """解析bondtypes section"""
        bond_types = {}
        for line in content.split('\n'):
            line = line.strip()
            if line:
                parts = line.split()
                if len(parts) >= 4:
                    key = f"{parts[0]}-{parts[1]}"
                    bond_type = {
                        'atom1': parts[0],
                        'atom2': parts[1],
                        'function_type': int(parts[2]),
                        'parameters': [float(x) for x in parts[3:]]
                    }
                    bond_types[key] = bond_type
        return bond_types
    
    def _parse_angletypes_section(self, content: str) -> Dict:
        """解析angletypes section"""
        angle_types = {}
        for line in content.split('\n'):
            line = line.strip()
            if line:
                parts = line.split()
                if len(parts) >= 5:
                    key = f"{parts[0]}-{parts[1]}-{parts[2]}"
                    angle_type = {
                        'atom1': parts[0],
                        'atom2': parts[1],
                        'atom3': parts[2],
                        'function_type': int(parts[3]),
                        'parameters': [float(x) for x in parts[4:]]
                    }
                    angle_types[key] = angle_type
        return angle_types
    
    def _parse_dihedraltypes_section(self, content: str) -> Dict:
        """解析dihedraltypes section"""
        dihedral_types = {}
        for line in content.split('\n'):
            line = line.strip()
            if line:
                parts = line.split()
                if len(parts) >= 6:
                    key = f"{parts[0]}-{parts[1]}-{parts[2]}-{parts[3]}"
                    dihedral_type = {
                        'atom1': parts[0],
                        'atom2': parts[1],
                        'atom3': parts[2],
                        'atom4': parts[3],
                        'function_type': int(parts[4]),
                        'parameters': [float(x) for x in parts[5:]]
                    }
                    dihedral_types[key] = dihedral_type
        return dihedral_types
    
    def _extract_bond_types_from_bonds(self, molecule_data: Dict, global_force_field: Dict):
        """从具体的bonds中提取bond types"""
        if 'bonds' not in molecule_data or 'atoms' not in molecule_data:
            return
        
        # 创建原子索引到类型的映射
        atom_type_map = {}
        for atom in molecule_data['atoms']:
            atom_type_map[atom['index']] = atom['type']
        
        # 处理每个键
        for bond in molecule_data['bonds']:
            atom1_idx = bond['atom1']
            atom2_idx = bond['atom2']
            
            if atom1_idx in atom_type_map and atom2_idx in atom_type_map:
                atom1_type = atom_type_map[atom1_idx]
                atom2_type = atom_type_map[atom2_idx]
                
                # 创建键类型名称（按字母顺序排序以保证一致性）
                if atom1_type <= atom2_type:
                    bond_type_name = f"{atom1_type}-{atom2_type}"
                else:
                    bond_type_name = f"{atom2_type}-{atom1_type}"
                
                # 如果该键类型还没有记录，则添加
                if bond_type_name not in global_force_field['bond_types']:
                    global_force_field['bond_types'][bond_type_name] = {
                        'atom1': atom1_type,
                        'atom2': atom2_type,
                        'function_type': bond.get('function_type', 1),
                        'parameters': bond.get('parameters', [])
                    }
                    self.logger.debug(f"提取键类型: {bond_type_name}, 参数: {bond.get('parameters', [])}")
    
    def _extract_angle_types_from_angles(self, molecule_data: Dict, global_force_field: Dict):
        """从具体的angles中提取angle types"""
        if 'angles' not in molecule_data or 'atoms' not in molecule_data:
            return
        
        # 创建原子索引到类型的映射
        atom_type_map = {}
        for atom in molecule_data['atoms']:
            atom_type_map[atom['index']] = atom['type']
        
        # 处理每个角度
        for angle in molecule_data['angles']:
            atom1_idx = angle['atom1']
            atom2_idx = angle['atom2']  # 中心原子
            atom3_idx = angle['atom3']
            
            if all(idx in atom_type_map for idx in [atom1_idx, atom2_idx, atom3_idx]):
                atom1_type = atom_type_map[atom1_idx]
                atom2_type = atom_type_map[atom2_idx]  # 中心原子
                atom3_type = atom_type_map[atom3_idx]
                
                # 创建角度类型名称（中心原子在中间）
                angle_type_name = f"{atom1_type}-{atom2_type}-{atom3_type}"
                
                # 如果该角度类型还没有记录，则添加
                if angle_type_name not in global_force_field['angle_types']:
                    global_force_field['angle_types'][angle_type_name] = {
                        'atom1': atom1_type,
                        'atom2': atom2_type,
                        'atom3': atom3_type,
                        'function_type': angle.get('function_type', 1),
                        'parameters': angle.get('parameters', [])
                    }
                    self.logger.debug(f"提取角度类型: {angle_type_name}, 参数: {angle.get('parameters', [])}")
    
    def _extract_dihedral_types_from_dihedrals(self, molecule_data: Dict, global_force_field: Dict):
        """从具体的dihedrals中提取dihedral types"""
        if 'dihedrals' not in molecule_data or 'atoms' not in molecule_data:
            return
        
        # 创建原子索引到类型的映射
        atom_type_map = {}
        for atom in molecule_data['atoms']:
            atom_type_map[atom['index']] = atom['type']
        
        # 处理每个二面角
        for dihedral in molecule_data['dihedrals']:
            atom1_idx = dihedral['atom1']
            atom2_idx = dihedral['atom2']  # 中心键的原子
            atom3_idx = dihedral['atom3']  # 中心键的原子
            atom4_idx = dihedral['atom4']
            
            if all(idx in atom_type_map for idx in [atom1_idx, atom2_idx, atom3_idx, atom4_idx]):
                atom1_type = atom_type_map[atom1_idx]
                atom2_type = atom_type_map[atom2_idx]
                atom3_type = atom_type_map[atom3_idx]
                atom4_type = atom_type_map[atom4_idx]
                
                # 创建二面角类型名称
                dihedral_type_name = f"{atom1_type}-{atom2_type}-{atom3_type}-{atom4_type}"
                
                # 如果该二面角类型还没有记录，则添加
                if dihedral_type_name not in global_force_field['dihedral_types']:
                    global_force_field['dihedral_types'][dihedral_type_name] = {
                        'atom1': atom1_type,
                        'atom2': atom2_type,
                        'atom3': atom3_type,
                        'atom4': atom4_type,
                        'function_type': dihedral.get('function_type', 1),
                        'parameters': dihedral.get('parameters', [])
                    }
                    self.logger.debug(f"提取二面角类型: {dihedral_type_name}, 参数: {dihedral.get('parameters', [])}")

    def _merge_itp_data(self, system_data: Dict, itp_data: Dict):
        """将ITP数据合并到系统数据中，支持多个分子类型"""
        
        # 处理新格式：包含多个分子的ITP文件
        if 'molecules' in itp_data:
            # 合并所有分子类型
            for mol_name, mol_data in itp_data['molecules'].items():
                system_data['molecules'][mol_name] = mol_data
            
            # 如果系统中还没有全局力场，则添加
            if 'global_force_field' not in system_data:
                system_data['global_force_field'] = {}
            
            # 合并全局力场参数
            if 'global_force_field' in itp_data:
                global_ff = itp_data['global_force_field']
                for ff_type in ['atom_types', 'bond_types', 'angle_types', 'dihedral_types']:
                    if ff_type not in system_data['global_force_field']:
                        system_data['global_force_field'][ff_type] = {}
                    if ff_type in global_ff:
                        system_data['global_force_field'][ff_type].update(global_ff[ff_type])
        
        # 处理旧格式：单个分子的ITP文件
        elif 'name' in itp_data:
            system_data['molecules'][itp_data['name']] = itp_data 