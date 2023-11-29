import re

from browsermobproxy import Server
import time
import undetected_chromedriver as uc
from selenium.webdriver.chrome.options import Options


class AjaxRequestInterception(object):
    def __init__(self, path, base_url, intercept_content=False, intercept_header=True):
        """
        :param path: browsermobproxy库的可执行文件路径
        :param base_url: 需要监听动态请求的url
        """
        self.base_url = base_url
        self.server = Server(path, {"prot": 8080})
        self.server.start()
        self.proxy = self.server.create_proxy()
        self.get_content = intercept_content
        self.get_header = intercept_header

        chrome_options = Options()
        # chrome_options.add_argument("--headless")  # 启动driver但无界面
        chrome_options.add_argument("-disable-gpu")  # 禁用GPU加速，可能会导致黑屏并且占用资源
        chrome_options.add_argument("--disable-dev-shm-usage")  # 防止有大量网页渲染时chrome崩溃
        # chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument('--proxy-server={0}'.format(self.proxy.proxy))

        self.browser = uc.Chrome(options=chrome_options)

    def intercept_request(self, regx):
        """
        截获浏览器请求base_url时所有动态加载的请求头，包括js, ajax, css, img等，
        用于获取自己分析过后认为有用的请求url
        :param regx: 正则表达式，匹配自己想要的url
        :return: st, match_re，返回函数状态st，如果匹配成功，返回True和正则结果，否则返回False和None
        """
        self.proxy.new_har(options={
            'captureContent': self.get_content,  # 获得监听到的请求的请求体
            'captureHeaders': self.get_header  # 获得监听到的请求的请求头
        })

        self.browser.get(self.base_url)
        time.sleep(3)
        result = self.proxy.har
        for res in result["log"]["entries"]:
            url = res["request"]["url"]
            match_re = re.match(regx, url)
            if match_re:
                print(url)
                return True, match_re.group(1)
            else:
                continue

        return False, None

    def intercept_content(self, **params):
        """
        截获浏览器请求base_url时所有动态加载的请求的请求体，包括js, ajax, css, img等，
        用于获取自己分析过后认为有用的请求体，暂时还没想好怎么用，没遇到需求
        :param params: 可能需要的参数
        :return:
        """
        pass

    def __del__(self):
        self.proxy.close()
        self.browser.close()


