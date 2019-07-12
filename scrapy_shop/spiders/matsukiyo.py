import scrapy
import re
from urllib.parse import urljoin
from scrapy_shop.utils import constant
from scrapy_shop.items import MatsukiyoItem

root_url = 'https://www.e-map.ne.jp/p/matukiyo/'


class MaTsuKiYoSpider(scrapy.Spider):
    name = 'matsukiyo'

    def start_requests(self):
        url_format = 'https://www.e-map.ne.jp/p/matukiyo/search.htm?&cond27=1&&&his=sa&&type=ShopA&area1={pref_code}&slogflg=1&areaptn=1&selnm=%B0%F1%BE%EB%B8%A9'
        for i in range(1, 48):
            pref_code = '%02d' % i
            url = url_format.format(pref_code=pref_code)
            yield scrapy.Request(url=url, callback=self.parse, meta={
                'first': True,
                'pref_code': pref_code,
            })

    def parse(self, response):
        is_first = response.meta.get('first', False)
        pref_code = response.meta.get('pref_code', None)
        if is_first:
            for ele in response.css("p.pagenation span a"):
                href = urljoin(root_url, ele.attrib['href'])
                yield scrapy.Request(url=href, callback=self.parse, meta={
                    'first': False,
                    'pref_code': pref_code,
                })
        # 市区町村を取得
        for ele in response.css('div.results p a'):
            city_name = ele.css('::text').get()
            city_name = re.sub(r'[()0-9]', '', city_name)
            href = ele.attrib['href']
            url = urljoin(root_url, href)
            yield scrapy.Request(url=url, callback=self.parse_city, meta={
                'first': True,
                'pref_code': pref_code,
                'city_name': city_name,
            })

    def parse_city(self, response):
        is_first = response.meta.get('first', False)
        pref_code = response.meta.get('pref_code', None)
        city_name = response.meta.get('city_name', None)
        if is_first:
            for ele in response.css("p.pagenation span a"):
                href = urljoin(root_url, ele.attrib['href'])
                yield scrapy.Request(url=href, callback=self.parse_city, meta={
                    'first': False,
                    'pref_code': pref_code,
                    'city_name': city_name,
                })
        for ele in response.css("div.shop-cont div.shop div.shop-prof h3 a"):
            href = ele.attrib['href']
            yield scrapy.Request(url=href, callback=self.parse_shop, meta={
                'pref_code': pref_code,
                'city_name': city_name,
            })

    def parse_shop(self, response):
        pref_code = response.meta.get('pref_code', None)
        city_name = response.meta.get('city_name', None)
        ele_table = response.css("table.shopspec tr")
        shop_name = ele_table[0].css('p::text').get()
        address = ele_table[1].css('p::text').get()
        tel = ele_table[2].css('p::text').get()
        service_time = ele_table[3].css('p.opentime::text').get()
        regular_holiday = ele_table[4].css('td::text').get()
        item = MatsukiyoItem()
        item['pref_code'] = pref_code
        item['pref_name'] = constant.DICT_PREF[pref_code]
        item['city_name'] = city_name
        item['aza_name'] = None
        item['shop_name'] = shop_name
        item['post_code'] = None
        item['address'] = address
        item['tel'] = tel
        item['regular_holiday'] = regular_holiday
        item['service_time'] = service_time
        item['link'] = response.url

        text = response.css('body').attrib['onload']
        m = re.findall(r'ZdcEmapInit\([\'"]([0-9.]+)[\'"]\s*,\s*[\'"]([0-9.]+)', text)
        if len(m) > 0:
            lat, lng = m[0]
            item['lat'] = lat
            item['lng'] = lng

        yield item
