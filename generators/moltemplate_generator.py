# -*- coding: utf-8 -*-
"""
Moltemplate文件生成器
根据解析的GROMACS数据生成.lt文件
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Any
from textwrap import dedent

# 添加父目录到路径以便导入config
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
sys.path.insert(0, str(parent_dir))

try:
    from config import UNIT_CONVERSIONS
except ImportError:
    # 如果无法导入，使用默认值
    UNIT_CONVERSIONS = {
        'length': 10.0,
        'energy': 0.239006,
        'bond_force': 0.239006 * 100,
        'angle_force': 0.239006,
        'sigma': 10.0,
        'epsilon': 0.239006,
        'mass': 1.0,
        'charge': 1.0,
        'angle_degree_to_radian': 3.14159265359 / 180.0,
    }

class MoltemplateGenerator:
    """Moltemplate文件生成器"""
    
    def __init__(self, logger):
        self.logger = logger
        
    def generate_moltemplate_files(self, system_data: Dict, force_field_data: Dict,
                                 output_dir: Path, output_name: str, 
                                 custom_ff: bool = False):
        """生成moltemplate文件"""
        
        # 创建输出目录
        output_dir.mkdir(exist_ok=True)
        
        is_standard_ff = not custom_ff and force_field_data.get('type') == 'standard'
        
        if custom_ff:
            # 生成完整的.lt文件（包含力场定义）
            self._generate_complete_lt_file(system_data, force_field_data, 
                                          output_dir, output_name)
        elif is_standard_ff:
            # 生成使用标准力场的简化.lt文件（只有Bond List）
            self._generate_standard_ff_molecule_files(system_data, force_field_data,
                                                    output_dir, output_name)
        else:
            # 生成使用标准力场的.lt文件
            self._generate_standard_lt_file(system_data, force_field_data,
                                          output_dir, output_name)
        
        # 仅在有系统组成信息时生成系统级别的.lt文件
        if 'system_composition' in system_data and not is_standard_ff:
            self._generate_system_lt_file(system_data, output_dir, output_name)
        
        # 复制或转换坐标文件
        self._handle_coordinate_file(system_data, output_dir, output_name)
        
        # 生成运行脚本
        self._generate_run_script(output_dir, output_name)
        
        self.logger.info("Moltemplate文件生成完成")
    
    def _generate_complete_lt_file(self, system_data: Dict, force_field_data: Dict,
                                 output_dir: Path, output_name: str):
        """生成包含自定义力场的完整.lt文件"""
        
        # 生成共享的力场文件
        force_field_file = self._generate_shared_force_field_file(
            system_data, output_dir, output_name
        )
        
        # 为每个分子生成单独的.lt文件
        for mol_name, mol_data in system_data['molecules'].items():
            lt_file = output_dir / f"{mol_name}.lt"
            
            with open(lt_file, 'w') as f:
                # 写入文件头部
                f.write(self._get_file_header(mol_name, custom_ff=True))
                
                # 导入共享力场文件
                if force_field_file:
                    f.write(f'import "{force_field_file.name}"\n\n')
                
                # 写入分子定义
                f.write(f"{mol_name} inherits ForceField {{\n\n")
                
                # 写入原子
                if 'atoms' in mol_data and mol_data['atoms']:
                    f.write("  # 原子定义\n")
                    self._write_atoms_for_custom_ff(f, mol_data['atoms'])
                
                # 写入键
                if 'bonds' in mol_data and mol_data['bonds']:
                    f.write("\n  # 键定义\n")
                    self._write_bonds_for_custom_ff(f, mol_data['bonds'], mol_data.get('atoms', []))
                
                # 写入角度
                if 'angles' in mol_data and mol_data['angles']:
                    f.write("\n  # 角度定义\n")
                    self._write_angles_for_custom_ff(f, mol_data['angles'], mol_data.get('atoms', []))
                
                # 写入二面角
                if 'dihedrals' in mol_data and mol_data['dihedrals']:
                    f.write("\n  # 二面角定义\n")
                    self._write_dihedrals_for_custom_ff(f, mol_data['dihedrals'], mol_data.get('atoms', []))
                
                f.write("\n}\n")
            
            self.logger.info(f"生成分子.lt文件: {lt_file}")
    
    def _generate_shared_force_field_file(self, system_data: Dict, output_dir: Path, 
                                        output_name: str) -> Path:
        """生成共享的力场文件"""
        
        force_field_file = output_dir / f"{output_name}_forcefield.lt"
        
        # 收集所有力场参数
        global_ff = system_data.get('global_force_field', {})
        
        # 检查是否有力场参数需要写入
        has_ff_params = any(global_ff.get(ff_type) for ff_type in 
                           ['atom_types', 'bond_types', 'angle_types', 'dihedral_types'])
        
        if not has_ff_params:
            self.logger.warning("没有找到力场参数，跳过力场文件生成")
            return None
        
        with open(force_field_file, 'w') as f:
            # 写入力场文件头部
            f.write(self._get_force_field_file_header(output_name))
            
            # 定义力场类
            f.write("ForceField {\n\n")
            
            # 写入原子类型定义
            if global_ff.get('atom_types'):
                f.write("  # 原子类型定义\n")
                self._write_atom_types(f, global_ff['atom_types'], indent="  ")
            
            # 写入键类型定义
            if global_ff.get('bond_types'):
                f.write("\n  # 键类型定义\n")
                self._write_bond_types(f, global_ff['bond_types'], indent="  ")
            
            # 写入角度类型定义
            if global_ff.get('angle_types'):
                f.write("\n  # 角度类型定义\n")
                self._write_angle_types(f, global_ff['angle_types'], indent="  ")
            
            # 写入二面角类型定义
            if global_ff.get('dihedral_types'):
                f.write("\n  # 二面角类型定义\n")
                self._write_dihedral_types(f, global_ff['dihedral_types'], indent="  ")
            
            f.write("\n}\n")
        
        self.logger.info(f"生成共享力场文件: {force_field_file}")
        return force_field_file
    
    def _generate_standard_lt_file(self, system_data: Dict, force_field_data: Dict,
                                 output_dir: Path, output_name: str):
        """生成使用标准力场的.lt文件"""
        
        force_field_name = force_field_data.get('name', 'gaff2')
        
        for mol_name, mol_data in system_data['molecules'].items():
            lt_file = output_dir / f"{mol_name}.lt"
            
            with open(lt_file, 'w') as f:
                # 写入文件头部
                f.write(self._get_file_header(mol_name, custom_ff=False))
                
                # 导入标准力场
                f.write(f'import "{force_field_name}.lt"\n\n')
                
                # 写入分子定义
                f.write(f"{mol_name} inherits {force_field_name.upper()} {{\n\n")
                
                # 写入原子（仅包含坐标和类型）
                if 'atoms' in mol_data:
                    f.write("  # 原子定义\n")
                    self._write_atoms_for_standard_ff(f, mol_data['atoms'])
                
                # 写入键（引用力场中的类型）
                if 'bonds' in mol_data:
                    f.write("\n  # 键定义\n")
                    self._write_bonds_for_standard_ff(f, mol_data['bonds'])
                
                # 写入角度
                if 'angles' in mol_data:
                    f.write("\n  # 角度定义\n")
                    self._write_angles_for_standard_ff(f, mol_data['angles'])
                
                # 写入二面角
                if 'dihedrals' in mol_data:
                    f.write("\n  # 二面角定义\n")
                    self._write_dihedrals_for_standard_ff(f, mol_data['dihedrals'])
                
                f.write("\n}\n")
            
            self.logger.info(f"生成标准力场.lt文件: {lt_file}")
    
    def _generate_system_lt_file(self, system_data: Dict, output_dir: Path, 
                               output_name: str):
        """生成系统级别的.lt文件（标准moltemplate格式）"""
        
        system_file = output_dir / f"{output_name}.lt"
        
        with open(system_file, 'w') as f:
            # 写入文件头部
            f.write(self._get_system_file_header(output_name))
            
            # 导入力场文件（如果存在）
            force_field_file = output_dir / f"{output_name}_forcefield.lt"
            if force_field_file.exists():
                f.write(f'import "{force_field_file.name}"\n')
            
            # 导入分子定义
            for mol_name in system_data['molecules'].keys():
                f.write(f'import "{mol_name}.lt"  # <- defines the "{mol_name}" molecule type\n')
            
            # 写入盒子尺寸（在分子实例化之前）
            if 'box_vectors' in system_data and system_data['box_vectors']:
                box = system_data['box_vectors']
                f.write("\n# Periodic boundary conditions:\n")
                f.write("write_once(\"Data Boundary\") {\n")
                f.write(f"   0.0  {box[0]:.2f}  xlo xhi\n")
                f.write(f"   0.0  {box[1]:.2f}  ylo yhi\n")
                f.write(f"   0.0  {box[2]:.2f}  zlo zhi\n")
                f.write("}\n\n")
            
            # 添加说明注释
            f.write("# NOTE: The order that you instantiate the molecules should match the order\n")
            f.write("#       that they appear in the coordinate file.\n")
            f.write("#       Molecule counts are read from the GROMACS topology file.\n\n")
            
            # 写入分子实例（标准moltemplate格式）
            if 'system_composition' in system_data:
                self.logger.info("使用TOP文件中的分子组成信息")
                
                for mol_name, mol_count in system_data['system_composition']:
                    # 检查分子是否在我们解析的分子列表中
                    if mol_name in system_data['molecules']:
                        # 使用标准moltemplate格式：molecules = new MoleculeType [count]
                        var_name = mol_name.lower() + 's' if not mol_name.lower().endswith('s') else mol_name.lower()
                        f.write(f"# Create {mol_count} \"{mol_name}\" molecules\n")
                        f.write(f"{var_name} = new {mol_name} [{mol_count}]\n\n")
                    else:
                        # 对于未解析的分子类型，添加注释
                        self.logger.warning(f"分子 {mol_name} 未在ITP文件中定义，但仍包含在系统中")
                        var_name = mol_name.lower() + 's' if not mol_name.lower().endswith('s') else mol_name.lower()
                        f.write(f"# {mol_name} molecules ({mol_count} total) - definition missing\n")
                        f.write(f"# {var_name} = new {mol_name} [{mol_count}]  # <- requires {mol_name}.lt file\n\n")
        
        self.logger.info(f"生成系统.lt文件: {system_file}")
    
    def _handle_coordinate_file(self, system_data: Dict, output_dir: Path, 
                              output_name: str):
        """处理坐标文件"""
        
        # 生成xyz格式的坐标文件供moltemplate使用
        xyz_file = output_dir / f"{output_name}.xyz"
        
        coordinates = system_data.get('coordinates', [])
        
        with open(xyz_file, 'w') as f:
            f.write(f"{len(coordinates)}\n")
            f.write(f"Generated from GROMACS files\n")
            
            for atom in coordinates:
                # 简化原子类型名称
                atom_type = atom.name
                f.write(f"{atom_type} {atom.x:.6f} {atom.y:.6f} {atom.z:.6f}\n")
        
        self.logger.info(f"生成坐标文件: {xyz_file}")
    
    def _generate_run_script(self, output_dir: Path, output_name: str):
        """生成运行脚本"""
        
        # 生成moltemplate运行脚本
        script_file = output_dir / "run_moltemplate.sh"
        
        with open(script_file, 'w') as f:
            f.write("#!/bin/bash\n")
            f.write("# Moltemplate 运行脚本\n\n")
            f.write("# 清理之前的输出文件\n")
            f.write("rm -f system.data system.in* system.settings\n\n")
            f.write("# 运行 moltemplate\n")
            f.write(f"moltemplate.sh {output_name}.lt\n\n")
            f.write("# 检查输出文件\n")
            f.write("if [ -f system.data ]; then\n")
            f.write("    echo '成功生成 LAMMPS 数据文件: system.data'\n")
            f.write("    echo '输入脚本文件: system.in*'\n")
            f.write("    echo '设置文件: system.settings'\n")
            f.write("else\n")
            f.write("    echo '错误: moltemplate 运行失败'\n")
            f.write("    exit 1\n")
            f.write("fi\n")
        
        # 设置执行权限
        os.chmod(script_file, 0o755)
        
        # 生成Python运行脚本
        py_script_file = output_dir / "run_moltemplate.py"
        
        with open(py_script_file, 'w') as f:
            f.write(dedent(f"""
            #!/usr/bin/env python3
            # -*- coding: utf-8 -*-
            \"\"\"
            Moltemplate 运行脚本 (Python版本)
            \"\"\"
            
            import subprocess
            import sys
            import os
            from pathlib import Path
            
            def run_moltemplate():
                \"\"\"运行moltemplate\"\"\"
                
                # 检查moltemplate是否安装
                try:
                    result = subprocess.run(['moltemplate.sh', '--version'], 
                                          capture_output=True, text=True)
                except FileNotFoundError:
                    print("错误: 未找到 moltemplate.sh")
                    print("请确保已安装 moltemplate 并且在 PATH 中")
                    return False
                
                # 清理之前的输出文件
                cleanup_files = ['system.data', 'system.in*', 'system.settings']
                for pattern in cleanup_files:
                    os.system(f'rm -f {{pattern}}')
                
                # 运行moltemplate
                print(f"运行 moltemplate.sh {output_name}.lt ...")
                result = subprocess.run(['moltemplate.sh', f'{output_name}.lt'],
                                      capture_output=True, text=True)
                
                if result.returncode == 0:
                    print("成功生成 LAMMPS 文件:")
                    if os.path.exists('system.data'):
                        print("  - system.data (数据文件)")
                    
                    in_files = list(Path('.').glob('system.in*'))
                    for in_file in in_files:
                        print(f"  - {{in_file}} (输入脚本)")
                    
                    if os.path.exists('system.settings'):
                        print("  - system.settings (设置文件)")
                    
                    return True
                else:
                    print("错误: moltemplate 运行失败")
                    print("标准输出:", result.stdout)
                    print("错误输出:", result.stderr)
                    return False
            
            if __name__ == "__main__":
                success = run_moltemplate()
                sys.exit(0 if success else 1)
            """).strip())
        
        # 设置执行权限
        os.chmod(py_script_file, 0o755)
        
        self.logger.info(f"生成运行脚本: {script_file}, {py_script_file}")
    
    def _get_file_header(self, mol_name: str, custom_ff: bool = False) -> str:
        """获取.lt文件头部"""
        ff_type = "自定义力场" if custom_ff else "标准力场"
        
        return dedent(f"""
        # Moltemplate文件: {mol_name}.lt
        # 由 GROMACS 到 LAMMPS 转换工具生成
        # 力场类型: {ff_type}
        # 
        # 使用方法:
        #   moltemplate.sh system.lt
        
        """).strip() + "\n\n"
    
    def _get_system_file_header(self, system_name: str) -> str:
        """获取系统.lt文件头部"""
        
        return dedent(f"""
        # Moltemplate系统文件: {system_name}.lt
        # 由 GROMACS 到 LAMMPS 转换工具生成
        # 
        # 此文件定义了完整的分子动力学系统
        # 包含所有分子类型和系统组成
        
        """).strip() + "\n\n"
    
    def _get_force_field_file_header(self, system_name: str) -> str:
        """获取力场.lt文件头部"""
        
        return dedent(f"""
        # Moltemplate力场文件: {system_name}_forcefield.lt
        # 由 GROMACS 到 LAMMPS 转换工具生成
        # 
        # 此文件包含从GROMACS文件提取的力场参数
        # 可被多个分子文件共享使用
        
        """).strip() + "\n\n"
    
    def _write_atom_types(self, f, atom_types: Dict, indent: str = ""):
        """写入原子类型定义，应用单位转换"""
        f.write(f"{indent}write_once(\"In Settings\") {{\n")
        
        for atom_type, data in atom_types.items():
            mass = data.get('mass', 1.0) * UNIT_CONVERSIONS['mass']
            f.write(f"{indent}  mass {atom_type} {mass:.6f}\n")
        
        f.write(f"{indent}}}\n\n")
        
        f.write(f"{indent}write_once(\"In Settings\") {{\n")
        for atom_type, data in atom_types.items():
            # 应用单位转换：nm -> Angstrom, kJ/mol -> kcal/mol
            sigma = data.get('sigma', 0.0) * UNIT_CONVERSIONS['sigma']
            epsilon = data.get('epsilon', 0.0) * UNIT_CONVERSIONS['epsilon']
            f.write(f"{indent}  pair_coeff {atom_type} {atom_type} {epsilon:.6f} {sigma:.6f}\n")
        
        f.write(f"{indent}}}\n")
    
    def _write_bond_types(self, f, bond_types: Dict, indent: str = ""):
        """写入键类型定义，应用单位转换"""
        f.write(f"{indent}write_once(\"In Settings\") {{\n")
        
        for bond_key, data in bond_types.items():
            atom1, atom2 = data['atom1'], data['atom2']
            params = data.get('parameters', [])
            if len(params) >= 2:
                # 应用单位转换：kJ/mol/nm² -> kcal/mol/Å², nm -> Angstrom
                r0 = params[0] * UNIT_CONVERSIONS['length']          # 平衡键长 (nm -> Å)
                k_bond = params[1] * UNIT_CONVERSIONS['bond_force']  # 力常数 (kJ/mol/nm² -> kcal/mol/Å²)
                bond_type = f"{atom1}-{atom2}"
                f.write(f"{indent}  bond_coeff @bond:{bond_type} {k_bond:.6f} {r0:.6f}\n")
        
        f.write(f"{indent}}}\n")
    
    def _write_angle_types(self, f, angle_types: Dict, indent: str = ""):
        """写入角度类型定义，应用单位转换"""
        f.write(f"{indent}write_once(\"In Settings\") {{\n")
        
        for angle_key, data in angle_types.items():
            atom1, atom2, atom3 = data['atom1'], data['atom2'], data['atom3']
            params = data.get('parameters', [])
            if len(params) >= 2:
                # 应用单位转换：kJ/mol/rad² -> kcal/mol/rad²
                k_angle = params[0] * UNIT_CONVERSIONS['angle_force']  # 力常数
                theta0 = params[1]   # 平衡角度 (度，moltemplate中仍然使用度)
                angle_type = f"{atom1}-{atom2}-{atom3}"
                f.write(f"{indent}  angle_coeff @angle:{angle_type} {k_angle:.6f} {theta0:.6f}\n")
        
        f.write(f"{indent}}}\n")
    
    def _write_dihedral_types(self, f, dihedral_types: Dict, indent: str = ""):
        """写入二面角类型定义，应用单位转换"""
        f.write(f"{indent}write_once(\"In Settings\") {{\n")
        
        for dihedral_key, data in dihedral_types.items():
            atoms = [data['atom1'], data['atom2'], data['atom3'], data['atom4']]
            params = data.get('parameters', [])
            if len(params) >= 3:
                # 应用单位转换：kJ/mol -> kcal/mol
                k_dihedral = params[0] * UNIT_CONVERSIONS['energy']  # 力常数
                multiplicity = int(params[1])  # 重数
                phase = params[2]       # 相位角 (度)
                dihedral_type = f"{atoms[0]}-{atoms[1]}-{atoms[2]}-{atoms[3]}"
                f.write(f"{indent}  dihedral_coeff @dihedral:{dihedral_type} {k_dihedral:.6f} {multiplicity} {phase:.6f}\n")
        
        f.write(f"{indent}}}\n")
    
    def _write_atoms(self, f, atoms: List[Dict]):
        """写入原子定义（自定义力场）"""
        f.write("  write(\"Data Atoms\") {\n")
        
        for atom in atoms:
            atom_id = atom['index']
            atom_type = atom['type']
            charge = atom.get('charge', 0.0)
            # 坐标会从坐标文件中读取
            f.write(f"    ${atom_id} 1 {atom_type} {charge:.6f} 0.0 0.0 0.0\n")
        
        f.write("  }\n")
    
    def _write_atoms_for_standard_ff(self, f, atoms: List[Dict]):
        """写入原子定义（标准力场）"""
        f.write("  write(\"Data Atoms\") {\n")
        
        for atom in atoms:
            atom_id = atom['index']
            atom_type = f"@atom:{atom['type']}"  # 使用力场中定义的原子类型
            charge = atom.get('charge', 0.0)
            f.write(f"    ${atom_id} $mol:{atom_type} {charge:.6f} 0.0 0.0 0.0\n")
        
        f.write("  }\n")
    
    def _write_bonds(self, f, bonds: List[Dict]):
        """写入键定义（自定义力场）"""
        f.write("  write(\"Data Bonds\") {\n")
        
        for i, bond in enumerate(bonds, 1):
            atom1 = bond['atom1']
            atom2 = bond['atom2']
            bond_type = f"bond_{atom1}_{atom2}"  # 简化的键类型名
            f.write(f"    ${i} {bond_type} ${atom1} ${atom2}\n")
        
        f.write("  }\n")
    
    def _write_bonds_for_standard_ff(self, f, bonds: List[Dict]):
        """写入键定义（标准力场）"""
        f.write("  write(\"Data Bonds\") {\n")
        
        for i, bond in enumerate(bonds, 1):
            atom1 = bond['atom1']
            atom2 = bond['atom2']
            f.write(f"    ${i} @bond:type1 ${atom1} ${atom2}\n")  # 使用通用键类型
        
        f.write("  }\n")
    
    def _write_angles(self, f, angles: List[Dict]):
        """写入角度定义"""
        f.write("  write(\"Data Angles\") {\n")
        
        for i, angle in enumerate(angles, 1):
            atom1 = angle['atom1']
            atom2 = angle['atom2']
            atom3 = angle['atom3']
            f.write(f"    ${i} @angle:type1 ${atom1} ${atom2} ${atom3}\n")
        
        f.write("  }\n")
    
    def _write_angles_for_standard_ff(self, f, angles: List[Dict]):
        """写入角度定义（标准力场）"""
        self._write_angles(f, angles)  # 使用相同的格式
    
    def _write_dihedrals(self, f, dihedrals: List[Dict]):
        """写入二面角定义"""
        f.write("  write(\"Data Dihedrals\") {\n")
        
        for i, dihedral in enumerate(dihedrals, 1):
            atom1 = dihedral['atom1']
            atom2 = dihedral['atom2']
            atom3 = dihedral['atom3']
            atom4 = dihedral['atom4']
            f.write(f"    ${i} @dihedral:type1 ${atom1} ${atom2} ${atom3} ${atom4}\n")
        
        f.write("  }\n")
    
    def _write_dihedrals_for_standard_ff(self, f, dihedrals: List[Dict]):
        """写入二面角定义（标准力场）"""
        self._write_dihedrals(f, dihedrals)  # 使用相同的格式
    
    def _write_atoms_for_custom_ff(self, f, atoms: List[Dict]):
        """写入原子定义（自定义力场，继承ForceField）"""
        f.write("  write(\"Data Atoms\") {\n")
        
        for atom in atoms:
            atom_name = atom.get('name', f"{atom['type']}{atom['index']}")
            atom_type = f"@atom:{atom['type']}"  # 引用ForceField中的原子类型
            charge = atom.get('charge', 0.0) * UNIT_CONVERSIONS['charge']
            # 坐标会从坐标文件中读取，使用正确的格式
            f.write(f"    $atom:{atom_name} $mol:. {atom_type} {charge:.3f} 0.0 0.0 0.0\n")
        
        f.write("  }\n")
    
    def _write_bonds_for_custom_ff(self, f, bonds: List[Dict], atoms: List[Dict]):
        """写入键定义（自定义力场，继承ForceField）"""
        f.write("  write(\"Data Bonds\") {\n")
        
        # 创建原子索引到名称的映射
        atom_name_map = {}
        for atom in atoms:
            atom_name_map[atom['index']] = atom.get('name', f"{atom['type']}{atom['index']}")
        
        for i, bond in enumerate(bonds, 1):
            atom1_idx = bond['atom1']
            atom2_idx = bond['atom2']
            atom1_name = atom_name_map.get(atom1_idx, f"atom{atom1_idx}")
            atom2_name = atom_name_map.get(atom2_idx, f"atom{atom2_idx}")
            
            # 根据原子类型创建键类型名称
            atom1_type = None
            atom2_type = None
            for atom in atoms:
                if atom['index'] == atom1_idx:
                    atom1_type = atom['type']
                elif atom['index'] == atom2_idx:
                    atom2_type = atom['type']
            
            if atom1_type and atom2_type:
                bond_type = f"{atom1_type}-{atom2_type}"
                bond_name = f"bond{i}"
                f.write(f"    $bond:{bond_name} @bond:{bond_type} $atom:{atom1_name} $atom:{atom2_name}\n")
        
        f.write("  }\n")
    
    def _write_angles_for_custom_ff(self, f, angles: List[Dict], atoms: List[Dict]):
        """写入角度定义（自定义力场，继承ForceField）"""
        if not angles:
            return
            
        f.write("  write(\"Data Angles\") {\n")
        
        # 创建原子索引到名称和类型的映射
        atom_info_map = {}
        for atom in atoms:
            atom_info_map[atom['index']] = {
                'name': atom.get('name', f"{atom['type']}{atom['index']}"),
                'type': atom['type']
            }
        
        for i, angle in enumerate(angles, 1):
            atom1_idx = angle['atom1']
            atom2_idx = angle['atom2']
            atom3_idx = angle['atom3']
            
            atom1_info = atom_info_map.get(atom1_idx, {'name': f'atom{atom1_idx}', 'type': 'UNK'})
            atom2_info = atom_info_map.get(atom2_idx, {'name': f'atom{atom2_idx}', 'type': 'UNK'})
            atom3_info = atom_info_map.get(atom3_idx, {'name': f'atom{atom3_idx}', 'type': 'UNK'})
            
            angle_type = f"{atom1_info['type']}-{atom2_info['type']}-{atom3_info['type']}"
            angle_name = f"angle{i}"
            f.write(f"    $angle:{angle_name} @angle:{angle_type} $atom:{atom1_info['name']} $atom:{atom2_info['name']} $atom:{atom3_info['name']}\n")
        
        f.write("  }\n")
    
    def _write_dihedrals_for_custom_ff(self, f, dihedrals: List[Dict], atoms: List[Dict]):
        """写入二面角定义（自定义力场，继承ForceField）"""
        if not dihedrals:
            return
            
        f.write("  write(\"Data Dihedrals\") {\n")
        
        # 创建原子索引到名称和类型的映射
        atom_info_map = {}
        for atom in atoms:
            atom_info_map[atom['index']] = {
                'name': atom.get('name', f"{atom['type']}{atom['index']}"),
                'type': atom['type']
            }
        
        for i, dihedral in enumerate(dihedrals, 1):
            atom1_idx = dihedral['atom1']
            atom2_idx = dihedral['atom2']
            atom3_idx = dihedral['atom3']
            atom4_idx = dihedral['atom4']
            
            atom1_info = atom_info_map.get(atom1_idx, {'name': f'atom{atom1_idx}', 'type': 'UNK'})
            atom2_info = atom_info_map.get(atom2_idx, {'name': f'atom{atom2_idx}', 'type': 'UNK'})
            atom3_info = atom_info_map.get(atom3_idx, {'name': f'atom{atom3_idx}', 'type': 'UNK'})
            atom4_info = atom_info_map.get(atom4_idx, {'name': f'atom{atom4_idx}', 'type': 'UNK'})
            
            dihedral_type = f"{atom1_info['type']}-{atom2_info['type']}-{atom3_info['type']}-{atom4_info['type']}"
            dihedral_name = f"dihedral{i}"
            f.write(f"    $dihedral:{dihedral_name} @dihedral:{dihedral_type} $atom:{atom1_info['name']} $atom:{atom2_info['name']} $atom:{atom3_info['name']} $atom:{atom4_info['name']}\n")
        
        f.write("  }\n")
    
    def _generate_standard_ff_molecule_files(self, system_data: Dict, force_field_data: Dict,
                                           output_dir: Path, output_name: str):
        """生成使用标准力场的简化分子文件（只包含Bond List）"""
        
        force_field_name = force_field_data.get('name', 'gaff2')
        force_field_file = force_field_data.get('file', f'{force_field_name}.lt')
        force_field_class = force_field_name.upper()
        
        for mol_name, mol_data in system_data['molecules'].items():
            lt_file = output_dir / f"{mol_name}.lt"
            
            with open(lt_file, 'w') as f:
                # 写入文件头部
                f.write(f"# Moltemplate file for '{mol_name}' generated from .itp and .xyz files.\n\n")
                
                # 导入标准力场
                f.write(f'import "{force_field_file}"\n\n')
                
                # 写入分子定义
                f.write(f"{mol_name} inherits {force_field_class} {{\n\n")
                
                # 添加special_bonds设置（对GAFF等力场很重要）
                f.write("  special_bonds lj/coul 0.0 0.0 0.5\n\n")
                
                # 写入原子定义
                if 'atoms' in mol_data and mol_data['atoms']:
                    f.write('  write("Data Atoms") {\n')
                    self._write_atoms_for_standard_ff_simple(f, mol_data['atoms'])
                    f.write("  }\n\n")
                
                # 写入键列表（Bond List）
                if 'bonds' in mol_data and mol_data['bonds']:
                    f.write('  write("Data Bond List") {\n')
                    self._write_bond_list_for_standard_ff(f, mol_data['bonds'], mol_data.get('atoms', []))
                    f.write("  }\n\n")
                
                f.write("} # end of molecule definition\n")
            
            self.logger.info(f"生成标准力场分子文件: {lt_file}")
    
    def _write_atoms_for_standard_ff_simple(self, f, atoms):
        """为标准力场写入原子定义（简化格式）"""
        
        for atom in atoms:
            # 生成有意义的原子名称
            atom_name = atom.get('atom_name', atom.get('name', f"{atom['type']}{atom['index']}"))
            atom_type = atom['type']
            charge = atom.get('charge', 0.0)
            
            # 从坐标信息获取位置（如果有的话）
            x = atom.get('x', 0.0) * UNIT_CONVERSIONS['length']  # nm to Angstrom
            y = atom.get('y', 0.0) * UNIT_CONVERSIONS['length']
            z = atom.get('z', 0.0) * UNIT_CONVERSIONS['length']
            
            f.write(f"    $atom:{atom_name} $mol:. @atom:{atom_type} {charge:.8f} {x:.4f} {y:.4f} {z:.4f}\n")
    
    def _write_bond_list_for_standard_ff(self, f, bonds, atoms):
        """为标准力场写入键列表"""
        
        # 创建原子索引到名称的映射
        atom_name_map = {}
        for atom in atoms:
            atom_name = atom.get('atom_name', atom.get('name', f"{atom['type']}{atom['index']}"))
            atom_name_map[atom['index']] = atom_name
        
        for i, bond in enumerate(bonds, 1):
            atom1_idx = bond['atom1']
            atom2_idx = bond['atom2']
            
            atom1_name = atom_name_map.get(atom1_idx, f'atom{atom1_idx}')
            atom2_name = atom_name_map.get(atom2_idx, f'atom{atom2_idx}')
            
            f.write(f"    $bond:b{i} $atom:{atom1_name} $atom:{atom2_name}\n") 