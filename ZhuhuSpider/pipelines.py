# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
import pymysql
import pymysql.cursors
from twisted.enterprise import adbapi

class ZhuhuspiderPipeline:
    def process_item(self, item, spider):
        return item


class ZhihuQuestionItemPipline(object):
    @classmethod
    def from_settings(cls, settings):
        db_params = {
            "host": settings["MYSQL_HOST"],
            "db": settings["MYSQL_DBNAME"],
            "user": settings["MYSQL_USER"],
            "passwd": settings["MYSQL_PASSWORD"],
            "charset": "utf8",
            "cursorclass": pymysql.cursors.DictCursor,
            "use_unicode": True
        }
        dbpool = adbapi.ConnectionPool("MySQLdb", **db_params)
        return cls(dbpool)

    def __init__(self, dbpool):
        self.dbpool = dbpool

    def process_item(self, item, spider):
        query = self.dbpool.runInteraction(self.__do_insert, item)
        query.addErrback(self.__handle_error)

    def __do_insert(self, cursor, item):
        insert_sql = ("INSERT INTO question(question_title, question_id, question_tags, question_view, question_focus, "
                      "question_answer_num, question_creat_date, question_url) VALUES (%s, %s, %s, %s, %s, %s, %s, %s) "
                      "ON DUPLICATE KEY UPDATE (question_creat_date)")
        cursor.excute(insert_sql, (item["question_title"], item["question_id"], item["question_tags"],
                                   item["question_view"], item["question_focus"], item["question_answer_num"],
                                   item["question_creat_date"], item["question_url"]))

    def __handle_error(self, failure):
        print(failure)


class ZhihuAnswerItemPipline(object):
    @classmethod
    def from_settings(cls, settings):
        db_params = {
            "host": settings["MYSQL_HOST"],
            "db": settings["MYSQL_DBNAME"],
            "user": settings["MYSQL_USER"],
            "passwd": settings["MYSQL_PASSWORD"],
            "charset": "utf8",
            "cursorclass": pymysql.cursors.DictCursor,
            "use_unicode": True
        }
        dbpool = adbapi.ConnectionPool("MySQLdb", **db_params)
        return cls(dbpool)

    def __init__(self, dbpool):
        self.dbpool = dbpool

    def process_item(self, item, spider):
        query = self.dbpool.runInteraction(self.__do_insert, item)
        query.addErrback(self.__handle_error)

    def __do_insert(self, cursor, item):
        insert_sql = ("INSERT INTO answer(question_id, question_title, answer_text, answer_comment_num, "
                      "answer_favor_num, answer_creat_date) VALUES (%s, %s, %s, %s, %s, %s) "
                      "ON DUPLICATE KEY UPDATE (answer_creat_date)")
        cursor.excute(insert_sql, (item["question_id"], item["question_title"], item["answer_text"],
                                   item["answer_comment_num"], item["answer_favor_num"], item["answer_creat_date"]))

    def __handle_error(self, failure):
        print(failure)
