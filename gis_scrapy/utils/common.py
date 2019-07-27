import os
import shapefile


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
    for shape_record in shp.iterShapeRecords():
        data = {}
        for f_name, f_type, f_length, f_decmail_length in fields:
            data[f_name] = shape_record.record[f_name]
        data['geom'] = shape_record.shape.__geo_interface__
        data['geom']['crs'] = {"type": "name", "properties": {"name": "EPSG:{}".format(srid)}}
        yield data
