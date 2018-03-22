#! usr/bin/env python
#-*- coding=utf-8 -*-
"""

    @author: 南辙一曲风华顾
    @file: send_email
    @date: 2018/01/24
    
"""
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
import smtplib
from methods import Methods

class Send_Mail(Methods):

    def __init__(self):
        self.conf = self.get_yaml('config/config.yaml')['email_conf']

        self.host = self.conf['host']
        self.header = self.conf['header']

        self.sender = self.conf['username']
        self.password = self.conf['password']
        self.template = self.conf['template']

        self.resource = self.conf['resource']
        self.email_list = self.get_txt('config/email_list.txt').split('\r\n')
        self.information = self.dict_to_kv('config/my_information.json')

    ''' 当传递邮件地址时发送向该邮件地址，当为传递参数时发送给email_list中的email地址 '''
    def send_email(self, message=None):

        msg = MIMEMultipart()

        ''' 邮件主题 '''
        msg['Subject'] = Header(self.header, 'utf-8')

        ''' 发件人 '''
        msg['From'] = self.sender

        ''' 收件人 '''
        msg['To'] = ','.join(self.conf['email_list'])

        try:
            smtp = smtplib.SMTP_SSL('smtp.gmail.com')

            smtp.connect(self.host)
            smtp.login(self.sender, self.password)

            msg.attach(MIMEText(message, 'plain', 'utf-8'))

            smtp.sendmail(self.sender, self.email_list, msg.as_string())
            smtp.quit()
            return "邮件已通知, 请查收"

        except smtplib.SMTPRecipientsRefused:
            return '接收邮箱填写错误或拒绝接收'

        except smtplib.SMTPAuthenticationError:
            return '身份认证失败'

        except smtplib.SMTPSenderRefused:
            return '发送方未启用服务'

        except smtplib.SMTPException as e:
            return e
