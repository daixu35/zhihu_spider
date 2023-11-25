import cv2
import numpy as np
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
import os

# img = cv2.imread("image.jpg", 1)
# img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
# template = cv2.imread("template.png", 0)
#
# height, width = template.shape[::-1]
#
# res = cv2.matchTemplate(img_gray, template, cv2.TM_CCOEFF_NORMED)
# min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
#
# cv2.rectangle(img, max_loc, (max_loc[0] + height, max_loc[1] + width), (255, 0, 0), 2)
#
# cv2.imshow("img_template", template)
# cv2.imshow("processed", img)
#
# cv2.waitKey(0)

# browser = uc.Chrome()
# browser.get("http://books.toscrape.com/index.html")
# test = browser.find_element(By.XPATH, "//div[@class='side_categories']")
# pass

print(os.path.join(os.path.dirname(__file__), "image.jpg"))
