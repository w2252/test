# -*- coding: utf-8 -*-
import efinance as ef
from django.shortcuts import render
from datetime import datetime
from DjangoWeb import ma
import time
from django.views.decorators import csrf
import json


# 接收POST请求数据
def monitor_post(request):
    ctx = {}
    if request.POST:
        ctx['rlt'] = request.POST['day1']
        day1 = request.POST.get("day1")
        day2 = request.POST.get("day2")
        day3 = request.POST.get("day3")
        # 获取连续涨停股票的id的list
        stock_codes = ma.get_twohigh_id(day3, day2)
        ma.msg_wx(f"一共选中了{len(stock_codes)}条股票")
        # 发送股票id
        for stockcode in stock_codes:
            ma.msg_wx(str(stockcode))
        # 数据间隔时间为 1 分钟
        freq = 1
        status = {stock_code: 0 for stock_code in stock_codes}
        data = ef.stock.get_latest_quote(stock_codes)
        columns = ['代码', '名称', '今开']
        data['五日涨停线'] = 0
        data['五日涨停线上界'] = 0
        data['五日涨停线下界'] = 0
        data['pos1'] = 0  # 破了五日涨停线上界的标志
        data['pos2'] = 0  # 在第一次破了五日涨停线下的条件下，再次破了五日线标志
        data['pos3'] = 0  # 破了五日涨停线的标志
        data['pos4'] = 0  # 回归到五日涨停线，但未下降达到五日涨停线下界的标志/无用
        data['pos5'] = 0  # 第一次破了五日涨停线下界的标志
        data['pos6'] = 0  # 破了五日涨停线后，将该股票排除的标志
        data['pos7'] = 0  # 破了五日涨停线下界之后回归到五日涨停线的标志/无用
        data['pos8'] = 0  # 破了五日涨停线下界之后回归到五日涨停线上界的标志/无用
        # 建立一个存储五日涨停线和布林线的表
        for i in range(len(data)):
            five_price = ma.get_fiveprice(sec_id=data.iloc[i]['代码'], date=day1)
            data.at[i, '五日涨停线'] = five_price
            data.at[i, '五日涨停线上界'] = five_price * 1.01
            data.at[i, '五日涨停线下界'] = five_price * 0.99
        stock_codes = []
        for i in range(len(data)):
            if data.loc[i]['今开'] < data.iloc[i]['五日涨停线上界']:  # 列表中删除该股票
                print(f"代码为{data.loc[i]['代码']}的{data.loc[i]['名称']}因为开盘低于五日涨停线下界而被删除停止监控")
                ma.msg_wx(
                    f"代码为{data.loc[i]['代码']}的{data.loc[i]['名称']}因为开盘低于五日涨停线下界而被删除停止监控")
            else:
                stock_codes.append(str(data.loc[i]['代码']))
        data = data[data['今开'] >= data['五日涨停线上界']]
        data = data[data['五日涨停线'] != -1]
        # 重置索引
        data = data.reset_index(drop=True)
        while len(stock_codes) != 0:
            # 获取最新一个交易日的分钟级别股票行情数据
            df = ef.stock.get_latest_quote(stock_codes)
            # 现在的时间
            now = str(datetime.today()).split('.')[0]
            # print(f"现在时间：{now},正在监控中")
            for i in range(len(data)):
                if data.iloc[i]['pos6'] == 1:
                    continue
                if df.iloc[i]['最新价'] <= data.iloc[i]['五日涨停线上界'] and data.iloc[i]['pos1'] == 0:
                    print(f"代码为{data.iloc[i]['代码']}的{data.iloc[i]['名称']}于时间{now}突破了五日涨停线上界")
                    ma.msg_wx(f"代码为{data.iloc[i]['代码']}的{data.iloc[i]['名称']}于时间{now}突破了五日涨停线上界")
                    print(
                        f"股票现价为{df.iloc[i]['最新价']}五日涨停线上界为{data.iloc[i]['五日涨停线上界']},五日涨停线为{data.iloc[i]['五日涨停线']}")
                    ma.msg_wx(
                        f"股票现价为{df.iloc[i]['最新价']}五日涨停线上界为{data.iloc[i]['五日涨停线上界']},五日涨停线为{data.iloc[i]['五日涨停线']}")
                    data.at[i, 'pos1'] = 1
                if df.iloc[i]['最新价'] <= data.iloc[i]['五日涨停线'] and data.iloc[i]['pos1'] == 1 and data.iloc[i][
                    'pos3'] == 0:
                    print(f"代码为{data.iloc[i]['代码']}的{data.iloc[i]['名称']}于时间{now}突破了五日涨停线")
                    print(
                        f"股票现价为{df.iloc[i]['最新价']}五日涨停线下界为{data.iloc[i]['五日涨停线下界']},五日涨停线为{data.iloc[i]['五日涨停线']}")
                    ma.msg_wx(f"代码为{data.iloc[i]['代码']}的{data.iloc[i]['名称']}于时间{now}突破了五日涨停线")
                    ma.msg_wx(
                        f"股票现价为{df.iloc[i]['最新价']}五日涨停线下界为{data.iloc[i]['五日涨停线下界']},五日涨停线为{data.iloc[i]['五日涨停线']}")
                    data.at[i, 'pos3'] = 1
                if df.iloc[i]['最新价'] > data.iloc[i]['五日涨停线上界'] and data.iloc[i]['pos1'] == 1 and data.iloc[i][
                    'pos3'] == 0:
                    print(
                        f"代码为{data.iloc[i]['代码']}的{data.iloc[i]['名称']}于时间{now}回归到了五日涨停线上界，且未突破五日涨停线")
                    print(f"股票现价为{df.iloc[i]['最新价']}五日涨停线上界为{data.iloc[i]['五日涨停线上界']}")
                    ma.msg_wx(
                        f"代码为{data.iloc[i]['代码']}的{data.iloc[i]['名称']}于时间{now}回归到了五日涨停线上界，且未突破五日涨停线")
                    ma.msg_wx(f"股票现价为{df.iloc[i]['最新价']}五日涨停线上界为{data.iloc[i]['五日涨停线上界']}")
                    # 回归到五日涨停线上界以后全部清零重新计数
                    data.at[i, 'pos1'] = 0
                    data.at[i, 'pos2'] = 0
                    data.at[i, 'pos3'] = 0
                    data.at[i, 'pos4'] = 0
                    data.at[i, 'pos5'] = 0
                    data.at[i, 'pos7'] = 0
                    data.at[i, 'pos8'] = 0
                    continue
                if df.iloc[i]['最新价'] <= data.iloc[i]['五日涨停线下界'] and data.iloc[i]['pos1'] == 1 and \
                        data.iloc[i]['pos3'] == 1 and data.iloc[i]['pos5'] == 0:
                    print(f"代码为{data.iloc[i]['代码']}的{data.iloc[i]['名称']}于时间{now}突破了五日涨停线下界")
                    print(
                        f"股票现价为{df.iloc[i]['最新价']}五日涨停线下界为{data.iloc[i]['五日涨停线下界']},五日涨停线为{data.iloc[i]['五日涨停线']}")
                    ma.msg_wx(f"代码为{data.iloc[i]['代码']}的{data.iloc[i]['名称']}于时间{now}突破了五日涨停线下界")
                    ma.msg_wx(
                        f"股票现价为{df.iloc[i]['最新价']}五日涨停线下界为{data.iloc[i]['五日涨停线下界']},五日涨停线为{data.iloc[i]['五日涨停线']}")
                    data.at[i, 'pos5'] = 1
                    data.at[i, 'pos6'] = 1
                    print(
                        f"代码为{data.iloc[i]['代码']}的{data.iloc[i]['名称']}由于突破了五日涨停线下界而将其排除监控名单")
                    continue
                if df.iloc[i]['最新价'] > data.iloc[i]['五日涨停线'] and data.iloc[i]['pos3'] == 1 and data.iloc[i][
                    'pos5'] == 0:
                    print(
                        f"代码为{data.iloc[i]['代码']}的{data.iloc[i]['名称']}于时间{now}回归到了五日涨停线，且未突破五日涨停线下界")
                    print(
                        f"股票现价为{df.iloc[i]['最新价']}五日涨停线上界为{data.iloc[i]['五日涨停线上界']},五日涨停线为{data.iloc[i]['五日涨停线']}")
                    ma.msg_wx(
                        f"代码为{data.iloc[i]['代码']}的{data.iloc[i]['名称']}于时间{now}回归到了五日涨停线，且未突破五日涨停线下界")
                    ma.msg_wx(
                        f"股票现价为{df.iloc[i]['最新价']}五日涨停线上界为{data.iloc[i]['五日涨停线上界']},五日涨停线为{data.iloc[i]['五日涨停线']}")
                    # 部分需要清零
                    data.at[i, 'pos3'] = 0
                    continue
            # print('暂停 40 秒')
            time.sleep(10)
    return render(request, "post.html", ctx)
