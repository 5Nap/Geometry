# -*- coding: utf-8 -*-

import arcpy
import os
import math

from geometry_functions import f_getAngle, f_floorAngle, f_lineEquation, f_linesCrossing
from readwrite_functions import readgeometryfromrow, creategeometryfromlist, wkt2list

webmercator_wkid = 3857
WEBMERC = arcpy.SpatialReference(webmercator_wkid)


def getindex(array, value):
	# Returns first index of given value from two-dimensional list
	for k in xrange(len(array)):
		for l in xrange(len(array[k])):
			if array[k][l] == value:
				return [k, l]


def getindexdiag(array, value):
	# Returns first index of given value from two-dimensional list where [i:j]: i!=j
	for k in xrange(len(array)):
		for l in xrange(len(array[k])):
			if array[k][l] == value and k != l:
				return [k, l]


############################################################################################################
############################################################################################################
############################################################################################################
############################################################################################################


def grouppolygons(layer):
	# Splits polygon layer to groups (blocks). In a group polygons have at least one common point.
	# Output is [[GroupNo1, [allhouseNo1, allhouseNo2,...]], [GroupNo2, [...]], ...]
	temp_buff = "in_memory\\TMPBuff"
	temp_diss = "in_memory\\TMPDiss"
	temp_join = "in_memory\\TMPJoin"
	
	# create a small buffer around every polygon
	arcpy.Buffer_analysis(
			in_features = layer,
			out_feature_class = temp_buff,
			buffer_distance_or_field = '0.15')

	arcpy.RepairGeometry_management(
			in_features = temp_buff,
			delete_null = 'DELETE_NULL')

	# dissolve it with no attributes
	arcpy.Dissolve_management(
			in_features = layer,
			out_feature_class = temp_diss,
			dissolve_field = '',
			statistics_fields = '',
			multi_part = 'SINGLE_PART')
	
	fieldmapping = arcpy.FieldMappings()

	fm = arcpy.FieldMap()
	fm.addInputField(layer, 'OBJECTID')
	fm_name = fm.outputField
	fm_name.name = 'ELEMENTID'
	fm_name.alias = 'ELEMENTID'
	fm_name.type = 'LONG'
	fm.outputField = fm_name
	fieldmapping.addFieldMap(fm)
	del fm

	fm = arcpy.FieldMap()
	fm.addInputField(temp_diss, 'OBJECTID')
	fm_name = fm.outputField
	fm_name.name = 'GROUPID'
	fm_name.alias = 'GROUPID'
	fm_name.type = 'LONG'
	fm.outputField = fm_name
	fieldmapping.addFieldMap(fm)
	del fm

	# join every polygon to it's group
	arcpy.SpatialJoin_analysis(
			target_features = layer,
			join_features = temp_diss,
			out_feature_class = temp_join,
			join_operation = 'JOIN_ONE_TO_ONE',
			join_type = 'KEEP_COMMON',
			field_mapping = fieldmapping,
			match_option = 'INTERSECT')

	# raw_groups - a list of [[GROUPID, ELEMENTID],...]
	raw_groups = [[row[0], row[1]] for row in arcpy.da.SearchCursor(temp_join, ['GROUPID', 'ELEMENTID'])]
	raw_groups.sort(key = lambda x: x[0], reverse = False)

	groups = [[raw_groups[0][0], []]]
	prev = raw_groups[0][0]
	for g in raw_groups:
		if g[0] != prev:
			groups += [[g[0], [g[1]]]]
			prev = g[0]
		else:
			groups[-1][1] += [g[1]]

	arcpy.Delete_management(temp_buff)
	arcpy.Delete_management(temp_diss)
	arcpy.Delete_management(temp_join)

	return groups


def groupgeometry(poly_dict, group):
	# Возвращает массив с координатами точек в формате [[x1,y1],
	# [x2,y2]...] и полигоны из группы в словаре {allhouseNo1: [[p1,
	# p2,p3..],[p4,p5, p6]], allhouseNo2:[[...],[...]], ...}. В
	# полигонах идут ссылки на точки из первого массива allhouseNo -
	# номер элемента poly_dict (не OID!)

	points_coords = []  # coordinates of all points of the group
	poly_points = {}  # polygons of the group defined by links to points from points_coords
	k = 0
	for x in group[1]:
		poly_points[x] = []
		for parts in poly_dict[x]['geom']:
			poly_points[x] += [[]]
			for point in parts[:-1]:
				if len([gP for gP in points_coords if gP[0] == point[0] and gP[1] == point[1]]) == 0:  # not equal coord
					points_coords += [point]
					poly_points[x][-1] += [k]
					k += 1
				else:
					poly_points[x][-1] += [points_coords.index(point)]
	return points_coords, poly_points


def removepoints(poly_dict, group, threshold):
	points_coords, points_id = groupgeometry(poly_dict, group)
	
	# Последовательный перебор - берём первую точку, идём в первый
	# полигон в группе, в его первую часть, сравниваем по номерам,
	# есть ли там эта точка. Если есть - count увеличиваем на 1. Если
	# count!=1 - значит точка есть в нескольких полигонах и мы её не
	# трогаем. Если в одном - считаем угол, сравниваем с 0. Если
	# близкий (близкий к 180) - удаляем точку отовсюду.

	for i in xrange(len(points_coords)):
		count = 0
		for gr in group[1]:
			for j in xrange(len(points_id[gr])):
				if i in points_id[gr][j]:
					count += 1
					# Порядковый номер полигона, части и точки:
					p_no = [gr, j, points_id[gr][j].index(i)]

		if count == 1:
			loop = len(poly_dict[p_no[0]]['geom'][p_no[1]])-1
			
			# ID точек в общей группе
			p_id_0 = points_id[p_no[0]][p_no[1]][(p_no[2]-1) % loop]
			p_id_1 = points_id[p_no[0]][p_no[1]][p_no[2]]
			p_id_2 = points_id[p_no[0]][p_no[1]][(p_no[2]+1) % loop]

			angle = f_floorAngle(f_getAngle(points_coords[p_id_0], points_coords[p_id_1], points_coords[p_id_2]))
			if -threshold < angle < threshold:
				del poly_dict[p_no[0]]['geom'][p_no[1]][p_no[2]]
				del points_id[p_no[0]][p_no[1]][p_no[2]]
				del points_coords[p_id_1]
				print "removed points {}".format(p_id_1)
				for gr in group[1]:
					for j in xrange(len(points_id[gr])):
						for k in xrange(len(points_id[gr][j])):
							if points_id[gr][j][k] > p_id_1:
								points_id[gr][j][k] -= 1

	return points_coords, points_id


def clusterizeangles(poly_dict, group, threshold):
	# Разбивает все грани полигона на группы по заданному пределу. На
	# вход принимает объект из класса poly_dict и предел в градусах По
	# смыслу представляет из себя Natural Neighbour. Создаёт матрицу
	# NxN, в которую записаны разницы углов поворта грани относительно
	# oX в пределах -90->90. Далее ребра, разница поворотов которы
	# меньше threshold/2 группируются, матрица превращается в N-1xN-1,
	# для объединённой строки записывается минимальное из двух
	# значений, т.е. группа постоянно разрастается "вширь". Пересчёт
	# индексов нужен, т.к. углы и длины записываются в одномерный
	# массив даже если полигон с дыркой или multipart.
	
	# Просчёт длин всех сторон и углов их наклона в диапазоне -90 ->
	# 90.
	lenghts = []
	angles = []
	for x in group[1]:
		for part in poly_dict[x]['geom']:
			quant = len(part)-1
			for i in xrange(quant):
				dx = part[(i+1) % quant][0] - part[i][0]
				dy = part[(i+1) % quant][1] - part[i][1]
				lenghts += [math.hypot(dx, dy)]
				angles += [f_floorAngle(math.degrees(math.atan2(dy, dx)))]
	arcpy.AddMessage('lenghts: {0}'.format(lenghts))
	arcpy.AddMessage(angles)
	# Matrix - матрица NxN с разницей углов наклона i-го и j-го	ребер.
	matrix = [[math.fabs(angles[i]-angles[j]) for i in xrange(len(angles))] for j in xrange(len(angles))]
	arcpy.AddMessage(matrix)
	
	delta = 0
	ind = []

	# Пока отклонение от предыдущей итерации меньше порогового значения - два ребра группируются.
	while delta < threshold/2:
		minimum = min(matrix[i][j] for i in xrange(len(matrix)) for j in xrange(len(matrix)) if i != j)
		delta = minimum
		if delta < threshold/2:
			min_ij = getindexdiag(matrix, minimum)
			trigger = 0
			for k in range(len(ind)):
				if min_ij[0] in ind[k]:
					ind[k].append(min_ij[1])
					trigger = 1
				elif min_ij[1] in ind[k]:
					ind[k].append(min_ij[0])
					trigger = 1
			if trigger == 0:
				ind += [min_ij]
			for k in xrange(len(matrix[min_ij[0]])):
				matrix[min_ij[0]][k] = matrix[k][min_ij[0]] = min(matrix[min_ij[0]][k], matrix[min_ij[1]][k])
			
			for k in xrange(len(matrix)):
				matrix[min_ij[1]][k] = 9999
				matrix[k][min_ij[1]] = 9999
	
	# Первый пересчёт идексов для объединения групп, имеющих общий элемент
	for k in xrange(len(angles)):
		trigger = 0
		for I in ind:
			if k in I:
				trigger = 1
				break
		if trigger == 0:
			ind += [[k]]

	new_ind = [ind[0]]
	for k in xrange(len(ind)):
		trigger = 0
		for x in ind[k]:
			for l in xrange(len(new_ind)):
				if x in new_ind[l]:
					new_ind[l] += [y for y in set(ind[k]) if y not in new_ind[l]]
					trigger = 1
		if trigger == 0:
			new_ind += [ind[k]]

	# Расчёт среднего угла для группы
	med_angles = []
	sum_lenghts = []
	for nI in new_ind:
		try:
			med_angles += [sum([angles[k]*lenghts[k] for k in nI]) / sum([lenghts[k] for k in nI])]
		except ZeroDivisionError:
			med_angles += [sum([angles[k] for k in nI]) / len(angles)]
		sum_lenghts += [sum([lenghts[k] for k in nI])]
	sum_lenghts_sort = sorted(range(len(sum_lenghts)), key=lambda q: sum_lenghts[q])[::-1]

	# Выравнивание групп относительно друг друга, начиная с той, у которой длина сторон больше.
	for i in xrange(len(sum_lenghts_sort)):
		for j in xrange(i):
			ang_diff = math.fabs(med_angles[sum_lenghts_sort[i]] - med_angles[sum_lenghts_sort[j]])
			if True in [X-threshold < ang_diff < X+threshold for X in [90]]:
				closest_angle = min([90], key=lambda d: abs(d-ang_diff))
				med_angles[sum_lenghts_sort[i]] = med_angles[sum_lenghts_sort[j]] + math.copysign(float(closest_angle), med_angles[sum_lenghts_sort[i]] - med_angles[sum_lenghts_sort[j]])
	
	# Второй пересчёт индексов, замена [X]	на [PartNO,NodeNO]
	true_ind = []
	for nI in new_ind:
		true_ind.append([])
		for i in nI:
			temp_ind = i
			trigger = 0
			for x in group[1]:
				for k in xrange(len(poly_dict[x]['geom'])):
					if temp_ind < len(poly_dict[x]['geom'][k])-1:
						true_ind[-1].append([x, k, temp_ind])
						trigger = 1
						break
					else:
						temp_ind -= (len(poly_dict[x]['geom'][k]) - 1)
				if trigger == 1:
					break
	return true_ind, med_angles


def orthogonalizegroup(poly_dict, group, index, angle, points_coords, points_id, threshold):
	# Выравнивание сторон по направляющим. Index - массив с группами индексов, для которых дан угол в массиве Angle.
	# Выравнивание проводится по порядку для каждого полигона в группе.

	# Словарь для сопоставления номер вертекса в полигоне - номер группы из index/angle
	get_index_group = {}
	for gr_no, gr in enumerate(index):
		for pnt_no, pnt in enumerate(gr):
			no = str(pnt)
			get_index_group[no] = gr_no

	for oid in group[1]:
		fixed_points = []
		for part_no, part in enumerate(points_id[oid]):
			for pnt_no, pnt in enumerate(part):
				if pnt_no not in fixed_points:
					group_no = get_index_group[str([oid, part_no, pnt_no])]
					loop = len(points_id[oid][part_no])

					p1_no = pnt_no
					p_prev_no = (pnt_no - 1) % loop
					p2_no = (pnt_no + 1) % loop
					p_next_no = (pnt_no + 2) % loop

					ok_1, ok_2 = False, False
					trigger = 0

					while not ok_1 or not ok_2:
						# Номера точек в общей нумерации внутри группы.
						p1_id = part[p1_no]
						p2_id = part[p2_no]
						p_prev_id = part[p_prev_no]
						p_next_id = part[p_next_no]

						angle_prev = f_floorAngle(
							f_getAngle(points_coords[p_prev_id], points_coords[p1_id], points_coords[p2_id]))
						angle_next = f_floorAngle(
							f_getAngle(points_coords[p1_id], points_coords[p2_id], points_coords[p_next_id]))

						# если угол около 180, то предыдущая/следующая точки берутся +1.
						if -threshold < angle_prev < threshold and not ok_1:
							fixed_points += [p1_no]
							p1_no = (p1_no - 1) % loop
							p_prev_no = (p1_no - 1) % loop
							trigger = 1
						else:
							ok_1 = True

						if -threshold < angle_next < threshold and not ok_2:
							fixed_points += [p2_no]
							p2_no = (p2_no + 1) % loop
							p_next_no = (p2_no + 1) % loop
							trigger = 1
						else:
							ok_2 = True

					# Костыль на перезапись ID
					p1_id = part[p1_no]
					p2_id = part[p2_no]
					p_prev_id = part[p_prev_no]
					p_next_id = part[p_next_no]

					x1 = points_coords[p1_id][0]
					y1 = points_coords[p1_id][1]

					x2 = points_coords[p2_id][0]
					y2 = points_coords[p2_id][1]

					corr_angle = angle[group_no]

					x = (x1 + x2) / 2
					y = (y1 + y2) / 2

					a = math.tan(math.radians(corr_angle))
					b = -1
					c = y - x * math.tan(math.radians(corr_angle))

					x_prev = points_coords[p_prev_id][0]
					y_prev = points_coords[p_prev_id][1]

					x_next = points_coords[p_next_id][0]
					y_next = points_coords[p_next_id][1]

					a_prev, b_prev, c_prev = f_lineEquation(x1, y1, x_prev, y_prev)
					a_next, b_next, c_next = f_lineEquation(x2, y2, x_next, y_next)

					# Если линии почему-то не пересекаются, то координаты точек остаются прежними
					x1_new, y1_new = f_linesCrossing(a, b, c, a_prev, b_prev, c_prev)
					x2_new, y2_new = f_linesCrossing(a, b, c, a_next, b_next, c_next)
					if x1_new is None:
						x1_new, y1_new = x1, y1
					if x2_new is None:
						x2_new, y2_new = x2, y2

					# Если длина какой-либо стороны увеличилась больше, чем на 50%,
					# то это считается ошибкой и координаты остаются прежними.
					try:
						test_eq_1 = ((x2 - x1)**2 + (y2 - y1)**2) / ((x2_new - x1_new)**2 + (y2_new - y1_new)**2)
						test_eq_2 = ((x_prev - x1)**2 + (y_prev - y1)**2) / ((x_prev - x1_new)**2 + (y_prev - y1_new)**2)
						test_eq_3 = ((x_next - x2)**2 + (y_next - y2)**2) / ((x_next - x2_new)**2 + (y_next - y2_new)**2)
						tests = [test_eq_1, test_eq_2, test_eq_3]
						if any(t > 4 for t in tests) or any(t < 0.25 for t in tests):
							print u"! - Failed difference, OID: {}, points: {}, {}".format(oid, p1_no, p2_no)
							x1_new, y1_new = x1, y1
							x2_new, y2_new = x2, y2
					except ZeroDivisionError:
						print u"! - Failed line crossing, OID: {}".format(oid)
						x1_new, y1_new = x1, y1
						x2_new, y2_new = x2, y2

					# Перезапись координат опорных (1,2) точек
					points_coords[p1_id][0], points_coords[p1_id][1] = x1_new, y1_new
					points_coords[p2_id][0], points_coords[p2_id][1] = x2_new, y2_new

					# Если пропускались точки с углами, близкими к 180 -
					# их новые координаты высчитываются как перпендикуляр.
					if trigger == 1:
						# print "point to check: {} -> {}".format(p1_no,p2_no)
						p_corr_no = (p1_no + 1) % loop
						ab, bb, cb = f_lineEquation(x1_new, y1_new, x2_new, y2_new)
						while p_corr_no != p2_no:
							p_corr_id = part[p_corr_no]

							x_corr = points_coords[p_corr_id][0]
							y_corr = points_coords[p_corr_id][1]

							a_corr = -bb
							b_corr = ab
							c_corr = bb * x_corr - ab * y_corr

							try:
								x_corr_new, y_corr_new = f_linesCrossing(ab, bb, cb, a_corr, b_corr, c_corr)
							except ZeroDivisionError:
								x_corr_new, y_corr_new = x_corr, y_corr
								arcpy.AddMessage("! - Failed perp, OID: {}".format(oid))

							points_coords[p_corr_id][0], points_coords[p_corr_id][1] = x_corr_new, y_corr_new

							p_corr_no = (p_corr_no + 1) % loop

	# Перезапись координат в классе.
	for oid in points_id:
		# print points_id[oid]
		for part_no, part in enumerate(points_id[oid]):
			for pnt_no, pnt in enumerate(part):
				poly_dict[oid]['geom'][part_no][pnt_no][0] = points_coords[pnt][0]
				poly_dict[oid]['geom'][part_no][pnt_no][1] = points_coords[pnt][1]

	# Перезапись последней точки, совпадающей с 0-ой.
	for x in group[1]:
		for k in xrange(len(poly_dict[x]['geom'])):
			poly_dict[x]['geom'][k][-1] = poly_dict[x]['geom'][k][0]

	return poly_dict

	
def orthogonalizepolygons(layer, in_edit = False, threshold = 10, proceed_groups = True, editor = None):
	# Main function

	arcpy.env.overwriteOutput = True
	arcpy.env.XYTolerance = "0.1 Meters"
	arcpy.env.XYResolution = "0.01 Meters"

	if not in_edit:
		if layer == '':
			layer = arcpy.GetParameterAsText(0)
			threshold = arcpy.GetParameterAsText(1)
			proceed_groups = arcpy.GetParameterAsText(2)

	try:
		threshold = float(threshold)
	except ValueError:
		threshold = 10

	try:
		if proceed_groups == 'false':
			proceed_groups = False
		else:
			proceed_groups = True
	except NameError:
		proceed_groups = True

	if proceed_groups:
		arcpy.AddMessage("-> All buildings will be proceeded")
	else:
		arcpy.AddMessage("-> Only detached buildings will be proceeded")

	if in_edit:
		layer_work = layer
	else:
		# Если операция надо всем слоем - работает в резервной копии
		dsc = arcpy.Describe(layer)
		layer_name = dsc.baseName
		fd = dsc.path
		dsc = arcpy.Describe(fd)
		if dsc.dataType == 'FeatureDataset':
			gdb = dsc.path
		else:
			gdb = fd

		arcpy.AddMessage("-> Feature dataset: " + fd)
		arcpy.AddMessage("-> Layer: " + layer_name)

		layer_path = os.path.join(fd, layer_name)
		layer_work = os.path.join(fd, layer_name + "_Result")

		arcpy.Copy_management(layer_path, layer_work)

	####################################################################################################################

	arcpy.Integrate_management(layer_work, '0.1 Meters')

	# dictionary created from main layer with {ID: {geom: [Geomentry], isAlone: T/F}
	poly_dict = {}
	with arcpy.da.SearchCursor(layer_work, ['OID@', 'SHAPE@WKT'], spatial_reference = WEBMERC) as sc:
		for row in sc:
			geom = wkt2list(row[1])
			poly_dict[row[0]] = {'geom': geom, 'isAlone': False}

	if in_edit:
		polygons_groups = [[0, [row[0] for row in arcpy.da.SearchCursor(layer_work, 'OID@')]]]
	else:
		polygons_groups = grouppolygons(layer_work)

	for g in polygons_groups:
		points_coords, points_id = removepoints(
				poly_dict = poly_dict,
				group = g,
				threshold = threshold)
		if proceed_groups or len(g[1]) == 1:
			cluster_index, cluster_angles = clusterizeangles(
					poly_dict = poly_dict,
					group = g,
					threshold = threshold)
			poly_dict = orthogonalizegroup(
					poly_dict = poly_dict,
					group = g,
					index = cluster_index,
					angle = cluster_angles,
					points_coords = points_coords,
					points_id = points_id,
					threshold = threshold/2)

	arcpy.AddMessage(u'-> Excessive points removed, polygons orthogonalized')

	if in_edit and editor is not None:
		editor.start_operation()

	with arcpy.da.UpdateCursor(layer_work, ['SHAPE@', 'OID@'], spatial_reference = WEBMERC) as uc:
		for row in uc:
			row = [creategeometryfromlist(poly_dict[row[1]]['geom']), row[1]]
			uc.updateRow(row)
	
	if in_edit and editor is not None:
		editor.stop_operation('Orthogonalize')


