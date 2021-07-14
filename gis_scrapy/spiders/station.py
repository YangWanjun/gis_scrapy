import scrapy
import re
import csv
from urllib.parse import urljoin
from gis_scrapy.items import RailwayCompanyItem, RailwayRouteItem, RailwayStationItem, JoinStationItem

ROOT_URL = 'https://www.ekidata.jp/dl/'


class StationSpider(scrapy.Spider):
    name = 'station'
    custom_settings = {
        'LOG_LEVEL': 'ERROR',
    }
    start_urls = [
        'https://www.ekidata.jp/dl/?p=1',
    ]
    join_station_pk = 1

    def __init__(self, *args, **kwargs):
        super(StationSpider, self).__init__(*args, **kwargs)
        self.username = kwargs.get('username', None)
        self.password = kwargs.get('password', None)

    def parse(self, response):
        return scrapy.FormRequest.from_response(
            response,
            formdata={'ac': self.username, 'ps': self.password},
            callback=self.after_login,
        )

    def after_login(self, response):
        exists = response.xpath("//a[text()='データダウンロード']/@href")
        if len(exists) == 0:
            self.logger.error('Login failed')
            return
    #     href = exists[0].get()
    #     yield scrapy.Request(url=href, callback=self.parse_download)
    #
    # def parse_download(self, response):
        table = response.css("table.list02")[0]
        for td in table.css("td"):
            ele = td.css('a')[0]
            url = urljoin(ROOT_URL, ele.attrib['href'])
            m = re.findall(r'\bt=(\d)+\b', url)
            if m:
                yield scrapy.Request(url=url, callback=self.parse_csv, meta={
                    'category': m[0]
                })
            else:
                self.logger.error('識別できないＵＲＬです')

    def parse_csv(self, response):
        category = response.meta.get('category')
        for data in self.get_csv_data(response):
            if category == '1':
                # 事業者データ
                item = RailwayCompanyItem()
                item['company_code'] = data.get('company_cd')
                item['railway_code'] = data.get('rr_cd')
                item['company_name'] = data.get('company_name')
                item['company_kana'] = data.get('company_name_k')
                item['company_full_name'] = data.get('company_name_h')
                item['company_short_name'] = data.get('company_name_r')
                item['company_url'] = data.get('company_url')
                item['company_type'] = data.get('company_type')
                item['status'] = data.get('e_status')
                yield item
            elif category == '3':
                # 路線データ
                item = RailwayRouteItem()
                item['line_code'] = data.get('line_cd')
                item['company_code'] = data.get('company_cd')
                item['line_name'] = data.get('line_name')
                item['line_kana'] = data.get('line_name_k')
                item['line_full_name'] = data.get('line_name_h')
                item['color_code'] = data.get('line_color_c')
                item['color_name'] = data.get('line_color_t')
                item['line_type'] = data.get('line_type')
                item['center_lng'] = data.get('lon')
                item['center_lat'] = data.get('lat')
                item['zoom'] = data.get('zoom')
                item['status'] = data.get('e_status')
                yield item
            elif category == '5':
                # 駅データ
                item = RailwayStationItem()
                item['station_code'] = data.get('station_cd')
                item['station_group_code'] = data.get('station_g_cd')
                item['station_name'] = data.get('station_name')
                item['station_kana'] = data.get('station_name_k')
                item['station_name_en'] = data.get('station_name_r')
                item['line_code'] = data.get('line_cd')
                item['pref_code'] = data.get('pref_cd')
                item['post_code'] = data.get('post')
                item['address'] = data.get('add')
                item['lng'] = data.get('lon')
                item['lat'] = data.get('lat')
                item['open_date'] = data.get('open_ymd')
                item['close_date'] = data.get('close_ymd')
                item['status'] = data.get('e_status')
                yield item
            elif category == '6':
                # 接続駅データ
                item = JoinStationItem()
                item['pk'] = self.join_station_pk
                item['line_code'] = data.get('line_cd')
                item['station_code1'] = data.get('station_cd1')
                item['station_code2'] = data.get('station_cd2')
                self.join_station_pk += 1
                yield item

    def get_csv_data(self, response):
        reader = csv.reader(response.text.strip().splitlines())
        header = next(reader)
        for row in reader:
            data = dict(zip(header, row))
            yield data
