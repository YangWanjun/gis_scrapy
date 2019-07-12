import scrapy
import lxml.html
import urllib.parse
import re
from . import errors
from scrapy_shop.items import SevenItem
from scrapy_shop.utils import constant

url_root = 'https://www.e-map.ne.jp/smt/711map/'


class SevenSpider(scrapy.Spider):
    name = 'seven'

    def start_requests(self):
        url_format = "https://www.e-map.ne.jp/smt/711map/sl.htm?ltype=1&area1={pref_code}&area2=&filter=&cond40=COL_02%3ADT%3ALTE%3ASYSDATE&cond41=COL_12%3A1&p_s1=40000&p_f2=1&p_f4=1&p_f8=1"
        for i in range(1, 48):
            pref_code = '%02d' % i
            url = url_format.format(pref_code=pref_code)
            yield scrapy.Request(url=url, callback=self.parse_pref, meta={
                'pref_code': pref_code,
            })

    def parse_pref(self, response):
        pref_code = response.meta.get('pref_code', None)
        url_format = "https://www.e-map.ne.jp/smt/711map/zdcemaphttp2.cgi?target=http%3A%2F%2F127.0.0.1%2Fsmt%2F711map%2Fsl_list.htm%3F%26ltype%3D1%26area1%3D{pref_code}%26cond40%3DCOL_02%253ADT%253ALTE%253ASYSDATE%26cond41%3DCOL_12%253A1%26p_s1%3D40000%26p_f2%3D1%26p_f4%3D1%26p_f8%3D1%26pg%3D{page}%26https_req%3D1%26PARENT_HTTP_HOST%3Dwww.e-map.ne.jp&zdccnt={page}&enc=UTF8&encodeflg=1"
        url_params = {'pref_code': pref_code, 'page': 1}
        url = url_format.format(**url_params)
        yield scrapy.Request(url=url, callback=self.parse_ajax, meta={
            'pref_code': pref_code,
            'category': constant.PARSE_PREF,
            'url_format': url_format,
            'url_params': url_params,
        })

    def parse_ajax(self, response):
        category = response.meta.get('category', None)
        pref_code = response.meta.get('pref_code', None)
        pref_name = constant.DICT_PREF[pref_code]
        city_name = response.meta.get('city_name', None)
        if response.text.find('z_error_msg') >= 0:
            index = response.meta.get('index', None)
            if category == constant.PARSE_PREF:
                raise errors.PrefParseException('{}解析エラー、{} page'.format(pref_name, index))
            elif category == constant.PARSE_CITY:
                raise errors.PrefParseException('{}解析エラー、{} page'.format(city_name, index))
        html = urllib.parse.unquote(response.text).strip('ZdcEmapHttpResult').strip("[0123456789]= ';")
        rootEl = lxml.html.fromstring(html)
        for el in rootEl.cssselect('div.z_litem > a'):
            href = el.get('href')
            el_span = el.cssselect('span')
            if len(el_span) > 0:
                name = el_span[0].text
                name = re.sub(r'[()0-9]', '', name)
                if category == constant.PARSE_PREF:
                    url_format = "https://www.e-map.ne.jp/smt/711map/zdcemaphttp2.cgi?target=http%3A%2F%2F127.0.0.1%2Fsmt%2F711map%2Fsl_list.htm%3F%26ltype%3D1%26area1%3D{pref_code}%26area2%3D{city_name}%26cond40%3DCOL_02%253ADT%253ALTE%253ASYSDATE%26cond41%3DCOL_12%253A1%26p_s1%3D40000%26p_f2%3D1%26p_f4%3D1%26p_f8%3D1%26pg%3D{page}%26https_req%3D1%26PARENT_HTTP_HOST%3Dwww.e-map.ne.jp&zdccnt={page}&enc=UTF8&encodeflg=1"
                    url_params = {'pref_code': pref_code, 'city_name': name, 'page': 1}
                    url = url_format.format(**url_params)
                    yield scrapy.Request(url=url, callback=self.parse_ajax, meta={
                        'category': constant.PARSE_CITY,
                        'pref_code': pref_code,
                        'city_name': name,
                        'url_format': url_format,
                        'url_params': url_params,
                    })
                elif category == constant.PARSE_CITY:
                    yield scrapy.Request(url=href, callback=self.parse_shop, meta={
                        'category': constant.PARSE_SHOP,
                        'pref_code': pref_code,
                        'city_name': city_name,
                        'aza_name': name,
                    })
        if len(rootEl.cssselect("div.z_litem_nextPage")) > 0:
            url_format = response.meta.get('url_format', None)
            url_params = response.meta.get('url_params', None)
            url_params['page'] += 1
            url = url_format.format(**url_params)
            if category == constant.PARSE_PREF:
                yield scrapy.Request(url=url, callback=self.parse_ajax, meta={
                    'category': constant.PARSE_PREF,
                    'pref_code': pref_code,
                    'url_format': url_format,
                    'url_params': url_params,
                })
            elif category == constant.PARSE_CITY:
                yield scrapy.Request(url=url, callback=self.parse_ajax, meta={
                    'category': constant.PARSE_CITY,
                    'pref_code': pref_code,
                    'city_name': city_name,
                    'url_format': url_format,
                    'url_params': url_params,
                })

    def parse_shop(self, response):
        # category = response.meta.get('category', None)
        pref_code = response.meta.get('pref_code', None)
        pref_name = constant.DICT_PREF[pref_code]
        city_name = response.meta.get('city_name', None)
        aza_name = response.meta.get('aza_name', None)
        shop_name = response.css("div.z_inf_name li span::text")[0].get()
        post_code = response.css("div.z_litem")[0].css('a span::text')[1].get().strip().strip('〒')
        address = response.css("div.z_litem")[0].css('a span::text')[2].get().strip()
        tel = response.css("div.z_litem")[1].css('a span::text')[1].get().strip()
        service_time = response.css("div.z_litem")[3].css('p span::text')[1].get().strip()
        # データを保存
        item = SevenItem()
        item['pref_code'] = pref_code
        item['pref_name'] = pref_name
        item['city_name'] = city_name
        item['aza_name'] = aza_name
        item['shop_name'] = shop_name
        item['post_code'] = post_code
        item['address'] = address
        item['tel'] = tel
        item['service_time'] = service_time
        item['link'] = response.url
        # ＵＲＬを解析
        m = re.findall(r'https://www.e-map.ne.jp/smt/711map/inf/(\d+)/\?(.+)', response.url)
        if len(m) > 0:
            code, params = m[0]
            url_format = "https://www.e-map.ne.jp/p/711map/dtl/{code}/?{params}"
            url = url_format.format(code=code, params=params)
            item['link'] = url
            # yield scrapy.Request(url=url, callback=self.parse_coordinate, meta={
            #     'data': item,
            # })
        yield item

    # def parse_coordinate(self, response):
    #     data = response.meta.get('data', None)
    #     print(data)
    #     print(response.url)
    #     print(response.text)
    #     if len(response.css("div#rightArea table").css('a')) > 0:
    #         href = response.css("div#rightArea table").css('a')[0].attrib['href']
    #         m = re.findall(r'javascript:ZdcEmapMapScroll\([\'"]*([0-9.]+[\'"]*),\s*[\'"]*([0-9.]+)[\'"]*\)', href)
    #         if len(m) > 0:
    #             lat, lng = m[0]
    #             item = SevenItem(**data)
    #             item['lat'] = lat
    #             item['lng'] = lng
    #             yield item
