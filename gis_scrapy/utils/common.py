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
    cursor.execute(
        "SELECT city_code FROM gis_city WHERE pref_name = %s AND city_name = %s;",
        (pref_name, city_name)
    )
    ret_value = cursor.fetchone()
    return ret_value[0] if ret_value else None
