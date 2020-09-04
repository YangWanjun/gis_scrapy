import os
import shapefile
from . import constant


def get_storage_path():
    dir_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    path = os.path.join(dir_path, 'output')
    if not os.path.exists(path):
        os.mkdir(path)
    return path


def read_shape_file(path, encoding='cp932', srid=4326):
    if not os.path.exists(path):
        raise Exception('シェープファイルが存在しません。')
    shp = shapefile.Reader(path, encoding=encoding)
    fields = shp.fields[1:]
    total = shp.numRecords
    for i, shape_record in enumerate(shp.iterShapeRecords()):
        data = {}
        for f_name, f_type, f_length, f_decmail_length in fields:
            data[f_name] = shape_record.record[f_name]
        data['geom'] = shape_record.shape.__geo_interface__
        data['geom']['crs'] = {"type": "name", "properties": {"name": "EPSG:{}".format(srid)}}
        yield i, total, data


def get_pref_code_by_name(name):
    for k, v in constant.DICT_PREF.items():
        if v == name:
            return k
    return None


def get_city_code_by_name(cursor, pref_name, city_name):
    if len(city_name[1:].split('郡')) > 1 and city_name[-1] != '郡' and city_name[-2:] not in ('郡市', '郡村') and \
            city_name not in ('大和郡山市',):
        index = city_name[1:].find('郡') + 1
        cursor.execute(
            "SELECT city_code FROM gis_city WHERE pref_name = %s AND gun_name = %s AND city_name = %s;",
            (pref_name, city_name[:index + 1], city_name[index + 1:])
        )
        ret_value = cursor.fetchone()
    elif len(city_name[1:].split('市')) > 1 and city_name[-1] != '市' and city_name[-2:] not in ('市郡', '市村'):
        index = city_name[1:].find('市') + 1
        cursor.execute(
            "SELECT city_code FROM gis_city WHERE pref_name = %s AND city_name = %s;",
            (pref_name, city_name[index + 1:])
        )
        ret_value = cursor.fetchone()
    elif len(city_name[1:].split('島')) > 1 and city_name[-2:] not in ('島郡', '島市', '島村', '島区', '島町') and \
            city_name not in ('南島原市',):
        index = city_name[1:].find('島') + 1
        cursor.execute(
            "SELECT city_code FROM gis_city WHERE pref_name = %s AND city_name = %s;",
            (pref_name, city_name[index + 1:])
        )
        ret_value = cursor.fetchone()
    else:
        if city_name in ('那珂川市', '那珂川町'):
            city_name = '那珂川町'
        cursor.execute(
            "SELECT city_code FROM gis_city WHERE pref_name = %s AND city_name = %s;",
            (pref_name, city_name)
        )
        ret_value = cursor.fetchone()
    if ret_value:
        return ret_value[0]
    else:
        return None
