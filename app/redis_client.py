import redis
import time
from redis.exceptions import ConnectionError
from app.logging_config import logger

class RedisClient:
    def __init__(self, host='localhost', port=6379, db=0, password=None, max_connections=10):
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.max_connections = max_connections
        self.connection_pool = None
        self.stream_name = "msg"
        self.consumer_group = "msg_group"
        self.consumer_name = None
        self.order_stream_name = None
        self._connect()

    def _connect(self):
        """创建 Redis 连接池"""
        self.connection_pool = redis.ConnectionPool(
            host=self.host,
            port=self.port,
            db=self.db,
            password=self.password,
            decode_responses=True,
            max_connections=self.max_connections,
            health_check_interval=30    # 每 30 秒检查健康一次
        )
        self._check_connection()

    def _check_connection(self):
        """检查 Redis 连接是否正常"""
        try:
            conn = self.get_connection()
            conn.ping()  # 测试连接
            logger.info("Redis 连接成功！")
        except ConnectionError as e:
            logger.error(f"Redis 连接失败: {e}")
            self._reconnect()

    def _reconnect(self):
        """重连 Redis"""
        print("尝试重新连接 Redis...")
        retry_count = 0
        max_retries = 5  # 最大重试次数
        retry_delay = 5  # 重试间隔（秒）

        while retry_count < max_retries:
            try:
                self._connect()  # 重新创建连接池
                logger.info("Redis 重连成功！")
                return
            except ConnectionError as e:
                retry_count += 1
                logger.error(f"重连失败 ({retry_count}/{max_retries}): {e}")
                time.sleep(retry_delay)

        raise ConnectionError("无法重新连接到 Redis，请检查 Redis 服务状态。")

    def set_stream_name(self, stream_name, consumer_group, consumer_name, order_stream_name):
        self.stream_name = stream_name
        self.consumer_group = consumer_group
        self.consumer_name = consumer_name
        self.order_stream_name = order_stream_name

    def get_connection(self):
        """从连接池获取一个 Redis 连接"""
        if not self.connection_pool:
            self._connect()
        return redis.Redis(connection_pool=self.connection_pool)

    def send_command(self, command=None, stream_name=None):
        """发送指令到 Redis Stream"""
        order_stream = stream_name
        if command:
            if not order_stream:
                order_stream = self.order_stream_name
            try:
                conn = self.get_connection()
                conn.xadd(order_stream, command)
            except ConnectionError:
                self._reconnect()
                conn = self.get_connection()
                conn.xadd(order_stream, command)

    def read_messages(self, stream_name, last_id='0', count=1):
        """从 Redis Stream 读取消息"""
        try:
            conn = self.get_connection()
            messages = conn.xread({stream_name: last_id}, block=3000, count=count)
            return messages
        except ConnectionError:
            self._reconnect()
            conn = self.get_connection()
            messages = conn.xread({stream_name: last_id}, block=3000, count=count)
            return messages

    def read_group_messages(self, last_id='>', count=1):
        """从 Redis Stream 读取消息"""
        try:
            conn = self.get_connection()
            messages = conn.xreadgroup(self.consumer_group, self.consumer_name,{self.stream_name: last_id}, block=3000, count=count)
            return messages
        except ConnectionError:
            self._reconnect()
            conn = self.get_connection()
            messages = conn.xreadgroup(self.consumer_group, self.consumer_name,{self.stream_name: last_id}, block=3000, count=count)
            return messages
        
    def ack_message(self, message_id):
        """确认 Redis Stream 消息"""
        try:
            conn = self.get_connection()
            conn.xack(self.stream_name, self.consumer_group, message_id)
            conn.xdel(self.stream_name, message_id)
        except ConnectionError:
            self._reconnect()
            conn = self.get_connection()
            conn.xack(self.stream_name, self.consumer_group, message_id)
            conn.xdel(self.stream_name, message_id)

    def delete_stream_id(self, stream_name, message_id):
        """删除 Redis Stream 消息"""
        try:
            conn = self.get_connection()
            conn.xdel(stream_name, message_id)
        except ConnectionError:
            self._reconnect()
            conn = self.get_connection()
            conn.xdel(stream_name, message_id)

    def delete_stream(self, stream_name): 
        """删除 Redis Stream"""
        try:
            conn = self.get_connection()
            conn.delete(stream_name)
        except ConnectionError:
            self._reconnect()
            conn = self.get_connection()
            conn.delete(stream_name)

    def xgroup_create(self, ):
        """
        创建消费组
        """
        if self.check_consumer_group_exists():
            logger.info('消费者组已存在')            
        else:
            my_rds = self.get_connection()
            my_rds.xgroup_create(self.stream_name, self.consumer_group, id='0', mkstream=True)
            logger.info('消费者组创建成功')

    def check_consumer_group_exists(self):
        # 获取指定Stream的消费者组列表
        try:
            my_rds = self.get_connection()
            groups = my_rds.xinfo_groups(self.stream_name)
            return any(group['name'] == self.consumer_group for group in groups)
        except Exception as e:
            logger.error(f"检查消费者组时出错: {e}")
            return False

# 全局 Redis 客户端实例
#redis_client = RedisClient(host='localhost', port=6379, db=0)