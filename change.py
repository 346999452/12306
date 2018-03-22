# ! usr/bin/env python
# -*- coding:utf-8 -*-
"""

    @author: 南辙一曲风华顾
    @file: change
    @time: 2018/03/21
    
"""
from login import *
import datetime

class Change(Login):

    def __init__(self):
        Login.__init__(self)
        self.from_station = self.set['from_station']                    # 出发站
        self.to_station = self.set['to_station']                        # 到达站
        self.is_check_user = dict()

    def conversion_int(self, str):
        return int(str)

    def time(self):
        today = datetime.date.today()
        tomorrow = today + datetime.timedelta(1)
        return tomorrow.strftime('%Y-%m-%d')

    ''' 获取坐席对应的代号码 '''
    def get_seat_code(self, seat_type):
        self.seat_code = str(self.get_json('config/seat.json')[seat_type].split(',')[1])
        return self.seat_code

    ''' 获取车次信息 '''
    def get_traf_info(self, from_station, to_station, station_date=None):
        select_url = self.get_url("select_url").format(
            station_date, from_station, to_station)
        info_json = self.send(select_url)
        return json.loads(info_json)

    ''' 将中文的站台名转换为字母代码 '''
    def get_station(self):
        station_name = self.get_json('config/station.json')
        return station_name[self.from_station], station_name[self.to_station]

    ''' 查询座次对应的数组位置 '''
    def station_seat(self, index):
        return int(self.get_json('config/seat.json')[index].split(',')[0])

    def call_login(self, auth=False):
        if auth:
            return self.auth()
        else:
            self.go_login()

    ''' 获取订单前需要进入订单列表页，获取订单列表页session '''
    def init_order_page(self):
        self.set_cookies(acw_tc="AQAAAG75UVgW1gwAq2Xet1Akn/mfpvEw", current_captcha_type="Z")
        url = self.get_url("initNoCompleteUrl")
        data = {"_json_att": ""}
        self.send(url, data)

    ''' 检查用户是否达到订票条件 '''
    def check_user(self):
        check_user_url = self.get_url('check_user_url')
        data = {"_json_att": ""}
        check_user = self.send(check_user_url, data)
        check_user_flag = check_user['data']['flag']
        if check_user_flag is True:
            self.is_check_user["user_time"] = datetime.datetime.now()
        else:
            if check_user['messages']:
                print('用户检查失败：{}，可能未登录，可能session已经失效'.format(check_user['messages'][0]))
            else:
                print('用户检查失败： {}，可能未登录，可能session已经失效'.format(check_user))
            print('正在尝试重新登录')
            self.call_login()
            self.is_check_user["user_time"] = datetime.datetime.now()

if __name__ == '__main__':
    c = Change()
    print(c.get_station())
