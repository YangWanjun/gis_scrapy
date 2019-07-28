import scrapy
import zipfile
import os
import psycopg2
import datetime
import json
import shutil
from io import BytesIO
from gis_scrapy.utils import common
from gis_scrapy.utils.base_scrapy import BaseSpider

# http://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-N03-v2_3.html
# https://www.e-stat.go.jp/gis/statmap-search?page=1&type=2&aggregateUnitForBoundary=A&toukeiCode=00200521
url_format = 'https://www.e-stat.go.jp/gis/statmap-search/data' \
             '?dlserveyId=A002005212015&code={pref_code}&coordSys=1&format=shape&downloadType=5'
TEMP_DIR = os.path.join(common.get_storage_path(), 'Boundary', 'chome')


class BoundaryChomeSpider(BaseSpider):
    name = 'boundary_chome'

    def start_requests(self):
        for i in range(1, 48):
            pref_code = '%02d' % i
            url = url_format.format(pref_code=pref_code)
            yield scrapy.Request(url, callback=self.parse)

    def parse(self, response):
        if not os.path.exists(TEMP_DIR):
            os.mkdir(TEMP_DIR)
        zip_ref = zipfile.ZipFile(BytesIO(response.body))
        zip_ref.extractall(TEMP_DIR)
        zip_ref.close()

    @staticmethod
    def close(spider, reason):
        conn_string = spider.settings.get('POSTGRESQL_URL')
        try:
            with psycopg2.connect(conn_string) as conn:
                with conn.cursor() as cursor:
                    cursor.execute('truncate gis_chome;')
                    for filename in os.listdir(TEMP_DIR):
                        if not filename.endswith('.shp'):
                            continue
                        for data in common.read_shape_file(os.path.join(TEMP_DIR, filename), encoding='cp932', srid=4326):
                            sql = "INSERT INTO gis_chome (" \
                                  "    pref_code, pref_name, " \
                                  "    city_code, city_name, chome_code, chome_name, " \
                                  "    category, special_symbol_e, area, perimeter, area_max_f, special_symbol_d, " \
                                  "    people_count, family_count, center_lng, center_lat, mpoly, " \
                                  "    created_dt, updated_dt, is_deleted" \
                                  ") " \
                                  "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s" \
                                  "     , ST_Multi(ST_GeomFromGeoJSON(%s)), %s, %s, %s);"
                            cursor.execute(sql, (
                                data.get('PREF'),
                                data.get('PREF_NAME'),
                                data.get('PREF') + data.get('CITY'),
                                data.get('CITY_NAME'),
                                data.get('KEY_CODE'),
                                data.get('S_NAME'),
                                data.get('HCODE'),
                                data.get('KIGO_E'),
                                data.get('AREA'),
                                data.get('PERIMETER'),
                                data.get('AREA_MAX_F'),
                                data.get('KIGO_D'),
                                data.get('JINKO'),
                                data.get('SETAI'),
                                data.get('X_CODE'),
                                data.get('Y_CODE'),
                                json.dumps(data.get('geom')),
                                datetime.datetime.now(),
                                datetime.datetime.now(),
                                False,
                            ))
                    conn.commit()
        finally:
            shutil.rmtree(TEMP_DIR)
