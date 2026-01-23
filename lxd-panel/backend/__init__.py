"""初始化包文件"""
# 确保backend作为包可以被导入
import sys
import os

# 将父目录添加到Python路径
backend_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(backend_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
