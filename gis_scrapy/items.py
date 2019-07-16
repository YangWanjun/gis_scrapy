# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class ShopItem(scrapy.Item):
    pref_code = scrapy.Field()
    pref_name = scrapy.Field()
    city_code = scrapy.Field()
    city_name = scrapy.Field()
    town_code = scrapy.Field()
    town_name = scrapy.Field()
    shop_name = scrapy.Field()
    post_code = scrapy.Field()
    address = scrapy.Field()
    tel = scrapy.Field()
    service_time = scrapy.Field()
    regular_holiday = scrapy.Field()
    link = scrapy.Field()
    lat = scrapy.Field()
    lng = scrapy.Field()
