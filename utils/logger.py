# -*- coding: utf-8 -*-
"""
日志管理模块
设置和管理转换工具的日志输出
"""

import logging
import sys
from pathlib import Path

def setup_logger(verbose: bool = False, log_file: str = None) -> logging.Logger:
    """设置日志记录器"""
    
    # 创建日志记录器
    logger = logging.getLogger('gro2mol2lmp')
    
    # 设置日志级别
    if verbose:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
    
    # 清除现有的处理器
    logger.handlers.clear()
    
    # 创建格式化器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 如果指定了日志文件，创建文件处理器
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # 防止日志重复
    logger.propagate = False
    
    return logger


class ProgressLogger:
    """进度日志记录器"""
    
    def __init__(self, logger, total_steps: int):
        self.logger = logger
        self.total_steps = total_steps
        self.current_step = 0
    
    def step(self, message: str = ""):
        """记录进度"""
        self.current_step += 1
        progress = (self.current_step / self.total_steps) * 100
        
        if message:
            self.logger.info(f"[{progress:.1f}%] {message}")
        else:
            self.logger.info(f"进度: {self.current_step}/{self.total_steps} ({progress:.1f}%)")
    
    def complete(self, message: str = "处理完成"):
        """标记完成"""
        self.logger.info(f"[100%] {message}")


def log_system_info(logger):
    """记录系统信息"""
    import platform
    import sys
    
    logger.info("="*50)
    logger.info("系统信息")
    logger.info("="*50)
    logger.info(f"Python版本: {sys.version}")
    logger.info(f"平台: {platform.platform()}")
    logger.info(f"处理器: {platform.processor()}")
    logger.info(f"内存: {get_memory_info()}")
    logger.info("="*50)


def get_memory_info():
    """获取内存信息"""
    try:
        import psutil
        memory = psutil.virtual_memory()
        return f"{memory.total / (1024**3):.1f} GB"
    except ImportError:
        return "未知 (需要安装psutil)" 