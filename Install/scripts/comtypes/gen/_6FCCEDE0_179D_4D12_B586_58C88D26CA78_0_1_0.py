# -*- coding: mbcs -*-
typelib_path = u'C:\\Program Files (x86)\\Common Files\\ArcGIS\\bin\\ArcGISVersion.dll'
_lcid = 0 # change this if required
from ctypes import *
import comtypes.gen._00020430_0000_0000_C000_000000000046_0_2_0
from comtypes import GUID
from ctypes import HRESULT
from comtypes import BSTR
from comtypes import helpstring
from comtypes import COMMETHOD
from comtypes import dispid
from comtypes import CoClass
from ctypes.wintypes import VARIANT_BOOL
from comtypes import IUnknown


class IEnumVersions(comtypes.gen._00020430_0000_0000_C000_000000000046_0_2_0.IUnknown):
    _case_insensitive_ = True
    u'IEnumVersions Interface'
    _iid_ = GUID('{18F07A02-956A-4D44-979B-B006ECC81D93}')
    _idlflags_ = ['nonextensible', 'oleautomation']

# values for enumeration 'esriProductCode'
esriArcGIS = 0
esriArcGISDesktop = 1
esriArcGISEngine = 2
esriArcGISReader = 3
esriArcGISExplorer = 4
esriArcGISServer = 5
esriProductCode = c_int # enum
IEnumVersions._methods_ = [
    COMMETHOD([helpstring(u'Resets the enumerator to the beggining of the sequence.')], HRESULT, 'Reset'),
    COMMETHOD([helpstring(u'Returns the next version in the sequence of installed versions.')], HRESULT, 'Next',
              ( ['out'], POINTER(esriProductCode), 'pCode' ),
              ( ['out'], POINTER(BSTR), 'pVer' ),
              ( ['out'], POINTER(BSTR), 'path' )),
]
################################################################
## code template for IEnumVersions implementation
##class IEnumVersions_Impl(object):
##    def Reset(self):
##        u'Resets the enumerator to the beggining of the sequence.'
##        #return 
##
##    def Next(self):
##        u'Returns the next version in the sequence of installed versions.'
##        #return pCode, pVer, path
##

class VersionManager(CoClass):
    u'VersionManager Class'
    _reg_clsid_ = GUID('{D0705D7D-0270-4607-BCDB-1D4F18624748}')
    _idlflags_ = []
    _typelib_path_ = typelib_path
    _reg_typelib_ = ('{6FCCEDE0-179D-4D12-B586-58C88D26CA78}', 1, 0)
class IArcGISVersion(comtypes.gen._00020430_0000_0000_C000_000000000046_0_2_0.IUnknown):
    _case_insensitive_ = True
    u'Interface used to bind an engine application to a specific ArcGIS runtime.'
    _iid_ = GUID('{4B666CA0-021E-408C-9ABE-A1CC182729FA}')
    _idlflags_ = ['nonextensible', 'oleautomation']
class IVersionHost(comtypes.gen._00020430_0000_0000_C000_000000000046_0_2_0.IUnknown):
    _case_insensitive_ = True
    u'IVersionHost Interface'
    _iid_ = GUID('{A4092E33-E459-4B9C-B04E-263FB7A8E1D1}')
    _idlflags_ = []
VersionManager._com_interfaces_ = [comtypes.gen._00020430_0000_0000_C000_000000000046_0_2_0.IUnknown, IArcGISVersion, IVersionHost, IEnumVersions]

IArcGISVersion._methods_ = [
    COMMETHOD([helpstring(u'Binds the client engine application against the specified ArcGIS runtime.')], HRESULT, 'LoadVersion',
              ( ['in'], esriProductCode, 'productCode' ),
              ( ['in'], BSTR, 'engineVersion' ),
              ( ['retval', 'out'], POINTER(VARIANT_BOOL), 'succeeded' )),
    COMMETHOD([helpstring(u'Returns the runtime that the calling application is currently bound to.')], HRESULT, 'GetActiveVersion',
              ( ['out'], POINTER(esriProductCode), 'pCode' ),
              ( ['out'], POINTER(BSTR), 'pVer' ),
              ( ['out'], POINTER(BSTR), 'pPath' )),
    COMMETHOD([helpstring(u'Returns an enumerator over the currently installed runtimes.')], HRESULT, 'GetVersions',
              ( ['out'], POINTER(POINTER(IEnumVersions)), 'ppVersions' )),
    COMMETHOD([helpstring(u'Returns a product name given a product code.')], HRESULT, 'ProductNameFromCode',
              ( ['in'], esriProductCode, '__MIDL__IArcGISVersion0000' ),
              ( ['retval', 'out'], POINTER(BSTR), 'pProductName' )),
]
################################################################
## code template for IArcGISVersion implementation
##class IArcGISVersion_Impl(object):
##    def GetVersions(self):
##        u'Returns an enumerator over the currently installed runtimes.'
##        #return ppVersions
##
##    def ProductNameFromCode(self, __MIDL__IArcGISVersion0000):
##        u'Returns a product name given a product code.'
##        #return pProductName
##
##    def LoadVersion(self, productCode, engineVersion):
##        u'Binds the client engine application against the specified ArcGIS runtime.'
##        #return succeeded
##
##    def GetActiveVersion(self):
##        u'Returns the runtime that the calling application is currently bound to.'
##        #return pCode, pVer, pPath
##

IVersionHost._methods_ = [
    COMMETHOD([helpstring(u'Used to create objects within a remote host process such as dllhost.')], HRESULT, 'CreateObject',
              ( ['in'], comtypes.gen._00020430_0000_0000_C000_000000000046_0_2_0.GUID, 'clsid' ),
              ( ['retval', 'out'], POINTER(POINTER(IUnknown)), 'ppv' )),
]
################################################################
## code template for IVersionHost implementation
##class IVersionHost_Impl(object):
##    def CreateObject(self, clsid):
##        u'Used to create objects within a remote host process such as dllhost.'
##        #return ppv
##

class Library(object):
    u'ArcGISVersion 1.0 Type Library'
    name = u'ArcGISVersionLib'
    _reg_typelib_ = ('{6FCCEDE0-179D-4D12-B586-58C88D26CA78}', 1, 0)

__all__ = [ 'IEnumVersions', 'esriArcGISReader', 'IVersionHost',
           'esriArcGIS', 'VersionManager', 'esriArcGISEngine',
           'esriArcGISServer', 'esriProductCode', 'esriArcGISDesktop',
           'IArcGISVersion', 'esriArcGISExplorer']
from comtypes import _check_version; _check_version('')
