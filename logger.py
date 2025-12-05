"""
日志类
"""
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    # filename='开发日志.log',  # 日志文件名称（默认在项目根目录）
    # filemode='a'  # 写入模式：a=追加（默认），w=覆盖
)

def get_logger(name=None):
    """获取配置好的logger"""
    return logging.getLogger(name)

