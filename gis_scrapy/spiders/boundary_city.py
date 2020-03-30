import scrapy
import zipfile
import os
import shutil
import psycopg2
import json
import datetime
from io import BytesIO
from gis_scrapy.utils import common, constant
from gis_scrapy.utils.base_scrapy import BaseSpider

# 参照ＵＲＬ
# https://www.esrij.com/products/japan-shp/
TEMP_DIR = os.path.join(common.get_storage_path(), 'Boundary', 'city')


class BoundaryCitySpider(BaseSpider):
    name = 'boundary_city'

    def start_requests(self):
        conn_string = self.settings.get('POSTGRESQL_URL')
        self.add_process('pref', 47, desc='都道府県')
        with psycopg2.connect(conn_string) as conn:
            with conn.cursor() as cursor:
                cursor.execute('truncate gis_pref CASCADE;')
                sql = "INSERT INTO gis_pref (pref_code, pref_name, created_dt, updated_dt, is_deleted) " \
                      "VALUES (%s, %s, %s, %s, %s);"
                for idx, (code, name) in enumerate(constant.DICT_PREF.items()):
                    cursor.execute(sql, (
                        code,
                        name,
                        datetime.datetime.now(),
                        datetime.datetime.now(),
                        False,
                    ))
                    self.update_process('pref')
                conn.commit()
        self.end_processes('pref')
        yield scrapy.Request(
            url='https://www.esrij.com/cgi-bin/wp/wp-content/uploads/2017/01/japan_ver81.zip',
            callback=self.parse,
        )

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
                cursor.execute('truncate gis_city cascade;')
                for filename in os.listdir(TEMP_DIR):
                    if not filename.endswith('.shp'):
                        continue
                    for i, num, data in common.read_shape_file(
                            os.path.join(TEMP_DIR, filename), encoding='cp932', srid=4326
                    ):
                        if i == 0:
                            self.add_process('city', num, desc='市区町村')
                        sql = "INSERT INTO gis_city (" \
                              "    pref_code, pref_name, " \
                              "    city_code, city_name, city_name_en, gun_name, " \
                              "    people_count, family_count, mpoly, " \
                              "    created_dt, updated_dt, is_deleted" \
                              ") " \
                              "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, ST_Multi(ST_GeomFromGeoJSON(%s)), %s, %s, %s);"
                        self.update_process('city')
                        if not data.get('JCODE'):
                            self.logger.warning('市区町村コードが空白です、{}'.format(data))
                            continue
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
                # 市区町村から都道府県をマージする
                cursor.execute("UPDATE gis_pref"
                               "   SET family_count = t.family_count"
                               "     , people_count = t.people_count"
                               "     , mpoly = t.mpoly"
                               "  FROM ("
                               "       SELECT pref_code"
                               "            , max(pref_name) as pref_name"
                               "            , max(people_count) as people_count"
                               "            , max(family_count) as family_count"
                               "            , ST_MULTI(ST_UNION(ST_SnapToGrid(mpoly,0.00001))) as mpoly"
                               "         from gis_city "
                               "        where pref_code is not null and pref_code <> ''"
                               "        group by pref_code"
                               "  ) AS t"
                               " WHERE gis_pref.pref_code = t.pref_code;")
                conn.commit()
        self.end_processes('city')
