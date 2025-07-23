#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
运行示例脚本
快速测试转换工具的功能
"""

import sys
import argparse
from pathlib import Path

# 添加当前目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from examples.basic_usage import main as run_examples
from utils.logger import setup_logger, log_system_info


def main():
    """主函数"""
    
    parser = argparse.ArgumentParser(
        description="运行GROMACS到LAMMPS转换工具的示例",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
    python run_example.py                    # 运行所有示例
    python run_example.py --verbose         # 详细输出
    python run_example.py --create-data     # 仅创建示例数据
        """
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="启用详细输出"
    )
    
    parser.add_argument(
        "--create-data",
        action="store_true",
        help="仅创建示例数据文件"
    )
    
    args = parser.parse_args()
    
    # 设置日志
    logger = setup_logger(verbose=args.verbose)
    
    try:
        if args.create_data:
            # 仅创建示例数据
            from examples.basic_usage import create_example_data
            create_example_data()
            logger.info("示例数据创建完成")
        else:
            # 记录系统信息
            if args.verbose:
                log_system_info(logger)
            
            # 运行所有示例
            logger.info("开始运行转换工具示例...")
            run_examples()
            logger.info("所有示例运行完成")
    
    except KeyboardInterrupt:
        logger.info("用户中断执行")
        sys.exit(1)
    
    except Exception as e:
        logger.error(f"运行示例时出错: {e}")
        if args.verbose:
            import traceback
            logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main() 