import scrapy
import re
import csv
from scrapy_shop.items import SevenCoordinateItem


class MapShopSpider(scrapy.Spider):
    name = 'map_shop'

    def start_requests(self):
        for header, row in self.get_seven_shops():
            data = dict(zip(header, row))
            yield scrapy.Request(url=data.get('link'), callback=self.parse, meta={'data': data})

    def parse(self, response):
        data = response.meta.get('data', None)
        if len(response.css("div#rightArea table").css('a')) > 0:
            href = response.css("div#rightArea table").css('a')[0].attrib['href']
            m = re.findall(r'javascript:ZdcEmapMapScroll\([\'"]*([0-9.]+)[\'"]*,\s*[\'"]*([0-9.]+)[\'"]*\)', href)
            if len(m) > 0:
                lat, lng = m[0]
                item = SevenCoordinateItem(**data)
                item['lat'] = lat
                item['lng'] = lng
                yield item

    def get_seven_shops(self):
        with open(r'seven.csv', 'r') as f:
            reader = csv.reader(f)
            header = next(reader)

            for row in reader:
                yield header, row
