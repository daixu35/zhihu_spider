import re
import json

import scrapy
import requests
from scrapy.crawler import Crawler
import undetected_chromedriver as uc
from selenium.webdriver.chrome.options import Options
from scrapy import signals
from scrapy.loader import ItemLoader
from scrapy import Request

from ZhuhuSpider.usualy.slider_login import Login
from ZhuhuSpider.items import ZhihuQuestionItem
from ZhuhuSpider.items import ZhihuAnswerItem
from ZhuhuSpider.usualy.get_ajax_request import AjaxRequestInterception


class ZhuhuSpider(scrapy.Spider):
    name = "zhuhu"
    allowed_domains = ["www.zhihu.com"]
    start_urls = ["https://www.zhihu.com/"]
    login_url = "https://www.zhihu.com/signin"

    custom_settings = {
        "COOKIES_ENABLED": True
    }

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        """
        类方法，因为spider组件没有自己的spider_closed进行重载，所以将spider关闭的信号连接到我们自己写的
        spider_closed函数
        """
        spider = super(ZhuhuSpider, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def __init__(self):
        """
        在这里初始化browser，这样的话在middleware中就始终操作一个浏览器，而不必每次请求都新开一个浏览器
        """
        super(ZhuhuSpider, self).__init__()
        chrome_options = Options()
        chrome_options.add_argument("-disable-gpu")  # 禁用GPU加速，可能会导致黑屏并且占用资源
        chrome_options.add_argument("--disable-dev-shm-usage")  # 防止有大量网页渲染时chrome崩溃
        self.browser = uc.Chrome()

    def start_requests(self):
        user = self.settings["USER"]
        password = self.settings["PASSWORD"]
        login = Login(self.login_url, user, password, 10)
        cookies = login.login()
        # self.browser.get(self.login_url)
        # input("回车以继续：")
        cookies = self.browser.get_cookies()
        print("获取到cookies: ", cookies)
        for cookie in cookies:
            cookie_dict = {
                'domain': '.zhihu.com',
                'name': cookie.get('name'),
                'value': cookie.get('value'),
                "expires": cookie.get('expires'),
                'path': cookie.get('path'),
                'httpOnly': cookie.get('httpOnly'),
                'HostOnly': cookie.get('HostOnly'),
                'Secure': cookie.get('Secure')
            }
            self.browser.add_cookie(cookie_dict)
        for url in self.start_urls:
            yield scrapy.Request(url, cookies=cookies, meta={"cookies": cookies}, callback=self.parse)

        # for url in self.start_urls:
        #     yield scrapy.Request(url, callback=self.parse)


    def parse(self, response):
        question_item = ZhihuQuestionItem()
        server_exe_path = self.settings["INTERCEPT_PROXY_PATH"]
        topic = response.xpath("//*[@id='TopstoryContent']//div[@class='Card TopstoryItem TopstoryItem-isRecommend']")[:2]
        for tp in topic:
            url = tp.xpath(".//div[@class='ContentItem AnswerItem']/meta[@itemprop='url']/@content").extract_first("")
            if url:
                intercept = AjaxRequestInterception(server_exe_path, url)
                regx = "(^https.*?questions/\d+/feeds.*)"
                st, res = intercept.intercept_request(regx)
                yield Request(url=res, callback=self.parse_answer)

                regx = "(.*question/(\d+))"
                match_re = re.match(regx, url)
                if match_re:
                    question_url = match_re.group(1)
                    question_id = match_re.group(2)
                    date = tp.xpath(".//meta[@itemprop='dateCreated']//@content").extract_first("")
                    regx = "(\d+-\d+-\d+)"
                    match_re = re.match(regx, date)
                    if match_re:
                        create_data = match_re.group(1)
                    else:
                        create_data = "1900-01-01"

                    question_item["question_url"] = question_url
                    question_item["question_url"] = question_id
                    question_item["question_creat_date"] = create_data
                    yield Request(url=question_url, meta={"question_item": question_item},
                                  callback=self.parse_question_detail)
                else:
                    continue

        ori_url = "https://www.zhihu.com/"
        yield Request(url=ori_url, callback=self.parse)

    def parse_question_detail(self, response):
        question_item = response.meta["question_item"]
        question_title = response.xpath("//div[@class='QuestionHeader-main']/h1/text()").extract_first("")
        question_tags = ",".join(response.xpath("//div[@class='QuestionHeader-main']//span[@class='Tag-content']"
                                                "//div[@class='css-1gomreu']/text()").extract())
        question_attention = response.xpath("//div[@class='QuestionHeader-side']//strong[@class='NumberBoard-itemValue'"
                                            "]/text()").extract()
        if question_attention:
            question_focus = question_attention[0]
            question_view = question_attention[1]
        else:
            question_focus, question_view = -1, -1

        question_answer_num = " ".join(response.xpath("//div[@class='List-header']/h4/span/text()").extract())

        question_item["question_title"] = question_title
        question_item["question_tags"] = question_tags
        question_item["question_focus"] = question_focus
        question_item["question_view"] = question_view
        question_item["question_answer_num"] = question_answer_num

        yield question_item

    def parse_answer(self, response):
        answer_item = ItemLoader(item=ZhihuAnswerItem(), response=response)
        json_dict = json.loads(response.text)
        answer_data = json_dict["data"]
        next_answer_url = json_dict["paging"].get("next", "")
        question_title = answer_data["data"][0]["target"]["question"]["title"]
        question_id = answer_data["data"][0]["target"]["question"]["id"]
        for answer in answer_data:
            answer_comment_num = answer["target"]["comment_count"]
            answer_text = answer["target"]["content"]
            answer_favor_num = answer["target"]["voteup_count"]
            answer_creat_date = answer["target"]["created_time"]

            answer_item.add_value("question_title", question_title)
            answer_item.add_value("question_id", question_id)
            answer_item.add_value("answer_comment_num", answer_comment_num)
            answer_item.add_value("answer_text", answer_text)
            answer_item.add_value("answer_favor_num", answer_favor_num)
            answer_item.add_value("answer_creat_date", answer_creat_date)

            answer = answer_item.load_item()
            yield answer

        yield Request(url=next_answer_url, callback=self.parse_answer)

    def spider_closed(self, spider):
        """
        spider没有而我们自己定义的spider_closed，因为爬虫退出时，不会帮我们关闭selenium启动的浏览器，所以
        要自己设置关闭
        """
        print("关闭爬虫")
        self.browser.close()

