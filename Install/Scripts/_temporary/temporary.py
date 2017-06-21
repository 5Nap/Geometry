# coding: utf-8

import arcpy
import os
import math

from geometry_functions import getanglebetweenvectors, floorangle, getlineequation, getlinesintersection
from readwrite_functions import readgeometryfromrow, creategeometryfromlist

webmercator_wkid = 3857
WEBMERC = arcpy.SpatialReference(webmercator_wkid)


def orthogonalizegroup(poly_dict, group, index, angle, points_coords, points_id, threshold):
	# Выравнивание сторон по направляющим. Index - массив с группами индексов, для которых дан угол в массиве Angle.
	# Выравнивание проводится по порядку для каждого полигона в группе.

	# Словарь для сопоставления номер вертекса в полигоне - номер группы из index/angle
	get_index_group = {}
	for gr in index:
		for point in gr:
			no = str(point)
			get_index_group[no] = gr

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

						angle_prev = floorangle(
							getanglebetweenvectors(points_coords[p_prev_id], points_coords[p1_id], points_coords[p2_id]))
						angle_next = floorangle(
							getanglebetweenvectors(points_coords[p1_id], points_coords[p2_id], points_coords[p_next_id]))

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

					try:
						a_prev, b_prev, c_prev = getlineequation(x1, y1, x_prev, y_prev)
						a_next, b_next, c_next = getlineequation(x2, y2, x_next, y_next)
					except ZeroDivisionError:
						arcpy.AddMessage("! - Failed line crossing, OID: {}, points: {}, {}".format(oid, p1_no, p2_no))

					# Если линии почему-то не пересекаются, то координаты точек остаются прежними
					x1_new, y1_new = getlinesintersection(a, b, c, a_prev, b_prev, c_prev)
					x2_new, y2_new = getlinesintersection(a, b, c, a_next, b_next, c_next)
					if x1_new is None:
						x1_new, y1_new = x1, y1
					if x2_new is None:
						x2_new, y2_new = x2, y2

					# Если длина какой-либо стороны увеличилась больше, чем на 50%,
					# то это считается ошибкой и координаты остаются прежними.
					try:
						test_eq_1 = ((x2 - x1) ** 2 + (y2 - y1) ** 2) / (
						(x2_new - x1_new) ** 2 + (y2_new - y1_new) ** 2)
						test_eq_2 = ((x_prev - x1) ** 2 + (y_prev - y1) ** 2) / (
						(x_prev - x1_new) ** 2 + (y_prev - y1_new) ** 2)
						test_eq_3 = ((x_next - x2) ** 2 + (y_next - y2) ** 2) / (
						(x_next - x2_new) ** 2 + (y_next - y2_new) ** 2)
						tests = [test_eq_1, test_eq_2, test_eq_3]
						if any(t > 4 for t in tests) or any(t < 0.25 for t in tests):
							arcpy.AddMessage("! - Failed difference, OID: {}, points: {}, {}".format(oid, p1_no, p2_no))
							x1_new, y1_new = x1, y1
							x2_new, y2_new = x2, y2
					except ZeroDivisionError:
						arcpy.AddMessage("! - Failed line crossing, OID: {}".format(oid))
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
						ab, bb, cb = getlineequation(x1_new, y1_new, x2_new, y2_new)
						while p_corr_no != p2_no:
							p_corr_id = part[p_corr_no]

							x_corr = points_coords[p_corr_id][0]
							y_corr = points_coords[p_corr_id][1]

							a_corr = -bb
							b_corr = ab
							c_corr = bb * x_corr - ab * y_corr

							try:
								x_corr_new, y_corr_new = getlinesintersection(ab, bb, cb, a_corr, b_corr, c_corr)
							except ZeroDivisionError:
								x_corr_new, y_corr_new = x_corr, y_corr
								arcpy.AddMessage("! - Failed perp, OID: {}".format(oid))

							points_coords[p_corr_id][0], points_coords[p_corr_id][1] = x_corr_new, y_corr_new

							p_corr_no = (p_corr_no + 1) % loop

	# Перезапись координат в классе.
	for oid in points_id:
		for part_no, part in enumerate(points_id[oid]):
			for pnt_no, pnt in enumerate(part):
				poly_dict[oid]['geom'][part_no][pnt_no][0] = pnt[0]
				poly_dict[oid]['geom'][part_no][pnt_no][1] = pnt[1]

	# Перезапись последней точки, совпадающей с 0-ой.
	for x in group[1]:
		for k in xrange(len(poly_dict[x]['geom'])):
			poly_dict[x]['geom'][k][-1] = poly_dict[x]['geom'][k][0]