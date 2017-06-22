# -*- coding: mbcs -*-
typelib_path = u'C:\\Program Files (x86)\\ArcGIS\\Desktop10.2\\com\\esriArcCatalogUI.olb'
_lcid = 0 # change this if required
from ctypes import *


class Library(object):
    u'Esri ArcCatalogUI Object Library 10.2'
    name = u'esriArcCatalogUI'
    _reg_typelib_ = ('{ED18C81D-E028-4F2A-8745-B6A5D0C6952B}', 10, 2)


# values for enumeration 'esriGxDlgIDs'
esriGxDlgCustomize = 0
esriGxDlgCatalogTree = 1
esriGxDlgMacros = 2
esriGxDlgVBA = 3
esriGxDlgIDs = c_int # enum
__all__ = [ 'esriGxDlgIDs', 'esriGxDlgCatalogTree',
           'esriGxDlgCustomize', 'esriGxDlgMacros', 'esriGxDlgVBA']
from comtypes import _check_version; _check_version('')
