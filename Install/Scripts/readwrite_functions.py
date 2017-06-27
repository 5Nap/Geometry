# coding: utf-8

import arcpy
webmercator_wkid = 3857
WEBMERC = arcpy.SpatialReference(webmercator_wkid)


def readwkt(wktstring):
	# Reads WKT string to list
	# TODO
	# rewrite to handle any type of geometry, not only LINESTRING

	geom_type, coord_string = wktstring.split(' (', 1)
	geometry = [strp.split(', ') for strp in coord_string[1:-2].split('), (')]
	for i in xrange(len(geometry)):
		for j in xrange(len(geometry[i])):
			geometry[i][j] = [float(xy) for xy in geometry[i][j].split(' ')]
	return {geom_type: geometry}


def wkt2list(wktstring):
	geom_type, coord_string = wktstring.split('(', 1)
	# geom_type = geom_type.strip()
	coord_string = '('+coord_string
	level = 0 
	curlevel = 0
	# lastlevel = 1
	# coords = []
	partstr = ''
	parts = {1: [], 2: [], 3: []}
	inlevel = False
	for i, l in enumerate(coord_string):
		if l == '(':
			if level == curlevel:
				level += 1
			curlevel += 1
			inlevel = True
		elif l == ')':
			if partstr != '':
				parts[curlevel].append([[float(y) for y in x.strip().split()] for x in partstr.split(',')])
			else:
				parts[curlevel].append(parts[curlevel+1])
				parts[curlevel+1] = []
			# lastlevel = curlevel
			curlevel += -1
			inlevel = False
			partstr = ''
		elif inlevel:
			partstr += l
	geometry = parts[1][0]
	# return {geom_type: geometry}
	return geometry[0]


def writewkt(wktlist):
	# Creates WKT-string from list
	wktstring = wktlist[0]+' '
	geomstring = '('

	for part in wktlist[1]:
		partstring = '('
		partstring += ', '.join([str(pnt[0]) + ' ' + str(pnt[1]) for pnt in part])
		partstring += '), '
		geomstring += partstring
	geomstring = geomstring[:-2]
	geomstring += ')'
	wktstring += geomstring
	return wktstring


def readgeometryfromrow(row):
	# Returns geometry as a list from Cursor row
	geom = []
	for part in row:
		geom_part = []
		for pnt in part:
			if pnt is not None:
				geom_part += [[pnt.X, pnt.Y]]
			else:
				geom += [geom_part]
				geom_part = []
		geom += [geom_part]
	return geom


def creategeometryfromlist(geom):
	# Creates arcpy geometry from list
	array = arcpy.Array()
	for parts in geom:
		polygon_part = arcpy.Array()
		for points in parts:
			polygon_part.append(arcpy.Point(points[0], points[1]))
		array.append(polygon_part)
	return arcpy.Polygon(array)
