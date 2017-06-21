# coding: utf-8

import arcpy
from transform_functions import rotatepolygon, calculateangle, checkangle

webmercator_wkid = 3857
WEBMERC = arcpy.SpatialReference(webmercator_wkid)


def alignpolygons(layer, mode, geometry, procent):
	arcpy.env.addOutputsToMap = False

	# perecent of rotation
	if procent == '':
		procent = 20
	else:
		procent = float(procent)
	
	with arcpy.da.UpdateCursor(layer, ["SHAPE@"], spatial_reference = WEBMERC) as cursor:
		for row in cursor:
			if mode == 1:
				print u'-> Allign to the largest building'
			elif mode == 2:
				print u'-> Allign to the closest road'
			angle = calculateangle(
					geometry = row[0],
					nearest_geometry = geometry)
			arcpy.AddMessage(u'Rotation angle: {0:.2f} deg'.format(angle))

			# get 0 if angle exceeds limits
			angle = checkangle(angle, procent)
			
			# rotate polygon and get a new geometry
			new_polygon = rotatepolygon(
					polygon = row[0],
					angle = angle)

			# update polygon geometry
			cursor.updateRow([new_polygon])
