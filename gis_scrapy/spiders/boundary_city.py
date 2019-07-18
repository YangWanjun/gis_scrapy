import scrapy
import zipfile
import os
from io import BytesIO
from gis_scrapy.utils import common

# 参照ＵＲＬ
# https://www.esrij.com/products/japan-shp/


class BoundaryCitySpider(scrapy.Spider):
    name = 'boundary_city'
    custom_settings = {
        'LOG_LEVEL': 'ERROR',
    }

    start_urls = [
        'https://www.esrij.com/cgi-bin/wp/wp-content/uploads/2017/01/japan_ver81.zip',
    ]

    def parse(self, response):
        path = os.path.join(common.get_storage_path(), 'Boundary', 'city')
        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)
        zip_ref = zipfile.ZipFile(BytesIO(response.body))
        zip_ref.extractall(path)
        zip_ref.close()
