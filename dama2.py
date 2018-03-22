#! usr/bin/env python
#-*- coding=utf-8 -*-
"""

    @author: 南辙一曲风华顾
    @file: shi
    @date: 2018/01/24
    
"""
import urllib.request, urllib, base64
from login import *

''' 打码兔API类 '''
class DamatuApi(Login):

    def __init__(self):
        Login.__init__(self)
        self.damatu = self.get_yaml('config/config.yaml')['damatu']
        self.damatu_username = self.damatu['username']
        self.damatu_password = self.damatu['password']
        self.ID = '53577'
        self.KEY = 'a06bf2449b0597e6eb5878ff4f7f7ba0'
        self.HOST = 'http://api.dama2.com:7766/app/'
        self.count = 0
        self.limit_count = 5

    ''' 计算用户签名，按照一定的规则对 key和userName 进行加密 '''
    def getSign(self, param=b''):
        return (self.md5(bytes(self.KEY, encoding="utf8") + bytes(self.damatu_username, encoding="utf8") + param))[:8]

    ''' 获得加密后的密钥 key , userName, password '''
    def getPwd(self):
        return self.hash(self.KEY + self.hash(self.hash(self.damatu_username) + self.hash(self.damatu_password)))

    ''' 向打码平台提交请求 '''
    def post(self, urlPath, formData = {}):
        url = self.HOST + urlPath
        try:
            response = requests.request(method='post',
                                        url=url,
                                        data=formData,
                                        timeout=60
                                        )
            print(f"text = {response.text}")
            return response.text
        except Exception as e:
            print(f"postRequest error. exception = {e}, urlPath = {urlPath}, formData = {formData}")
            return {"ret": -1}

    ''' 查询余额 return 是正数为余额, 如果为负数 则为错误码 '''
    def getBalance(self):
        data = {
            'appID': self.ID,
            'user': self.damatu_username,
            'pwd': self.getPwd(),
            'sign': self.getSign()
        }
        res = self.post('d2Balance', data)
        jres = json.loads(res)
        if jres['ret'] == 0:
            return (True, jres['balance'])
        else:
            return (False, jres['ret'])

    ''' 上传验证码图片 '''
    def decode(self, filePath, type):
        if self.count >= self.limit_count:
            print(f"decode: 请求验证码数量超过限制自定义数量。")
            return (False, False)

        f = open(filePath, 'rb')
        fdata = f.read()
        filedata = base64.b64encode(fdata)
        f.close()
        data = {
            'appID': self.ID,
            'user': self.damatu_username,
            'pwd': self.getPwd(),
            'type': type,
            'fileDataBase64': filedata,
            'sign': self.getSign(fdata)
        }
        res = self.post('d2File', data)
        jres = json.loads(res)
        self.count += 1
        if jres['ret'] == 0:
            return (True, jres['result'])
        else:
            return (False, jres['ret'])

    ''' url地址打码，提供验证码链接 '''
    def decodeUrl(self, url, type):
        if self.count >= self.limit_count:
            print(f"decodeUrl: 请求验证码数量超过限制自定义数量。")
            return (False, False)

        data = {
            'appID': self.ID,
            'user': self.damatu_username,
            'pwd': self.getPwd(),
            'type': type,
            'url': urllib.request.quote(url),
            'sign': self.getSign(url.encode(encoding="utf-8"))
        }
        res = self.post('d2Url', data)
        jres = json.loads(res)
        self.count += 1
        if jres['ret'] == 0:
            return (True, jres['result'])
        else:
            return (False, jres['ret'])

    ''' 报错，暂时先不关心。 参数id(string类型)由上传打码函数的结果获得 return 0为成功 其他见错误码 '''
    def reportError(self, id):
        data = {
            'appID': self.ID,
            'user': self.damatu_username,
            'pwd': self.getPwd(),
            'id': id,
            'sign': self.getSign(id.encode(encoding="utf-8"))
        }
        res = self.post('d2ReportError', data)
        res = str(res, encoding="utf-8")
        jres = json.loads(res)
        return jres['ret']

if __name__ == '__main__':
    dmt = DamatuApi()
    print(dmt.decode('./1.png', 42))