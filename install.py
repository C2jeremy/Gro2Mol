#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gro2mol2lmp 安装脚本

使用方法：
    python install.py          # 正常安装
    python install.py --dev    # 开发模式安装
    python install.py --user   # 用户模式安装
"""

import subprocess
import sys
import os
import argparse
from pathlib import Path

def run_command(cmd, check=True, shell=False):
    """运行命令并处理错误"""
    print(f"执行命令: {' '.join(cmd) if isinstance(cmd, list) else cmd}")
    try:
        if shell:
            result = subprocess.run(cmd, shell=True, check=check, 
                                  capture_output=True, text=True)
        else:
            result = subprocess.run(cmd, check=check, 
                                  capture_output=True, text=True)
        
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr)
        return result
    except subprocess.CalledProcessError as e:
        print(f"命令执行失败: {e}")
        if e.stdout:
            print("标准输出:", e.stdout)
        if e.stderr:
            print("错误输出:", e.stderr)
        raise

def check_python_version():
    """检查Python版本"""
    if sys.version_info < (3, 7):
        print("错误：需要Python 3.7或更高版本")
        print(f"当前版本：{sys.version}")
        sys.exit(1)
    print(f"Python版本检查通过：{sys.version}")

def check_pip():
    """检查pip是否可用"""
    try:
        run_command([sys.executable, "-m", "pip", "--version"])
        return True
    except subprocess.CalledProcessError:
        print("错误：pip不可用")
        return False

def install_package(dev_mode=False, user_mode=False):
    """安装包"""
    cmd = [sys.executable, "-m", "pip", "install"]
    
    if user_mode:
        cmd.append("--user")
    
    if dev_mode:
        cmd.extend(["-e", "."])
        print("开发模式安装...")
    else:
        cmd.append(".")
        print("正常模式安装...")
    
    run_command(cmd)

def install_optional_dependencies():
    """安装可选依赖"""
    print("安装可选依赖...")
    
    # 询问是否安装moltemplate
    install_moltemplate = input("是否安装moltemplate？这是运行工具所必需的 (y/n): ").lower().strip()
    if install_moltemplate in ['y', 'yes', '是']:
        try:
            print("尝试通过conda安装moltemplate...")
            run_command("conda install -c conda-forge moltemplate -y", shell=True)
        except subprocess.CalledProcessError:
            try:
                print("conda安装失败，尝试通过pip安装...")
                run_command([sys.executable, "-m", "pip", "install", "moltemplate"])
            except subprocess.CalledProcessError:
                print("警告：moltemplate安装失败，请手动安装")
    
    # 询问是否安装完整依赖
    install_full = input("是否安装完整依赖（包括psutil等）？(y/n): ").lower().strip()
    if install_full in ['y', 'yes', '是']:
        try:
            run_command([sys.executable, "-m", "pip", "install", ".[full]"])
        except subprocess.CalledProcessError:
            print("完整依赖安装失败，跳过...")

def test_installation():
    """测试安装是否成功"""
    print("测试安装...")
    try:
        # 测试导入
        run_command([sys.executable, "-c", "import gro2mol2lmp; print('包导入成功')"])
        
        # 测试命令行工具
        run_command(["gro2mol2lmp", "--help"])
        print("✓ 安装成功！")
        print("\n可用命令：")
        print("  gro2mol2lmp --help     # 查看完整帮助")
        print("  gro2lammps --help      # 简短别名")
        
    except subprocess.CalledProcessError:
        print("❌ 安装测试失败")
        print("请检查安装过程中的错误信息")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="gro2mol2lmp 安装脚本")
    parser.add_argument("--dev", action="store_true", 
                       help="开发模式安装（可编辑模式）")
    parser.add_argument("--user", action="store_true",
                       help="用户模式安装（只为当前用户安装）")
    parser.add_argument("--skip-test", action="store_true",
                       help="跳过安装测试")
    parser.add_argument("--skip-optional", action="store_true",
                       help="跳过可选依赖安装")
    
    args = parser.parse_args()
    
    # 切换到脚本所在目录
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    print("开始安装 gro2mol2lmp...")
    print("=" * 50)
    
    # 检查环境
    check_python_version()
    if not check_pip():
        sys.exit(1)
    
    try:
        # 升级pip和setuptools
        print("升级pip和setuptools...")
        run_command([sys.executable, "-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel"])
        
        # 安装包
        install_package(dev_mode=args.dev, user_mode=args.user)
        
        # 安装可选依赖
        if not args.skip_optional:
            install_optional_dependencies()
        
        # 测试安装
        if not args.skip_test:
            test_installation()
        
        print("\n" + "=" * 50)
        print("安装完成！")
        
        if args.dev:
            print("开发模式安装完成，代码更改会立即生效")
        
        print("\n快速开始：")
        print("  gro2mol2lmp -t system.top -c system.gro -f gaff2 -o output")
        
    except Exception as e:
        print(f"\n安装失败：{e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 