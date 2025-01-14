import logging
from config import Config

# 设置日志
# 创建日志记录器
logger = logging.getLogger(__name__)
logger.setLevel(Config.LOG_LEVEL)

# 创建格式化器
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# 创建文件处理器
file_handler = logging.FileHandler(Config.LOG_FILE)
file_handler.setFormatter(formatter)
file_handler.setLevel(Config.LOG_LEVEL)

# 创建控制台处理器
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
console_handler.setLevel(Config.LOG_LEVEL)

# 添加处理器
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# 设置日志回滚
from logging.handlers import RotatingFileHandler
file_handler = RotatingFileHandler(
    Config.LOG_FILE,
    maxBytes=getattr(Config, 'LOG_FILE_MAX_SIZE', 10*1024*1024),  # 默认10MB
    backupCount=getattr(Config, 'LOG_BACKUP_COUNT', 5),  # 默认5个备份
    encoding='utf-8'
)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

logging.getLogger('werkzeug').setLevel(logging.ERROR)
