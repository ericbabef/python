#-*- coding: utf-8 -*-
import itertools, os
from xml.etree import ElementTree
from osgeo import ogr
from osgeo import osr

class ConfigDtDict(object):
    """
    Configuration DT DICT
    """

    # ----------------------------------------------------------------------
    def __init__(self, dictionary):
        """Constructeur pour le dictionnaire : config.json"""
        for key in dictionary:
            setattr(self, key, dictionary[key])

    def projection_layer(self, layer, source_epsg, target_epsg):
        """Fonction pour la reprojection des données"""
        source = osr.SpatialReference()
        source.ImportFromEPSG(source_epsg)
        target = osr.SpatialReference()
        target.ImportFromEPSG(target_epsg)
        transform = osr.CoordinateTransformation(source, target)
        layer_proj = ogr.CreateGeometryFromWkt(layer)
        layer_proj.Transform(transform)
        # spatialRef = layer_proj.GetSpatialReference()
        # print(spatialRef)
        layer_proj = layer_proj.ExportToWkt()
        return layer_proj

    def shape_line(self):
        """Fonction pour unifier le réseau"""
        path_shp = self.path_shp
        layer_line = ogr.Open(path_shp)
        layer = layer_line.GetLayer()
        # print(layer.GetGeomType())
        union_line = ogr.Geometry(ogr.wkbLineString)
        for feature in layer:
            geom = feature.GetGeometryRef()
            union_line = union_line.Union(geom)
        union_line = union_line.ExportToWkt()
        return union_line

    def xml_parser(self):
        """Fonction pour parser le xml"""
        #path_xml = self.path_xml
        path_xml = os.path.join(os.path.abspath(os.path.dirname(__file__)), "xml" + os.sep)
        epsg = self.epsg
        for root, dirs, files in os.walk(path_xml):
            try:
                for name in files:
                    if name.endswith(".xml"):
                        fullpath = os.path.join(root, name)
                        print(fullpath)
                        with open(fullpath, 'rt') as f:
                            tree = ElementTree.parse(f)

                        nsp = 'http://www.reseaux-et-canalisations.gouv.fr/schema-teleservice/2.2'
                        gml = 'http://www.opengis.net/gml/3.2'
                        list_dt_dict = ['DT', 'DICT', 'dtDictConjointes', 'ATU']
                        list_surface_members = ['surfaceMembers', 'surfaceMember']
                        list_coordinates = ['coordinates', 'posList']

                        for list_dt_dict in list_dt_dict:
                            type_dt_dict = None
                            noConsultationDuTeleservice = None
                            coordinates = None
                            if list_dt_dict == 'dtDictConjointes':
                                for node in tree.iter('{' + nsp + '}' + list_dt_dict):
                                    type_dt_dict = list_dt_dict
                                    noConsultationDuTeleservice = node.findtext('{' + nsp + '}' + 'noConsultationDuTeleservice')
                                    for a in node.iter('{' + nsp + '}' + 'partieDICT'):
                                        for b in a.iter('{' + nsp + '}' + 'emprise'):
                                            for c in b.iter('{' + nsp + '}' + 'geometrie'):
                                                for list_surface_members in list_surface_members:
                                                    h = []
                                                    for d in c.iter('{' + gml + '}' + list_surface_members):
                                                        for e in d.iter('{' + gml + '}' + 'Polygon'):
                                                            for f in e.iter('{' + gml + '}' + 'exterior'):
                                                                for g in f.iter('{' + gml + '}' + 'LinearRing'):
                                                                    h.append([
                                                                                 '<gml:surfaceMember><gml:Polygon><gml:exterior><gml:LinearRing><gml:posList>' + g.findtext(
                                                                                     '{' + gml + '}' + 'coordinates').replace(',',
                                                                                                                              ' ') + '</gml:posList></gml:LinearRing></gml:exterior></gml:Polygon></gml:surfaceMember>'])
                                                                    coordinates = list(itertools.chain.from_iterable(h))
                                                                    coordinates = ''.join(coordinates)
                                yield coordinates, noConsultationDuTeleservice, epsg, type_dt_dict, fullpath
            except:
                print('erreur : {}'.format(fullpath))
                return