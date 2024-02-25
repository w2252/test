import efinance as ef
import pandas as pd
import numpy as np
from typing import Dict
from datetime import datetime
import requests
from scipy.optimize import fsolve
import json
import os
from pathlib import Path

# 布林线指标，输入值为单个股票id,返回值为一个列表，顺序为布林线下轨，布林线中轨，布林线上轨(历史)
def get_bollinger( sec_id:str, date:str):
    df = ef.stock.get_quote_history(sec_id)
    index_date = df[df['日期'] == date].index[0]
    my_array = np.array([])
    for i in range(index_date - 19, index_date+1):
        my_array = np.append(my_array, df.at[i, '收盘'])

    bollinger_middle = my_array.mean()
    bollinger_high = bollinger_middle + np.std(my_array) * 2
    bollinger_low = bollinger_middle - np.std(my_array) * 2
    return [bollinger_low, bollinger_middle, bollinger_high]

def get_bollinger_hand( sec_id:str, date:str,data:float):
    df = ef.stock.get_quote_history(sec_id)
    index_date = df[df['日期'] == date].index[0]
    my_array = np.array([])
    for i in range(index_date - 18, index_date+1):
        my_array = np.append(my_array, df.at[i, '收盘'])
    my_array = np.append(my_array,data)
    bollinger_middle = my_array.mean()
    bollinger_high = bollinger_middle + np.std(my_array) * 2
    bollinger_low = bollinger_middle - np.std(my_array) * 2
    return [bollinger_low, bollinger_middle, bollinger_high]

# k日均线，输入k值，来获得k日均线（历史）
def get_k_ma (sec_id:str, date:str, k:int):
    df = ef.stock.get_quote_history(sec_id)
    index_date = df[df['日期'] == date].index[0]
    my_array = np.array([])
    for i in range(index_date - k + 1, index_date + 1):
        my_array = np.append(my_array, df.at[i, '收盘'])
    middle = my_array.mean()
    return middle


# 最后一天以最高价作为参数计算布林线（弃用）
def get_bollinger_high( sec_id:str, date:str):
    df = ef.stock.get_quote_history(sec_id)
    index_date = df[df['日期'] == date].index[0]
    my_array = np.array([])
    for i in range(index_date - 19, index_date):
        my_array = np.append(my_array, df.at[i, '收盘'])
    my_array = np.append(my_array, df.at[index_date, '最高'])
    bollinger_middle = my_array.mean()
    bollinger_high = bollinger_middle + np.std(my_array) * 2
    bollinger_low = bollinger_middle - np.std(my_array) * 2
    return [bollinger_low, bollinger_middle, bollinger_high]


# 以实时价格计算实时的布林线（实时价格）
def get_bollinger_now(sec_id:str, date:str):
    df = ef.stock.get_quote_history(sec_id)
    index_date = df[df['日期'] == date].index[0]
    my_array = np.array([])
    for i in range(index_date - 19, index_date):
        my_array = np.append(my_array, df.at[i, '收盘'])
    df1 = ef.stock.get_latest_quote(sec_id)
    my_array = np.append(my_array, df1.at[0,'最新价'])
    bollinger_middle = my_array.mean()
    bollinger_high = bollinger_middle + np.std(my_array) * 2
    bollinger_low = bollinger_middle - np.std(my_array) * 2
    return [bollinger_low, bollinger_middle, bollinger_high]


# 以实时价格计算实时日期的以开盘价计算布林线（实时价格）
def get_bollinger_today_open(sec_id:str, date:str):
    df = ef.stock.get_quote_history(sec_id)
    index_date = df[df['日期'] == date].index[0]
    my_array = np.array([])
    for i in range(index_date - 19, index_date):
        my_array = np.append(my_array, df.at[i, '收盘'])
    df1 = ef.stock.get_latest_quote(sec_id)
    my_array = np.append(my_array, df1.at[0,'最新价'])
    bollinger_middle = my_array.mean()
    bollinger_high = bollinger_middle + np.std(my_array) * 2
    bollinger_low = bollinger_middle - np.std(my_array) * 2
    return [bollinger_low, bollinger_middle, bollinger_high]


def equation_for_high(x, my_array):
    total = sum(my_array) + x
    mean = total / 20
    var = sum((xi - mean) ** 2 for xi in my_array) / 20
    var += (x - mean) ** 2 / 20
    std_dev = np.sqrt(var)
    return x - (mean + 2 * std_dev)


def equation_for_low(x, known_numbers):
    total = sum(known_numbers) + x
    mean = total / 20
    var = sum((xi - mean) ** 2 for xi in known_numbers) / 20
    var += (x - mean) ** 2 / 20
    std_dev = np.sqrt(var)
    return x - (mean - 2 * std_dev)


def equation_for_average(x, known_numbers):
    total = sum(known_numbers) + x
    mean = total / 20
    return x - mean


# 当日计算计算布林线预计交点,输入日期为前一个交易日,返回值为下轨，中轨，上轨
def get_bollinger_today(sec_id:str,Pre_date:str):
    df = ef.stock.get_quote_history(sec_id)
    index_date = df[df['日期'] == Pre_date].index[0]
    my_array = np.array([])
    for i in range(index_date - 18, index_date+1):
        my_array = np.append(my_array, df.at[i, '收盘'])
    # 计算已知数的平均值和标准差
    average = np.mean(my_array)
    std_dev = np.std(my_array)
    # 计算未知数使其满足bollinger_high的条件
    unknown_for_high = (average + 2 * std_dev) * 20 - sum(my_array)
    # 计算未知数使其满足bollinger_low的条件
    unknown_for_low = (average - 2 * std_dev) * 20 - sum(my_array)
    # 计算未知数使其满足average的条件
    unknown_for_average = average * 20 - sum(my_array)
    solution1 = fsolve(equation_for_high, unknown_for_high, args=(my_array,))
    solution2 = fsolve(equation_for_average, unknown_for_average, args=(my_array,))
    solution3 = fsolve(equation_for_low, unknown_for_low, args=(my_array,))
    return [solution3[0], solution2[0], solution1[0]]


def bollinger_test(sec_id:str,date:str,x:float):
    df = ef.stock.get_quote_history(sec_id)
    index_date = df[df['日期'] == date].index[0]
    my_array = np.array([])
    for i in range(index_date - 19, index_date):
        my_array = np.append(my_array, df.at[i, '收盘'])
    df1 = ef.stock.get_latest_quote(sec_id)
    my_array = np.append(my_array, x)
    bollinger_middle = my_array.mean()
    bollinger_high = bollinger_middle + np.std(my_array) * 2
    bollinger_low = bollinger_middle - np.std(my_array) * 2
    return [bollinger_low, bollinger_middle, bollinger_high]


def bollinger_handle():
    my_array = [2788.55, 2830.53, 2883.36, 2910.22, 2906.11, 2820.77, 2770.98, 2756.34, 2832.28, 2845.78, 2833.62, 2893.99, 2886.29, 2881.98, 2886.65, 2877.70, 2893.25, 2887.54, 2929.18]
    # 计算已知数的平均值和标准差
    average = np.mean(my_array)
    std_dev = np.std(my_array)
    # 计算未知数使其满足bollinger_high的条件
    unknown_for_high = (average + 2 * std_dev) * 20 - sum(my_array)
    # 计算未知数使其满足bollinger_low的条件
    unknown_for_low = (average - 2 * std_dev) * 20 - sum(my_array)
    # 计算未知数使其满足average的条件
    unknown_for_average = average * 20 - sum(my_array)
    solution1 = fsolve(equation_for_high, unknown_for_high, args=(my_array,))
    solution2 = fsolve(equation_for_average, unknown_for_average, args=(my_array,))
    solution3 = fsolve(equation_for_low, unknown_for_low, args=(my_array,))
    return [solution3[0], solution2[0], solution1[0]]


# 求五日涨停线
def get_fiveprice( sec_id:str, date:str)->float:
    df = ef.stock.get_quote_history(sec_id)
    index_date = -1
    if len(df[df['日期'] == date])>0:
        index_date = df[df['日期'] == date].index[0]
    if index_date != -1:
        my_array = np.array([])
        for i in range(index_date - 4, index_date):
            my_array = np.append(my_array, df.at[i, '收盘'])
        my_array = np.append(my_array, df.at[index_date - 1, '收盘']*1.1)
        return my_array.sum()/5
    else:
        return -1


# 求k日涨停线
def get_k_price(sec_id:str, date:str, k:int)->float:
    df = ef.stock.get_quote_history(sec_id)
    index_date = -1
    if len(df[df['日期'] == date])>0:
        index_date = df[df['日期'] == date].index[0]
    if index_date != -1:
        my_array = np.array([])
        for i in range(index_date - k + 1, index_date):
            my_array = np.append(my_array, df.at[i, '收盘'])
        my_array = np.append(my_array, df.at[index_date - 1, '收盘']*1.1)
        return my_array.sum()/k
    else:
        return -1


# 获取连续两天涨停的股票
def get_twohigh_id(begin_date:str,end_date:str)->list:
    # 日期格式转换
    date_format_1 = "%Y-%m-%d"
    date_format_2 = "%Y%m%d"
    date_obj_1 = datetime.strptime(begin_date, date_format_1)
    date_obj_2 = datetime.strptime(end_date, date_format_1)
    begindate = date_obj_1.strftime(date_format_2)
    enddate = date_obj_2.strftime(date_format_2)
    file_path = 'data/股票代码.csv'
    BASE_DIR = Path(__file__).resolve(strict=True).parent.parent
    df1= pd.read_csv(os.path.join(BASE_DIR, 'DjangoWeb/static', file_path))
    stock_codes = df1['股票代码'].tolist()
    freq = 101
    result = []
    stocks_df: Dict[str, pd.DataFrame] = ef.stock.get_quote_history(stock_codes, beg=begindate, end=enddate, klt=freq)
    # 筛选出现连续涨停的股票
    stocks_to_remove = []
    for stock_code, df in stocks_df.items():
        pos = 0
        if len(df)==2 and 9.7 < df.loc[0,"涨跌幅"]< 11 and 9.7 <df.loc[1,"涨跌幅"] < 11 :
            pos = 1
        if pos == 0:
            stocks_to_remove.append(stock_code)
    # 删除不符合条件的
    for stock_code in stocks_to_remove:
        del stocks_df[stock_code]
    print("符合连续两天涨停的股票一共有"+str(len(stocks_df))+"个")
    for stock_code, df in stocks_df.items():
        print(df.at[0,'股票代码'])
        result.append(df.at[0,'股票代码'])
    return result


# 获取连续涨停k天的股票列表（从起始天的k个交易日后到终止日开始进行选择）
def get_k_high_id(begin_date: str, end_date: str, k: int) -> list:
    # 日期格式转换
    date_format_1 = "%Y-%m-%d"
    date_format_2 = "%Y%m%d"
    date_obj_1 = datetime.strptime(begin_date, date_format_1)
    date_obj_2 = datetime.strptime(end_date, date_format_1)
    begindate = date_obj_1.strftime(date_format_2)
    enddate = date_obj_2.strftime(date_format_2)
    df1 = pd.read_csv('static/data/股票代码.csv')
    stock_codes = df1['股票代码'].tolist()
    freq = 101
    result = []
    stocks_df: Dict[str, pd.DataFrame] = ef.stock.get_quote_history(stock_codes, beg=begindate, end=enddate, klt=freq)

    for stock_code, df in stocks_df.items():
        if len(df) < k:  # 检查数据长度是否足够
            continue
        for i in range(k-1,len(df)):
            if all(9.7 < df.loc[i - n, "涨跌幅"] < 11 for n in range(k)):
                # 格式化股票代码，确保是6位数
                formatted_code = str(stock_code).zfill(6)
                result.append(formatted_code)
                break  # 找到连续k天涨停后，跳出循环
    return result


# 像企业微信发送消息 ，str为发送的字符串
def msg_wx(message:str):
    Secret = "nrO6EE6QsRD0pWj0uP8YImMg3HbEVUAgh1TOoI0CwMY"
    corpid = 'wwba92dac327f7dc76'
    url = 'https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={}&corpsecret={}'

    getr = requests.get(url=url.format(corpid, Secret))

    access_token = getr.json().get('access_token')
    data = {
        "touser": "WangJiaNing|Lishuxin",  # 向这些用户账户发送
        # "toparty" : "PartyID1|PartyID2",   # 向这些部门发送
        "msgtype": "text",
        "agentid": 1000002,  # 应用的 id 号
        "text": {
            "content": message
        },
        "safe": 0
    }
    r = requests.post(url="https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={}".format(access_token),
                      data=json.dumps(data))
    print(r.json())


# 获取筛选后的利率，address为excel文件的地址，columns_name为需要计算的列名，需要在源文件中添加一列名为“是否买入的列”，并在买入的行填1
def after_filter_profit(address:str, columns_name:str):
    df = pd.read_excel(address)  # 在引号中填写文件的地址，格式如"E:\\burp\\pythonProject\\情况2.xlsx"
    profit_average_1 = 0
    profit_total = 1
    count = 0
    for i in range(len(df)):
        if df.iloc[i]["是否买入"] == 1:
            profit_average_1 += df.iloc[i][columns_name] / 100  # 该行引号内可修改为所需计算列名，如盈利率1，盈利率2
            profit_total *= (df.iloc[i][columns_name] / 100 + 1)  # 该行引号内可修改为所需计算列名，如盈利率1，盈利率2
            count += 1
    profit_average_1 = profit_average_1 / count
    print(f"经过筛选后，买入的平均利率为{profit_average_1}")
    print(f"经过筛选后，假设本金为1，经过全部买入后，本金为{profit_total}")


# base1,base2为确定的两个位置值，pos1，pos2为对应线的位置，填数字1-7，分别对应0%，23.6%，38.2%，50%，61.8%，80.9%，100%
def get_fibonacci_by_two(base1:float,base2:float,pos1:int,pos2:int):
    # 示例：print(get_fibonacci_by_two(57,41.29,1,3))
    dic = {1: 0, 2: 0.236, 3: 0.382, 4: 0.5, 5: 0.618, 6: 0.809, 7: 1}
    a1 = dic.get(pos1)
    a2 = dic.get(pos2)
    diff_ratio = a1 - a2
    diff_real = base1 - base2
    total = diff_real / diff_ratio
    total = abs(total)
    base = total * a1 + base1
    return [base, base - total * 0.236, base - total * 0.382, base - total * 0.5, base - total * 0.618,
            base - total * 0.809, base - total]


# 计算某股票某日的连板数,日期格式20240131
def get_continue_day(stock_id: str, date: str):
    freq = 101
    df = ef.stock.get_quote_history(stock_id, klt=freq)
    i = df[df['日期'] == date].index
    count = 0
    while not i.empty and i[0] >= 0 and df.iloc[i[0]]['涨跌幅'] > 9.8:
        i -= 1
        count += 1
    return count


# 得到一个时间段内，建立一个字典，保存每一天的炸板率，与总体连板率,日期格式20240131
def get_bomb_dictionary(begin_date, end_date):
    bomb_dictionary = {}
    bomb_dictionary_1 = {}
    bomb_dictionary_2 = {}
    con_dictionary = {}
    con_dictionary_1 = {}
    con_dictionary_2 = {}
    freq = 101
    df1 = pd.read_csv('static/data/股票代码.csv')
    stock_codes = df1['股票代码'].astype(str).tolist()  # 将股票代码转换为字符串类型
    temp = ef.stock.get_quote_history('600519',  beg=begin_date, end=end_date, klt=freq)
    date_list = temp['日期'].tolist()
    date_list = date_list[1:]
    # 初始化字典
    for date in date_list:
        bomb_dictionary_1[date] = 0
        bomb_dictionary_2[date] = 0
        bomb_dictionary[date] = 0
        con_dictionary_1[date] = 0
        con_dictionary_2[date] = 0
        con_dictionary[date] = 0
    stocks_df: Dict[str, pd.DataFrame] = ef.stock.get_quote_history(stock_codes, beg=begin_date, end=end_date, klt=freq)
    for stock,df in stocks_df.items():
        for i in range(1,len(df)):
            if df.iloc[i]['最高']-df.iloc[i-1]['收盘']/df.iloc[i-1]['收盘']*100 > 9.8:
                bomb_dictionary_2[df.iloc[i]['日期']] += 1
                if df.iloc[i]['最高'] == df.iloc[i]['收盘']:
                    bomb_dictionary_1[df.iloc[i]['日期']] += 1
            if df.iloc[i-1]['涨跌幅'] > 9.8:
                con_dictionary_2[df.iloc[i]['日期']] += 1
                if df.iloc[i]['涨跌幅'] > 9.8:
                    con_dictionary_1[df.iloc[i]['日期']] += 1
    for date in date_list:
        if bomb_dictionary_2[date] != 0:
            bomb_dictionary[date] = bomb_dictionary_1[date]/bomb_dictionary_2[date]
        if con_dictionary_2[date] != 0:
            con_dictionary[date] = con_dictionary_1[date]/con_dictionary_2[date]
    return bomb_dictionary,con_dictionary


# 得到一个时间段内的，所有交易日，返回一个列表
def get_day_list(begin_date,end_date):
    freq = 101
    temp = ef.stock.get_quote_history('600519', beg=begin_date, end=end_date, klt=freq)
    date_list = temp['日期'].tolist()
    return date_list


# 计算i转i+1连板率，某日
# 计算i转i+1连板率，一段时间
# 测试部分
"""
print(get_bollinger('600519','2023-12-28'))
print(get_k_ma('600519','2023-12-28',10))
print(get_bollinger('002347','2024-01-11'))
print(get_bollinger_high('002347','2024-01-09'))
print(get_bollinger_now('002347','2024-01-11'))

print(get_twohigh_id("2024-01-10","2024-01-11"))


print(get_bollinger('600519','2023-12-28'))
print(get_bollinger('002347','2024-01-11'))
print(get_k_high_id('2023-09-01','2024-01-22',6))
print(get_k_price('600519','2023-12-28',5))
print(get_fiveprice('600519','2023-12-28'))
data = get_twohigh_id("2023-11-16","2023-11-17")
print(data)
print(get_k_high_id('2023-09-01','2024-01-22',6))
print(get_fibonacci_by_two(55.97,45.84,1,2))
after_filter_profit("E:\\burp\\pythonProject\\情况2.xlsx","盈利率")
print(get_continue_day('600519','20240130'))
print(get_bomb_dictionary('20240131','20240208'))
"""