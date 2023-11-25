import scrapy

from ZhuhuSpider.usualy.slider_login import Login


class ZhuhuSpider(scrapy.Spider):
    name = "zhuhu"
    allowed_domains = ["www.zhihu.com"]
    start_urls = ["https://www.zhihu.com/"]
    login_url = "https://www.zhihu.com/signin"

    headers = {
        "HOST": "www.zhihu.com",
        "Referer": "https://www.zhizhu.com",
        'User-Agent': "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:51.0) Gecko/20100101 Firefox/51.0"
    }

    custom_settings = {
        "COOKIES_ENABLED": True
    }

    def start_requests(self):
        user = self.settings["USER"]
        password = self.settings["PASSWORD"]
        login = Login(self.login_url, user, password, 6)
        cookies = login.login()
        print("获取到cookies: ", cookies)
        for url in self.start_urls:
            yield scrapy.Request(url, headers=self.headers, cookies=cookies, callback=self.parse)


    def parse(self, response):
        pass
