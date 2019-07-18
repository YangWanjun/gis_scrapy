import scrapy
import zipfile
from urllib.parse import urljoin
from io import BytesIO


class AddressSpider(scrapy.Spider):
    name = 'address'
    custom_settings = {
        'LOG_LEVEL': 'ERROR',
    }
    start_urls = [
        'https://saigai.gsi.go.jp/jusho/download/index.html',
    ]

    def parse(self, response):
        for sel_link in response.xpath('//a[contains(@href, "pref")]'):
            name = sel_link.xpath('text()').extract_first()
            p_link = sel_link.xpath('@href').extract_first()
            a_link = urljoin(response.url, p_link)
            yield scrapy.Request(url=a_link, callback=self.parse_city, meta={'pref_name': name})
            break

    def parse_city(self, response):
        pref_name = response.meta.get('pref_name')
        for sel_link in response.xpath('//li/a[contains(@href, "data")]'):
            name = sel_link.xpath('text()').extract_first()
            p_link = sel_link.xpath('@href').extract_first()
            a_link = urljoin(response.url, p_link)
            yield scrapy.Request(url=a_link, callback=self.save_address, meta={
                'pref_name': pref_name, 'city_name': name
            })
            break

    def save_address(self, response):
        # pref_name = response.meta.get('pref_name')
        # city_name = response.meta.get('city_name')
        # file_name = '%s_%s' % (pref_name, city_name)
        zip_ref = zipfile.ZipFile(BytesIO(response.body))
        for name in zip_ref.namelist():
            if name[-4:].lower() == '.csv':
                print(name)
