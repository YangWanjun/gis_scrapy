# -*- coding: utf-8 -*-
import scrapy
import psycopg2
import datetime
from .items import RailwayCompanyItem, RailwayRouteItem, RailwayStationItem, JoinStationItem

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html


class RailwayCompanyPipeline(object):

    def __init__(self, *args, **kwargs):
        super(RailwayCompanyPipeline, self).__init__(*args, **kwargs)
        self.conn = None
        self.cur = None
        self.railway_company_list = []
        self.railway_route_list = []
        self.railway_station_list = []
        self.join_station_list = []

    def open_spider(self, spider: scrapy.Spider):
        # コネクションの開始
        url = spider.settings.get('POSTGRESQL_URL')
        self.conn = psycopg2.connect(url)
        self.cur = self.conn.cursor()

    def close_spider(self, spider: scrapy.Spider):
        # コネクションの終了
        for item in self.railway_company_list:
            self.add_railway_company(item)
        for item in self.railway_route_list:
            self.add_railway_route(item)
        for item in self.railway_station_list:
            self.add_railway_station(item)
        for item in self.join_station_list:
            self.add_join_station(item)
        if self.conn:
            self.conn.commit()
            self.cur.close()
            self.conn.close()

    def process_item(self, item: scrapy.Item, spider: scrapy.Spider):
        if isinstance(item, RailwayCompanyItem):
            self.railway_company_list.append(item)
        elif isinstance(item, RailwayRouteItem):
            self.railway_route_list.append(item)
        elif isinstance(item, RailwayStationItem):
            self.railway_station_list.append(item)
        elif isinstance(item, JoinStationItem):
            self.join_station_list.append(item)
        else:
            print('UNKNOWN')
        return item

    def add_railway_company(self, item):
        sql = "INSERT INTO gis_railway_company (" \
              "    company_code, railway_code, " \
              "    company_name, company_kana, company_full_name, company_short_name, " \
              "    company_url, company_type, status, " \
              "    created_dt, updated_dt, is_deleted" \
              ") " \
              "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"

        data = (
            int(item.get('company_code')),
            int(item.get('railway_code')),
            item.get('company_name'),
            item.get('company_kana'),
            item.get('company_full_name'),
            item.get('company_short_name'),
            item.get('company_url'),
            item.get('company_type'),
            item.get('status'),
            datetime.datetime.now(),
            datetime.datetime.now(),
            False,
        )
        self.cur.execute(sql, data)

    def add_railway_route(self, item):
        sql = "INSERT INTO gis_railway_route (" \
              "    line_code, company_code, " \
              "    line_name, line_kana, line_full_name, color_code, color_name, " \
              "    line_type, center_lng, center_lat, zoom, status, " \
              "    created_dt, updated_dt, is_deleted" \
              ") " \
              "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"

        data = (
            int(item.get('line_code')),
            int(item.get('company_code')),
            item.get('line_name'),
            item.get('line_kana'),
            item.get('line_full_name'),
            item.get('color_code'),
            item.get('color_name'),
            item.get('line_type'),
            float(item.get('center_lng')) if item.get('center_lng') else None,
            float(item.get('center_lat')) if item.get('center_lng') else None,
            int(item.get('zoom')) if item.get('zoom') else None,
            item.get('status'),
            datetime.datetime.now(),
            datetime.datetime.now(),
            False,
        )
        self.cur.execute(sql, data)

    def add_railway_station(self, item):
        sql = "INSERT INTO gis_station (" \
              "    station_code, station_group_code, " \
              "    station_name, station_kana, station_name_en, line_code, pref_code, " \
              "    post_code, address, lng, lat, open_date, close_date, status, point, " \
              "    created_dt, updated_dt, is_deleted" \
              ") " \
              "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, " \
              "CASE WHEN %s is not null and %s is not null" \
              "          THEN ST_GeomFromText('POINT (%s %s)', 4326)" \
              "      ELSE NULL " \
              "END , %s, %s, %s);"

        lng = float(item.get('lng')) if item.get('lng') else None
        lat = float(item.get('lat')) if item.get('lat') else None
        data = (
            int(item.get('station_code')),
            int(item.get('station_group_code')),
            item.get('station_name'),
            item.get('station_kana'),
            item.get('station_name_en'),
            int(item.get('line_code')),
            '%02d' % int(item.get('pref_code')) if item.get('pref_code') else None,
            item.get('post_code'),
            item.get('address'),
            lng,
            lat,
            datetime.datetime.strptime(item.get('open_date'), '%Y-%m-%d').date() if item.get('open_date') and item.get('open_date') != '0000-00-00' else None,
            datetime.datetime.strptime(item.get('close_date'), '%Y-%m-%d').date() if item.get('close_date') and item.get('close_date') != '0000-00-00' else None,
            item.get('status'),
            lng,
            lat,
            lng,
            lat,
            datetime.datetime.now(),
            datetime.datetime.now(),
            False,
        )
        self.cur.execute(sql, data)

    def add_join_station(self, item):
        sql = "INSERT INTO gis_join_station (" \
              "    id, line_code, station_code1, station_code2, " \
              "    created_dt, updated_dt, is_deleted" \
              ") " \
              "VALUES (%s, %s, %s, %s, %s, %s, %s);"

        line_code = int(item.get('line_code'))
        station_code1 = int(item.get('station_code1'))
        station_code2 = int(item.get('station_code2'))
        self.cur.execute('SELECT COUNT(1) FROM gis_railway_route WHERE line_code = %s', (line_code,))
        if self.cur.fetchone()[0] == 0:
            print('路線{}が存在しません。'.format(line_code))
            return
        self.cur.execute('SELECT COUNT(1) FROM gis_station WHERE station_code = %s', (station_code1,))
        if self.cur.fetchone()[0] == 0:
            print('駅{}が存在しません。'.format(station_code1))
            return
        self.cur.execute('SELECT COUNT(1) FROM gis_station WHERE station_code = %s', (station_code2,))
        if self.cur.fetchone()[0] == 0:
            print('駅{}が存在しません。'.format(station_code2))
            return
        data = (
            int(item.get('pk')),
            line_code,
            station_code1,
            station_code2,
            datetime.datetime.now(),
            datetime.datetime.now(),
            False,
        )
        self.cur.execute(sql, data)
