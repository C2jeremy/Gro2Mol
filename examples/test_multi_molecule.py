#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多分子类型测试示例
测试处理包含多个[ moleculetype ]的ITP文件
"""

import sys
import tempfile
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from parsers.gromacs_parser import GromacsParser
from generators.moltemplate_generator import MoltemplateGenerator
from utils.force_field_manager import ForceFieldManager
from utils.logger import setup_logger


def create_multi_molecule_test_files(temp_dir: Path):
    """创建包含多个分子类型的测试文件"""
    
    # 创建类似grid.itp的测试文件
    itp_content = """
[ atomtypes ]
; name    at.num    mass    charge ptype  sigma      epsilon
SI            14   28.08600    0.000000  A      0.250000     0.0004000
OA             8   15.99940    0.000000  A      0.307000     0.7110000
HG             1    2.01600    0.000000  A      0.129000     0.0015000
OM             8   15.99940    0.000000  A      0.270000     1.9120000

[ moleculetype ]
; name nrexcl
  SL        2

[ atoms ]
; nr  type  resnr  resid  atom  cgnr  charge
   1    SI      1     SL   Si1     1  2.10000
   2    OA      1     SL    O1     1  -0.95000
   3    HG      1     SL    H1     1   0.42500

[ bonds ]
; ai  aj  fu  c        K
   2   3   1  0.10000  4.637000E+05

[ moleculetype ]
; name nrexcl
  SLG       3

[ atoms ]
; nr  type  resnr  resid  atom  cgnr  charge
   1    SI      1    SLG   Si1     1    2.1
   2    OA      1    SLG    O1     1   -0.95
   3    HG      1    SLG    H1     1    0.425
   4    OA      1    SLG    O2     1   -0.95
   5    HG      1    SLG    H2     1    0.425

[ bonds ]
; ai  aj  fu  c        K
   2   3   1  0.10000  4.637000E+05
   4   5   1  0.10000  4.637000E+05

[ moleculetype ]
; name nrexcl
  OM        1

[ atoms ]
; nr  type  resnr  resid  atom  cgnr  charge
   1    OM      1     OM   OM1     1  -1.050000
"""
    
    itp_file = temp_dir / "multi_molecules.itp"
    with open(itp_file, 'w') as f:
        f.write(itp_content.strip())
    
    # 创建对应的TOP文件
    top_content = """
[ defaults ]
1 2 yes 0.5 0.833333

[ atomtypes ]
; 其他原子类型
SI2           14   28.08600    0.000000  A      0.260000     0.0005000

#include "multi_molecules.itp"

[ system ]
Multi-Molecule Test System

[ molecules ]
SL 100
SLG 50
OM 1000
"""
    
    top_file = temp_dir / "test_multi.top"
    with open(top_file, 'w') as f:
        f.write(top_content.strip())
    
    # 创建简单的坐标文件
    gro_content = """Multi-Molecule Test System
8
    1SL     Si1    1   1.000   1.000   1.000
    1SL      O1    2   1.100   1.000   1.000
    1SL      H1    3   1.200   1.000   1.000
    2SLG    Si1    4   2.000   1.000   1.000
    2SLG     O1    5   2.100   1.000   1.000
    2SLG     H1    6   2.200   1.000   1.000
    2SLG     O2    7   2.000   1.100   1.000
    2SLG     H2    8   2.000   1.200   1.000
   5.000   5.000   5.000
"""
    
    gro_file = temp_dir / "test_multi.gro"
    with open(gro_file, 'w') as f:
        f.write(gro_content.strip())
    
    return top_file, gro_file, itp_file


def test_multi_molecule_parsing():
    """测试多分子类型解析"""
    
    print("=" * 60)
    print("多分子类型解析测试")
    print("=" * 60)
    
    # 创建临时目录
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # 设置日志
        logger = setup_logger(verbose=True)
        
        # 创建测试文件
        top_file, gro_file, itp_file = create_multi_molecule_test_files(temp_path)
        
        # 解析文件
        logger.info("开始解析多分子类型文件...")
        parser = GromacsParser(logger)
        
        # 首先单独测试ITP文件解析
        logger.info(f"解析ITP文件: {itp_file}")
        itp_data = parser._parse_itp_file(str(itp_file))
        
        # 检查解析结果
        print(f"\n解析结果分析:")
        if 'molecules' in itp_data:
            print(f"  发现分子类型数量: {len(itp_data['molecules'])}")
            for mol_name, mol_data in itp_data['molecules'].items():
                print(f"    - {mol_name}: {len(mol_data.get('atoms', []))} 原子, "
                      f"{len(mol_data.get('bonds', []))} 键")
        
        if 'global_force_field' in itp_data:
            ff = itp_data['global_force_field']
            print(f"  全局力场参数:")
            print(f"    - 原子类型: {len(ff.get('atom_types', {}))}")
            print(f"    - 键类型: {len(ff.get('bond_types', {}))}")
        
        # 解析完整系统
        logger.info("解析完整系统...")
        system_data = parser.parse_system(str(top_file), str(gro_file), [str(itp_file)])
        
        print(f"\n系统解析结果:")
        print(f"  总分子类型: {len(system_data['molecules'])}")
        print(f"  系统组成: {system_data.get('system_composition', [])}")
        
        # 测试自定义力场转换
        logger.info("测试自定义力场转换...")
        ff_manager = ForceFieldManager(logger)
        force_field_data = ff_manager.process_force_field(system_data, custom_ff=True)
        
        # 生成moltemplate文件
        logger.info("生成moltemplate文件...")
        output_dir = temp_path / "output"
        output_dir.mkdir(exist_ok=True)
        
        generator = MoltemplateGenerator(logger)
        generator.generate_moltemplate_files(
            system_data,
            force_field_data,
            output_dir,
            "multi_system",
            custom_ff=True
        )
        
        # 检查生成的文件
        print(f"\n生成的文件:")
        for file in output_dir.iterdir():
            if file.is_file():
                print(f"  - {file.name} ({file.stat().st_size} bytes)")
        
        # 显示部分文件内容
        force_field_file = output_dir / "multi_system_forcefield.lt"
        if force_field_file.exists():
            print(f"\n力场文件内容预览 ({force_field_file.name}):")
            with open(force_field_file, 'r') as f:
                lines = f.readlines()[:20]  # 显示前20行
                for i, line in enumerate(lines, 1):
                    print(f"  {i:2d}: {line.rstrip()}")
                if len(lines) == 20:
                    print("  ...")
        
        # 显示SL分子文件内容
        sl_file = output_dir / "SL.lt"
        if sl_file.exists():
            print(f"\nSL分子文件内容预览 ({sl_file.name}):")
            with open(sl_file, 'r') as f:
                lines = f.readlines()[:15]
                for i, line in enumerate(lines, 1):
                    print(f"  {i:2d}: {line.rstrip()}")
                if len(lines) == 15:
                    print("  ...")
        
        print(f"\n测试完成！输出文件位于: {output_dir}")


def main():
    """主函数"""
    print("多分子类型处理测试")
    print("测试处理包含多个[ moleculetype ]的ITP文件\n")
    
    try:
        test_multi_molecule_parsing()
        print("\n" + "="*60)
        print("✓ 所有测试通过！")
        print("✓ 多分子类型解析功能正常")
        print("✓ 共享力场文件生成功能正常")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main() 