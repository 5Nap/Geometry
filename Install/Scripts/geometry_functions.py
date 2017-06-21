# coding: utf-8

import math
import arcpy

webmercator_wkid = 3857
WEBMERC = arcpy.SpatialReference(webmercator_wkid)


def getlineangle(p0, p1):
	angle = math.atan2(p1[1]-p0[1], p1[0]-p0[0])
	if angle > 180:
		return angle - 360
	elif angle < -180:
		return angle + 360
	else:
		return angle


def getanglebetweenvectors(p0, p1, p2):
	# Returns angle between vectors p1p0 and p1p2
	# if vector turns counter-clockwise - angle >= 0 else < 0
	angle1 = math.atan2(p1[1]-p0[1], p1[0]-p0[0])
	angle2 = math.atan2(p2[1]-p1[1], p2[0]-p1[0])
	angle = math.degrees(angle2 - angle1)
	if angle > 180:
		return angle - 360
	elif angle < -180:
		return angle + 360
	else:
		return angle


def getanglebetweenlines(vector1, vector2):
	# returns angle between vectors line1 and line2
	# line = [[x0, y0], [x1, y1]]
	angle1 = math.atan2(vector1[1][1] - vector1[0][1], vector1[1][0] - vector1[0][0])
	angle2 = math.atan2(vector2[1][1] - vector2[0][1], vector2[1][0] - vector2[0][0])
	angle = math.degrees(angle2 - angle1)
	if angle > 180:
		return angle - 360
	elif angle < -180:
		return angle + 360
	else:
		return angle


def floorangle(angle):
	# Returns angle in (-90, 90) from (-180,180) after atan2
	if angle > 90:
		return angle-180
	elif angle < -90:
		return angle+180
	else:
		return angle


def getlineequation(x1, y1, x2, y2):
	# Equation of a line between two points
	a = (y1-y2)
	b = (x2-x1)
	c = (x1*y2-x2*y1)
	return a, b, c


def getlinesintersection(a1, b1, c1, a2, b2, c2):
	# Returns a point where two lines with coeff a-b-c cross
	if (a1*b2-a2*b1) != 0:
		x = -(c1*b2-c2*b1)/(a1*b2-a2*b1)
		y = -(a1*c2-a2*c1)/(a1*b2-a2*b1)
		return x, y
	else:
		return None, None


def getpointonvector(p1, p2, l):
	x1, y1 = p1
	x2, y2 = p2
	length = math.sqrt((x2-x1)**2+(y2-y1)**2)
	if length != 0:
		kx = (x2-x1) / length
		ky = (y2-y1) / length
		x_new = x1 + kx * l
		y_new = y1 + ky * l
		return [x_new, y_new]
	else:
		return None


def calcoffsetpoint(pt1, pt2, offset):
	theta = math.atan2(pt2[1] - pt1[1], pt2[0] - pt1[0])
	theta += math.pi / 2.0
	return pt1[0] + math.cos(theta) * offset, pt1[1] + math.sin(theta) * offset


def getoffsetintercept(pt1, pt2, m, offset):
	# From points pt1 and pt2 defining a line in the Cartesian plane, the slope of the line m,
	# and an offset distance, calculates the y intercept of the new line offset from the original.
	x, y = calcoffsetpoint(pt1, pt2, offset)
	return y - m * x


def getpt(pt1, pt2, pt3, offset):
	# Gets intersection point of the two lines defined by pt1, pt2, and pt3; offset is the
	# distance to offset the point from the polygon.

	# Get first offset intercept
	if pt2[0] - pt1[0] != 0:
		m = (pt2[1] - pt1[1]) / (pt2[0] - pt1[0])
		boffset = getoffsetintercept(pt1, pt2, m, offset)
	else:  # if vertical line (i.e. undefined slope)
		m = "undefined"

	# Get second offset intercept
	if pt3[0] - pt2[0] != 0:
		mprime = (pt3[1] - pt2[1]) / (pt3[0] - pt2[0])
		boffsetprime = getoffsetintercept(pt2, pt3, mprime, offset)
	else:  # if vertical line (i.e. undefined slope)
		mprime = "undefined"

	# Get intersection of two offset lines
	if m != "undefined" and mprime != "undefined" and m != mprime:
		# if neither offset intercepts are vertical
		newx = (boffsetprime - boffset) / (m - mprime)
		newy = m * newx + boffset
	elif m == "undefined":
		# if first offset intercept is vertical
		newx, y_infinity = calcoffsetpoint(pt1, pt2, offset)
		newy = mprime * newx + boffsetprime
	elif mprime == "undefined":
		# if second offset intercept is vertical
		newx, y_infinity = calcoffsetpoint(pt2, pt3, offset)
		newy = m * newx + boffset
	elif m == "undefined" and mprime == "undefined":
		# if both offset intercepts are vertical (same line)
		newx, y_infinity = calcoffsetpoint(pt1, pt2, offset)
		newy = pt2[1]
	elif m == mprime:
		dx = (pt3[0] - pt2[0])
		dy = (pt3[1] - pt2[1])
		length = (dx**2 + dy**2)**0.5
		newx = pt2[0] - (dy/length)*offset
		newy = pt2[1] + (dx/length)*offset
	return newx, newy