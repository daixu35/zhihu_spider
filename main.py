import os
import sys

from scrapy.cmdline import execute

sys.path.append(os.path.abspath(__file__))
execute(["scrapy", "crawl", "zhuhu"])

