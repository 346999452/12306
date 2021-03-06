#! usr/bin/env python
#-*- coding=utf-8 -*-
"""

    @author: 南辙一曲风华顾
    @file: methods
    @date: 2018/01/25
    
"""
import yaml, json, hashlib, os

class Methods():

    resource_path = '12306/'
    absolute_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/' + resource_path

    '''  
        这里都采用静态方法是为了既能让继承Methods类的类使用
        也让其他方法也能不实例化Methods类直接使用该类里的方法
    '''

    @staticmethod
    def get_txt(url):
        try:
            '''
                Windows下读取其他文件时路径用resource_path就可以了
                Linux服务器里读取文件要用绝对路径
            '''
            with open(Methods.resource_path + url, 'rb') as f:
                return f.read().decode('utf-8')
        except FileNotFoundError:
            try:
                with open(Methods.absolute_path + url, 'rb') as f:
                    return f.read().decode('utf-8')
            except FileNotFoundError as e:
                print(e)

    @staticmethod
    def get_yaml(url):
        return yaml.load(Methods.get_txt(url))

    @staticmethod
    def get_json(url):
        return json.loads(Methods.get_txt(url))

    @staticmethod
    def hash(string):
        has = bytes(string, encoding='utf-8')
        return hashlib.md5(has).hexdigest()

    @staticmethod
    def md5(byte):
        m = hashlib.md5(byte)
        return m.hexdigest()

    ''' 
            ——————————————————————————————————————————————————————————————————————————————————————
            虽然windows下运行得到的字典顺序与json中的数据顺序一样
            但是在Linux服务器中运行时读取到的json数据顺序会被随机打乱，所以这里采用归并排序对从json读取到的数据进行排序 
        '''

    @staticmethod
    def dict_to_kv(url):
        dict = Methods.get_json(url)
        list = []
        for key, value in dict.items():
            list.append(Methods.key_value(key, str(value).split(';')[0], str(value).split(';')[1]))
        return Methods.merge_sort(list)

    @staticmethod
    def merge(left, right):
        c = []
        while len(left) > 0 and len(right) > 0:
            c.append(left.pop(0) if int(left[0].more) < int(right[0].more) else right.pop(0))
        return c + left + right

    @staticmethod
    def merge_sort(list):
        if len(list) <= 1:
            return list
        middle = len(list) // 2
        return Methods.merge(Methods.merge_sort(list[:middle]), Methods.merge_sort(list[middle:]))

    class key_value():
        def __init__(self, key=None, value=None, more=None):
            self.key = key
            self.value = value
            self.more = more

    '''
        ——————————————————————————————————————————————————————————————————————————————————————
    '''

if __name__ == '__main__':

    ''' 测试 '''
    method = Methods()
    print(method.get_txt('seat.json'))