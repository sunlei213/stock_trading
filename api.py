from flask import Flask, request, jsonify
from pytdx.hq import TdxHq_API
import re
from datetime import datetime

app = Flask(__name__)


def get_price(code):
    match_res = re.compile(r'(\d{6}).([A-Z]{4})').search(code)
    if not match_res:
        print(f"非法的股票代码格式: {code}")
        return False
    tmp_code = match_res.group(1)  # 股票代码
    mkt = 1 if match_res.group(2) == "XSHG" else 0  # # 市场类型（XSHG 或 XSHE）转换为1,0
    api = TdxHq_API()
    if api.connect('shtdx.gtjas.com',7709):
        stock_data = api.get_security_quotes(mkt,tmp_code)[0]
        data = {
            'code': stock_data['code'],
            'time': stock_data['reversed_bytes0'],
            'buy': [stock_data['bid1']/10,stock_data['bid2']/10,stock_data['bid3']/10] if tmp_code[0] in ['1','5'] else [stock_data['bid1'],stock_data['bid2'],stock_data['bid3']],
            'b_vol': [stock_data['bid_vol1'],stock_data['bid_vol2'],stock_data['bid_vol3']],
            'sell': [stock_data['ask1']/10,stock_data['ask2']/10,stock_data['ask3']/10] if tmp_code[0] in ['1','5'] else [stock_data['ask1'],stock_data['ask2'],stock_data['ask3']],
            's_vol': [stock_data['ask_vol1'],stock_data['ask_vol2'],stock_data['ask_vol3']],
        }
        api.disconnect()
        return data
    else:
        print("无法连接到服务器")
        return False

def order(data, type):
    choice= {
        'BUY': ['buy', 'b_vol'],
        'SELL': ['sell', 's_vol']
    }
    rec = get_price(data.get('code', ''))
    pri = choice[type][0]
    vol = choice[type][1]
    if rec:
        if rec[pri][0] == 0.0:
            return jsonify({"answer": "已经涨停无法买入" if pri == 'buy' else "已经跌停无法卖出"}), 500
        pct = data.get('pct', 0)
        # amt = int(pct / rec[pri][1] / 100) * 100
        amt = pct
        if (amt / 100) < (rec[vol][0] + rec[vol][1]):
            price = rec[pri][1]
        else:
            price = rec[pri][2]
        now1 = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"{now1}时间：{rec['time']} {type}账号：{data.get('strategy','')} 金额：{price * amt} 价格：{price} 数量：{amt}")
        message_data = {
            'stg': data.get('strategy',''),
            'type': type,
            'code': data.get('code', ''),
            'amt': amt,
            'price': price,
            'ttype' : ""
        }
        return message_data
    else:
        return None

@app.route('/api', methods=['POST'])
def api():
    try:
        data = request.json
        print(f"收到数据：{data}")
        type = data.get('type', '')
        if type == 'BUY' or type == 'SELL':
            message_data = order(data, type)
            if message_data:
                 return jsonify({"answer": message_data}), 200
            else:
                return jsonify({"answer": "无法获取股票数据"}), 500               
        elif type == 'balance':
            print(f"查询账号：{data.get('stg','')} 购买记录：{data}\n")
        elif type == 'trade':
            print(f"成交账号：{data.get('stg','')} 购买记录：{data}\n")
        elif type == 'position':
            print(f"持仓账号：{data.get('stg','')} 购买记录：{data}\n")
        elif type == 'cancel':
            print(f"撤单账号：{data.get('stg','')} 购买记录：{data}\n")
        else:
            print(f"未知类型：{type} \n")
            return jsonify({"answer": "未知类型"}), 203
        return jsonify({"answer": '正常'}), 200
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"answer": f"{e}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0')