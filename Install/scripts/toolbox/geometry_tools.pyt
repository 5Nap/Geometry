# coding: utf-8

import os
import sys
import arcpy


class Toolbox(object):
	def __init__(self):
		"""Define the toolbox (the name of the toolbox is the name of the
		.pyt file)."""
		self.label = "GeometryTools"
		self.alias = "GeometryTools"

		# List of tool classes associated with this toolbox
		self.tools = [OrthogonalizeBuildings, CreateCurves]


class OrthogonalizeBuildings(object):
	def __init__(self):
		"""Define the tool (tool name is the name of the class)."""
		self.label = "Orthogonalize Buildings"
		self.description = "Rectify polygons in a layer by making it's angles right. Tool creates a copy of input layer"
		self.canRunInBackground = False

	def getParameterInfo(self):
		"""Define parameter definitions"""
		parameter0 = arcpy.Parameter(
				name = "in_layer",
				displayName = "Input layer for correction",
				direction = "Input",
				parameterType = "Required",
				datatype = "GPFeatureLayer",
				multiValue = False)
		parameter1 = arcpy.Parameter(
				name = "in_threshold",
				displayName = "Angle threshold",
				direction = "Input",
				parameterType = "Required",
				datatype = "GPDouble")
		parameters = [parameter0, parameter1]
		return parameters

	def isLicensed(self):
		"""Set whether tool is licensed to execute."""
		return True

	def updateParameters(self, parameters):
		"""Modify the values and properties of parameters before internal
		validation is performed.  This method is called whenever a parameter
		has been changed."""
		return

	def updateMessages(self, parameters):
		"""Modify the messages created by internal validation for each tool
		parameter.  This method is called after internal validation."""
		return

	def execute(self, parameters, messages):
		"""The source code of the tool."""
		sys.path.append(os.path.dirname(os.path.dirname(__file__)))
		from orthogonalization import orthogonalizepolygons
		in_layer = parameters[0].value
		in_thr = parameters[1].value

		orthogonalizepolygons(
				layer = in_layer,
				in_edit = False,
				threshold = in_thr,
				proceed_groups = True,
				editor = None)
		return


class CreateCurves(object):
	def __init__(self):
		"""Define the tool (tool name is the name of the class)."""
		self.label = "Create Curves"
		self.description = "Smooth line layer by creating curves on it's corners like fillet tool"
		self.canRunInBackground = False

	def getParameterInfo(self):
		"""Define parameter definitions"""
		parameter0 = arcpy.Parameter(
				name = "in_layer",
				displayName = "Input layer for smoothing",
				direction = "Input",
				parameterType = "Required",
				datatype = "GPFeatureLayer",
				multiValue = False)
		parameter1 = arcpy.Parameter(
				name = "in_angle",
				displayName = "Angle threshold",
				direction = "Input",
				parameterType = "Required",
				datatype = "GPDouble")
		parameter1.value = 0
		parameter2 = arcpy.Parameter(
				name = "in_radius",
				displayName = "Curve radius",
				direction = "Input",
				parameterType = "Required",
				datatype = "GPDouble")
		parameter2.value = 5
		parameter3 = arcpy.Parameter(
				name = "in_copy",
				displayName = "Create layer's copy?",
				direction = "Input",
				parameterType = "Optional",
				datatype = "GPBoolean")
		parameter3.value = True
		parameters = [parameter0, parameter1, parameter2, parameter3]
		return parameters

	def isLicensed(self):
		"""Set whether tool is licensed to execute."""
		return True

	def updateParameters(self, parameters):
		"""Modify the values and properties of parameters before internal
		validation is performed.  This method is called whenever a parameter
		has been changed."""
		return

	def updateMessages(self, parameters):
		"""Modify the messages created by internal validation for each tool
		parameter.  This method is called after internal validation."""
		return

	def execute(self, parameters, messages):
		"""The source code of the tool."""
		sys.path.append(os.path.dirname(os.path.dirname(__file__)))
		from curving import createcurves
		in_layer = parameters[0].value
		in_angle = parameters[1].value
		in_radius = parameters[2].value

		dsc = arcpy.Describe(in_layer)
		layer_path = dsc.catalogPath
		if parameters[3].value:
			if len(os.path.splitext(layer_path)[1]) >= 1:
				layer_work = u'{0}_curved.{1}'.format(os.path.splitext(layer_path)[0], os.path.splitext(layer_path)[1])
			else:
				layer_work = u'{0}_curved'.format(layer_path)
			arcpy.AddMessage(u'-> New Layer: {0}'.format(layer_work))
			arcpy.Copy_management(layer_path, layer_work)
		else:
			layer_work = layer_path

		createcurves(
				layer = layer_work,
				jsonwkt = 'WKT',
				angle_th = in_angle,
				radius_th = in_radius)
		return
