#-*- coding: utf-8 -*-
from intersect_dt_dict import IntersectDtDict
import os, mapnik
from osgeo import ogr
from math import ceil
from pdfjinja import PdfJinja

class TraitementsDtDict(IntersectDtDict):
    """
        Traitements DT DICT
    """

    # ----------------------------------------------------------------------
    def vider_dossier(self):
        """Fonction vider le dossier"""
        path_temp = os.path.join(os.path.abspath(os.path.dirname(__file__)), "temp" + os.sep)
        for filename in os.listdir(path_temp):
            os.remove(path_temp + filename)

    def grid(self, min_x, min_y, max_x, max_y):
        """Fonction pour creer le grid"""
        # convert sys.argv to float
        xmin = float(min_x)
        xmax = float(max_x)
        ymin = float(min_y)
        ymax = float(max_y)
        gridWidth = 50
        gridHeight = 50
        # get rows
        rows = ceil((ymax - ymin) / gridHeight)
        # get columns
        cols = ceil((xmax - xmin) / gridWidth)
        # start grid cell envelope
        ringXleftOrigin = xmin
        ringXrightOrigin = xmin + gridWidth
        ringYtopOrigin = ymax
        ringYbottomOrigin = ymax - gridHeight
        # create output file
        outDriver = ogr.GetDriverByName('ESRI Shapefile')
        outputGridfn = os.path.join(os.path.abspath(os.path.dirname(__file__)), "temp" + os.sep + "grid.shp")
        if os.path.exists(outputGridfn):
            os.remove(outputGridfn)
        outDataSource = outDriver.CreateDataSource(outputGridfn)
        outLayer = outDataSource.CreateLayer(outputGridfn, geom_type=ogr.wkbPolygon)
        featureDefn = outLayer.GetLayerDefn()
        # create grid cells
        countcols = 0
        while countcols < cols:
            countcols += 1
            # reset envelope for rows
            ringYtop = ringYtopOrigin
            ringYbottom = ringYbottomOrigin
            countrows = 0
            while countrows < rows:
                countrows += 1
                ring = ogr.Geometry(ogr.wkbLinearRing)
                ring.AddPoint(ringXleftOrigin, ringYtop)
                ring.AddPoint(ringXrightOrigin, ringYtop)
                ring.AddPoint(ringXrightOrigin, ringYbottom)
                ring.AddPoint(ringXleftOrigin, ringYbottom)
                ring.AddPoint(ringXleftOrigin, ringYtop)
                poly = ogr.Geometry(ogr.wkbPolygon)
                poly.AddGeometry(ring)
                # add new geom to layer
                outFeature = ogr.Feature(featureDefn)
                outFeature.SetGeometry(poly)
                outLayer.CreateFeature(outFeature)
                outFeature.Destroy
                # new envelope for next poly
                ringYtop = ringYtop - gridHeight
                ringYbottom = ringYbottom - gridHeight
            # new envelope for next poly
            ringXleftOrigin = ringXleftOrigin + gridWidth
            ringXrightOrigin = ringXrightOrigin + gridWidth
        # Close DataSources
        outDataSource.Destroy()
        return outputGridfn

    def grid_enveloppe(self):
        """Fonction pour l'enveloppe sur le grid avec buffer"""
        path_grid_shp = os.path.join(os.path.abspath(os.path.dirname(__file__)), "temp" + os.sep + "grid.shp")
        layer_poly = ogr.Open(path_grid_shp)
        layer = layer_poly.GetLayer()
        union_poly = ogr.Geometry(ogr.wkbLineString)
        for feature in layer:
            geom = feature.GetGeometryRef()
            union_poly = union_poly.Union(geom)
        union_poly = union_poly.ExportToWkt()
        poly = ogr.CreateGeometryFromWkt(union_poly)
        buffer_poly = 100
        poly_buffer_poly = poly.Buffer(buffer_poly)
        env_poly = poly_buffer_poly.GetEnvelope()
        min_poly_x = env_poly[0]
        min_poly_y = env_poly[2]
        max_poly_x = env_poly[1]
        max_poly_y = env_poly[3]
        return min_poly_x, min_poly_y, max_poly_x, max_poly_y

    def mapnik_config(self, min_x, min_y, max_x, max_y):
        """Fonction pour configuer la carto => sa largeur et sa longueur"""
        dx = min_x - max_x
        dy = min_y - max_y
        ratio = dy / dx
        desired_ratio = 700 / 700
        if (ratio > desired_ratio):
            sizey = 700
            sizex = sizey / ratio
            pixel_width = dx / sizex
            scale = pixel_width / 0.00028
            return int(sizey), int(sizex), float(scale)
        else:
            sizex = 700
            sizey = sizex * ratio
            pixel_width = dx / sizex
            scale = pixel_width / 0.00028
            return int(sizey), int(sizex), float(scale)

    def mapnik_output(self, min_x, min_y, max_x, max_y, epsg, multi_poly_proj, union_line, noConsultationDuTeleservice):
        """Fonction creer une sortie carto"""
        mapnik_x_y = self.mapnik_config(min_x, min_y, max_x, max_y)
        sizex = mapnik_x_y[0]
        sizey = mapnik_x_y[1]
        m = mapnik.Map(sizey, sizex, '+init=epsg:' + str(epsg))

        m.background = mapnik.Color('steelblue')

        #si la couche du grid existe, on l'utilise
        if os.path.exists(os.path.join(os.path.abspath(os.path.dirname(__file__)), "temp" + os.sep + "grid.shp")):
            provpoly_lyr = mapnik.Layer('Atlas', '+init=epsg:' + str(epsg))
            path_temp = os.path.join(os.path.abspath(os.path.dirname(__file__)), "temp" + os.sep)
            provpoly_lyr.datasource = mapnik.Shapefile(file=path_temp + 'grid', encoding='latin1')
            provpoly_style = mapnik.Style()
            provpoly_rule_qc = mapnik.Rule()
            provpoly_rule_qc.symbols.append(mapnik.PolygonSymbolizer(mapnik.Color(217, 235, 203)))
            provpoly_style.rules.append(provpoly_rule_qc)
            m.append_style('atlas', provpoly_style)
            provpoly_lyr.styles.append('atlas')
            m.layers.append(provpoly_lyr)

        s_wkt_poly = mapnik.Style()
        r_wkt_poly = mapnik.Rule()
        wkt_polygon_symbolizer = mapnik.PolygonSymbolizer(mapnik.Color('#FF3366'))
        r_wkt_poly.symbols.append(wkt_polygon_symbolizer)
        wkt_line_symbolizer = mapnik.LineSymbolizer(mapnik.Color('#000'), 1.0)
        r_wkt_poly.symbols.append(wkt_line_symbolizer)
        s_wkt_poly.rules.append(r_wkt_poly)
        m.append_style('Travaux', s_wkt_poly)
        wkt_poly_geom = multi_poly_proj
        csv_string_wkt_poly = '''
                 wkt,Name
                "%s","test"
                ''' % wkt_poly_geom
        ds_wkt_poly = mapnik.Datasource(**{"type": "csv", "inline": csv_string_wkt_poly})
        layer_wkt_poly = mapnik.Layer('Travaux', '+init=epsg:' + str(epsg))
        layer_wkt_poly.datasource = ds_wkt_poly
        layer_wkt_poly.styles.append('Travaux')
        m.layers.append(layer_wkt_poly)

        wkt_line_geom = union_line
        csv_string_wkt_line_geom = '''
                 wkt,Name
                "%s","test"
                ''' % wkt_line_geom
        wkt_line_geom_ds = mapnik.Datasource(**{"type": "csv", "inline": csv_string_wkt_line_geom})
        wkt_line_layer = mapnik.Layer('Reseau', '+init=epsg:' + str(epsg))
        wkt_line_layer.datasource = wkt_line_geom_ds
        wkt_line_style = mapnik.Style()
        wkt_line_rule = mapnik.Rule()
        wkt_line = mapnik.Stroke()
        wkt_line.color = mapnik.Color(171, 158, 137)
        wkt_line.width = 2.0
        wkt_line_rule.symbols.append(mapnik.LineSymbolizer(wkt_line))
        wkt_line_style.rules.append(wkt_line_rule)
        m.append_style('reseau', wkt_line_style)
        wkt_line_layer.styles.append('reseau')
        m.layers.append(wkt_line_layer)

        #m.zoom_all()
        m.zoom_to_box(mapnik.Box2d(min_x, min_y, max_x, max_y))
        mapnik_output = mapnik.render_to_file(m, os.path.join(os.path.abspath(os.path.dirname(__file__)), "output" + os.sep + "plan_" + noConsultationDuTeleservice + ".png"), 'png')
        #mapnik_output = mapnik.render_to_file(m, 'plan_' + noConsultationDuTeleservice + '.png', 'png')
        return mapnik_output

    def res_negatif(self, fullpath, type_dt_dict, noConsultationDuTeleservice, multi_poly_proj, union_line, distance, epsg, min_x, min_y, max_x, max_y):
        try:
            name_reseau = self.name_reseau
            path_output = os.path.join(os.path.abspath(os.path.dirname(__file__)), "output" + os.sep)
            path_model_cerfa = os.path.join(os.path.abspath(os.path.dirname(__file__)), "cerfa_modele" + os.sep + "cerfa_14435-03.pdf")

            self.vider_dossier()

            #calcul de l'echelle obtenu a partir de l'enveloppe du polygone et son buffer
            scale = self.mapnik_config(min_x, min_y, max_x, max_y)

            distance = int(distance)
            pdfjinja = PdfJinja(path_model_cerfa)
            pdfout = pdfjinja(dict(NoGU=noConsultationDuTeleservice, Echelle1=scale[2], DistanceReseau=distance))
            pdfout.write(open(path_output + 'cerfa_' + noConsultationDuTeleservice + '.pdf', 'wb'))

            #vue carto avec le buffer creer sur emplacement travaux et le calcul de l'enveloppe
            self.mapnik_output(min_x, min_y, max_x, max_y, epsg, multi_poly_proj, union_line, noConsultationDuTeleservice)

            print(name_reseau, type_dt_dict, noConsultationDuTeleservice, multi_poly_proj, union_line, distance)
            os.remove(fullpath)
        except:
            print('erreur : objet output, function res -')

    def res_positif(self, fullpath, type_dt_dict, noConsultationDuTeleservice, multi_poly_proj, union_line, count_intersection, epsg, min_poly_x, min_poly_y, max_poly_x, max_poly_y):
        try:
            name_reseau = self.name_reseau
            path_output = os.path.join(os.path.abspath(os.path.dirname(__file__)), "output" + os.sep)
            path_model_cerfa = os.path.join(os.path.abspath(os.path.dirname(__file__)), "cerfa_modele" + os.sep + "cerfa_14435-03.pdf")

            self.vider_dossier()

            # creation du grid
            self.grid(min_poly_x, min_poly_y, max_poly_x, max_poly_y)
            # enveloppe avec un buffer sur le grid
            env_grid = self.grid_enveloppe()

            # calcul de l'echelle obtenu a partir de l'enveloppe du grid et son buffer
            scale = self.mapnik_config(env_grid[0], env_grid[1], env_grid[2], env_grid[3])

            pdfjinja = PdfJinja(path_model_cerfa)
            pdfout = pdfjinja(dict(NoGU=noConsultationDuTeleservice, Echelle1=scale[2]))
            pdfout.write(open(path_output + 'cerfa_' + noConsultationDuTeleservice + '.pdf', 'wb'))

            self.mapnik_output(env_grid[0], env_grid[1], env_grid[2], env_grid[3], epsg, multi_poly_proj, union_line, noConsultationDuTeleservice)

            print(name_reseau, type_dt_dict, noConsultationDuTeleservice, multi_poly_proj, union_line, count_intersection)
            os.remove(fullpath)
        except:
            print('erreur : objet output, function res +')