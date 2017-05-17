# coding: utf-8

import arcpy
from comtypes.client import GetModule, CreateObject
from snippets102 import *
import comtypes.gen.esriSystem as esriSystem
import comtypes.gen.esriEditor as esriEditor
import comtypes.gen.esriGeoDatabase as esriGeoDatabase
import comtypes.gen.esriDataSourcesGDB as esriDataSourcesGDB


class Editor:
	def __init__(self, path = None):
		GetDesktopModules()
		self.app = GetCurrentApp()
		GetModule("esriEditor.olb")
		self.path = path
		self.pid = NewObj(esriSystem.UID, esriSystem.IUID)
		self.pid.Value = CLSID(esriEditor.Editor)
		self.pext = self.app.FindExtensionByCLSID(self.pid)
		self.editor = CType(self.pext, esriEditor.IEditor)
		if self.path is not None:
			self.wsf = NewObj(esriDataSourcesGDB.FileGDBWorkspaceFactory, esriGeoDatabase.IWorkspaceFactory)
			self.ws = self.wsf.OpenFromFile(path, 0)
			self.wse = CType(self.ws, esriGeoDatabase.IWorkspaceEdit)
			self.ds = CType(self.ws, esriGeoDatabase.IDataset)
			if self.editor.EditState == esriEditor.esriStateEditing:
				self.isediting = True
			else:
				self.isediting = False

	def get_current(self):
		if self.editor.EditState == esriEditor.esriStateEditing:
			self.ws = self.editor.EditWorkspace
			self.wse = CType(self.ws, esriGeoDatabase.IWorkspaceEdit)
			self.ds = CType(self.ws, esriGeoDatabase.IDataset)
			self.path = self.ws.PathName
		else:
			self.path = None
			print u'start edit session!'

	def start_editing(self):
		if self.editor.EditState != esriEditor.esriStateEditing:
			self.editor.startEditing(self.ds)
			print u'edit session started'
		self.isediting = True

	def stop_editing(self):
		if self.editor.EditState == esriEditor.esriStateEditing:
			self.editor.stopEditing(True)
			print u'edit session closed'
		self.isediting = False

	def start_operation(self):
		self.editor.StartOperation()

	def stop_operation(self, menutext):
		self.editor.StopOperation(menutext)

