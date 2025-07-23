#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GROMACS to LAMMPS converter via moltemplate
将GROMACS工程文件转换为LAMMPS工程文件的主程序

作者: 
日期: 2024
"""

import argparse
import os
import sys
from pathlib import Path

from parsers.gromacs_parser import GromacsParser
from generators.moltemplate_generator import MoltemplateGenerator
from utils.force_field_manager import ForceFieldManager
from utils.logger import setup_logger


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="将GROMACS文件转换为LAMMPS文件（通过moltemplate）"
    )
    
    # 输入文件参数
    parser.add_argument("-t", "--topology", 
                       help="GROMACS拓扑文件(.top)")
    parser.add_argument("-c", "--coordinate",
                       help="坐标文件(.gro或.pdb)")
    parser.add_argument("-f", "--force-field", 
                       help="力场类型 (gaff2, opls, amber等)")
    parser.add_argument("--itp-files", nargs="+",
                       help="ITP文件列表（可作为主要输入）")
    
    # 输出参数
    parser.add_argument("-o", "--output", default="output",
                       help="输出目录 (默认: output)")
    parser.add_argument("--output-name", default="system",
                       help="输出文件名前缀 (默认: system)")
    
    # 选项参数
    parser.add_argument("--custom-ff", action="store_true",
                       help="使用自定义力场 (将生成完整的.lt文件)")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="详细输出")
    
    args = parser.parse_args()
    
    # 设置日志
    logger = setup_logger(args.verbose)
    
    try:
        # 检查输入文件
        check_input_files(args, logger)
        
        # 创建输出目录
        output_dir = Path(args.output)
        output_dir.mkdir(exist_ok=True)
        
        # 解析GROMACS文件
        logger.info("开始解析GROMACS文件...")
        gromacs_parser = GromacsParser(logger)
        
        # 支持只有itp文件的情况（标准力场模式）
        if args.topology is None and args.coordinate is None and args.itp_files:
            logger.info("仅使用ITP文件模式")
            system_data = gromacs_parser.parse_itp_only(args.itp_files)
        else:
            system_data = gromacs_parser.parse_system(
                top_file=args.topology,
                coord_file=args.coordinate,
                itp_files=args.itp_files
            )
        
        # 管理力场
        logger.info("处理力场信息...")
        ff_manager = ForceFieldManager(logger)
        force_field_data = ff_manager.process_force_field(
            system_data, 
            args.force_field,
            custom_ff=args.custom_ff
        )
        
        # 生成moltemplate文件
        logger.info("生成moltemplate文件...")
        mt_generator = MoltemplateGenerator(logger)
        mt_generator.generate_moltemplate_files(
            system_data,
            force_field_data,
            output_dir,
            args.output_name,
            custom_ff=args.custom_ff
        )
        
        logger.info(f"转换完成！输出文件位于: {output_dir}")
        
    except Exception as e:
        logger.error(f"转换失败: {e}")
        sys.exit(1)


def check_input_files(args, logger):
    """检查输入文件是否存在"""
    
    # 检查是否提供了有效的输入组合
    if not args.topology and not args.coordinate and not args.itp_files:
        raise ValueError("必须提供以下其中一种输入：\n"
                        "1. TOP和坐标文件 (完整系统模式)\n"
                        "2. 仅ITP文件 (单分子标准力场模式)")
    
    # 如果提供了topology或coordinate，两者都必须存在
    if (args.topology and not args.coordinate) or (not args.topology and args.coordinate):
        raise ValueError("如果提供TOP或坐标文件，两者都必须提供")
    
    # 如果只有itp文件，必须指定力场
    if not args.topology and not args.coordinate and args.itp_files and not args.force_field:
        raise ValueError("仅使用ITP文件时，必须指定力场类型 (-f/--force-field)")
    
    # 检查文件是否存在
    files_to_check = []
    
    if args.topology:
        files_to_check.append(args.topology)
    if args.coordinate:
        files_to_check.append(args.coordinate)
    if args.itp_files:
        files_to_check.extend(args.itp_files)
    
    for file_path in files_to_check:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"找不到文件: {file_path}")
    
    logger.info("输入文件检查完成")


if __name__ == "__main__":
    main() 