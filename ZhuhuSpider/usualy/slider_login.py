import time
import random
import json
import base64
import os

import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as Ec
from selenium.webdriver.common.action_chains import ActionChains
import undetected_chromedriver as uc


class SliderMove(object):
    """
    破解滑动验证码滑块需要滑动的距离
    """
    def __init__(self):
        self.image_path = os.path.join(os.path.dirname(__file__), "image.jpg")
        self.params = {"threshold": 0.8}
        self.model_url = "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/detection/zhuhu_spider"
        self.access_token = "24.fbec6d588e7b91a638ad3759c5848b04.2592000.1703420388.282335-33422951"
        self.AK = "KMeC6p83vA9jE171ZmC0dOQI"
        self.SK = "ZP0FepRMKDC9gqSnG2beD2pTEGj3czt7"

    def get_distance(self, bg_img_url):
        """
        如果识别成功，返回识别状态和缺口左边界距离
        :param bg_img_url: 滑动验证码背景图片url
        :return: st，识别成功返回True，否则False。pos是缺口的左边界距离
        """
        self.__download_img(bg_img_url)  # 先下载背景图片
        print("读取目标图片：")
        with open(self.image_path, "rb") as f:
            base64_data = base64.b64encode(f.read())
            base64_str = base64_data.decode('UTF8')
        self.params["image"] = base64_str

        # 调用机器学习模型进行图像缺口识别
        bg_img_test_url = "{}?access_token={}".format(self.model_url, self.access_token)
        response = requests.post(bg_img_test_url, json=self.params)
        response_dict = dict(response.json())
        # response_dict = json.loads(response_json)
        if response_dict.get("results", ""):
            return True, response_dict["results"]
        else:
            return False, 0

    def slider_move(self, chrome_driver, slider_element, distance):
        """
        移动滑块的方法
        :param chrome_driver: chrome_driver对象
        :param slider_element: 网页滑块元素
        :param distance: 滑块需要滑动的距离
        :return:
        """
        print("需要滑动的距离是：{}".format(distance))
        move_arr = self.__get_move_track(distance)
        print('生成的滑动轨迹为:{},轨迹的距离之和为{}'.format(move_arr, distance))
        ActionChains(chrome_driver).click_and_hold(slider_element).perform()
        time.sleep(0.5)

        for move in move_arr:
            time.sleep(0.01)
            ActionChains(chrome_driver).move_by_offset(move, random.randint(-5, 5)).perform()
            ActionChains(chrome_driver).context_click(slider_element)

        ActionChains(chrome_driver).release(on_element=slider_element).perform()

    def __get_move_track(self, distance):
        tracks = []
        v = 0
        m = 2
        current = 0
        mid = distance * 4 / 5
        while current <= distance:
            if current < mid:
                a = 2
            else:
                a = -3
            v0 = v
            s = v0 * m + 0.5 * a * (m ** 2)
            current += s
            tracks.append(round(s))
            v = v0 + a * m
        return tracks

    def __download_img(self, bg_img_url):
        """
        下载背景图片的私有方法
        :param bg_img_url: 背景图片url
        :return:
        """
        try:
            response = requests.get(bg_img_url)
        except Exception as e:
            print("图片下载失败")
            raise e
        else:
            with open(self.image_path, "wb") as f:
                f.write(response.content)


class Login(object):
    """
    这个类用于滑动验证码的模拟登陆破解来获取cookie
    """
    def __init__(self, login_url, user, password, retry):
        """
        :param login_url: 登陆界面的url
        :param user: 登陆所用用户名
        :param password: 登录所用密码
        :param retry: 因为识别图像方法破解可能不能一次成功，设置了重试次数
        """
        chrome_options = webdriver.ChromeOptions()  # 可以控制chrome driver的一些行为
        # chrome_options.add_argument("--headless")  # 启动driver但无界面
        chrome_options.add_argument("-disable-gpu")  # 禁用GPU加速，可能会导致黑屏并且占用资源
        chrome_options.add_argument("--disable-dev-shm-usage")  # 防止有大量网页渲染时chrome崩溃

        # from selenium import webdriver
        # from selenium.webdriver.common.by import By
        # from selenium.webdriver.support.wait import WebDriverWait
        # from selenium.webdriver.support import expected_conditions as Ec
        # 这四个库是在爬虫集成selenium时常用的四个模块：
        # 1. WebDriverWait用于等待页面加载完成或某个元素出现。WebDriverWait类的构造函数需要传入一个WebDriver实例和超时时间，
        #    然后可以使用until()方法等待某个条件满足。
        # 2. Ec中提供一系列判断网页中某些元素满足什么条件的函数，配合WebDriverWait的until函数简洁的实现当某个条件满足时操作元
        #    素的操作
        # 3. By模块用于将查找元素的操作语句集成到一个元祖中(By.CSS_SELECTOR/By.XPATH/By.ID, 选择器语句)，这样实现选择所需元
        #    素的快速操作，比如：element = browser.find_element(By.CSS_SELECTOR, '.someClass')
        self.browser = uc.Chrome()
        self.wait = WebDriverWait(self.browser, 20)
        self.url = login_url
        self.user = user
        self.password = password
        self.retry = retry
        self.slider = SliderMove()  # 自定义的滑块类，用于获取滑动验证需要滑动距离

    def login(self):
        """
        登录函数的逻辑，点击用户密码登陆选项，输入用户名密码，破解滑动验证码
        :return:
        """
        self.browser.get(self.url)
        longin_element = self.browser.find_element(
            By.XPATH, '//*[@id="root"]/div/main/div/div/div/div/div[2]/div/div[1]/div/div[1]/form/div[1]/div[2]'
        )
        self.browser.execute_script("arguments[0].click()", longin_element)
        # js中arguments对象是一个类数组对象，它包含了函数调用时传递的所有参数。下面中代表传递给script代码执行的参数中，第一个执行
        # 函数的变量。还有一点是，知乎屏蔽了chrome driver模拟的点击函数操作，所以使用这种方法进行元素的点击，否则可以直接使用：
        # login_element.click()进行操作

        username = self.wait.until(
            Ec.element_to_be_clickable((By.XPATH, "//div[@class='SignFlow-account']//input"))
        )
        username.send_keys(self.user)
        password = self.wait.until(
            Ec.element_to_be_clickable((By.XPATH, "//div[@class='SignFlow-password']//input"))
        )
        password.send_keys(self.password)
        submit = self.wait.until(
            Ec.element_to_be_clickable((By.XPATH, "//button[@type='submit']"))
        )
        time.sleep(3)
        self.browser.execute_script("arguments[0].click()", submit)
        time.sleep(3)

        # 点击登录以后，开始破解滑动验证码
        k = 1
        while k < self.retry:
            # 取得滑动验证的背景元素和滑块元素
            bg_img = self.wait.until(
                Ec.presence_of_element_located((By.CSS_SELECTOR, "body > div.yidun_popup--light.yidun_popup.yidun_popup--size-small > div.yidun_modal__wrap > div > div > div.yidun_modal__body > div > div.yidun_panel > div > div.yidun_bgimg > img.yidun_bg-img"))
            )
            slider_img = self.wait.until(
                Ec.presence_of_element_located((By.XPATH, "/html/body/div[4]/div[2]/div/div/div[2]/div/div[1]/div/div[1]/img[2]"))
            )
            bg_img_url = bg_img.get_attribute("src")
            st, res = self.slider.get_distance(bg_img_url)
            if st:
                pos = res[0]["location"]["left"]
                start_url = self.browser.current_url  # 滑动前当前url
                distance = pos - 4
                self.slider.slider_move(self.browser, slider_img, distance)
                time.sleep(5)
                try:
                    submit = self.wait.until(
                        Ec.element_to_be_clickable((By.XPATH, "//button[@type='submit']"))
                    )
                    submit.click()
                    time.sleep(3)
                except:
                    pass

                end_url = self.browser.current_url
                print(end_url)
                if end_url != start_url:
                    return self.__get_cookies()
                else:
                    k += 1
                    time.sleep(3)
            else:
                self.slider.slider_move(self.browser, slider_img, 10)
                k += 1
                time.sleep(3)
        return None

    def __get_cookies(self):
        cookies = self.browser.get_cookies()
        self.cookies = ""
        for cookie in cookies:
            self.cookies += '{}={};'.format(cookie.get('name'), cookie.get('value'))
        return cookies

    def __del__(self):
        self.browser.close()
        print("界面关闭")

