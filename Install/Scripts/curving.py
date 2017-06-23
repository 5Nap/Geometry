# coding: utf-8

import os
import sys
import json
import arcpy
import math


from geometry_functions import getanglebetweenvectors, getpointonvector, getlineequation, getlinesintersection
from readwrite_functions import readwkt, writewkt

sys.path.append(os.path.dirname(__file__))

webmercator_wkid = 3857
WEBMERC = arcpy.SpatialReference(webmercator_wkid)


def getjsonpoint(jsonobj):
	if type(jsonobj) is list:
		return jsonobj, u'point'
	elif type(jsonobj) is dict:
		if u'c' in jsonobj:
			return jsonobj[u'c'][0], u'curve'


def createcurves(layer, jsonwkt, angle_th, radius_th):
	from find_functions import findsinglevertex
	shapetype = arcpy.Describe(layer).shapeType
	single = findsinglevertex(layer)

	if jsonwkt == u'JSON':
		# dictionary {OID: ESRI geoJSON}
		shape_as_json = {
				row[0]: json.loads(row[1])
				for row in arcpy.da.SearchCursor(layer, ['OID@', 'SHAPE@JSON'], spatial_reference = WEBMERC)}

	else:
		shape_as_json = {
				row[0]: json.loads(arcpy.FromWKT(row[1]).JSON)
				for row in arcpy.da.SearchCursor(layer, ['OID@', 'SHAPE@WKT'], spatial_reference = WEBMERC)}

	# field to omit
	service_fields = ['hasZ', 'hasM', 'spatialReference']

	for oid in shape_as_json:
		# first - find geometry key in dictionary
		keys = [k for k in shape_as_json[oid] if k not in service_fields]
		geom_key = keys[0]

		geom = shape_as_json[oid][geom_key]

		newgeom = []
		trigger = 0
		pnt_no = 0

		for part in geom:
			fixed_points = [0, len(part)-1] if shapetype == 'Polyline' else [len(part)-1]
			newpart = []
			for i, pnt in enumerate(part):
				if i in fixed_points or pnt_no not in single[oid]:
					# if it's the first, last or non-single point - write it down and go further
					newpart.append(pnt)
				else:
					# read 3 points and it's types from ESRI geoJson
					if i == 0 and shapetype == 'Polygon':
						pnt_prev, type_prev = getjsonpoint(part[i-2])
					else:
						pnt_prev, type_prev = getjsonpoint(part[i-1])
					pnt_next, type_next = getjsonpoint(part[i+1])
					pnt_cur, type_cur = getjsonpoint(pnt)

					# TODO
					# check polygons with curves
					if u'curve' in [type_next, type_cur]:   # +type_prev
						# if current or next point are curves - write it down, go further
						newpart.append(pnt)
						trigger = 1
						new_geom_key = u'curvePaths'
						old_geom_key = geom_key
					else:
						# calculate angle and compare it with limits
						angle = getanglebetweenvectors(pnt_prev, pnt_cur, pnt_next)
						if angle_th < abs(angle) < 180 - angle_th:
							# calculate two radiuses
							d1 = (pnt_cur[0]-pnt_prev[0])**2+(pnt_cur[1]-pnt_prev[1])**2
							d2 = (pnt_cur[0]-pnt_next[0])**2+(pnt_cur[1]-pnt_next[1])**2
							# set it as basic radius if any of it is less then limit
							if d1 < 4 * radius_th**2 or d2 < 4 * radius_th**2:
								radius_th_w = min([d1, d2])**0.5 / 2
							else:
								radius_th_w = radius_th
							# calculate basic point on previous side and next side
							new_prev = getpointonvector(pnt_cur, pnt_prev, radius_th_w)
							new_next = getpointonvector(pnt_cur, pnt_next, radius_th_w)

							# calculate deltas
							dx1 = pnt_cur[0] - pnt_prev[0]
							dy1 = pnt_cur[1] - pnt_prev[1]
							dx2 = pnt_next[0] - pnt_cur[0]
							dy2 = pnt_next[1] - pnt_cur[1]

							# calculate fake points on perpendicular to previous and next sides
							fake_prev = [new_prev[0] + dy1, new_prev[1] - dx1]
							fake_next = [new_next[0] + dy2, new_next[1] - dx2]

							# calculate two radiuses
							radius_prev = getlineequation(new_prev[0], new_prev[1], fake_prev[0], fake_prev[1])
							radius_next = getlineequation(new_next[0], new_next[1], fake_next[0], fake_next[1])

							# find circle center
							center = getlinesintersection(
									radius_prev[0], radius_prev[1], radius_prev[2],
									radius_next[0], radius_next[1], radius_next[2])

							radius_act = ((center[0]-new_prev[0])**2 + (center[1]-new_prev[1])**2)**0.5
							
							if jsonwkt == 'JSON':
								# TODO
								# check polygons with curves

								# get center of new arc
								arc_center = getpointonvector(center, pnt_cur, radius_act)
								# write it (lastpoint of arc, center of arc)
								arc = {u'c': [new_next, arc_center]}

								newpart.append(new_prev)
								newpart.append(arc)

								# rewrite geometry keys
								new_geom_key = u'curvePaths'
								old_geom_key = geom_key
								trigger = 1
							else:
								# vector from center to the first point of 'arc'
								base_vector = [center[0] - new_prev[0], center[1] - new_prev[1]]

								# calculate angular step
								step_angle = math.degrees(2 * math.acos((radius_act - 0.01)/radius_act))
								step_angle *= math.copysign(1, angle)

								# calculate quantity of intermadiate points
								quant = int(round(abs(angle/step_angle)))

								newpart.append(new_prev)

								# if there is more than 1 intermediate point
								if quant > 1:
									true_step = angle / float(quant)
									for j in range(quant):
										sin_angle = math.sin(-math.radians((j+1)*true_step))
										cos_angle = math.cos(-math.radians((j+1)*true_step))
										x = base_vector[0]
										y = base_vector[1]
										vect = [x*cos_angle + y*sin_angle, -x*sin_angle + y*cos_angle]
										vect_x = center[0] - vect[0]
										vect_y = center[1] - vect[1]
										newpart.append([vect_x, vect_y])

								newpart.append(new_next)

								trigger = 1
						else:
							newpart.append(pnt_cur)
				pnt_no += 1
			# rewrite last point in polygon
			if shapetype == 'Polygon':
				newpart[-1] = newpart[0]
				
			# append part to geometry list
			newgeom.append(newpart)
		
		# rewrite geometry (and key)
		if trigger == 1:
			if jsonwkt == 'JSON':
				del shape_as_json[oid][old_geom_key]
				shape_as_json[oid][new_geom_key] = newgeom
			else:
				shape_as_json[oid][geom_key] = newgeom

		shape_as_json[oid]['shape'] = arcpy.AsShape(shape_as_json[oid], True)

	with arcpy.da.UpdateCursor(layer, ['SHAPE@', 'OID@'], spatial_reference = WEBMERC) as uc:
		for row in uc:
			row[0] = shape_as_json[row[1]]['shape']
			uc.updateRow(row)


if __name__ == '__main__':
	in_layer = arcpy.GetParameterAsText(0)
	# in_layer = ur'D:\Projects\_тест\test_tline.gdb\allhouse'
	# in_layer = ur'D:\Projects\_тест\test_tline.gdb\line_test'
	# in_layer = ur'D:\Projects\_тест\test_tline.gdb\тлайнwgs

	createcurves(
			layer = in_layer,
			jsonwkt = 'WKT',
			angle_th = 0,
			radius_th = 50)
