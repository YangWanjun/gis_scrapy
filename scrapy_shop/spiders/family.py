import scrapy
import re
from collections import defaultdict
from urllib.parse import urljoin
from scrapy_shop.utils import constant
from scrapy_shop.items import FamilyShopItem
from scrapy import signals
from scrapy.xlib.pydispatch import dispatcher

root_url = 'http://as.chizumaru.com/'

dict_cnt = defaultdict(int)


class FamilySpider(scrapy.Spider):
    name = 'family'

    def __init__(self, *args, **kwargs):
        super(FamilySpider, self).__init__(*args, **kwargs)
        self.pref_code = kwargs.get('code', None)
        dispatcher.connect(self.spider_closed, signals.spider_closed)

    def spider_closed(self, spider):
        print(dict_cnt)

    def start_requests(self):
        url_format = 'http://as.chizumaru.com/famima/articleList?c1=1&template=Ctrl/DispListArticle_g12&pageLimit=10000&pageSize=5&account=famima&accmd=0&bpref={pref_code}&c2=1'
        # for i in range(1, 48):
        pref_code = self.pref_code
        url = url_format.format(pref_code=pref_code)
        yield scrapy.Request(url=url, callback=self.parse, meta={
            'pref_code': pref_code,
        })
        # break

    def parse(self, response):
        pref_code = response.meta.get('pref_code', None)
        for tr in response.css("table.cz_table01 tbody tr"):
            ele = tr.css('a')[0] if len(tr.css('a')) > 0 else None
            if ele:
                href = ele.attrib['href']
                name = ele.css('::text').get()
                url = urljoin(root_url, href)
                # print(pref_code, name, url)
                yield scrapy.Request(url=url, callback=self.parse_shop, meta={
                    'pref_code': pref_code,
                })
        next_ele = response.xpath("//*[contains(text(), '次へ')]")
        if len(next_ele) > 0:
            onclick = next_ele[0].attrib['onclick']
            page = re.findall(r'pg=(\d+)', onclick)[0]
            url = re.sub(r'&?pg=\d+', '', response.url) + '&pg={}'.format(page)
            # print(url)
            yield scrapy.Request(url=url, callback=self.parse, meta={
                'pref_code': pref_code,
            })

    def parse_shop(self, response):
        pref_code = response.meta.get('pref_code', None)
        tds = response.css('table.cz_table01 tr td')
        shop_name = tds[0].css('::text').get()
        address = tds[1].css('::text').get()
        tel = tds[2].css('::text').get()
        service_time = tds[3].css('::text').get().strip()
        dict_cnt[pref_code] += 1

        item = FamilyShopItem()
        item['pref_code'] = pref_code
        item['pref_name'] = constant.DICT_PREF[pref_code]
        item['city_name'] = None
        item['aza_name'] = None
        item['shop_name'] = shop_name
        item['post_code'] = None
        item['address'] = address
        item['tel'] = tel
        item['service_time'] = service_time
        item['link'] = response.url

        m = re.findall(r'detailBukkenXYAry\[cntXY\]\s*=\s*(\d+\.\d+)', response.text)
        if m:
            x, y = m
            lng = self.get_coordinate(x)
            lat = self.get_coordinate(y)
            item['lng'] = lng
            item['lat'] = lat
        yield item

    @classmethod
    def get_coordinate(cls, x):
        if not isinstance(x, (int, float)):
            x = float(x)
        d_part, dec_part = divmod(x, 3600)
        m_part, s_part = divmod(dec_part, 60)
        return d_part + m_part / 60 + s_part / 3600
