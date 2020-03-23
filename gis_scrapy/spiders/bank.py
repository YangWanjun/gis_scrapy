import os
import datetime
import MySQLdb
import scrapy
from gis_scrapy.utils.base_scrapy import BaseSpider

MYSQL_CONFIG = {
    'host': os.environ['MYSQL_PORT_3306_TCP_ADDR'],
    'db': 'sales',  # Database Name
    'user': 'root',
    'passwd': os.environ['MYSQL_ENV_MYSQL_ROOT_PASSWORD'],
    'charset': 'utf8',
}


class BankSpider(BaseSpider):
    name = 'bank'
    start_urls = [
        'https://bkichiran.hikak.com/',
        'https://bkichiran.hikak.com/index2.php',
        'https://bkichiran.hikak.com/index3.php',
        'https://bkichiran.hikak.com/index4.php',
        'https://bkichiran.hikak.com/index5.php',
        'https://bkichiran.hikak.com/index6.php',
        'https://bkichiran.hikak.com/index7.php',
    ]

    def __init__(self, *args, **kwargs):
        super(BankSpider, self).__init__(*args, **kwargs)
        self.conn = MySQLdb.connect(**MYSQL_CONFIG)

    def parse(self, response):
        for tr in response.css("div.tb1 table.tb2 tbody tr"):
            if len(tr.css("td.t1 a")) == 0:
                continue
            for i, item in enumerate(tr.css("td.t1 a")):
                bank_name = item.css("::text").get()
                bank_code = tr.css("td.t2::text")[i].get()
                href = item.attrib['href']
                self.insert_bank(bank_code, bank_name)
                yield scrapy.Request(url='https://bkichiran.hikak.com/' + href, callback=self.parse_branch, meta={
                    'bank_code': bank_code,
                    'bank_name': bank_name,
                })

    def insert_bank(self, code, name):
        with self.conn.cursor() as cursor:
            sql = "SELECT COUNT(1) FROM mst_bank WHERE CODE = %s"
            cursor.execute(sql, (code,))
            row = cursor.fetchone()
            if row[0] == 0:
                now = datetime.datetime.now()
                cursor.execute("INSERT INTO mst_bank (code, name, kana, created_dt, updated_dt, is_deleted) "
                               "VALUES (%s, %s, null, %s, %s, 0)", (code, name, now, now))
                print(code, name, '追加済')
        self.conn.commit()

    def parse_branch(self, response):
        bank_code = response.meta.get('bank_code')
        bank_name = response.meta.get('bank_name')
        now = datetime.datetime.now()
        with self.conn.cursor() as cursor:
            for tr in response.css("div.tb1 table.tb2 tbody tr"):
                if len(tr.css("td.t1 a")) == 0:
                    continue
                for i, item in enumerate(tr.css("td.t1 a")):
                    branch_name = item.css("::text").get()
                    branch_code = tr.css("td.t2::text")[i].get()
                    cursor.execute(
                        "SELECT COUNT(1) FROM mst_bank_branch WHERE bank_id = %s AND branch_no = %s",
                        (bank_code, branch_code)
                    )
                    row = cursor.fetchone()
                    if row[0] == 0:
                        cursor.execute("INSERT INTO mst_bank_branch (bank_id, branch_no, branch_name, created_dt, updated_dt, is_deleted) "
                                       "VALUES (%s, %s, %s, %s, %s, 0)", (bank_code, branch_code, branch_name, now, now))
                        self.conn.commit()
                        print(bank_code, bank_name, branch_code, branch_name, '追加済')
                        yield scrapy.Request(url=item.attrib['href'], callback=self.parse_detail, meta={
                            'bank_code': bank_code,
                            'branch_code': branch_code
                        })

    def parse_detail(self, response):
        bank_code = response.meta.get('bank_code')
        branch_code = response.meta.get('branch_code')
        data = {}
        for i, tr in enumerate(response.css("div.ds15 table.tbl1 tbody tr")):
            if len(tr.css("td.b53")) == 0:
                continue
            name = tr.css("td.b53::text").get()
            value = tr.css("td.b54::text").get()
            if name == 'フリガナ' and i == 3:
                data['bank_kana'] = value
            elif name == 'フリガナ' and i == 6:
                data['branch_kana'] = value
            elif name == '住所':
                data['address'] = value.replace("［", "").strip() if value else None
            elif name == "電話番号":
                data['tel'] = value.replace('-', '') if value else None
            elif name == '外部リンク':
                if len(tr.css('td a')) > 0:
                    data['url'] = tr.css('td a')[0].attrib['href']
        with self.conn.cursor() as cursor:
            cursor.execute(
                "UPDATE mst_bank SET kana = %s, homepage = %s WHERE code = %s", (
                    data.get('bank_kana'),
                    data.get('url'),
                    bank_code,
                )
            )
            cursor.execute(
                "UPDATE mst_bank_branch SET branch_kana = %s, address = %s, tel = %s WHERE bank_id = %s AND branch_no = %s", (
                    data.get('branch_kana'),
                    data.get('address'),
                    data.get('tel'),
                    bank_code,
                    branch_code
                )
            )
        self.conn.commit()
