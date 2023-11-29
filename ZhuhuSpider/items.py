# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy
from scrapy.loader import ItemLoader
from itemloaders.processors import MapCompose, TakeFirst, Identity, Join

class ZhuhuspiderItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass


class ZhihuQuestionItem(scrapy.Item):
    question_title = scrapy.Field()
    question_tags = scrapy.Field()
    question_id = scrapy.Field()
    question_view = scrapy.Field()
    question_focus = scrapy.Field()
    question_answer_num = scrapy.Field()
    question_creat_date = scrapy.Field()
    question_url = scrapy.Field()


class ZhihuAnswerItem(scrapy.Item):
    question_title = scrapy.Field()
    question_id = scrapy.Field()
    answer_text = scrapy.Field()
    answer_comment_num = scrapy.Field()
    answer_favor_num = scrapy.Field()
    answer_creat_date = scrapy.Field()


