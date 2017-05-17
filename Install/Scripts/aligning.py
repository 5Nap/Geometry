# coding: utf-8

import arcpy
from transform_functions import rotatepolygon, calculateangle, checkangle

webmercator_wkid = 3857
WEBMERC = arcpy.SpatialReference(webmercator_wkid)


def alignpolygons(layer, mode, geometry, radius, procent):
	arcpy.env.addOutputsToMap = False

	# set input parameters
	if radius == '':
		radius = 50
	else:
		radius = float(radius)						# area of search in m
	
	if procent == '':
		procent = 20
	else:
		procent = float(procent) 						# perecent of rotation
	
	with arcpy.da.UpdateCursor(layer, ["SHAPE@"], spatial_reference = WEBMERC) as cursor:
		# for all houses
		for row in cursor:
			if mode == 1:
				print u'-> Allign to the largest building'
			elif mode == 2:
				print u'-> Allign to the closest road'
			angle = calculateangle(
					geometry = row[0],
					nearest_geometry = geometry)
			arcpy.AddMessage(u'Angle: {0:.2f} deg'.format(angle))
			angle = checkangle(angle, procent)
			
			# rotate polygon and add them to new layer
			new_polygon = rotatepolygon(
					polygon = row[0],
					angle = angle)
			cursor.updateRow([new_polygon])
