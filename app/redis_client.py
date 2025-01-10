import redis
import time
from redis.exceptions import ConnectionError

class RedisClient:
    def __init__(self, host='localhost', port=6379, db=0, password=None, max_connections=10):
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.max_connections = max_connections
        self.connection_pool = None
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
            print("Redis 连接成功！")
        except ConnectionError as e:
            print(f"Redis 连接失败: {e}")
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
                print("Redis 重连成功！")
                return
            except ConnectionError as e:
                retry_count += 1
                print(f"重连失败 ({retry_count}/{max_retries}): {e}")
                time.sleep(retry_delay)

        raise ConnectionError("无法重新连接到 Redis，请检查 Redis 服务状态。")

    def get_connection(self):
        """从连接池获取一个 Redis 连接"""
        if not self.connection_pool:
            self._connect()
        return redis.Redis(connection_pool=self.connection_pool)

    def send_command(self, stream_name, command):
        """发送指令到 Redis Stream"""
        try:
            conn = self.get_connection()
            conn.xadd(stream_name, command)
        except ConnectionError:
            self._reconnect()
            conn = self.get_connection()
            conn.xadd(stream_name, command)

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

    def read_group_messages(self, consumer_group, consumer_name,stream_name, last_id='>', count=1):
        """从 Redis Stream 读取消息"""
        try:
            conn = self.get_connection()
            messages = conn.xreadgroup(consumer_group, consumer_name,{stream_name: last_id}, block=3000, count=count)
            return messages
        except ConnectionError:
            self._reconnect()
            conn = self.get_connection()
            messages = conn.xreadgroup(consumer_group, consumer_name,{stream_name: last_id}, block=3000, count=count)
            return messages
        
    def ack_message(self, stream_name, consumer_group, message_id):
        """确认 Redis Stream 消息"""
        try:
            conn = self.get_connection()
            conn.xack(stream_name, consumer_group, message_id)
            conn.xdel(stream_name, message_id)
        except ConnectionError:
            self._reconnect()
            conn = self.get_connection()
            conn.xack(stream_name, consumer_group, message_id)
            conn.xdel(stream_name, message_id)

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

# 全局 Redis 客户端实例
#redis_client = RedisClient(host='localhost', port=6379, db=0)