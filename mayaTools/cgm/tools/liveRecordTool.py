"""
------------------------------------------
liveRecordTool : cgm.tools
Author: David Bokser
email: dbokser@cgmonks.com
Website : http://www.cgmonks.com
------------------------------------------

================================================================
"""
# From Python =============================================================
import copy
import re
import time
import pprint
import os
import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

import maya.cmds as mc

import cgm.core.classes.GuiFactory as cgmUI
from cgm.core import cgm_RigMeta as cgmRigMeta
mUI = cgmUI.mUI

from cgm.core.lib import shared_data as SHARED
from cgm.core.cgmPy import validateArgs as VALID
from cgm.core import cgm_General as cgmGEN
from cgm.core import cgm_Meta as cgmMeta
import cgm.core.lib.transform_utils as TRANS
from cgm.core.cgmPy import path_Utils as CGMPATH
import cgm.core.lib.math_utils as MATH
from cgm.lib import lists

from cgm.tools import liveRecord
from cgm.tools import dragger as DRAGGER

#>>> Root settings =============================================================
__version__ = '0.1.05172020'
__toolname__ ='cgmAnimDraw'

_padding = 5

class ui(cgmUI.cgmGUI):
    USE_Template = 'cgmUITemplate'
    WINDOW_NAME = '{0}_ui'.format(__toolname__)    
    WINDOW_TITLE = '{1} - {0}'.format(__version__,__toolname__)
    DEFAULT_MENU = None
    RETAIN = True
    MIN_BUTTON = True
    MAX_BUTTON = False
    FORCE_DEFAULT_SIZE = True  #always resets the size of the window when its re-created  
    DEFAULT_SIZE = 425,350
    TOOLNAME = '{0}.ui'.format(__toolname__)
    
    def insert_init(self,*args,**kws):
        _str_func = '__init__[{0}]'.format(self.__class__.TOOLNAME)            
        log.info("|{0}| >>...".format(_str_func))        

        if kws:log.debug("kws: %s"%str(kws))
        if args:log.debug("args: %s"%str(args))
        log.info(self.__call__(q=True, title=True))

        self.__version__ = __version__
        self.__toolName__ = self.__class__.WINDOW_NAME  

        #self.l_allowedDockAreas = []
        self.WINDOW_TITLE = self.__class__.WINDOW_TITLE
        self.DEFAULT_SIZE = self.__class__.DEFAULT_SIZE

        self._liveRecordTool = None
        self._mTransformTarget = False
        self._mPlaneObject = False

        self._optionDict = {
            'mode' : 'position',
            'plane' : 'screen',
            'aimFwd' : 'z+',
            'aimUp' : 'y+',
            'loopTime' : False,
            'debug' : False
        }

 
    def build_menus(self):
        self.uiMenu_FirstMenu = mUI.MelMenu(l='Setup', pmc = cgmGEN.Callback(self.buildMenu_first))

    def buildMenu_first(self):
        self.uiMenu_FirstMenu.clear()
        #>>> Reset Options                           

        mUI.MelMenuItemDiv( self.uiMenu_FirstMenu )

        mUI.MelMenuItem( self.uiMenu_FirstMenu, l="Reload",
                         c = lambda *a:mc.evalDeferred(self.reload,lp=True))

        mUI.MelMenuItem( self.uiMenu_FirstMenu, l="Reset",
                         c = lambda *a:mc.evalDeferred(self.reload,lp=True))
        
    def build_layoutWrapper(self,parent):
        _str_func = 'build_layoutWrapper'
        #self._d_uiCheckBoxes = {}
    
        #_MainForm = mUI.MelFormLayout(parent,ut='cgmUISubTemplate')
        _MainForm = mUI.MelFormLayout(self,ut='cgmUITemplate')
        _column = buildColumn_main(self,_MainForm,True)

    
        _row_cgm = cgmUI.add_cgmFooter(_MainForm)            
        _MainForm(edit = True,
                  af = [(_column,"top",0),
                        (_column,"left",0),
                        (_column,"right",0),                        
                        (_row_cgm,"left",0),
                        (_row_cgm,"right",0),                        
                        (_row_cgm,"bottom",0),
    
                        ],
                  ac = [(_column,"bottom",2,_row_cgm),
                        ],
                  attachNone = [(_row_cgm,"top")])          
        

def buildColumn_main(self,parent, asScroll = False):
    """
    Trying to put all this in here so it's insertable in other uis
    
    """   
    if asScroll:
        _inside = mUI.MelScrollLayout(parent,useTemplate = 'cgmUISubTemplate') 
    else:
        _inside = mUI.MelColumnLayout(parent,useTemplate = 'cgmUISubTemplate') 
    
    #>>>Objects Load Row ---------------------------------------------------------------------------------------
    _row_objLoad = mUI.MelHSingleStretchLayout(_inside,ut='cgmUISubTemplate',padding = _padding)        

    mUI.MelSpacer(_row_objLoad,w=_padding)
    mUI.MelLabel(_row_objLoad, 
                 l='Target:')

    self.uiTF_objLoad = mUI.MelLabel(_row_objLoad,ut='cgmUIInstructionsTemplate',l='',en=True)

    cgmUI.add_Button(_row_objLoad,'<<',
                     cgmGEN.Callback(uiFunc_load_selected,self),
                     "Load first selected object.")  
    _row_objLoad.setStretchWidget(self.uiTF_objLoad)
    mUI.MelSpacer(_row_objLoad,w=_padding)

    _row_objLoad.layout()

    mc.setParent(_inside)
    cgmUI.add_LineSubBreak()

    _row = mUI.MelHSingleStretchLayout(_inside,ut='cgmUISubTemplate',padding = _padding)        

    mUI.MelSpacer(_row,w=_padding)

    _subColumn = mUI.MelColumnLayout(_row,useTemplate = 'cgmUIHeaderTemplate') 

    _optionFrame = mUI.MelFrameLayout(_subColumn, label='Options', collapsable=True, collapse=True,useTemplate = 'cgmUIHeaderTemplate')
    
    self._optionColumn = mUI.MelColumnLayout(_optionFrame,useTemplate = 'cgmUIHeaderTemplate') 

    uiFunc_build_options_column(self)

    _row.setStretchWidget(_subColumn)

    mUI.MelSpacer(_row,w=_padding)

    #mUI.MelSpacer(_row,w=_padding)
    _row.layout()

    mc.setParent(_inside)
    cgmUI.add_LineSubBreak()

    _row = mUI.MelHLayout(_inside,ut='cgmUISubTemplate',padding = _padding*2)
    
    self.liveRecordBtn = cgmUI.add_Button(_row,'Start Live Record',
        cgmGEN.Callback(uiFunc_toggleContext,self),                         
        #lambda *a: attrToolsLib.doAddAttributesToSelected(self),
        'Start Live Record',h=50)

    _row.layout()    

    uiFunc_load_selected(self)


    return _inside

def uiFunc_build_options_column(self):
    mc.setParent(self._optionColumn)
    cgmUI.add_LineSubBreak()

    _row = mUI.MelHSingleStretchLayout(self._optionColumn,ut='cgmUISubTemplate',padding = 5)

    mUI.MelSpacer(_row,w=_padding)                      
    mUI.MelLabel(_row,l='Mode:')
    _row.setStretchWidget( mUI.MelSeparator(_row) )

    uiRC = mUI.MelRadioCollection()

    _on = self._optionDict['mode']

    for i,item in enumerate(['position','aim']):
        if item == _on:
            _rb = True
        else:_rb = False

        uiRC.createButton(_row,label=item,sl=_rb,
                          onCommand = cgmGEN.Callback(uiFunc_setModeOption,self,'mode', item))

        mUI.MelSpacer(_row,w=_padding)       

    _row.layout()  

    mc.setParent(self._optionColumn)
    cgmUI.add_LineSubBreak()    

    _row = mUI.MelHSingleStretchLayout(self._optionColumn,ut='cgmUISubTemplate',padding = 5)

    mUI.MelSpacer(_row,w=_padding)                          
    mUI.MelLabel(_row,l='Plane:')  

    _row.setStretchWidget( mUI.MelSeparator(_row) )

    planeOptions = ['screen', 'planeX', 'planeY', 'planeZ', 'axisX', 'axisY', 'axisZ', 'custom']
   
    self.planeMenu = mUI.MelOptionMenu(_row,useTemplate = 'cgmUITemplate')
    for option in planeOptions:
        self.planeMenu.append(option)

    self.planeMenu.setValue( 'screen' )

    self.planeMenu(edit=True, changeCommand=cgmGEN.Callback(uiFunc_set_plane,self))

    mUI.MelSpacer(_row,w=_padding)

    _row.layout()

    _row = mUI.MelHSingleStretchLayout(self._optionColumn,ut='cgmUISubTemplate',padding = 5)
    self._row_planeObject = _row

    mUI.MelSpacer(_row,w=_padding)                          
    mUI.MelLabel(_row,l='Plane Object:')  

    self.uiTF_planeObject = mUI.MelLabel(_row,ut='cgmUIInstructionsTemplate',l='',en=False)

    _row.setStretchWidget( self.uiTF_planeObject )

    cgmUI.add_Button(_row,'<<',
                     cgmGEN.Callback(uiFunc_load_planeObject,self),
                     "Load first selected object.")  

    cgmUI.add_Button(_row,'Create',
                     cgmGEN.Callback(uiFunc_create_planeObject,self),
                     "Load first selected object.") 

    mUI.MelSpacer(_row,w=_padding)

    _row.layout()

    self._row_planeObject(edit=True, vis=False)

    mc.setParent(self._optionColumn)
    cgmUI.add_LineSubBreak()   

def uiFunc_setModeOption(self, option, val):
    self._optionDict[option] = val

def uiFunc_set_plane(self):
    uiFunc_setModeOption(self, 'plane', self.planeMenu.getValue())
    if self.planeMenu.getValue() == 'custom':
        self._row_planeObject(edit=True, vis=True)
    else:
        self._row_planeObject(edit=True, vis=False)      

def uiFunc_create_planeObject(self):
    mc.polyPlane(name='customDrawPlane', sx=2, sy=2)
    uiFunc_load_planeObject(self)

def uiFunc_load_planeObject(self):
    _str_func = 'uiFunc_load_planeObject'  
    self._mPlaneObject = False

    _sel = mc.ls(sl=True,type='transform')

    #Get our raw data
    if _sel:
        mNode = cgmMeta.validateObjArg(_sel[0])
        _short = mNode.p_nameBase            
        log.debug("|{0}| >> Target: {1}".format(_str_func, _short))
        self._mPlaneObject = mNode

        uiFunc_updateObjectDisplay(self.uiTF_planeObject, self._mPlaneObject)
    else:
        log.warning("|{0}| >> Nothing selected.".format(_str_func))            
        uiFunc_clear_loaded(self.uiTF_planeObject)

def uiFunc_toggleContext(self):
    _str_func = 'liveRecordTool.uiFunc_toggleContext'

    if not self._mTransformTarget:
        log.error("|{0}| >> No target transform found.".format(_str_func))
        return

    if self._liveRecordTool:
        self._liveRecordTool.quit()
        self._liveRecordTool = None
        self.liveRecordBtn(e=True, label='Start Recording Context', bgc=[.35,.35,.35])
    else:
        mc.select(self._mTransformTarget.mNode)
        self._liveRecordTool = liveRecord.LiveRecord(plane='screen', mode='position', loopTime=False, onStart=cgmGEN.Callback(uiFunc_recordingStarted,self), onComplete=cgmGEN.Callback(uiFunc_recordingCompleted,self))
        self._liveRecordTool.activate()
        self.liveRecordBtn(e=True, label='Stop Recording Context', bgc=[.35,1,.35])

def uiFunc_recordingStarted(self):
    _str_func = 'liveRecordTool.uiFunc_recordingStarted'

    log.debug("|{0}| >> Starting Recording in UI".format(_str_func))

    self.liveRecordBtn(e=True, label='Recording in Process', bgc=[1,.35,.35])

def uiFunc_recordingCompleted(self):
    _str_func = 'liveRecordTool.uiFunc_recordingCompleted'
    log.debug("|{0}| >> Starting Recording in UI".format(_str_func))
    self.liveRecordBtn(e=True, label='Stop Recording Context', bgc=[.35,1,.35])

def uiFunc_load_selected(self, bypassAttrCheck = False):
    _str_func = 'uiFunc_load_selected'  
    self._mTransformTarget = False

    _sel = mc.ls(sl=True,type='transform')

    #Get our raw data
    if _sel:
        mNode = cgmMeta.validateObjArg(_sel[0])
        _short = mNode.p_nameBase            
        log.debug("|{0}| >> Target: {1}".format(_str_func, _short))
        self._mTransformTarget = mNode

        uiFunc_updateObjectDisplay(self.uiTF_objLoad, self._mTransformTarget)
    else:
        log.warning("|{0}| >> Nothing selected.".format(_str_func))            
        uiFunc_clear_loaded(self.uiTF_objLoad)

def uiFunc_clear_loaded(uiElement):
    _str_func = 'uiFunc_clear_loaded'  
    uiElement(edit=True, l='',en=False)      
     
def uiFunc_updateObjectDisplay(uiElement, mObj):
    _str_func = 'uiFunc_updateObjectDisplay'  

    if not object:
        log.info("|{0}| >> No target.".format(_str_func))                        
        #No obj
        #self.uiTF_objLoad(edit=True, l='',en=False)
        uiElement(edit=True, l='',en=False)

        return
    
    #_short = self._mTransformTarget.p_nameBase
    _short = mObj.p_nameBase
    uiElement(edit=True, ann=_short)
    
    if len(_short)>20:
        _short = _short[:20]+"..."
    uiElement(edit=True, l=_short)   
    
    uiElement(edit=True, en=True)
    
    return