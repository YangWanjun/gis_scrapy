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


class RailwayCompanyItem(scrapy.Item):
    company_code = scrapy.Field()
    railway_code = scrapy.Field()
    company_name = scrapy.Field()
    company_kana = scrapy.Field()
    company_full_name = scrapy.Field()
    company_short_name = scrapy.Field()
    company_url = scrapy.Field()
    company_type = scrapy.Field()
    status = scrapy.Field()


class RailwayRouteItem(scrapy.Item):
    line_code = scrapy.Field()
    company_code = scrapy.Field()
    line_name = scrapy.Field()
    line_kana = scrapy.Field()
    line_full_name = scrapy.Field()
    color_code = scrapy.Field()
    color_name = scrapy.Field()
    line_type = scrapy.Field()
    lng = scrapy.Field()
    lat = scrapy.Field()
    zoom = scrapy.Field()
    status = scrapy.Field()


class RailwayStationItem(scrapy.Item):
    station_code = scrapy.Field()
    station_group_code = scrapy.Field()
    station_name = scrapy.Field()
    station_kana = scrapy.Field()
    station_name_en = scrapy.Field()
    line_code = scrapy.Field()
    pref_code = scrapy.Field()
    post_code = scrapy.Field()
    address = scrapy.Field()
    lng = scrapy.Field()
    lat = scrapy.Field()
    open_date = scrapy.Field()
    close_date = scrapy.Field()
    status = scrapy.Field()


class JoinStationItem(scrapy.Item):
    pk = scrapy.Field()
    line_code = scrapy.Field()
    station_code1 = scrapy.Field()
    station_code2 = scrapy.Field()
