import scrapy
import re
import lxml.html
from collections import defaultdict
from urllib.parse import urljoin
from scrapy import signals
from scrapy.xlib.pydispatch import dispatcher
from gis_scrapy.items import ShopItem
from gis_scrapy.utils import constant

root_url = 'https://www.e-map.ne.jp/p/lawson/'
url_format = 'https://www.e-map.ne.jp/p/lawson/zdcemaphttp2.cgi?target=http%3A%2F%2F127.0.0.1%2Fp%2Flawson%2Fnlist.htm%3F%26lat%3D{lat}%26lon%3D{lng}%26latlon%3D%26radius%3D50000%26jkn%3D%26page%3D{page}%26%26his%3Dal1%252Cal2%252Cal3%252Cal4%252Cnm%26srchplace%3D{lat}%2C{lng}%26https_req%3D1%26PARENT_HTTP_HOST%3Dwww.e-map.ne.jp&zdccnt=2&enc=EUC&encodeflg=0'
dict_cnt = defaultdict(int)
existed_links = []


class LawsonSpider(scrapy.Spider):
    name = 'lawson'
    custom_settings = {
        'LOG_LEVEL': 'ERROR',
    }

    def __init__(self, *args, **kwargs):
        super(LawsonSpider, self).__init__(*args, **kwargs)
        dispatcher.connect(self.spider_closed, signals.spider_closed)

    def spider_closed(self, spider):
        print(dict_cnt)

    def start_requests(self):
        url_format = 'https://www.e-map.ne.jp/p/lawson/search.htm?type=AddrL&adcd={pref_code}'
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

        for ele in response.css("div.result-address ul li a"):
            href = ele.attrib['href']
            if not href:
                continue
            city_code = None
            m = re.findall(r'adcd=(\d{5})', href)
            if m:
                city_code = m[0]
            city_name = ele.css('::text').get()
            url = urljoin(root_url, href)
            yield scrapy.Request(url=url, callback=self.parse_city, meta={
                'first': True,
                'pref_code': pref_code,
                'city_code': city_code,
                'city_name': city_name,
            })
        if is_first:
            for ele in response.css("div.ward li a")[1:]:
                href = ele.attrib['href']
                if not href:
                    continue
                url = urljoin(root_url, href)
                yield scrapy.Request(url=url, callback=self.parse, meta={
                    'first': False,
                    'pref_code': pref_code,
                })

    def parse_city(self, response):
        is_first = response.meta.get('first', False)
        pref_code = response.meta.get('pref_code', None)
        city_code = response.meta.get('city_code', None)
        city_name = response.meta.get('city_name', None)

        for ele in response.css("div.result-address ul li a"):
            href = ele.attrib['href']
            if not href:
                continue
            town_code = None
            m = re.findall(r'adcd=(\d{8})', href)
            if m:
                town_code = m[0]
            town_name = ele.css('::text').get()
            url = urljoin(root_url, href)
            yield scrapy.Request(url=url, callback=self.parse_town, meta={
                'first': True,
                'pref_code': pref_code,
                'city_code': city_code,
                'city_name': city_name,
                'town_code': town_code,
                'town_name': town_name,
            })
        if is_first:
            for ele in response.css("div.ward li a")[1:]:
                href = ele.attrib['href']
                if not href:
                    continue
                url = urljoin(root_url, href)
                yield scrapy.Request(url=url, callback=self.parse_city, meta={
                    'first': False,
                    'pref_code': pref_code,
                    'city_code': city_code,
                    'city_name': city_name,
                })

    def parse_town(self, response):
        pref_code = response.meta.get('pref_code', None)
        city_code = response.meta.get('city_code', None)
        city_name = response.meta.get('city_name', None)
        town_code = response.meta.get('town_code', None)
        town_name = response.meta.get('town_name', None)
        ele = response.css("ul.address-list-select li.link-text-right a")
        if ele and len(ele) > 0:
            href = ele.attrib['href']
            m = re.findall(r'lat=(\d+\.\d+)&lon=(\d+\.\d+)', href)
            if m:
                lat, lng = m[0]
                url = url_format.format(lat=lat, lng=lng, page=0)
                yield scrapy.Request(url=url, callback=self.parse_shop_list, meta={
                    'pref_code': pref_code,
                    'city_code': city_code,
                    'city_name': city_name,
                    'town_code': town_code,
                    'town_name': town_name,
                })
            else:
                print(pref_code, city_name, town_name, response.url, '座標取得できない。')
        else:
            m = re.findall(r'lat=(\d+\.\d+)&lon=(\d+\.\d+)', response.url)
            if m:
                lat, lng = m[0]
                url = url_format.format(lat=lat, lng=lng, page=0)
                yield scrapy.Request(url=url, callback=self.parse_shop_list, meta={
                    'pref_code': pref_code,
                    'city_code': city_code,
                    'city_name': city_name,
                    'town_code': town_code,
                    'town_name': town_name,
                })
            else:
                print(pref_code, city_name, town_name, response.url, '地図情報見つからない。')

    def parse_shop_list(self, response):
        pref_code = response.meta.get('pref_code', None)
        city_code = response.meta.get('city_code', None)
        city_name = response.meta.get('city_name', None)
        town_code = response.meta.get('town_code', None)
        town_name = response.meta.get('town_name', None)
        html = response.body.decode(encoding='euc-jp').strip('ZdcEmapHttpResult').strip("[0123456789]= ';")
        rootEl = lxml.html.fromstring(html)
        for ele in rootEl.cssselect('div.nearest-result-left > div > dl.div-cond'):
            a = ele.cssselect('dt > a')[0] if len(ele.cssselect('dt > a')) > 0 else None
            if not a:
                print(response.url, '店舗取得できない')
                continue
            link = a.get('href')
            domain_link = link[:link.find('?')]
            if domain_link in existed_links:
                continue
            else:
                existed_links.append(domain_link)
            if len(a.cssselect('p.name')) > 0:
                shop_name = a.cssselect('p.name')[0].text
            else:
                print(link, '店舗取得できない')
                continue
            ele_list = ele.cssselect('dd > ul > li')
            address = ele_list[0].text
            tel = ele_list[1].text
            service_time = ele_list[2].text

            item = dict()
            item['pref_code'] = pref_code
            item['pref_name'] = constant.DICT_PREF[pref_code]
            item['city_code'] = city_code
            item['city_name'] = city_name
            item['town_code'] = town_code
            item['town_name'] = town_name
            item['shop_name'] = shop_name
            item['post_code'] = None
            item['address'] = address
            item['tel'] = tel
            item['service_time'] = service_time
            item['regular_holiday'] = None
            item['link'] = link
            yield scrapy.Request(url=link, callback=self.parse_shop, meta={
                'data': item,
            })

        next_list = rootEl.xpath('.//a[text()="次へ"]')
        if len(next_list) > 0:
            href = next_list[0].get('href')
            m = re.findall(r'ZdcEmapSearchShopListClick\((\d+)\)', href)
            if m:
                page = m[0]
                url = re.sub(r'page%3D(\d+)', '%26page%3D{}'.format(page), response.url)
                yield scrapy.Request(url=url, callback=self.parse_shop_list, meta={
                    'pref_code': pref_code,
                    'city_code': city_code,
                    'city_name': city_name,
                    'town_code': town_code,
                    'town_name': town_name,
                })

    def parse_shop(self, response):
        data = response.meta.get('data')
        item = ShopItem(**data)
        pref_code = data.get('pref_code')
        dict_cnt[pref_code] += 1

        onload = response.css('body').attrib['onload']
        m = re.findall(r'ZdcEmapInit\([\'"]*(\d+\.\d+)[\'",]+(\d+\.\d+)', onload)
        if m:
            lat, lng = m[0]
            item['lat'] = lat
            item['lng'] = lng
        yield item
