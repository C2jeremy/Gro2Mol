#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
命令行接口模块
提供gro2mol2lmp命令行工具的入口点
"""

import sys
import os
from pathlib import Path

# 将当前包目录添加到Python路径
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

def main():
    """命令行工具的主入口点"""
    try:
        # 导入主函数
        from .main import main as main_func
        # 调用主函数
        main_func()
    except ImportError:
        # 如果相对导入失败，尝试绝对导入
        try:
            from main import main as main_func
            main_func()
        except ImportError as e:
            print(f"错误：无法导入主模块。{e}")
            print("请确保在正确的目录中运行此工具。")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n用户中断操作")
        sys.exit(1)
    except Exception as e:
        print(f"运行时错误：{e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 