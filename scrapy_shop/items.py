# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class ScrapyShopItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass


class BaseShopItem(scrapy.Item):
    pref_code = scrapy.Field()
    pref_name = scrapy.Field()
    city_name = scrapy.Field()
    aza_name = scrapy.Field()
    shop_name = scrapy.Field()
    post_code = scrapy.Field()
    address = scrapy.Field()
    tel = scrapy.Field()
    service_time = scrapy.Field()
    link = scrapy.Field()


class SevenItem(BaseShopItem):
    pass


class SevenCoordinateItem(SevenItem):
    lat = scrapy.Field()
    lng = scrapy.Field()


class MatsukiyoItem(BaseShopItem):
    regular_holiday = scrapy.Field()
    lat = scrapy.Field()
    lng = scrapy.Field()


class FamilyShopItem(BaseShopItem):
    lat = scrapy.Field()
    lng = scrapy.Field()
