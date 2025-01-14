import re
import redis
from threading import Thread
import signal
from config import redisConfig
# import easytrader


class miniqmt(object):
    def __init__(self):
        self.process = {}
        self.process['CANCEL'] = self.cancel_all
        self.process['BUY'] = self.buy
        self.process['SELL'] = self.sell
        self.process['BUY_MKT'] = self.buy_mkt
        self.process['SELL_MKT'] = self.sell_mkt
        self.process['TRADE'] = self.trade
        self.process['POSITION'] = self.position
        self.process['BALANCE'] = self.balance
        self.stk_code_pattern = re.compile(r'(\d{6}).([A-Z]{4})')   #(r'(\d{6}).*')
        self.traders = {}
        self.keys = []
        self.code = ''
        self.amount = 0
        self.price = 0
        self.stg = ''
        self.ttype = ''


    def CustomTrade(self, path, acc):
        if len(path) != len(acc):
            return False
        self.keys = acc
        """
        for x, y in zip(acc, path):
            self.traders[x] = easytrader.use('zx_client')
            self.traders[x].prepare(y)"""

        return True
    
    def set_data(self,data):
        code = data.get('code', '600000.XSHG')
        match_res = self.stk_code_pattern.search(code)
        if not match_res:
            print("illegal param code %s" % code)
            return False
        code = match_res.group(1)
        mkt = match_res.group(2)
        self.code = ('sh' + code) if mkt == 'XSHG' else ('sz' + code)
        self.amount = int(data.get('amt','0'))
        self.price = float(data.get('price','0.00'))
        self.ttype = data.get('ttype', '')
        self.stg = data.get('stg','')
        return True        
    
    def buy(self):
        return {'entrust_no': '7985'} if self.stg == '536' else {'entrust_no': '17985'}

    def sell(self):
        return {'entrust_no': '217985'} if self.stg == '536' else {'entrust_no': '3217985'}

    def buy_mkt(self):
        #return self.traders[stg].market_buy(code, amt, ttype)
        pass

    def sell_mkt(self):
        #return self.traders[stg].market_sell(code, amt, ttype)
        pass
    
    def trade(self):
        return [{'委托时间': '09:51:27', '申报编号': 7097, '证券代码': '="600030"', '证券名称': '中信证券', 
                 '买卖': '证券买入', '委托类型': '买卖', '委托状态': '废单', '委托价格': 1.26, '委托数量': 500.0, 
                 '成交 价格': 0.0, '成交数量': 0.0, '已撤数量': 0, '股东代码': '="A298058695"', 
                 '资金帐号': '21110046537', '交易市场': '上海', '返回信息': '[60450][订单价格超出范围]', 
                 '委托编号': '7097', '委托类别': '委托', 'Unnamed: 18': ''}] if self.stg == '537' else [{'委托时间': '10:53:27', 
                 '申报编号': 7097, '证券代码': '="600030"', '证券名称': '中信证券', 
                 '买卖': '证券买入', '委托类型': '买卖', '委托状态': '废单', '委托价格': 1.26, '委托数量': 500.0, 
                 '成交 价格': 0.0, '成交数量': 0.0, '已撤数量': 0, '股东代码': '="A298058695"', 
                 '资金帐号': '21110046537', '交易市场': '上海', '返回信息': '[60450][订单价格超出范围]', 
                 '委托编号': '7120', '委托类别': '委托', 'Unnamed: 18': ''}]
 
    
    def cancel_all(self):

        return '撤销成功'
        
    def position(self):
        if self.stg == '536':
            return [{'证券名称': '上证50ETF', '证券代码': '="510050"', '参考持股': 30000, 
                    '可用股份': 30000.0, '成本价': 2.726, '当前价': 2.615, '当前成本': 81792.27, 
                    '最新市值': 78450.0, '浮动盈亏': -3342.27, '盈亏比例(%)': -4.086, '冻结数量': 0.0, 
                    '在途股份(买入成交)': 0.0, '股份余额': 30000.0, '股东代码': '="A298058695"', 
                    '资金帐户': '21110046537', '交易市场': '上海', '卖出成交数量': 0.0, 'Unnamed: 17': ''}]
        return [{'证券名称': '上证50ETF', '证券代码': '="510050"', '参考持股': 30000, 
                    '可用股份': 30000.0, '成本价': 2.726, '当前价': 2.615, '当前成本': 81792.27, 
                    '最新市值': 78450.0, '浮动盈亏': -3342.27, '盈亏比例(%)': -4.086, 
                    '冻结数量': 0.0, '在途股份(买入成交)': 0.0, '股份余额': 30000.0, 
                    '股东代码': '="A298058695"', '资金帐户': '21110046537', '交易市场': '上海', 
                    '卖出成交数量': 0.0, 'Unnamed: 17': ''}, 
                    {'证券名称': '科创芯片ETF基金', '证券代码': '="588290"', '参考持股': 156000, 
                    '可用股份': 156000.0, '成本价': 1.369, '当前价': 1.395, '当前成本': 213542.87,
                    '最新市值': 217620.0, '浮动盈亏': 4077.13, '盈亏比例(%)': 1.909, '冻结数量': 0.0,
                    '在途股份(买入成交)': 0.0, '股份余额': 156000.0, '股东代码': '="A298058695"', 
                    '资金帐户': '21110046537', '交易市场': '上海', '卖出成交数量': 0.0, 'Unnamed: 17': ''}, 
                    {'证券名称': '中证A500ETF景顺', '证券代码': '="159353"', '参考持股': 25002, 
                    '可用股份': 25002.0, '成本价': 1.008, '当前价': 0.924, '当前成本': 25200.0, 
                    '最新市值': 23101.85, '浮动盈亏': -2098.15, '盈亏比例(%)': -8.326, '冻结数量': 0.0, 
                    '在途股份(买入成交)': 0.0, '股份余额': 25002.0, '股东代码': '="0381863761"', 
                    '资金帐户': '21110046537', '交易市场': '深圳', '卖出成交数量': 0.0, 'Unnamed: 17': ''}
                    ]

    def balance(self):
        return {'资金余额': 126582.21, '可用金额': 126482.21, '可取金额': 126482.21, '股票市值': 319171.85, '总资产': 465444.95} if self.stg == '537' else {'资金余额': 140.63, '可用金额': 140.63, '可取金额': 140.63, '股票市值': 71912.5, '总资产': 72053.13}   

class RedisService(object):

    #host='127.0.0.1'


    def __init__(self):
        self.redis = redis.Redis(
            host = redisConfig.host,
            port = redisConfig.port,
            password = redisConfig.pwd)
        self.stream_name = redisConfig.order_stream_name
        self.msg_name = redisConfig.msg_stream_name
        self.consumer_group = redisConfig.order_consumer_group
        self.consumer_name = redisConfig.order_consumer_name
        self.path = [r'C:\Users\sunlei\Documents\stock\536.json', r'C:\Users\sunlei\Documents\stock\537.json']
        self.acc = ['536', '537']
        self.receivers = ['xxx@qq.com']
        self.CQMT = miniqmt()
        self.is_test = False

        #self.CQMT.CustomTrade(RedisService.path, RedisService.acc)
        self.thread = Thread(target=self.loop_consuming, daemon=True)
        signal.signal(signal.SIGINT, self.handle_interrupt)
    
    def handle_interrupt(self, signal, frame):
        print("Caught KeyboardInterrupt")
        # do some cleanup and exit
        exit(0)

    def loop_consuming(self):
        while True:
            self.consume(self.consumer_name, count=3, target=self.biz_execute)

    def start_background(self):
        self.thread.start()

    def xgroup_create(self):
        """
        创建消费组
        """
        if self.check_consumer_group_exists():
            print('消费者组已存在')            
        else:
            self.redis.xgroup_create(self.stream_name, self.consumer_group, id='0', mkstream=True)
            print('消费者组创建成功')

    def check_consumer_group_exists(self):
        try:
            groups = self.redis.xinfo_groups(self.stream_name)
            return any(group['name'].decode('utf-8') == self.consumer_group for group in groups)
        except Exception as e:
            print(f"检查消费者组时出错: {e}")
            return False

    def __get_data(self, data):
        """
        从消息流中获取业务数据
        """
        if not data or not data[0]:
            return None, None
        msgId = str(data[0], 'utf-8')
        data = {str(key, 'utf-8'): str(val, 'utf-8') for key, val in data[1].items()}
        if not data.get("bizData"):
            return msgId, data
        return msgId, data["bizData"]

    def consume(self, consumer_name, id=">", block=30000, count=1, target=None):
        """
        消费数据
        :param consumer_name: 消费者名称，建议传递ip
        :param id: 从哪开始消费
        :param block: 无消息阻塞时间，毫秒，默认60秒，在60秒内有消息直接消费
        :param count: 消费多少条，默认1
        :param target: 业务处理回调方法
        :return:
        """
        # block 0 时阻塞等待, 其他数值表示读取超时时间
        streams = {self.stream_name: id}
        rst = self.redis.xreadgroup( self.consumer_group, consumer_name, streams, block=block, count=count)
        print(f'消费到的数据 {rst}')
        if not rst or not rst[0] or not rst[0][1]:
           return None
        # 遍历获取到的列表信息（可以消费多条，根据count）
        for item in rst[0][1]:
           try:
               #解析数据
               msgId, data = self.__get_data(item)
               """
               执行回调函数target，成功后ack
               """
               if target and target(msgId,data):
                   # 将处理完成的消息标记，类似于kafka的offset
                   self.redis.xack( self.stream_name,  self.consumer_group, msgId)
                   self.redis.xdel( self.stream_name, msgId)
           except Exception as e:
               # 消费失败，下次从头消费(消费成功的都已经提交ack了，可以先不处理，以后再处理)
               print("consumer is error:",repr(e))
    
    def biz_execute(self, msgId, data):
        """
        业务处理，不建议多个场景共用一个stream，建议分开，
        如果数据量比较少，通过工厂处理分发
        :param msgId:
        :param data:
        :return:
        """
        print(f'业务执行msgId={msgId} bizData={data}')
        strategy = data.get('stg')
        rec_type = data.get('type')
        if not strategy or not rec_type:
            return True
        try:
            if not self.CQMT.set_data(data):
                return False
            #remark = data.get('remark', '')
            rec_no = 1 
            tmp = ''
            if self.is_test:
                print(f'{data}')
                return True
            if rec_type in self.CQMT.process:
                func = self.CQMT.process[rec_type]
                tmp = func()
            else:
                rec_no = 0
                tmp = f'{data}'
            """
            if data['type'] == 'BUY':
                #print(f'买入{mkt}， {code}, 价格： { data["price"] if data["price"] != "0" else "市价"}, 股数： {amt} ')
                tmp = self.CQMT.buy(code, amt, float(data['price']), stg)
            elif data['type'] == 'BUY_MK':
                print(f'市价买入{mkt}， {code}, 价格： { data["price"] if data["price"] != "0" else "市价"}, 股数： {amt} ')
                #self.CQMT.buy_latest(code, amt, stg, remark)
            elif data['type'] == 'SELL':
                #print(f'卖出{mkt}， {code}, 价格： { data["price"] if data["price"] != "0" else "市价"}, 股数： {amt} ')
                tmp = self.CQMT.sell(code, amt, float(data['price']), stg)
                #rec_no = f'卖出成功,{tmp}'
            elif data['type'] == 'SELL_MK':
                print(f'市价卖出{mkt}， {code}, 价格： { data["price"] if data["price"] != "0" else "市价"}, 股数： {amt} ')
                #self.CQMT.sell_latest(code, amt, stg, remark)
            elif data['type'] == 'CANCEL':
                tmp = self.CQMT.cancel_all(stg)
                #rec_no = '全部撤销' if tmp else '撤销失败'
            elif data['type'] == 'BALANCE':
                tmp = self.CQMT.balance(stg)
                #rec_no = f'资产查询： {tmp}'
            else:
                rec_no = 0
                tmp = f'{data["type"]}_{mkt}， {code}, 价格： { data["price"] if data["price"] != "0" else "市价"}, 股数： {amt} '
            #mail.send_mail_async("order new notice", f"{data['type']} {code}, price is { data['price'] if data['price'] != '0' else 'market'}, amt {amt} ", RedisService.receivers)
            """
            msg_data = {
                'stg': data.get('stg', ''),
                'ret': rec_no,
                'type': rec_type,
                'msg': str(tmp)
            }
            self.redis.xadd(self.msg_name, msg_data)
            return True
        except Exception as e:
            print(repr(e))
            msg_data = {
                'stg': data.get('stg', ''),
                'ret': 0,
                'type': data['type'],
                'msg': repr(e)
            }
            self.redis.xadd(self.msg_name, msg_data)
            return False


if __name__ == '__main__':
    stream = RedisService()
    #注意：第一次运行需要创建消费组，取消下面这一句注释即可
    stream.xgroup_create()
    stream.start_background()
    input("press enter to exit...\n")
