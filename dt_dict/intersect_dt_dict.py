#-*- coding: utf-8 -*-
from config_dt_dict import ConfigDtDict
from osgeo import ogr

class IntersectDtDict(ConfigDtDict):
    """
        Intersect DT DICT : intersection entre travaux et reseau
    """

    # ----------------------------------------------------------------------
    def intersect_geom(self):
        try:
            result_xml_parser = self.xml_parser()
            for item in result_xml_parser:
                coordinates = item[0]
                noConsultationDuTeleservice = item[1]
                epsg = item[2]
                type_dt_dict = item[3]
                fullpath = item[4]

                #création l'emplacement des travaux et reprojection
                gml = '<gml:MultiSurface><gml:surfaceMembers><gml:CompositeSurface>{}</gml:CompositeSurface></gml:surfaceMembers></gml:MultiSurface>'.format(coordinates)
                geom = ogr.CreateGeometryFromGML(gml)
                multi_poly = geom.ExportToWkt()
                multi_poly_proj = self.projection_layer(multi_poly, 4326, epsg)

                #récupération de la géométrie du réseau unifiée
                union_line = self.shape_line()

                #intersection emplacement travaux et réseau. Si l'intersection est positif, les trauvaux peuvent impacter le réseau
                poly = ogr.CreateGeometryFromWkt(multi_poly_proj)

                #buffer sur emplacement travaux et enveloppe => utiliser pour apercu dans carto pour resultat "negatif"
                buffer_poly = 100
                poly_buffer_poly = poly.Buffer(buffer_poly)
                poly_buffer_polygon = poly_buffer_poly.ExportToWkt()
                poly_buffer_polygon = ogr.CreateGeometryFromWkt(poly_buffer_polygon)
                #calcul enveloppe
                env = poly_buffer_polygon.GetEnvelope()
                min_x = env[0]
                min_y = env[2]
                max_x = env[1]
                max_y = env[3]

                #calcul enveloppe sur emplacement travaux sans buffer => utiliser pour creation du grid
                env_poly = poly.GetEnvelope()
                min_poly_x = env_poly[0]
                min_poly_y = env_poly[2]
                max_poly_x = env_poly[1]
                max_poly_y = env_poly[3]

                #calcul intersection pour definir si le resultat est positif ou negatif
                line = ogr.CreateGeometryFromWkt(union_line)
                intersection = poly.Intersection(line)
                intersection = intersection.ExportToWkt()
                intersection = ogr.CreateGeometryFromWkt(intersection)
                count_intersection = intersection.Length()
                if count_intersection > 0:
                    yield self.res_positif(fullpath, type_dt_dict, noConsultationDuTeleservice, multi_poly_proj, union_line, count_intersection, epsg, min_poly_x, min_poly_y, max_poly_x, max_poly_y)
                else:
                    distance = poly.Distance(line)
                    yield self.res_negatif(fullpath, type_dt_dict, noConsultationDuTeleservice, multi_poly_proj, union_line, distance, epsg, min_x, min_y, max_x, max_y)
        except:
            print('erreur : object intersect')
