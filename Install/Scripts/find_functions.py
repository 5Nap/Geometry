# coding: utf-8

import arcpy
import math

EPSILON = 0.1
webmercator_wkid = 3857
WEBMERC = arcpy.SpatialReference(webmercator_wkid)


def findnearestbuilding(layerwork, houses_array, radius):
	radius = float(radius)
	min_dist = 9999
	near_poly = None

	with arcpy.da.SearchCursor(layerwork, ['SHAPE@'], spatial_reference = WEBMERC) as sc:
		for row in sc:													# for every feature in selection
			for polygon in houses_array:										# for every polygon in extent
				if abs(row[0].length - polygon.length) > EPSILON:  # features perimeter must differ or it counts as one polygon
					dist = row[0].distanceTo(polygon)
					if dist < EPSILON:   # if one feature is less than EPSILON far from other - test it's intersection
						buff = row[0].buffer(EPSILON)  # create small buffer around selected feature
						if not buff.disjoint(polygon):
							intersection = buff.intersect(polygon, 4)  # intersect this buffer with found polygon
							if 0 < intersection.area < (4 * EPSILON * row[0].length) / row[0].pointCount:
								arcpy.AddMessage(u'! Touching polygon was found via buffer')
								return [0, 0]
							# it almost doubles previos if-case but sometimes it works better
							if row[0].touches(polygon):
								arcpy.AddMessage(u'! Touching polygon was found via touches() method')
								return [0, 0]
					if dist < min_dist and dist < radius:
						min_dist = dist
						near_poly = polygon
	# if the nearest polygon was found - return mode = 1 (align to polygon) and its geometry
	# else - return mode = 2 (align to line) and 0 as geometry.
	if near_poly is not None:
		return [1, near_poly]
	else:
		return [2, 0]


# function for find nearest Geometry
def findnearestline(layer, other_layer, radius=0):
	find_flag = 0
	min_distance = radius
	nearest_geometry = None
	base_geometry = None

	with arcpy.da.SearchCursor(layer, ['SHAPE@'], spatial_reference = WEBMERC) as sc:
		for row in sc:
			if find_flag != 2:
				for geom in other_layer:
					arcpy.AddMessage(geom.WKT)
					distance = row[0].distanceTo(geom)
					if distance <= radius:
						if distance <= min_distance:
							min_distance = distance
							nearest_geometry = geom
							base_geometry = row[0]
							find_flag = 1
						if distance == 0:
							find_flag = 2

			# know to select nearest two points from line
	line = 0
	if find_flag >= 1 and nearest_geometry is not None and base_geometry is not None:
		atuple = nearest_geometry.queryPointAndDistance(base_geometry.centroid, False)
		pnt_on_line = atuple[0].centroid
		array = arcpy.Array()
		array.add(base_geometry.centroid)
		array.add(pnt_on_line)
		line = arcpy.Polyline(array)
	return [2, line]


# finction for find the biggest geometry
def findbiggestgeometry(houses_around):
	find_flag = 0
	max_square = 0
	max_geometry = arcpy.Geometry()

	for geometry in houses_around:
		square = geometry.area

		if square >= max_square:
			max_square = square
			max_geometry = geometry
			find_flag = 1

	return max_geometry, find_flag


# find and return list of vertex located not at the crossroads
def findsinglevertex(layer):
	# find single vertices
	# arcpy.Integrate_management(layer, 0.1)
	arcpy.env.addOutputsToMap = False
	vert = u'in_memory\\vert'
	ident = u'in_memory\\ident'
	arcpy.FeatureVerticesToPoints_management(
			in_features = layer,
			out_feature_class = vert,
			point_location = u'ALL')

	# points = {PointFID: [LineID, PointNo], ...}
	points = {}
	lines_id = []
	with arcpy.da.SearchCursor(vert, ['OID@', 'ORIG_FID']) as sc:
		feat_num = -1
		vert_num = -1
		for row in sc:
			if row[1] != feat_num:
				feat_num = row[1]
				vert_num = 0
				lines_id.append(feat_num)
			else:
				vert_num += 1
			points[row[0]] = [feat_num, vert_num]

	arcpy.FindIdentical_management(
			in_dataset = vert,
			out_dataset = ident,
			fields = u'SHAPE',
			xy_tolerance = u'0.2 Meters',
			output_record_option = u'ONLY_DUPLICATES')

	identical_v = [row[0] for row in arcpy.da.SearchCursor(ident, 'IN_FID')]  # ids of identical vetices
	single_v = [x+1 for x in xrange(len(points)) if x+1 not in identical_v]      # ids of single vertices

	single_pair = [points[x] for x in single_v]   # [LineID, PointNo]

	single_out = {oid: [] for oid in lines_id}

	for p in single_pair:
		single_out[p[0]].append(p[1])

	arcpy.Delete_management(vert)
	arcpy.Delete_management(ident)

	return single_out


def findlongestside(geomlist):
	max_len = 0
	max_side = None

	for part in geomlist:
		pnt_count = len(part)-1
		for k in xrange(pnt_count):
			bp = part[k]
			np = part[(k+1)%pnt_count]
			length = math.sqrt((np[0]-bp[0])**2 + (np[1]-bp[1])**2)
			if length > max_len:
				max_len = length
				max_side = [bp, np]
	return max_side




