import psycopg2
import datetime
from gis_scrapy.utils import common
from gis_scrapy.utils.base_scrapy import BaseSpider

# PAGE URL
# https://www.post.japanpost.jp/zipcode/dl/kogaki-zip.html


class PostcodeSpider(BaseSpider):
    name = 'postcode'
    start_urls = [
        'https://www.post.japanpost.jp/zipcode/dl/kogaki/zip/ken_all.zip'
    ]

    def parse(self, response):
        conn_string = self.settings.get('POSTGRESQL_URL')
        zip_file = self.download_zip(response)
        with psycopg2.connect(conn_string) as conn:
            with conn.cursor() as cursor:
                cursor.execute('truncate gis_post_code;')
                for name in zip_file.namelist():
                    with zip_file.open(name) as f:
                        text = f.read().decode('cp932')
                        for idx, num, row in self.read_csv_from_text(text):
                            if idx == 0:
                                self.add_process(name, num)
                            self.insert_postcode(name, row, cursor)
                conn.commit()

    def insert_postcode(self, process_name, data, cursor):
        self.update_process(process_name)
        post_code = data[2]
        pref_name = data[6]
        pref_code = common.get_pref_code_by_name(pref_name)
        if not pref_code:
            self.logger.warning('{} の都道府県番号が見つからない'.format(pref_name))
            return
        pref_kana = data[3]
        city_name = data[7]
        city_kana = data[4]
        city_code = common.get_city_code_by_name(cursor, pref_name, city_name)
        if not city_code:
            self.logger.warning('{} {} の市区町村番号が見つからない'.format(pref_name, city_name))
            return
        town_name = data[8]
        town_kana = data[5]
        is_partial = data[9] == '1'
        is_multi_chome = data[11] == '1'
        is_multi_town = data[12] == '1'

        sql = "INSERT INTO gis_post_code (" \
              "    post_code, pref_name, " \
              "    pref_code, pref_kana, city_name, city_kana, city_code, " \
              "    town_name, town_kana, is_partial, is_multi_chome, is_multi_town, " \
              "    created_dt, updated_dt, is_deleted" \
              ") " \
              "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"
        cursor.execute(sql, (
            post_code,
            pref_name,
            pref_code,
            pref_kana,
            city_name,
            city_kana,
            city_code,
            town_name,
            town_kana,
            is_partial,
            is_multi_chome,
            is_multi_town,
            datetime.datetime.now(),
            datetime.datetime.now(),
            False,
        ))
