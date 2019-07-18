import scrapy
import zipfile
import os
from io import BytesIO
from gis_scrapy.utils import common

# http://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-N03-v2_3.html
# https://www.e-stat.go.jp/gis/statmap-search?page=1&type=2&aggregateUnitForBoundary=A&toukeiCode=00200521
url_format = 'https://www.e-stat.go.jp/gis/statmap-search/data?dlserveyId=A002005212015&code={pref_code}&coordSys=1&format=shape&downloadType=5'


class BoundaryChomeSpider(scrapy.Spider):
    name = 'boundary_chome'
    custom_settings = {
        'LOG_LEVEL': 'ERROR',
    }

    def start_requests(self):
        for i in range(1, 48):
            pref_code = '%02d' % i
            url = url_format.format(pref_code=pref_code)
            yield scrapy.Request(url, callback=self.parse)

    def parse(self, response):
        path = os.path.join(common.get_storage_path(), 'Boundary', 'chome')
        if not os.path.exists(path):
            os.mkdir(path)
        zip_ref = zipfile.ZipFile(BytesIO(response.body))
        zip_ref.extractall(path)
        zip_ref.close()
