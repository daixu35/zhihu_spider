# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html
import re
import time

import requests
from scrapy import signals
from fake_useragent import UserAgent
from scrapy.http import HtmlResponse

from ZhuhuSpider.usualy.get_random_ip import ValidIp
from ZhuhuSpider.usualy.get_ajax_request import AjaxRequestInterception

# useful for handling different item types with a single interface
from itemadapter import is_item, ItemAdapter


class ZhuhuspiderSpiderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, or item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Request or item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)


class ZhuhuspiderDownloaderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        # Called for each request that goes through the downloader
        # middleware.

        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        return None

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)


class RandomUserAgentMiddleWare(object):
    # 实现每一个request随机更换ua
    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)

    def __init__(self, crawler):
        super(RandomUserAgentMiddleWare, self).__init__()
        self.ua = UserAgent()
        self.ua_type = crawler.settings.get("UA_TYPE", "random")

    def process_request(self, request, spider):
        def random_ua():
            return getattr(self.ua, self.ua_type)

        request.headers.setdefault("User-Agent", random_ua())


class RandomProxyMiddleware(object):
    def process_request(self, request, spider):
        random_ip = ValidIp()
        request.meta["proxy"] = random_ip.get_valid_ip()


class DynamicPageMiddleware(object):
    def process_request(self, request, spider):
        if request.url == "https://www.zhihu.com/":
            spider.browser.get(request.url)
            print("进入知乎首页，等待页面操作完成：")
            time.sleep(3)

            # 拖动页面让ajax请求的页面加载完成。
            # 这里是没有办法的办法，我通过抓包工具已经解析出了问题项的ajax请求url，但是当我拿出去单独请求的时候，拿到的json数据中
            # 的问题项和首页本来新加载的不一样，就是返回的单独json和抓包preview也不一样，我也查看了url的请求参数，完全一致也还是
            # 如此，没办法，只能采取selenium性能不算高的方法了
            for i in range(5):
                spider.browser.execute_script("window.scrollTo(0, document.body.scrollHeight); "
                                            "var lenOfPage=document.body.scrollHeight; return lenOfPage;")
                time.sleep(2)

            return HtmlResponse(url=spider.browser.current_url, body=spider.browser.page_source,
                                encoding="utf-8", request=request)


class InterceptionAjaxMiddleware(object):
    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)

    def __init__(self, crawler):
        super(InterceptionAjaxMiddleware, self).__init__()
        self.server_exe_path = crawler.settings.get("INTERCEPT_PROXY_PATH",
                                                    "browsermob-proxy-2.1.4/bin/browsermob-proxy")

    def process_request(self, request, spider):
        regx = "(.*question/\d+/answer/\d+)"
        match_re = re.match(regx, request.url)
        if match_re:
            intercept = AjaxRequestInterception(self.server_exe_path, request.url)
            regx = "(^https.*?questions/\d+/feeds.*)"
            st, res = intercept.intercept_request(regx)
            if st:
                response = requests.get(res)
                return HtmlResponse(url=res, body=response.text, encoding="utf-8", request=request)
