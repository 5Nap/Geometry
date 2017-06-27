# coding: utf-8

import os
import arcpy

webmercator_wkid = 3857
WEBMERC = arcpy.SpatialReference(webmercator_wkid)
WGS = arcpy.SpatialReference(4326)


def layerworkspace(layer):
	if type(layer) is arcpy.mapping.Layer:
		layer = layer.dataSource
	fd_or_ws = os.path.dirname(layer)
	if arcpy.Describe(fd_or_ws).dataType == 'FeatureDataset':
		fd_or_ws = os.path.dirname(fd_or_ws)
	return fd_or_ws


def getworkspace(geomtype = None, names = None):
	trigger = 0

	# current project
	mxd = arcpy.mapping.MapDocument('current')
	df = arcpy.mapping.ListDataFrames(mxd)

	map_layers = arcpy.mapping.ListLayers(df[0])

	# get tline layer
	tline_lyr = None
	if [lyr.name for lyr in map_layers].count(u'tline') == 1:
		tline_lyr = [lyr for lyr in map_layers if lyr.name == u'tline'][0]
		# tlinepath = arcpy.Describe(u'tline').dataElement.catalogPath
	elif u'tline' in [lyr.name for lyr in map_layers]:
		message = u'Duplicate TLINE names in mxd.\nRename:\n-\ttline'
		print u'! Duplicate TLINE names in mxd'
		return {u'data': None, u'extent': None, u'message': message}

	# create a list of all layers except SDE layers
	if names is None:
		layers = [
				l for l in map_layers
				if l.isFeatureLayer and
				not l.isBroken and
				arcpy.Describe(layerworkspace(l)).workspaceType != u'RemoteDatabase']
	else:
		layers = [
				l for l in map_layers
				if l.isFeatureLayer and
				not l.isBroken and
				arcpy.Describe(layerworkspace(l)).workspaceType != u'RemoteDatabase' and
				l.name in names]

	# Filter list if geometry type had been set
	if geomtype is not None:
		layers = [l for l in layers if arcpy.Describe(l.dataSource).shapeType == geomtype]

	# find layers with selection
	selected_layers = []

	for lyr in layers:
		# 10.4 way:
		# if arcpy.Describe(lyr).FIDSet != '':
		# TODO
		# This will fail in following cases:
		# 1. there is only one feature in a layer
		# 2. all features in a layer are selected
		# 3. a huge feature which is setting layer extent is selected.
		if str(lyr.getExtent()) != str(lyr.getSelectedExtent()):
			trigger = 1
			gdb = layerworkspace(lyr)
			selected_layers.append({u'gdb': gdb, u'lyr': lyr, u'tline': tline_lyr})

	if trigger == 1:
		# calculate common extent for all selections
		extents = [
			(lambda k: [k.XMin, k.YMin, k.XMax, k.YMax])(data[u'lyr'].getSelectedExtent().projectAs(WEBMERC))
			for data in selected_layers]
		combined_extent = [
			min(extents, key = lambda k: k[0])[0],
			min(extents, key = lambda k: k[1])[1],
			max(extents, key = lambda k: k[2])[2],
			max(extents, key = lambda k: k[3])[3]]

		extent = arcpy.Extent(*combined_extent)
		return {u'data': selected_layers, u'extent': extent, u'message': u'ok'}
	else:
		message = u'No selection or wrong geometry type'
		print u'! No selection or wrong geometry type'
		return {u'data': None, u'extent': None, u'message': message}


def checklayers():
	try:
		mxd = arcpy.mapping.MapDocument(u'current')
		df = arcpy.mapping.ListDataFrames(mxd)
		layers = [l.name for l in arcpy.mapping.ListLayers(df[0]) if l.isFeatureLayer and not l.isBroken]
		duplicates = [x for x in layers if layers.count(x) > 1]
		if len(duplicates) > 0:
			return False
		else:
			return True
	except RuntimeError:
		return False


def checkallhouse():
	mxd = arcpy.mapping.MapDocument(u'current')
	df = arcpy.mapping.ListDataFrames(mxd)
	layers = [
		l.name for l in arcpy.mapping.ListLayers(df[0])
		if l.isFeatureLayer and
		not l.isBroken and
		arcpy.Describe(layerworkspace(l)).workspaceType != u'RemoteDatabase']
	if layers.count(u'allhouse') == 1:
		return True
	else:
		return False


def removelayers():
	mxd = arcpy.mapping.MapDocument(u'current')
	df = arcpy.mapping.ListDataFrames(mxd)
	for layer in arcpy.mapping.ListLayers(df[0]):
		if layer.isFeatureLayer and layer.isBroken:
			arcpy.mapping.RemoveLayer(df, layer)
	arcpy.RefreshTOC()


def projectextent(extent, sr, radius = 0):
	ll_merc = arcpy.PointGeometry(arcpy.Point(extent.XMin, extent.YMin), WEBMERC)
	ur_merc = arcpy.PointGeometry(arcpy.Point(extent.XMax, extent.YMax), WEBMERC)

	ll_sr = ll_merc.projectAs(sr).centroid
	ur_sr = ur_merc.projectAs(sr).centroid

	return arcpy.Extent(ll_sr.X - radius, ll_sr.Y - radius, ur_sr.X + radius, ur_sr.Y + radius)


def readnearestbuildings(layer, extent, radius = 0):
	arcpy.env.addOutputsToMap = False
	dsc = arcpy.Describe(layer)
	sr = dsc.spatialReference
	arcpy.env.extent = projectextent(extent, sr, radius)
	path = dsc.dataElement.catalogPath
	temp = arcpy.CopyFeatures_management(path, u'in_memory\\housesArray')
	array = [row[0] for row in arcpy.da.SearchCursor(temp, 'SHAPE@', spatial_reference=WEBMERC)]
	arcpy.Delete_management(temp)
	arcpy.env.extent = 'MAXOF'
	return array


def readnearestroads(layer, extent, radius = 0):
	arcpy.env.addOutputsToMap = False
	dsc = arcpy.Describe(layer)
	sr = dsc.spatialReference
	arcpy.env.extent = projectextent(extent, sr, radius)
	path = dsc.dataElement.catalogPath
	query = 'TYP_COD = 7700' if u"TYP_COD" in [f.name for f in arcpy.ListFields(layer)] else ''
	temp = arcpy.CopyFeatures_management(path, u'in_memory\\roadsArray')
	array = [row[0] for row in arcpy.da.SearchCursor(temp, 'SHAPE@', query, spatial_reference=WEBMERC)]
	arcpy.Delete_management(temp)
	arcpy.env.extent = 'MAXOF'
	return array
