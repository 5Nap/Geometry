﻿# coding: utf-8

import os
import sys
import arcpy
import subprocess
import pythonaddins

# append 'scripts' dir to system path
filesystem_enc = sys.getfilesystemencoding()
try:
	rel_path = os.path.normpath(os.path.dirname(__file__).decode(filesystem_enc))
except UnicodeEncodeError:
	rel_path = os.path.normpath(os.path.dirname(__file__))

SRC = os.path.join(rel_path, u'scripts')
sys.path.append(SRC)

# don't create pyc
sys.dont_write_bytecode = True

# import functions from local modules
from layer_functions import getworkspace, checkallhouse, readnearestroads, readnearestbuildings
from find_functions import findnearestbuilding, findnearestline
from curving import createcurves
from orthogonalization import orthogonalizepolygons
from aligning import alignpolygons
from offsetting import createoffset
from cls_editor import Editor
from cls_timer import Timer

__version__ = '1.0.1'

# 10.2 wouldn't work with JSON and curves so use WKT instead
json_or_wkt = u'WKT' if arcpy.GetInstallInfo()['Version'] < '10.3' else u'JSON'

# default settings dictionary
settings_dict = {
	u'Ortho Threshold': 10,
	u'Search Radius': 50,
	u'Rotation Threshold': 20,
	u'Offset': 10,
	u'Curves Radius': 5,
	u'Curves Angle': 0,
	u'Align to Roads': 0,
	u'Read Offset from Field': 0}  # align to roads

# set default XY tolerance
arcpy.env.XYTolerance = u'0.1 Meters'

# find path to python executable (need it to run subprocess)
python_path = os.path.join(sys.exec_prefix, u'python.exe')

# create dummy Editor and Timer objects
editor = Editor()
timer = Timer()

# ##################################################################################################################
# Base logic for every processing buttons:
# 1. get global Editor and update it. Editor now have .path with current workspace or None if no session'd started
# 2. get all layers with selection. getworkspace return Lyr object + gdb + extent
# 3. run processing function for every Lyr where gdb == Editor.path
# 4. ask user to run geoprocessing tool if gdb != Editor.path
# ##################################################################################################################


class CurveButton(object):
	"""Implementation for Geometry_addin.btnCurve (Button)"""
	def __init__(self):
		self.enabled = True
		self.checked = False

	def onClick(self):
		# get and update Editor object
		global editor
		editor.get_current()

		# get layer with selection
		workspace = getworkspace()

		# if there is a layer with selection:
		if workspace[u'data'] is not None:
			# for every layer with selection:
			for data in workspace[u'data']:
				# if layer's workspace and editor's workspace are the same location
				if data[u'gdb'] == editor.path:
					# get Layer object
					layer = data[u'lyr']

					timer.start()

					# if WKT - generalize curves
					if json_or_wkt == u'WKT':
						arcpy.Densify_edit(
								in_features = layer,
								densification_method = u'OFFSET',
								max_deviation = u'0.01 Meters')

					editor.start_operation()
					# run processing
					createcurves(
							layer = layer,
							jsonwkt = json_or_wkt,
							angle_th = settings_dict[u'Curves Angle'],
							radius_th = settings_dict[u'Curves Radius'])
					editor.stop_operation('Create Curves')

					arcpy.RefreshActiveView()
					timer.stop(message = u'Create Curves')
				elif editor.path is None:
					# Fire a tool from toolbox if layer isn't in an edit session
					layer = data[u'lyr']
					title = u'Warning'
					message = u'{0} layer is not in edit session\nWould you run a geoprocessing tool?'.format(
						layer.name)
					mb_type = 1
					answer = pythonaddins.MessageBox(message, title, mb_type)
					if answer == u'OK':
						relpath = os.path.dirname(__file__)
						toolbox = os.path.join(relpath, u'scripts', u'toolbox', u'geometry_tools.pyt')
						pythonaddins.GPToolDialog(toolbox, u'CreateCurves')

		else:
			if editor.path is None:
				# Fire a tool from toolbox if there is no selection in a layer and no edit session
				title = u'Warning'
				message = u'{0}\nWould you run a geoprocessing tool?'.format(workspace[u'message'])
				mb_type = 1
				answer = pythonaddins.MessageBox(message, title, mb_type)
				if answer == u'OK':
					relpath = os.path.dirname(__file__)
					toolbox = os.path.join(relpath, u'scripts', u'toolbox', u'geometry_tools.pyt')
					pythonaddins.GPToolDialog(toolbox, u'CreateCurves')
			else:
				title = u'Warning'
				message = u'{0}'.format(workspace[u'message'])
				mb_type = 0
				pythonaddins.MessageBox(message, title, mb_type)


class OrthoBuildingsButton(object):
	# Implementation for Geom_addin.Geom_addin.btnOrthoBuildings (Button)
	def __init__(self):
		self.enabled = True
		self.checked = False

	def onClick(self):
		global editor
		editor.get_current()

		workspace = getworkspace(geomtype = u'Polygon')
		if workspace[u'data'] is not None:
			for data in workspace[u'data']:
				if data[u'gdb'] == editor.path:
					# create dummy settings_dict with 'Align to Roads' set to 0
					temp_settings = {key: value for key, value in settings_dict.items()}
					temp_settings[u'Align to Roads'] = 0

					rectifybuildings(
							layer = data[u'lyr'],
							roads = data[u'tline'],
							extent = workspace[u'extent'],
							settings = temp_settings,
							force = True,
							editor_object = editor)
					arcpy.RefreshActiveView()
				elif editor.path is None:
					# Fire a tool from toolbox if layer isn't in an edit session
					layer = data[u'lyr']
					title = u'Warning'
					message = u'{0} layer is not in edit session\nWould you run a geoprocessing tool?'.format(layer.name)
					mb_type = 1
					answer = pythonaddins.MessageBox(message, title, mb_type)
					if answer == u'OK':
						relpath = os.path.dirname(__file__)
						toolbox = os.path.join(relpath, u'scripts', u'toolbox', u'geometry_tools.pyt')
						pythonaddins.GPToolDialog(toolbox, u'OrthogonalizeBuildings')

		else:
			if editor.path is None:
				# Fire a tool from toolbox if there is no selection in a layer and no edit session
				title = u'Warning'
				message = u'{0}\nWould you run a geoprocessing tool?'.format(workspace[u'message'])
				mb_type = 1
				answer = pythonaddins.MessageBox(message, title, mb_type)
				if answer == u'OK':
					relpath = os.path.dirname(__file__)
					toolbox = os.path.join(relpath, u'scripts', u'toolbox', u'geometry_tools.pyt')
					pythonaddins.GPToolDialog(toolbox, u'OrthogonalizeBuildings')
			else:
				title = u'Warning'
				message = u'{0}'.format(workspace[u'message'])
				mb_type = 0
				pythonaddins.MessageBox(message, title, mb_type)


class OrthoRoadsButton(object):
	# Implementation for Geom_addin.Geom_addin.btnOrthoRoads (Button)
	def __init__(self):
		self.enabled = True
		self.checked = False

	def onClick(self):
		global editor
		editor.get_current()

		workspace = getworkspace(geomtype = u'Polygon')

		if workspace[u'data'] is not None:
			for data in workspace[u'data']:
				if data[u'gdb'] == editor.path:
					# create dummy settings_dict with 'Align to Roads' set to 1
					temp_settings = {key: value for key, value in settings_dict.items()}
					temp_settings[u'Align to Roads'] = 1

					rectifybuildings(
							layer = data[u'lyr'],
							roads = data[u'tline'],
							extent = workspace[u'extent'],
							settings = temp_settings,
							force = True,
							editor_object = editor)
					arcpy.RefreshActiveView()
				elif editor.path is None:
					# Fire a tool from toolbox if layer isn't in an edit session
					layer = data[u'lyr']
					title = u'Warning'
					message = u'{0} layer is not in edit session\nWould you run a geoprocessing tool?'.format(
						layer.name)
					mb_type = 1
					answer = pythonaddins.MessageBox(message, title, mb_type)
					if answer == u'OK':
						relpath = os.path.dirname(__file__)
						toolbox = os.path.join(relpath, u'scripts', u'toolbox', u'geometry_tools.pyt')
						pythonaddins.GPToolDialog(toolbox, u'OrthogonalizeBuildings')
		else:
			if editor.path is None:
				# Fire a tool from toolbox if there is no selection in a layer and no edit session
				title = u'Warning'
				message = u'{0}\nWould you run a geoprocessing tool?'.format(workspace[u'message'])
				mb_type = 1
				answer = pythonaddins.MessageBox(message, title, mb_type)
				if answer == u'OK':
					relpath = os.path.dirname(__file__)
					toolbox = os.path.join(relpath, u'scripts', u'toolbox', u'geometry_tools.pyt')
					pythonaddins.GPToolDialog(toolbox, u'OrthogonalizeBuildings')
			else:
				title = u'Warning'
				message = u'{0}'.format(workspace[u'message'])
				mb_type = 0
				pythonaddins.MessageBox(message, title, mb_type)


class OffsetButton(object):
	# Implementation for Geom_addin.btnOffset (Button)
	def __init__(self):
		self.enabled = True
		self.checked = False

	def onClick(self):
		global editor
		editor.get_current()

		check_allhouse = checkallhouse()
		if check_allhouse:
			workspace = getworkspace(geomtype = u'Polyline')
			if workspace[u'data'] is not None:
				for data in workspace[u'data']:
					if data[u'gdb'] == editor.path:
						layer = data[u'lyr']

						editor.start_operation()
						if settings_dict[u'Read Offset from Field'] == 1:
							createoffset(
									in_fc = layer,
									out_fc = u'allhouse',
									mode = u'field')
						else:
							offset = settings_dict[u'Offset']
							createoffset(
									in_fc = layer,
									out_fc = u'allhouse',
									mode = u'value',
									offset = offset)
						editor.stop_operation('Offset')

						arcpy.RefreshActiveView()
					else:
						layer = data[u'lyr']
						title = u'Warning'
						message = u'{0} is not in edit session'.format(layer.name)
						pythonaddins.MessageBox(message, title, 0)
			else:
				title = u'Warning'
				message = workspace[u'message']
				pythonaddins.MessageBox(message, title, 0)

		else:
			title = u'Warning'
			message = u'Allhouse is not in TOC.'
			pythonaddins.MessageBox(message, title, 0)


class SettingsButton(object):
	# Implementation for Geom_addin.btnSettings (Button)

	# Fires a GUI (Tk). Runs as a subprocess because of a conflict between ArcGIS and Tk.
	# The settings would be saved back to settings_dict and kept until ArcGIS shutdown.

	def __init__(self):
		self.enabled = True
		self.checked = False

	def onClick(self):
		global settings_dict

		script = os.path.join(SRC, u'settings_button.py')

		script_string = u'{0},{1},{2},{3},{4},{5},{6},{7}'.format(
			unicode(settings_dict[u'Ortho Threshold']),
			unicode(settings_dict[u'Search Radius']),
			unicode(settings_dict[u'Rotation Threshold']),
			unicode(settings_dict[u'Offset']),
			unicode(settings_dict[u'Curves Radius']),
			unicode(settings_dict[u'Curves Angle']),
			unicode(settings_dict[u'Align to Roads']),
			unicode(settings_dict[u'Read Offset from Field']))

		# it'll pop-up until the setting are correct
		loop = True
		while loop:
			exec_string = u'{0} {1} {2}'.format(python_path, script, script_string).encode('cp1251')
			arcpy.AddMessage(exec_string)
			proc = subprocess.Popen(
					exec_string,
					stdout = subprocess.PIPE,
					stderr = subprocess.STDOUT,
					shell = True)
			proc.wait()
			try:
				out_sting = proc.communicate()[0]
				out = [float(x) for x in out_sting.split('\n')[:-1]]
				settings_dict[u'Ortho Threshold'] = out[0]
				settings_dict[u'Search Radius'] = out[1]
				settings_dict[u'Rotation Threshold'] = out[2]
				settings_dict[u'Offset'] = out[3]
				settings_dict[u'Curves Radius'] = out[4]
				settings_dict[u'Curves Angle'] = out[5]
				settings_dict[u'Align to Roads'] = int(out[6])
				settings_dict[u'Read Offset from Field'] = int(out[7])
				arcpy.AddMessage(u'New settings:')
				for key in settings_dict:
					arcpy.AddMessage('-> ' + key + ': ' + str(settings_dict[key]))
				loop = False
				break
			except ValueError as err:
				arcpy.AddMessage('{0}, {1}'.format(err, err.args))
			except Exception as err:
				arcpy.AddMessage('{0} {1}'.format(err, err.args))
				break


def rectifybuildings(layer, roads, extent, settings, force = False, editor_object = None):
	timer.start()

	# read nearby buildings geometry
	houses_array = readnearestbuildings(
			layer = layer,
			extent = extent,
			radius = settings[u'Search Radius'])

	# find closest building
	mode, geometry = findnearestbuilding(
				layerwork = layer,
				houses_array = houses_array,
				radius = settings[u'Search Radius'])
	timer.stop_lap(message = u'Copy Polygons')

	# if mode == 0 -> a polygon shares a segment with other building.
	if mode != 0:
		orthogonalizepolygons(
				layer = layer,
				in_edit = True,
				threshold = settings[u'Ortho Threshold'],
				editor = editor)
		timer.stop_lap(message = u'Orthogonalize')

		# if alignRoads was set to True or if no polygons were found
		if (settings[u'Align to Roads'] == 1 or mode == 2) and roads is not None:
			# read nearby roads geometry with query if possible
			roads_array = readnearestroads(
					layer = roads,
					extent = extent,
					radius = settings[u'Search Radius'])

			# find closest road
			mode, geometry = findnearestline(
					layer = layer,
					other_layer = roads_array,
					radius = settings[u'Search Radius'])
			timer.stop_lap(message = u'Copy Lines')

		if geometry != 0:
			# if geometry != 0 - there is an object in a given radius
			editor_object.start_operation()
			alignpolygons(
					layer = layer,
					mode = mode,
					geometry = geometry,
					procent = settings[u'Rotation Threshold'])
			editor_object.stop_operation('Aligning')

			timer.stop(message = u'Aligning')

		else:
			print u'! No objects were found in {0:.0f} m buffer'.format(settings[u'Search Radius'])
	elif force:
		print u'force mode'
		orthogonalizepolygons(
				layer = layer,
				in_edit = True,
				threshold = settings[u'Ortho Threshold'],
				editor = editor)

		timer.stop(message = u'Orthogonalize')
