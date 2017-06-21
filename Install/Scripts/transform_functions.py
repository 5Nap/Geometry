# -*- coding: utf-8 -*-

import math
import arcpy

EPSILON = 0.1
webmercator_wkid = 3857
WEBMERC = arcpy.SpatialReference(webmercator_wkid)


def rotatexy(x, y, xc=0, yc=0, angle=0):
	# Function to rotate a point about another point, returning a list [X,Y]
	x -= xc
	y -= yc
	xr = (x * math.cos(angle)) - (y * math.sin(angle)) + xc
	yr = (x * math.sin(angle)) + (y * math.cos(angle)) + yc
	return [xr, yr]


def rotatepolygon(polygon, angle=0, is_rad=0):
	# function for Rotate polygon
	# convert from radian
	if is_rad == 0:
		angle = angle * math.pi / 180

	# get centroid point
	centroid = polygon.centroid
	# form array for new points
	poly_array = arcpy.Array()
	part_array = arcpy.Array()

	# get all points from polygon and rotate them, and create new point and add to array
	for points in polygon:
		for point in points:
			if point is not None:
				x, y = rotatexy(point.X, point.Y, centroid.X, centroid.Y, angle)
				new_point = arcpy.Point(x, y)
				part_array.add(new_point)
			else:
				poly_array.add(part_array)
				part_array.removeAll()
	# add last part:
	poly_array.add(part_array)

	# create new polygon from array
	new_polygon = arcpy.Polygon(poly_array, polygon.spatialReference)

	part_array.removeAll()
	poly_array.removeAll()

	return new_polygon


def calculateangle(geometry, nearest_geometry):
	# function for calculate angle

	min_angle = 180
	min_sign = 1

	# get the point from nearest Geometry
	for pointsNear in nearest_geometry:
		for i in xrange(len(pointsNear) - 1):
			nearest_pnt1 = pointsNear[i]
			nearest_pnt2 = pointsNear[i + 1]

			# check is nearestPnt1 = nearestPnt2
			if nearest_pnt1 is not None and nearest_pnt2 is not None:
				if abs(nearest_pnt1.X - nearest_pnt2.X) + abs(nearest_pnt1.Y - nearest_pnt2.Y) > EPSILON:
					length1 = nearest_pnt2.Y - nearest_pnt1.Y
					length2 = nearest_pnt2.X - nearest_pnt1.X
					nearest_angle = math.atan2(length1, length2)
					nearest_angle = nearest_angle * 180 / math.pi
					if nearest_angle < 0:
						nearest_angle += 360

					# get the points from segment of geometry
					for pointsGeom in geometry:
						for j in xrange(len(pointsGeom) - 1):
							pnt1 = pointsGeom[j]
							pnt2 = pointsGeom[j + 1]

							if pnt1 is not None and pnt2 is not None:
								if abs(pnt1.X - pnt2.X) + abs(pnt1.Y - pnt2.Y) > EPSILON:
									length1 = pnt2.Y - pnt1.Y
									length2 = pnt2.X - pnt1.X
									angle = math.atan2(length1, length2)
									angle = angle * 180 / math.pi
									if angle < 0:
										angle += 360

									delta = math.fabs(nearest_angle - angle)
									if nearest_angle < angle:
										sign = -1
									else:
										sign = 1

									if math.fabs(min_angle) >= math.fabs(delta):
										min_angle = delta
										min_sign = sign
	arcpy.AddMessage(min_angle)
	min_angle *= min_sign

	return min_angle


def checkangle(angle=0.0, procent=0):
	# Check if angle is within a limit
	min_angle = (90 / 100.0) * procent
	if angle > min_angle or angle < -min_angle:
		angle = 0

	return angle
