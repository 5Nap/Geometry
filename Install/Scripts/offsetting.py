####################################################################################################
# Author:   William Walker
# Date:     05-03-2014
# Modified: 28-11-2016
####################################################################################################


import arcpy
from geometry_functions import getpt

webmercator_wkid = 3857
WEBMERC = arcpy.SpatialReference(webmercator_wkid)


def offsetfeature(polyx, offset, geomtype):
	# Offsets a clockwise list of coordinates polyx distance offset to the outside of the polygon.
	# Returns list of offset points.
	if geomtype == u'Polygon':
		k = 0
	else:
		k = 2

	polyy = []

	# need three points at a time
	loop = len(polyx)
	for counter in range(0, loop-k):
		# get first offset intercept
		pt = getpt(
					polyx[counter % loop],
					polyx[(counter + 1) % loop],
					polyx[(counter + 2) % loop],
					offset)
		# append new point to polyy
		polyy.append(pt)
	return polyy


def createoffset(in_fc, out_fc, mode, offset = 0, offset_field = u'WIDTH'):

	# check geometry type (Polygon or Polyline)
	desc_in = arcpy.Describe(in_fc)
	geom_type = desc_in.shapeType

	desc_out = arcpy.Describe(out_fc)
	out_sr = desc_out.spatialReference

	# Enable overwrite permission
	arcpy.env.overwriteOutput = True

	# Create empty Array objects
	parts = arcpy.Array()
	rings = arcpy.Array()
	ring = arcpy.Array()

	if mode == u'field':
		sc_fields = ['SHAPE@', offset_field]
	else:
		sc_fields = ['SHAPE@']

	# Create cursor and update vertex coordinates
	with arcpy.da.InsertCursor(out_fc, 'SHAPE@') as ic:
		# Loop through features of in_fc
		with arcpy.da.SearchCursor(in_fc, sc_fields, spatial_reference = WEBMERC) as sc:
			for inRow in sc:
				if mode == u'fields':
					offset = inRow[1]
				new_part_list = []
				# loop trough parts of feature
				for part in inRow[0]:
					coord_list = []
					counter = 0
					# loop through points in part
					for pnt in part:
						if counter == 0 and geom_type == u'Polygon':  # skip first point
							counter += 1
						else:
							if pnt:
								coord_list.append((pnt.X, pnt.Y))
								counter += 1
							else:  # null point, denotes beginning of inner ring
								counter = 0  # reset counter
								if geom_type == u'Polyline':
									# if input is polyline - add two fake vertices on both ends
									# first point
									fpoint = coord_list[0]
									spoint = coord_list[1]
									dx = spoint[0]-fpoint[0]
									dy = spoint[1]-fpoint[1]
									addpoint = (fpoint[0]-dx, fpoint[1]-dy)
									coord_list.insert(0, addpoint)

									# last point
									fpoint = coord_list[-1]
									spoint = coord_list[-2]
									dx = spoint[0] - fpoint[0]
									dy = spoint[1] - fpoint[1]
									addpoint = (fpoint[0] - dx, fpoint[1] - dy)
									coord_list.append(addpoint)

									# for polyline - create buffer on one side, then on the other and merge it
									offset_list_right = offsetfeature(coord_list, offset, geom_type)  # calculate offset points
									offset_list_left = offsetfeature(coord_list[::-1], offset, geom_type)  # same line reverted
									new_part_list.append(offset_list_right+offset_list_left)  # add coordinates to new list
								else:
									offset_list = offsetfeature(coord_list, offset, geom_type)  # calculate offset points
									new_part_list.append(offset_list)  # add coordinates to new list

								# reset coord_list and start over again
								coord_list = []  # empty list

					# Add final (or only) offset coordinates for part

					if geom_type == 'Polyline':

						# first point
						fpoint = coord_list[0]
						spoint = coord_list[1]
						dx = spoint[0] - fpoint[0]
						dy = spoint[1] - fpoint[1]
						addpoint = (fpoint[0] - dx, fpoint[1] - dy)
						coord_list.insert(0, addpoint)

						# last point
						fpoint = coord_list[-1]
						spoint = coord_list[-2]
						dx = spoint[0] - fpoint[0]
						dy = spoint[1] - fpoint[1]
						addpoint = (fpoint[0] - dx, fpoint[1] - dy)
						coord_list.append(addpoint)

						offset_list_right = offsetfeature(coord_list, offset, geom_type)
						offset_list_left = offsetfeature(coord_list[::-1], offset, geom_type)
						new_part_list.append(offset_list_right + offset_list_left)
					else:
						offset_list = offsetfeature(coord_list, offset, geom_type)  # calculate offset points
						new_part_list.append(offset_list)  # add coordinates to new list

				# loop through new_part_list, to create new polygon geometry object for row
				for part in new_part_list:
					for pnt in part:
						if pnt:
							ring.add(arcpy.Point(pnt[0], pnt[1]))
						else:  # null point
							rings.add(ring)
							ring.removeAll()

					# if last ring, add it
					rings.add(ring)
					ring.removeAll()

					# if only one ring, remove nesting
					if len(rings) == 1:
						rings = rings.getObject(0)

					parts.add(rings)
					rings.removeAll()

				# if single-part, remove nesting
				if len(parts) == 1:
					parts = parts.getObject(0)

				# create polygon object based on parts array
				polygon = arcpy.Polygon(parts, WEBMERC).projectAs(out_sr)
				parts.removeAll()

				ic.insertRow([polygon])
