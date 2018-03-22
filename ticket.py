#! usr/bin/env python
#-*- coding=utf-8 -*-
"""

    @author: 南辙一曲风华顾
    @file: ticket
    @date: 2018/01/25
    
"""
from time import localtime, strftime, time
from urllib.request import unquote
from collections import OrderedDict
from dama2 import *
from change import *
from send_email import Send_Mail
import re

class select(DamatuApi, Change):

    def __init__(self):
        DamatuApi.__init__(self)
        Change.__init__(self)

        self.station_dates = self.set['station_dates']                          # 乘车日期
        self.seat_type = self.set['seat_type']                                  # 坐席
        self.is_more_ticket = self.set['is_more_ticket']                        # 是否有票自动提交
        self.ticke_peoples = self.set['ticke_peoples']                          # 乘车人
        self.select_refresh_interval = self.set['select_refresh_interval']      # 刷新间隔
        self.station_trains = self.set['station_trains']                        # 候选购买车次
        self.expect_refresh_interval = self.set['expect_refresh_interval']      # 未开始刷票间隔时间
        self.ticket_black_list_time = self.set['ticket_black_list_time']        # 僵尸票关小黑屋时长

        self.order_request_params = {}                                          # 订单提交时的参数
        self.passenger_form = {}                                                # 初始化当前页面参数
        self.current_seats = {}                                                 # 席别信息
        self.token = ''
        self.user_info = ''
        self.secretStr = ''

        self.seat_code = ''
        self.ticket_black_list = dict()

    def passenger_info(self):
        passengerTicketStr = []
        oldPassengerStr = []
        if not self.user_info:
            print('联系人不在列表内，请查证后添加')
        else:
            for i in self.user_info:
                passengerTicketStr.append('{},0,' + i['passenger_type'] + ',' + i['passenger_name'] + ',' +
                                          i['passenger_id_type_code'] + ',' + i['passenger_id_no'] + ',' +
                                          i['mobile_no'] + ',N')
                oldPassengerStr.append(i['passenger_name'] + ',' + i['passenger_id_type_code'] + ',' +
                                       i['passenger_id_no'] + ',' + i['passenger_type'] + '_')
        return passengerTicketStr, oldPassengerStr

    ''' 提交车次 '''
    def submit_station(self):
        submit_station_url = self.get_url("submit_station_url")
        data = [('secretStr', unquote(self.secretStr)),             # 字符串加密
                ('train_date', self.time()),                        # 出发时间
                ('back_train_date', self.time()),                   # 返程时间
                ('tour_flag', 'dc'),                                # 旅途类型
                ('purpose_codes', 'ADULT'),                         # 成人票还是学生票
                ('query_from_station_name', self.from_station),     # 起始车站
                ('query_to_station_name', self.to_station),         # 终点车站
                ]
        result = self.send(submit_station_url, data)
        if 'data' in result and result['data']:
            if result['data'] == 'N':
                print ('出票成功')
            else:
                print ('出票失败')
        elif 'messages' in result and result['messages']:
            print(result['messages'][0])

    """ 提交车次信息 """
    def submit_traf_info(self, from_station, to_station,):
        station_tickets = [self.get_traf_info(from_station, to_station, station_date) for station_date in self.station_dates]
        for station_ticket in station_tickets:
            value = station_ticket['data']
            if not value:
                print ('{0}-{1} 车次坐席查询为空...'.format(self.from_station, self.to_station))
            else:
                if value['result']:
                    for i in value['result']:
                        ticket_info = i.split('|')
                        if ticket_info[11] == "Y" and ticket_info[1] == "预订":  # 筛选未在开始时间内的车次
                            for tp in self.seat_type:
                                is_ticket_pass = ticket_info[self.station_seat(tp)]
                                '''
                                    is_ticket_pass: 座位类型对应在获取车次信息数组中的位置
                                    ticket_info[3]: 车次号
                                    station_trains: 需要购买的车次号
                                '''
                                if is_ticket_pass != '' and is_ticket_pass != '无' and ticket_info[3] in self.station_trains and is_ticket_pass != '*':  # 过滤有效目标车次
                                    self.secretStr = ticket_info[0]
                                    train_no = ticket_info[3]
                                    if train_no in self.ticket_black_list and (datetime.datetime.now() - self.ticket_black_list[train_no]).seconds / 60 < int(self.ticket_black_list_time):
                                        print("该车次{} 正在被关小黑屋，跳过此车次".format(train_no))
                                        break
                                    else:
                                        print ('正在尝试提交订票...', train_no)
                                        self.submit_station()
                                        self.get_seat_code(tp)
                                        self.set_token()
                                        if not self.user_info:  # 修改每次都调用用户接口导致用户接口不能用
                                            self.user_info = self.get_passengers()
                                        if self.check_order_info(train_no, tp):
                                            print(1)
                                            break
                                else:
                                    pass
                        else:
                            pass
                    sleep(self.expect_refresh_interval)
                else:
                    print("车次配置信息有误，或者返回数据异常，请检查 {}".format(station_ticket))

    ''' 获取订单列表信息 '''
    def get_my_order(self):
        self.init_order_page()
        url = self.get_url("queryMyOrderNoCompleteUrl")
        data = {"_json_att": ""}
        try:
            result = self.send(url, data)
        except ValueError:
            result = {}
        if result:
            if "data" in result and result["data"] and "orderDBList" in result["data"] and result["data"][
                "orderDBList"]:
                orderId = result["data"]["orderDBList"][0]["sequence_no"]
                return orderId
            elif "data" in result and "orderCacheDTO" in result["data"] and result["data"]["orderCacheDTO"]:
                if "message" in result["data"]["orderCacheDTO"] and result["data"]["orderCacheDTO"]["message"]:
                    print(result["data"]["orderCacheDTO"]["message"]["message"])
            else:
                print('目前没有订单')
        else:
            print("接口 {} 无响应".format(url))

    ''' 获取乘客信息 '''
    def get_passengers(self):
        url = self.get_url("get_passengerDTOs")
        data = {
            '_json_att': None,
            'REPEAT_SUBMIT_TOKEN': self.token
        }
        result = self.send(url, data)
        if 'data' in result and result['data'] and 'normal_passengers' in result['data'] and result['data']['normal_passengers']:
            all_passengers = result['data']['normal_passengers']
            order_passengers = [all_passengers[i] for i in range(len(all_passengers))if all_passengers[i]["passenger_name"] in self.ticke_peoples]
            
            ''' 返回常用联系人里的配置的联系人信息，如果所有配置乘车人没有在账号，则默认返回第一个用户，一般为号主 '''
            return order_passengers if order_passengers else [all_passengers[0]]
        else:
            if 'data' in result and 'exMsg' in result['data'] and result['data']['exMsg']:
                print(result['data']['exMsg'])
            elif 'messages' in result and result['messages']:
                print(result['messages'][0])
            else:
                print("未查找到常用联系人")
                print("未查找到常用联系人,请先添加联系人在试试")

    ''' 检查支付订单 '''
    def check_order_info(self, train_no, seat_type):
        passenger_list, passenger_str = self.passenger_info()
        checkOrderInfoUrl = self.get_url("checkOrderInfoUrl")
        seat_code = self.get_seat_code(seat_type)

        ''' OrderedDict相对于一般的dict是有序的，且排序按照插入的顺序而非key的顺序 '''
        data = OrderedDict()
        data['cancel_flag'] = 2
        data['bed_level_order_num'] = "000000000000000000000000000000"
        data['passengerTicketStr'] = "_".join(passenger_list).format(* [seat_code] * len(passenger_list))
        data['oldPassengerStr'] = "".join(passenger_str)
        data['tour_flag'] = 'dc'
        data['whatsSelect'] = 1
        data['REPEAT_SUBMIT_TOKEN'] = self.token
        check_order_info = self.send(checkOrderInfoUrl, data)
        if 'data' in check_order_info:
            if "ifShowPassCode" in check_order_info["data"] and check_order_info["data"]["ifShowPassCode"] == "Y":
                is_need_code = True
                if self.get_queue_count(train_no, seat_type, is_need_code):
                    return True
            if "ifShowPassCode" in check_order_info["data"] and check_order_info['data']['submitStatus'] is True:
                print('车票提交通过，正在尝试排队')
                is_need_code = False
                if self.get_queue_count(train_no, seat_type, is_need_code):
                    return True
            else:
                if "errMsg" in check_order_info['data'] and check_order_info['data']["errMsg"]:
                    print(check_order_info['data']["errMsg"])

                else:
                    print(check_order_info)
        elif 'messages' in check_order_info and check_order_info['messages']:
            print(check_order_info['messages'][0])

    ''' 获取提交车票请求token '''
    def set_token(self):
        initdc_url = self.get_url("initdc_url")
        initdc_result = self.send(initdc_url)
        token_name = re.compile(r"var globalRepeatSubmitToken = '(\S+)'")
        passenger_form_name = re.compile(r'var ticketInfoForPassengerForm=(\{.+\})?')
        order_request_params_name = re.compile(r'var orderRequestDTO=(\{.+\})?')
        self.token = re.search(token_name, initdc_result).group(1)
        re_tfpf = re.findall(passenger_form_name, initdc_result)
        re_orp = re.findall(order_request_params_name, initdc_result)
        if re_tfpf:
            self.passenger_form = json.loads(re_tfpf[0].replace("'", '"'))
        else:
            pass
        if re_orp:
            self.order_request_params = json.loads(re_orp[0].replace("'", '"'))
        else:
            pass

    ''' 模拟查询当前的列车排队人数的方法,返回信息组成的提示字符串 '''
    def get_queue_count(self, train_no, seat_type, is_need_code):
        l_time = localtime(time())
        new_train_date = strftime("%a %b %d %Y", l_time)
        url = self.get_url("getQueueCountUrl")
        data = {
            'train_date': str(new_train_date) + " 00:00:00 GMT+0800 (中国标准时间)",
            'train_no': self.passenger_form['queryLeftTicketRequestDTO']['train_no'],
            'stationTrainCode':	self.passenger_form['queryLeftTicketRequestDTO']['station_train_code'],
            'seatType':	self.seat_type,
            'fromStationTelecode': self.passenger_form['queryLeftTicketRequestDTO']['from_station'],
            'toStationTelecode': self.passenger_form['queryLeftTicketRequestDTO']['to_station'],
            'leftTicket': self.passenger_form['leftTicketStr'],
            'purpose_codes': self.passenger_form['purpose_codes'],
            'train_location': self.passenger_form['train_location'],
            'REPEAT_SUBMIT_TOKEN': self.token,
        }
        result = self.send(url, data)
        print(result)
        if "status" in result and result["status"] is True:
            if "countT" in result["data"]:
                ticket = result["data"]["ticket"]
                ticket_split = sum(map(self.conversion_int, ticket.split(","))) if ticket.find(",") != -1 else ticket
                countT = result["data"]["countT"]
                if int(countT) is 0:
                    if int(ticket_split) < len(self.user_info):
                        print("当前余票数小于乘车人数，放弃订票")
                    else:
                        print("排队成功, 当前余票还剩余: {0} 张".format(ticket_split))
                        if self.check_queue_order(is_need_code):
                            return True
                else:
                    print("当前排队人数:" + str(countT) + "当前余票还剩余:{0} 张，继续排队中".format(ticket_split))
            else:
                print("排队发现未知错误{0}，将此列车 {1}加入小黑屋".format(result, train_no))
                self.ticket_black_list[train_no] = datetime.datetime.now()
        elif "messages" in result and result["messages"]:
            print("排队异常，错误信息：{0}, 将此列车 {1}加入小黑屋".format(result["messages"][0], train_no))
            self.ticket_black_list[train_no] = datetime.datetime.now()
        else:
            if "validateMessages" in result and result["validateMessages"]:
                print(str(result["validateMessages"]))
                self.ticket_black_list[train_no] = datetime.datetime.now()
            else:
                print("未知错误 {0}".format("".join(result)))

    ''' 模拟提交订单是确认按钮，参数获取方法还是get_passenger_form 中获取 '''
    def check_queue_order(self, is_node_code=False):
        passenger_list, passenger_str = self.passenger_info()
        url = self.get_url("checkQueueOrderUrl")
        data = {
            "passengerTicketStr": self.seat_type + "," + ",".join(passenger_list).rstrip("_{0}".format(self.seat_type)),
            "oldPassengerStr": "".join(passenger_str),
            "purpose_codes": self.passenger_form["purpose_codes"],
            "key_check_isChange": self.passenger_form["key_check_isChange"],
            "leftTicketStr": self.passenger_form["leftTicketStr"],
            "train_location": self.passenger_form["train_location"],
            "seatDetailType": "000",                            # 开始需要选择座位，但是目前12306不支持自动选择作为，那这个参数为默认
            "roomType": "00",                                   # 好像是根据一个id来判断选中的，两种 第一种是00，第二种是10，但是我在12306的页面没找到该id，目前写死是00，不知道会出什么错
            "dwAll": "N",
            "whatsSelect": 1,
            "_json_at": "",
            "REPEAT_SUBMIT_TOKEN": self.token,
        }
        try:
            for i in range(3):
                if is_node_code:
                    print("正在使用自动识别验证码功能")
                    ansyn_url = self.get_url("checkRandCodeAnsyn")
                    code_img = self.get_url("codeImgByOrder").format(random.random())
                    result = self.send(code_img)
                    img_path = './tkcode'
                    open(img_path, 'wb').write(result)
                    rand_code = self.decode(img_path, 287)
                    rand_data = {
                        "randCode": rand_code,
                        "rand": "randp",
                        "_json_att": None,
                        "REPEAT_SUBMIT_TOKEN": self.token
                    }
                    check_code = self.send(ansyn_url, rand_data)['data']['msg']
                    if check_code == 'TRUE':
                        print("验证码通过,正在提交订单")
                        data['randCode'] = rand_code
                        break
                    else:
                        print ("验证码有误")
                else:
                    print("不需要验证码")
                    break
            result = self.send(url, data)
            if "status" in result and result["status"]:
                c_data = result["data"] if "data" in result else {}
                if 'submitStatus' in c_data and c_data['submitStatus'] is True:
                    print("提交订单成功！")
                    self.query_wait()
                else:
                    if 'errMsg' in c_data and c_data['errMsg']:
                        print("提交订单失败，{0}".format(c_data['errMsg']))
                    else:
                        print(c_data)
                        print('订票失败!很抱歉,请重试提交预订功能!')
            elif "messages" in result and result["messages"]:
                print("提交订单失败,错误信息: " + result["messages"])
            else:
                print("提交订单中，请耐心等待：" + str(result["validateMessages"]))
        except ValueError:
            print("接口无响应")

    ''' 排队获取订单等待信息,每隔3秒请求一次，最高请求次数为20次！ '''
    def query_wait(self):
        num = 1
        while True:
            _random = int(round(time() * 1000))
            num += 1
            if num > 30:
                print("超出排队时间，自动放弃，正在重新刷票")
                order_id = self.get_my_order()  # 排队失败，自动取消排队订单
                if order_id:
                    self.cancel_order(order_id)
                break
            try:
                data = {"random": _random, "tourFlag": "dc"}
                url = self.get_url("queryOrderWaitTimeUrl")
                result = self.send(url, data)
            except ValueError:
                result = {}
            if result:
                if "status" in result and result["status"]:
                    if "orderId" in result["data"] and result["data"]["orderId"] is not None:
                        Send_Mail().send_email("恭喜您订票成功，订单号为：{}, 请立即打开浏览器登录12306，访问‘未完成订单’，在30分钟内完成支付！".format(result["data"]["orderId"]))
                        print("恭喜您订票成功，订单号为：{}, 请立即打开浏览器登录12306，访问‘未完成订单’，在30分钟内完成支付！".format(result["data"]["orderId"]))
                    elif "msg" in result["data"] and result["data"]["msg"]:
                        print(result["data"]["msg"])
                        break
                    elif "waitTime"in result["data"] and result["data"]["waitTime"]:
                        print("排队等待时间预计还剩 {0} ms".format(0-result["data"]["waitTime"]))
                    else:
                        print ("正在等待中")
                elif "messages" in result and result["messages"]:
                    print("排队等待失败： " + result["messages"])
                else:
                    print("第{}次排队中,请耐心等待".format(num))
            else:
                print("排队中")
            sleep(2)

        else:
            print("订单提交失败！,正在重新刷票")

    ''' 取消订单 '''
    def cancel_order(self, sequence_no):
        url = self.get_url("cancelNoCompleteMyOrder")
        data = {
            "sequence_no": sequence_no,
            "cancel_flag": "cancel_order",
            "_json_att": ""
        }
        result = self.send(url, data)
        if "data" in result and "existError" in result["data"] and result["data"]["existError"] == "N":
            print("排队超时，已为您自动取消订单，订单编号: {}".format(sequence_no))
            sleep(2)
            return True
        else:
            print("排队超时，取消订单失败，订单号{}".format(sequence_no))

    def main(self):
        self.call_login()
        from_station, to_station = self.get_station()
        self.check_user()
        num = 1
        while True:
            try:
                num += 1
                if "user_time" in self.is_check_user and (datetime.datetime.now() - self.is_check_user["user_time"]).seconds/60 > 5:
                    self.check_user()                                       # 十分钟检查一次用户是否登录
                sleep(self.select_refresh_interval)
                if strftime('%H:%M:%S', localtime(time())) > "23:00:00":
                    print("12306休息时间，本程序自动停止,明天早上6点将自动运行")
                    sleep(60 * 60 * 7)
                    self.call_login()
                start_time = datetime.datetime.now()
                self.submit_traf_info(from_station, to_station)
                print("正在第{0}次查询  乘车日期: {1}  车次{2} 查询无票  代理设置 无  总耗时{3}ms".format(num, ",".join(self.station_dates), ",".join(self.station_trains), (datetime.datetime.now()-start_time).microseconds/1000))
            except Exception as e:
                if e.args[0] == "No JSON object could be decoded":
                    print("12306接口无响应，正在重试")
                else:
                    print(e)
                    print('嘿，boy，你又整错了')

if __name__ == '__main__':
    s = select()
    s.main()
