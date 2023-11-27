import requests
import MySQLdb
from fake_useragent import UserAgent

class ValidIp(object):
    def __init__(self):
        self.conn = MySQLdb.connect(host="127.0.0.1", port=3306, user="root", passwd="995626",
                                    db="ip_pool", charset="utf8")
        self.cursor = self.conn.cursor()
        self.ua = UserAgent()

    def get_valid_ip(self):
        #从数据库中随机获取一个可用的ip
        random_sql = "SELECT ip, port FROM ip_data ORDER BY RAND() LIMIT 1"
        result = self.cursor.execute(random_sql)
        for ip_info in self.cursor.fetchall():
            ip = ip_info[0]
            port = ip_info[1]

            judge_re = self.judge_ip(ip, port)
            if judge_re:
                valid_ip = "http://{0}:{1}".format(ip, port)
                print("有效ip：{}".format(valid_ip))
                return valid_ip
            else:
                return self.get_valid_ip()

    def judge_ip(self, ip, port):
        #判断ip是否可用
        http_url = "http://www.baidu.com"
        proxy_url = "http://{0}:{1}".format(ip, port)
        try:
            proxy_dict = {
                "http": proxy_url,
            }
            response = requests.get(http_url, proxies=proxy_dict)
        except Exception as e:
            print("请求异常直接被断开链接的无用ip: {}:{}".format(ip, port))
            print(e)
            self.delete_ip(ip)
            return False
        else:
            code = response.status_code
            if code >= 200 and code < 300:
                print("effective ip")
                return True
            else:
                print("请求异常直接被断开链接的无用ip: {}:{}".format(ip, port))
                self.delete_ip(ip)
                return False

    def delete_ip(self, ip):
        #从数据库中删除无效的ip
        delete_sql = "DELETE FROM ip_data WHERE ip='{}'".format(ip)
        self.cursor.execute(delete_sql)
        self.conn.commit()
        return True