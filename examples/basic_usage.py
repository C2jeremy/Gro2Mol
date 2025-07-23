#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基本使用示例
演示如何使用GROMACS到LAMMPS转换工具
"""

import sys
import os
from pathlib import Path

# 添加父目录到路径，以便导入模块
sys.path.insert(0, str(Path(__file__).parent.parent))

from parsers.gromacs_parser import GromacsParser
from generators.moltemplate_generator import MoltemplateGenerator
from utils.force_field_manager import ForceFieldManager
from utils.logger import setup_logger


def example_standard_force_field():
    """示例：使用标准力场进行转换"""
    
    print("=" * 60)
    print("示例1: 使用标准力场(GAFF2)进行转换")
    print("=" * 60)
    
    # 设置日志
    logger = setup_logger(verbose=True)
    
    # 示例文件路径（需要根据实际情况修改）
    top_file = "examples/data/system.top"
    gro_file = "examples/data/system.gro"
    output_dir = Path("examples/output/standard_ff")
    
    try:
        # 检查输入文件是否存在
        if not os.path.exists(top_file):
            logger.warning(f"示例文件不存在: {top_file}")
            logger.info("请准备相应的GROMACS文件进行测试")
            return
        
        # 创建输出目录
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 解析GROMACS文件
        logger.info("开始解析GROMACS文件...")
        parser = GromacsParser(logger)
        system_data = parser.parse_system(top_file, gro_file)
        
        # 处理标准力场
        logger.info("处理标准力场...")
        ff_manager = ForceFieldManager(logger)
        force_field_data = ff_manager.process_force_field(
            system_data, 
            force_field="gaff2",
            custom_ff=False
        )
        
        # 生成moltemplate文件
        logger.info("生成moltemplate文件...")
        generator = MoltemplateGenerator(logger)
        generator.generate_moltemplate_files(
            system_data,
            force_field_data,
            output_dir,
            "system",
            custom_ff=False
        )
        
        logger.info(f"转换完成！输出文件位于: {output_dir}")
        
    except Exception as e:
        logger.error(f"转换失败: {e}")


def example_custom_force_field():
    """示例：使用自定义力场进行转换"""
    
    print("\n" + "=" * 60)
    print("示例2: 使用自定义力场进行转换")
    print("=" * 60)
    
    # 设置日志
    logger = setup_logger(verbose=True)
    
    # 示例文件路径
    top_file = "examples/data/system.top"
    gro_file = "examples/data/system.gro"
    itp_files = ["examples/data/molecule.itp"]
    output_dir = Path("examples/output/custom_ff")
    
    try:
        # 检查输入文件
        if not os.path.exists(top_file):
            logger.warning(f"示例文件不存在: {top_file}")
            logger.info("请准备相应的GROMACS文件进行测试")
            return
        
        # 创建输出目录
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 解析GROMACS文件
        logger.info("开始解析GROMACS文件...")
        parser = GromacsParser(logger)
        system_data = parser.parse_system(top_file, gro_file, itp_files)
        
        # 处理自定义力场
        logger.info("处理自定义力场...")
        ff_manager = ForceFieldManager(logger)
        force_field_data = ff_manager.process_force_field(
            system_data,
            custom_ff=True
        )
        
        # 验证力场兼容性
        is_compatible = ff_manager.validate_force_field_compatibility(
            system_data, force_field_data
        )
        
        if not is_compatible:
            logger.warning("力场兼容性验证失败，但继续转换...")
        
        # 生成moltemplate文件
        logger.info("生成moltemplate文件...")
        generator = MoltemplateGenerator(logger)
        generator.generate_moltemplate_files(
            system_data,
            force_field_data,
            output_dir,
            "system",
            custom_ff=True
        )
        
        # 生成力场信息
        ff_manager.generate_force_field_info(output_dir, force_field_data)
        
        logger.info(f"转换完成！输出文件位于: {output_dir}")
        
    except Exception as e:
        logger.error(f"转换失败: {e}")


def create_example_data():
    """创建示例数据文件"""
    
    print("\n" + "=" * 60)
    print("创建示例数据文件")
    print("=" * 60)
    
    # 创建数据目录
    data_dir = Path("examples/data")
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # 创建示例.top文件
    top_content = """
; 示例GROMACS拓扑文件
; system.top

[ defaults ]
1 2 yes 1.0 1.0

[ system ]
Example System

[ molecules ]
; 分子名     数量
Water        1000
Methane      100
"""
    
    with open(data_dir / "system.top", 'w') as f:
        f.write(top_content.strip())
    
    # 创建示例.gro文件
    gro_content = """
Example System
3
    1WATER     OW    1   1.000   1.000   1.000
    1WATER    HW1    2   1.100   1.000   1.000
    1WATER    HW2    3   0.900   1.000   1.000
   3.000   3.000   3.000
"""
    
    with open(data_dir / "system.gro", 'w') as f:
        f.write(gro_content.strip())
    
    # 创建示例.itp文件
    itp_content = """
; 示例分子定义文件
; molecule.itp

[ moleculetype ]
; 分子名     排除规则
Water        2

[ atoms ]
;   nr   type  resnr residue  atom   cgnr     charge       mass
     1     OW      1    WAT     OW      1     -0.834   15.99940
     2    HW1      1    WAT    HW1      1      0.417    1.00800
     3    HW2      1    WAT    HW2      1      0.417    1.00800

[ bonds ]
; i  j  func  length  force_constant
  1  2     1    0.1    345000
  1  3     1    0.1    345000

[ angles ]
; i  j  k  func  angle  force_constant
  2  1  3     1    109.5    383
"""
    
    with open(data_dir / "molecule.itp", 'w') as f:
        f.write(itp_content.strip())
    
    print(f"示例数据文件已创建在: {data_dir}")
    print("文件列表:")
    for file in data_dir.iterdir():
        print(f"  - {file.name}")


def main():
    """主函数"""
    
    print("GROMACS to LAMMPS 转换工具 - 使用示例")
    print("="*60)
    
    # 创建示例数据
    create_example_data()
    
    # 运行示例
    example_standard_force_field()
    example_custom_force_field()
    
    print("\n" + "="*60)
    print("示例运行完成！")
    print("请查看examples/output/目录下的生成文件")
    print("="*60)


if __name__ == "__main__":
    main() 