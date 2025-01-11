import logging
from config import Config

# 设置日志
logging.basicConfig(
    level=Config.LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Config.LOG_FILE),
        logging.StreamHandler()
    ]
)

logging.getLogger('werkzeug').setLevel(logging.ERROR)

logger = logging.getLogger(__name__)