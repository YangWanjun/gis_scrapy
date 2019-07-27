import zipfile
import os
import shutil
import psycopg2
import json
import datetime
from io import BytesIO
from gis_scrapy.utils import common
from gis_scrapy.utils.base_scrapy import BaseSpider

# 参照ＵＲＬ
# https://www.esrij.com/products/japan-shp/
TEMP_DIR = os.path.join(common.get_storage_path(), 'Boundary', 'city')


class BoundaryCitySpider(BaseSpider):
    name = 'boundary_city'

    start_urls = [
        'https://www.esrij.com/cgi-bin/wp/wp-content/uploads/2017/01/japan_ver81.zip',
    ]

    def parse(self, response):
        if os.path.exists(TEMP_DIR):
            shutil.rmtree(TEMP_DIR)
        os.makedirs(TEMP_DIR, exist_ok=True)
        zip_ref = zipfile.ZipFile(BytesIO(response.body))
        zip_ref.extractall(TEMP_DIR)
        zip_ref.close()
        try:
            self.save_to_database()
        finally:
            shutil.rmtree(TEMP_DIR)

    def save_to_database(self):
        conn_string = self.settings.get('POSTGRESQL_URL')
        with psycopg2.connect(conn_string) as conn:
            with conn.cursor() as cursor:
                for filename in os.listdir(TEMP_DIR):
                    if not filename.endswith('.shp'):
                        continue
                    for data in common.read_shape_file(os.path.join(TEMP_DIR, filename), encoding='cp932', srid=4326):
                        sql = "INSERT INTO gis_city (" \
                              "    pref_code, pref_name, " \
                              "    city_code, city_name, city_name_en, gun_name, " \
                              "    people_count, family_count, mpoly, " \
                              "    created_dt, updated_dt, is_deleted" \
                              ") " \
                              "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, ST_Multi(ST_GeomFromGeoJSON(%s)), %s, %s, %s);"
                        cursor.execute(sql, (
                            data.get('JCODE')[:2],
                            data.get('KEN'),
                            data.get('JCODE'),
                            data.get('SIKUCHOSON'),
                            data.get('CITY_ENG'),
                            data.get('GUN'),
                            data.get('P_NUM'),
                            data.get('H_NUM'),
                            json.dumps(data.get('geom')),
                            datetime.datetime.now(),
                            datetime.datetime.now(),
                            False,
                        ))
