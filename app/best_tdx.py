#coding: utf-8
# see https://github.com/rainx/pytdx/issues/38 IP寻优的简单办法
# by yutianst

import datetime
from pytdx.hq import TdxHq_API
from pytdx.exhq import TdxExHq_API

stock_ip = [{'ip': 'sztdx.gtjas.com', 'port': 7709, 'name': '国泰君安深圳电信组站'},
 {'ip': 'jstdx.gtjas.com', 'port': 7709, 'name': '国泰君安江苏电信组站'},
 {'ip': 'shtdx.gtjas.com', 'port': 7709, 'name': '国泰君安上海电信组站'},
 {'ip': 'bjwttdx.gtjas.com', 'port': 7709, 'name': '国泰君安北京网通组站'},
 {'ip': 'bfwttdx.gtjas.com', 'port': 7709, 'name': '国泰君安北方网通组站'},
 {'ip': 'hbwttdx.gtjas.com', 'port': 7709, 'name': '国泰君安河北网通组站'},
 {'ip': 'cdtdx.gtjas.com', 'port': 7709, 'name': '国泰君安成都电信组站'},
 {'ip': '182.118.47.141', 'port': 7709, 'name': '郑州网通行情一'},
 {'ip': '182.118.47.168', 'port': 7709, 'name': '郑州网通行情二'},
 {'ip': '182.118.47.169', 'port': 7709, 'name': '郑州网通行情三'},
 {'ip': '119.97.164.184', 'port': 7709, 'name': '武汉电信行情一'},
 {'ip': '119.97.164.189', 'port': 7709, 'name': '武汉电信行情二'},
 {'ip': '116.211.121.102', 'port': 7709, 'name': '武汉电信行情三'},
 {'ip': '116.211.121.108', 'port': 7709, 'name': '武汉电信行情四'},
 {'ip': '116.211.121.31', 'port': 7709, 'name': '武汉电信行情五'},
 {'ip': '202.100.166.117', 'port': 7709, 'name': '新疆电信云行情一'},
 {'ip': '202.100.166.118', 'port': 7709, 'name': '新疆电信云行情二'},
 {'ip': '222.73.139.166', 'port': 7709, 'name': '上海电信行情八'},
 {'ip': '222.73.139.167', 'port': 7709, 'name': '上海电信行情九'},
 {'ip': '222.73.139.168', 'port': 7709, 'name': '上海电信行情十'},
 {'ip': '103.251.85.90', 'port': 7709, 'name': '上海BGP行情一'},
 {'ip': '123.125.108.213', 'port': 7709, 'name': '北京联通行情一'},
 {'ip': '123.125.108.214', 'port': 7709, 'name': '北京联通行情二'},
 {'ip': '222.73.139.151', 'port': 7709, 'name': '上海电信行情六'},
 {'ip': '222.73.139.152', 'port': 7709, 'name': '上海电信行情七'},
 {'ip': '148.70.110.41', 'port': 7709, 'name': '成都BGP行情一'},
 {'ip': '148.70.93.117', 'port': 7709, 'name': '成都BGP行情二'},
 {'ip': '148.70.31.16', 'port': 7709, 'name': '成都BGP行情三'},
 {'ip': '148.70.111.63', 'port': 7709, 'name': '成都BGP行情四'},
 {'ip': '139.159.143.228', 'port': 7709, 'name': '广州BGP行情一'},
 {'ip': '139.159.183.76', 'port': 7709, 'name': '广州BGP行情二'},
 {'ip': '139.159.193.118', 'port': 7709, 'name': '广州BGP行情三'},
 {'ip': '139.159.195.177', 'port': 7709, 'name': '广州BGP行情四'},
 {'ip': '139.159.202.253', 'port': 7709, 'name': '广州BGP行情五'},
 {'ip': '139.159.214.78', 'port': 7709, 'name': '广州BGP行情六'},
 {'ip': '139.9.38.206', 'port': 7709, 'name': '广州BGP行情七'},
 {'ip': '139.9.43.104', 'port': 7709, 'name': '广州BGP行情八'},
 {'ip': '139.9.43.31', 'port': 7709, 'name': '广州BGP行情九'},
 {'ip': '139.9.50.246', 'port': 7709, 'name': '广州BGP行情十'},
 {'ip': '139.9.52.158', 'port': 7709, 'name': '广州BGP行情十一'},
 {'ip': '139.9.90.169', 'port': 7709, 'name': '广州BGP行情十二'},
 {'ip': '101.226.180.73', 'port': 7709, 'name': '上海电信行情十一'},
 {'ip': '101.226.180.74', 'port': 7709, 'name': '上海电信行情十二'},
 {'ip': '103.251.85.200', 'port': 7709, 'name': '上海BGP行情六'},
 {'ip': '103.251.85.201', 'port': 7709, 'name': '上海BGP行情七'},
 {'ip': '103.221.142.65', 'port': 7709, 'name': '南京电信行情一'},
 {'ip': '103.221.142.66', 'port': 7709, 'name': '南京电信行情二'},
 {'ip': '103.221.142.67', 'port': 7709, 'name': '南京电信行情三'},
 {'ip': '103.221.142.68', 'port': 7709, 'name': '南京电信行情四'},
 {'ip': '103.221.142.69', 'port': 7709, 'name': '南京电信行情五'},
 {'ip': '103.221.142.70', 'port': 7709, 'name': '南京电信行情六'},
 {'ip': '103.221.142.71', 'port': 7709, 'name': '南京电信行情七'},
 {'ip': '103.221.142.72', 'port': 7709, 'name': '南京电信行情八'},
 {'ip': '117.34.114.13', 'port': 7709, 'name': '西安电信行情一'},
 {'ip': '117.34.114.14', 'port': 7709, 'name': '西安电信行情二'},
 {'ip': '117.34.114.15', 'port': 7709, 'name': '西安电信行情三'},
 {'ip': '117.34.114.16', 'port': 7709, 'name': '西安电信行情四'},
 {'ip': '117.34.114.17', 'port': 7709, 'name': '西安电信行情五'},
 {'ip': '117.34.114.18', 'port': 7709, 'name': '西安电信行情六'},
 {'ip': '117.34.114.20', 'port': 7709, 'name': '西安电信行情七'},
 {'ip': '117.34.114.27', 'port': 7709, 'name': '西安电信行情八'},
 {'ip': '117.34.114.30', 'port': 7709, 'name': '西安电信行情九'},
 {'ip': '103.251.85.202', 'port': 7709, 'name': '上海BGP行情八'},
 {'ip': '183.60.224.142', 'port': 7709, 'name': '东莞电信行情一'},
 {'ip': '183.60.224.143', 'port': 7709, 'name': '东莞电信行情二'},
 {'ip': '183.60.224.144', 'port': 7709, 'name': '东莞电信行情三'},
 {'ip': '183.60.224.145', 'port': 7709, 'name': '东莞电信行情四'},
 {'ip': '183.60.224.146', 'port': 7709, 'name': '东莞电信行情五'},
 {'ip': '183.60.224.147', 'port': 7709, 'name': '东莞电信行情六'},
 {'ip': '183.60.224.148', 'port': 7709, 'name': '东莞电信行情七'}]

future_ip = [{'ip': '106.14.95.149', 'port': 7727, 'name': '扩展市场上海双线'},
 {'ip': '112.74.214.43', 'port': 7727, 'name': '扩展市场深圳双线1'},
 {'ip': '119.147.86.171', 'port': 7727, 'name': '扩展市场深圳主站'},
 {'ip': '119.97.185.5', 'port': 7727, 'name': '扩展市场武汉主站1'},
 {'ip': '120.24.0.77', 'port': 7727, 'name': '扩展市场深圳双线2'},
 {'ip': '124.74.236.94', 'port': 7721},
 {'ip': '202.103.36.71', 'port': 443, 'name': '扩展市场武汉主站2'},
 {'ip': '47.92.127.181', 'port': 7727, 'name': '扩展市场北京主站'},
 {'ip': '59.175.238.38', 'port': 7727, 'name': '扩展市场武汉主站3'},
 {'ip': '61.152.107.141', 'port': 7727, 'name': '扩展市场上海主站1'},
 {'ip': '61.152.107.171', 'port': 7727, 'name': '扩展市场上海主站2'},
 {'ip': '119.147.86.171', 'port': 7721, 'name': '扩展市场深圳主站'},
 {'ip': '47.107.75.159', 'port': 7727, 'name': '扩展市场深圳双线3'}]

def ping(ip, port=7709, type_='stock'):
    api = TdxHq_API()
    apix = TdxExHq_API()
    __time1 = datetime.datetime.now()
    try:
        if type_ in ['stock']:
            with api.connect(ip, port, time_out=0.7):
                res = api.get_security_list(0, 1)
                #print(len(res))
                if res is not None:
                    if len(res) > 800:
                        print('GOOD RESPONSE {}'.format(ip))
                        return datetime.datetime.now() - __time1
                    else:
                        print('BAD RESPONSE {}'.format(ip))
                        return datetime.timedelta(9, 9, 0)
                else:

                    print('BAD RESPONSE {}'.format(ip))
                    return datetime.timedelta(9, 9, 0)
        elif type_ in ['future']:
            with apix.connect(ip, port, time_out=0.7):
                res = apix.get_instrument_count()
                if res is not None:
                    if res > 20000:
                        print('GOOD RESPONSE {}'.format(ip))
                        return datetime.datetime.now() - __time1
                    else:
                        print('Bad FUTUREIP REPSONSE {}'.format(ip))
                        return datetime.timedelta(9, 9, 0)
                else:
                    print('Bad FUTUREIP REPSONSE {}'.format(ip))
                    return datetime.timedelta(9, 9, 0)
    except Exception as e:
        if isinstance(e, TypeError):
            print(e)
            print('Tushare内置的pytdx版本和最新的pytdx 版本不同, 请重新安装pytdx以解决此问题')
            print('pip uninstall pytdx')
            print('pip install pytdx')

        else:
            print('BAD RESPONSE {}'.format(ip))
        return datetime.timedelta(9, 9, 0)



def select_best_ip(_type='stock'):
    """目前这里给的是单线程的选优, 如果需要多进程的选优/ 最优ip缓存 可以参考
    https://github.com/QUANTAXIS/QUANTAXIS/blob/master/QUANTAXIS/QAFetch/QATdx.py#L106


    Keyword Arguments:
        _type {str} -- [description] (default: {'stock'})
    
    Returns:
        [type] -- [description]
    """
    best_ip = {
        'stock': {
            'ip': None, 'port': None
        },
        'future': {
            'ip': None, 'port': None
        }
    }
    ip_list = stock_ip if _type== 'stock' else future_ip
    
    data = [ping(x['ip'], x['port'], _type) for x in ip_list]
    results = []
    for i in range(len(data)):
        # 删除ping不通的数据
        if data[i] < datetime.timedelta(0, 9, 0):
            results.append((data[i], ip_list[i]))
    # 按照ping值从小大大排序
    results = [x[1] for x in sorted(results, key=lambda x: x[0])]
    
    return results[0]