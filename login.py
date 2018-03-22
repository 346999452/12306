#! usr/bin/env python
#-*- coding=utf-8 -*-
"""

    @author: 南辙一曲风华顾
    @file: login
    @date: 2018/01/25
    
"""
from time import sleep
from PIL import Image
from random import random
from methods import *
from http_client import *

class Login(Methods, Http_Client):

    def __init__(self):
        Http_Client.__init__(self)
        self.set = self.get_yaml('config/config.yaml')['set']
        self.conf_url = self.get_json('config/12306_urls.json')
        self.username = self.set['12306count']['username']
        self.password = self.set['12306count']['password']

    def get_url(self, url):
        return 'https://kyfw.12306.cn/' + self.conf_url[url]

    def cookietp(self):
        url = self.get_url('loginInit')
        self.send(url)

    def read_image(self):
        print ('正在下载验证码...')
        codeimgUrl = self.get_url('getCodeImg').format(random())
        img_path = self.absolute_path + 'image/source/tkcode.png'
        result = self.send(codeimgUrl)
        try:
            with open(img_path, 'wb') as f:
                f.write(result)
            img = Image.open(img_path)
            img.show()
        except OSError as e:
            print (e)

    def get_xy(self):
        test_code = input('请输入验证码: ')
        num = [int(_) for _ in test_code]
        coordinate = ['42,46', '105,46', '184,45', '256,48',
                      '42,113', '115,112', '181,114', '252,111']
        return ','.join(list(map(lambda x: coordinate[x - 1], num)))

    ''' 认证 '''
    def auth(self):
        auth_url = self.get_url('auth')
        auth_data = {'appid': 'otn'}
        return self.send(auth_url, auth_data)

    ''' 验证码校验 '''
    def code_check(self):
        code_check = self.get_url('codeCheck')
        code_check_data = {
            'answer': self.get_xy(),
            'rand': 'sjrand',
            'login_site': 'E'
        }
        result = self.send(code_check, code_check_data)
        if 'result_code' in result and result['result_code'] == '4':
            print ('验证码通过,开始登录..')
            return True
        else:
            if 'result_message' in result:
                print(result['result_message'])
            sleep(1)
            self.del_cookies()

    ''' 登录过程 '''
    def base_login(self, user, passwd):

        logurl = self.get_url('login')
        log_data = {
            'username': user,
            'password': passwd,
            'appid': 'otn'
        }
        tresult = self.send(logurl, log_data)
        if 'result_code' in tresult and tresult['result_code'] == 0:
            print ('登录成功')
            tk = self.auth()
            if 'newapptk' in tk and tk['newapptk']:
                return tk['newapptk']
                ''' 登陆成功返回权限校验码 '''
            else:
                return False
        elif 'result_message' in tresult and tresult['result_message']:
            messages = tresult['result_message']
            if messages.find('密码输入错误') is not -1:
                print(messages)
            else:
                print ('登录失败: {0}'.format(messages))
                print ('尝试重新登陆')
                return False
        else:
            return False

    ''' 登录成功后,显示用户名 '''
    def get_username(self, uamtk):
        if not uamtk:
            return '权限校验码不能为空'
        else:
            uamauth_client_url = self.get_url('uamauthclient')
            data = {'tk': uamtk}
            result = self.send(uamauth_client_url, data)
            if result:
                if 'result_code' in result and result['result_code'] == 0:
                    print('欢迎 {} 登录'.format(result['username']))
                    return True
                else:
                    return False
            else:
                self.send(uamauth_client_url, data)
                url = self.get_url('getUserInfo')
                self.send(url)

    ''' 登陆 '''
    def go_login(self):
        while True:
            self.set_cookies(_jc_save_wfdc_flag='dc',
                                         _jc_save_fromStation='%u6210%u90FD%2CCDW',
                                         _jc_save_toStation='%u592A%u539F%2CTYV',
                                         _jc_save_fromDate='2018-02-23',
                                         _jc_save_toDate='2018-01-25',
                                         RAIL_DEVICEID='HAc_gYB8rHQmph2Cj98NpAsTLiUVZx_drRyiOUare1fHBtcaXK88r6RnR7ZfV_eNpQON9RsSRl5FpwfevlLYxAXt_vNqe8SduF6qKvvoGRsxH8K8vi91K4kMxImSjwZ0qWeWAHAVUEJEyIKeBsRZbI5Baiats15F')
            self.read_image()
            self.auth()
            if self.code_check():
                uamtk = self.base_login(self.username, self.password)
                if uamtk:
                    self.get_username(uamtk)
                    break

    def logout(self):
        result = self.get_url('loginOut')
        print ('已退出') if result else print ('退出失败')

if __name__ == '__main__':
    ''' 测试 '''
    login = Login()
    print(login.auth())
    login.go_login()
    print(login.auth())
    login.logout()
    print(login.auth())