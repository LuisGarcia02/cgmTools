"""
------------------------------------------
cgm.core.mrs.blocks.organic.eye
Author: Josh Burton
email: jjburton@cgmonks.com

Website : http://www.cgmonks.com
------------------------------------------

================================================================
"""
__MAYALOCAL = 'FACS'

# From Python =============================================================
import copy
import re
import pprint
import time
import os

#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

# From Maya =============================================================
import maya.cmds as mc

# From Red9 =============================================================
from Red9.core import Red9_Meta as r9Meta
import Red9.core.Red9_AnimationUtils as r9Anim
#r9Meta.cleanCache()#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< TEMP!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!


import cgm.core.cgm_General as cgmGEN
from cgm.core.rigger import ModuleShapeCaster as mShapeCast

import cgm.core.cgmPy.os_Utils as cgmOS
import cgm.core.cgmPy.path_Utils as cgmPATH
import cgm.core.mrs.assets as MRSASSETS
path_assets = cgmPATH.Path(MRSASSETS.__file__).up().asFriendly()

import cgm.core.mrs.lib.ModuleControlFactory as MODULECONTROL
#reload(MODULECONTROL)
from cgm.core.lib import curve_Utils as CURVES
import cgm.core.lib.rigging_utils as CORERIG
from cgm.core.lib import snap_utils as SNAP
import cgm.core.lib.attribute_utils as ATTR
import cgm.core.rig.joint_utils as JOINT
import cgm.core.classes.NodeFactory as NODEFACTORY
import cgm.core.lib.transform_utils as TRANS
import cgm.core.lib.distance_utils as DIST
import cgm.core.lib.position_utils as POS
import cgm.core.lib.math_utils as MATH
import cgm.core.rig.constraint_utils as RIGCONSTRAINT
import cgm.core.rig.general_utils as RIGGEN
import cgm.core.lib.constraint_utils as CONSTRAINT
import cgm.core.lib.locator_utils as LOC
import cgm.core.lib.rayCaster as RAYS
import cgm.core.lib.shape_utils as SHAPES
import cgm.core.mrs.lib.block_utils as BLOCKUTILS
import cgm.core.mrs.lib.builder_utils as BUILDERUTILS
import cgm.core.mrs.lib.shared_dat as BLOCKSHARE
import cgm.core.tools.lib.snap_calls as SNAPCALLS
import cgm.core.rig.ik_utils as IK
import cgm.core.cgm_RigMeta as cgmRIGMETA
import cgm.core.lib.nameTools as NAMETOOLS
import cgm.core.lib.surface_Utils as SURF
import cgm.core.lib.string_utils as STR
import cgm.core.rig.create_utils as RIGCREATE
import cgm.core.mrs.lib.post_utils as MRSPOST
import cgm.core.mrs.lib.blockShapes_utils as BLOCKSHAPES
import cgm.core.mrs.lib.facs_utils as FACSUTILS
#reload(BLOCKSHAPES)
#for m in DIST,POS,MATH,IK,CONSTRAINT,LOC,BLOCKUTILS,BUILDERUTILS,CORERIG,RAYS,JOINT,RIGCONSTRAINT,RIGGEN:
#    reload(m)
    
# From cgm ==============================================================
from cgm.core import cgm_Meta as cgmMeta

#=============================================================================================================
#>> Block Settings
#=============================================================================================================
__version__ = cgmGEN.__RELEASE
__autoForm__ = False
__menuVisible__ = True
__faceBlock__ = True

#These are our base dimensions. In this case it is for human
__dimensions_by_type = {'box':[22,22,22],
                        'human':[15.2, 23.2, 19.7]}

__l_rigBuildOrder__ = ['rig_dataBuffer',
                       'rig_skeleton',
                       'rig_shapes',
                       'rig_controls',
                       'rig_frame',
                       'rig_cleanUp']


d_wiring_skeleton = {'msgLinks':[],
                     'msgLists':['moduleJoints','skinJoints']}
d_wiring_prerig = {'msgLinks':['moduleTarget','prerigNull','noTransPrerigNull']}
d_wiring_form = {'msgLinks':['formNull','noTransFormNull'],
                     }
d_wiring_extraDags = {'msgLinks':['bbHelper'],
                      'msgLists':[]}

d_attrStateMask = {'define':['addEyeSqueeze',
                             'browSetup',
                             'browType',
                             'buildCenter',
                             'controlTemple',
                             'jointDepth',
    ],
                   'form':[ 'formBrowNum',
                            'formForeheadNum',
                            'numSplit_u',
                            'numSplit_v',
                       ],
                   'prerig':[
                    'conDirectOffset',
                    'controlOffset',
                    'numBrowControl',
                             ],
                   'skeleton':[ 'numBrowJoints',
                    ],
                   'rig':[
                   ]}


#>>>Profiles ==============================================================================================
d_build_profiles = {}


d_block_profiles = {'default':{'baseSize':[13.5,16.3,8.8],},
                    }

#>>>Attrs =================================================================================================
l_attrsStandard = ['side',
                   'position',
                   'attachPoint',
                   'attachIndex',
                   'nameList',
                   'loftDegree',
                   'loftSplit',
                   'scaleSetup',
                   'visLabels',
                   'jointRadius',
                   'jointDepth',
                   'controlOffset',
                   'conDirectOffset',
                   'ribbonAim',
                   'visProximityMode',
                   'moduleTarget']

d_attrsToMake = {'formForeheadNum':'int',
                 'formBrowNum':'int',
                 'numBrowJoints':'int',
                 'eyeSize':'float3',
                 'irisDepth':'float',
                 'pupilDepth':'float',
}

d_defaultSettings = {'version':__version__,
                     'attachPoint':'end',
                     'side':'none',
                     'loftDegree':'cubic',
                     'visLabels':True,
                     'formForeheadNum':1,
                     'formBrowNum':1,
                     'numBrowJoints':3,
                     'jointDepth':-.01,
                     'jointRadius':1.0,
                     'controlOffset':1,
                     'eyeSize':[3.4,3.4,3.4],
                     'pupilDepth':-.059,
                     'irisDepth':-.028,
                     #'baseSize':MATH.get_space_value(__dimensions[1]),
                     }

       
#=============================================================================================================
#>> Define
#=============================================================================================================
def create_defineHelpers(self, force = True):
    #>>Joint placers ================================================================================    
    _str_func = 'create_defineHelpers'
    mStateNull = self.defineNull
    
    #Joint placer aim....
    
    return
    #Clean up
    ml_jointHelpers = self.msgList_get('jointHelpers')
    if not force:
        return True

    
    #If we have existing, we want to save that result so we can try to match those changes 
    _targetCurve = None
 
    if ml_jointHelpers:
        _targetCurve = CORERIG.create_at(None, 'curveLinear',
                                                 l_pos = [mObj.p_position for mObj in ml_jointHelpers])
        for mJointHelper in ml_jointHelpers:
            try:mJointHelper
            except:continue
            bfr = mJointHelper.getMessage('mController')
            if bfr:
                log.warning("Deleting controller: {0}".format(bfr))
                mc.delete(bfr)        

        mc.delete([mObj.mNode for mObj in ml_jointHelpers])
        
    for k in ['jointHelpersGroup','jointHelpersNoTransGroup']:
        old = mPrerigNull.getMessage(k)
        if old:
            log.warning("Deleting old: {0}".format(old))
            mc.delete(old)
    
    old_loft = self.getMessage('jointLoftMesh')
    if old_loft:
        mc.delete(old_loft)
        
    
    ml_handles = self.msgList_get('prerigHandles')
    mNoTrans = self.noTransPrerigNull




@cgmGEN.Timer
def define(self):

    _str_func = 'define'    
    log.debug("|{0}| >>  ".format(_str_func)+ '-'*80)
    log.debug("{0}".format(self))
    _short = self.mNode
    
    #Attributes =========================================================
    ATTR.set_alias(_short,'sy','blockScale')    
    self.setAttrFlags(attrs=['sx','sz'])
    self.doConnectOut('sy',['sx','sz'])

    ATTR.set_min(_short, 'loftSplit', 1)
    
    
    #Cleaning =========================================================        
    _shapes = self.getShapes()
    if _shapes:
        log.debug("|{0}| >>  Removing old shapes...".format(_str_func))        
        mc.delete(_shapes)
        defineNull = self.getMessage('defineNull')
        if defineNull:
            log.debug("|{0}| >>  Removing old defineNull...".format(_str_func))
            mc.delete(defineNull)
    
    ml_handles = []
    
    #Make our handles creation data =======================================================
    d_pairs = {}
    d_creation = {}
    l_order = []
    d_curves = {}
    d_curveCreation = {}
    d_toParent = {}    
    
    #rigBlock Handle ===========================================================
    log.debug("|{0}| >>  RigBlock Handle...".format(_str_func))            
    _size = MATH.average(self.baseSize[1:])
    _crv = CURVES.create_fromName(name='locatorForm',#'axis3d',#'arrowsAxis', 
                                  direction = 'z+', size = _size/4)
    
    if self.jointRadius > _size/4:
        log.warning("|{0}| >> jointRadius too small. Reset".format(_str_func))   
        self.jointRadius = _size/4
        
        
    SNAP.go(_crv,self.mNode,)
    CORERIG.override_color(_crv, 'white')        
    CORERIG.shapeParent_in_place(self.mNode,_crv,False)
    mHandleFactory = self.asHandleFactory()
    self.addAttr('cgmColorLock',True,lock=True, hidden=True)
    mDefineNull = self.atUtils('stateNull_verify','define')
    
    mNoTransformNull = self.atUtils('noTransformNull_verify','define',forceNew=True,mVisLink=self)
    
    #Bounding Cube ==================================================================
    _bb_shape = CURVES.create_controlCurve(self.mNode,'cubeOpen', size = 1.0, sizeMode='fixed')
    mBBShape = cgmMeta.validateObjArg(_bb_shape, 'cgmObject',setClass=True)
    mBBShape.p_parent = mDefineNull    
    mBBShape.tz = -.5
    mBBShape.ty = .5
    
    
    CORERIG.copy_pivot(mBBShape.mNode,self.mNode)
    self.doConnectOut('baseSize', "{0}.scale".format(mBBShape.mNode))
    mHandleFactory.color(mBBShape.mNode,controlType='sub')
    mBBShape.setAttrFlags()
    
    mBBShape.doStore('cgmName', self)
    mBBShape.doStore('cgmType','bbVisualize')
    mBBShape.doName()    
    
    self.connectChildNode(mBBShape.mNode,'bbHelper')
    
    _d_pairs = {}
    _d = {}    
    _d_base = {'color':'yellowWhite','tagOnly':1,'arrow':0,'vectorLine':0}
    
    l_sideKeys = ['sideUprAnchor','eyeAnchor','jawCornerAnchor','nostrilAnchor',
                  'orbitFrontAnchor','cheekAnchor','lipAnchor'
                  ]

    for k in l_sideKeys:
        _d_pairs['L_'+k] = 'R_'+k

    d_pairs.update(_d_pairs)
    

    for k in 'top','brow','nose','mouth','bottom','chin','noseTop':
        _d[k+'Anchor'] = copy.copy(_d_base)
    
    #...build base dicts
    for k in l_sideKeys:
        _d['L_'+k] =  {'color':'blueWhite','tagOnly':1,'arrow':0,'vectorLine':0}
        _d['R_'+k] =  {'color':'redWhite','tagOnly':1,'arrow':0,'vectorLine':0}
        
    
    #We need to get our anchors for some processing help later
    l_anchors = _d.keys()
    #pprint.pprint(l_anchors)

    #Get poses
    _str_pose = 'default'

    
    _tmp = [.01,0,0]
    size_locForm = self.jointRadius * 2.0
    
    reload(FACSUTILS)
    d_defineScaleSpace = FACSUTILS.d_defineScaleSpace
    
    for k,d in _d.iteritems():
        if 'Anchor' in k:
            _d[k]['shape'] = 'defineAnchor'
            #_d[k]['size'] = size_locForm
        else:
            _d[k]['jointScale'] = 1
            _d[k]['jointLabel'] = 1
            #_d[k]['size'] = size_locForm
            
        if 'eye' in k:
            _d[k]['jointScale'] = False
        #else:
            #_d[k]['jointScale'] = 1
            
        _v = None
        if 'L_' in k:
            k_use = str(k).replace('L_','R_')
            _v = copy.copy(d_defineScaleSpace[_str_pose].get(k_use))
            if _v:
                _v[0] = -1 * _v[0]
        else:
            _v = d_defineScaleSpace[_str_pose].get(k)
            
        if _v is not None:
            _d[k]['scaleSpace'] = _v
        else:
            _d[k]['scaleSpace'] = _tmp
            _tmp = [v * 1.1 for v in _tmp]
            
    #Set directions for our anchor casts....................
    _d['L_jawCornerAnchor']['anchorDir'] = 'x+'
    _d['R_jawCornerAnchor']['anchorDir'] = 'x-'
    _d['R_sideUprAnchor']['anchorDir'] = 'x-'
    _d['L_sideUprAnchor']['anchorDir'] = 'x+'
    
    
    _keys = _d.keys()
    _keys.sort()
    l_order.extend(_keys)
    d_creation.update(_d)

        
        
    #make em...============================================================
    log.debug(cgmGEN.logString_sub(_str_func,'Make handles'))

    md_res = self.UTILS.create_defineHandles(self, l_order, d_creation, self.jointRadius, mDefineNull, mBBShape,
                                             forceSize=1)

    md_handles = md_res['md_handles']
    ml_handles = md_res['ml_handles']
    
    
    for k,p in d_toParent.iteritems():
        md_handles[k].p_parent = md_handles[p]
        

    
    #Parent setup.....=============================================================================
    #                  'lidInnerOut','lidInner','lidUpr','lidUprOut','lidOuter','lidOuterOut','lidLwr','lidLwrOut',
"""
    d_contraints = {'L_nostrilAnchor':['noseAnchor'],
                    'L_cheekAnchor':['L_lipAnchor','L_jawCornerAnchor'],
                    'L_lipAnchor':['mouthAnchor'],
                    'L_orbitFrontAnchor':['noseAnchor','L_sideUprAnchor'],
                    }"""
    
    d_contraints = {}
    
    for k,l in d_contraints.iteritems():
        if k.startswith('L_'):
            k_use = str(k).replace('L_','R_')
            l_use = []
            for i,k2 in enumerate(l):
                if k2.startswith('L'):
                    l_use.append(str(k2).replace('L_','R_'))
                else:
                    l_use.append(k2)
                    
            mGroup = md_handles[k_use].doGroup(True,True,asMeta=True,typeModifier = 'track',setClass='cgmObject')
            RIGCONSTRAINT.byDistance(mGroup,[md_handles[n] for n in l_use],
                                     mc.parentConstraint,maxUse=3,maintainOffset=1)            
            #after the other side, do the original
            k_use = k
            l_use = l
        else:
            k_use = k
            l_use = l            
            
        mGroup = md_handles[k_use].doGroup(True,True,asMeta=True,typeModifier = 'track',setClass='cgmObject')
        RIGCONSTRAINT.byDistance(mGroup,[md_handles[n] for n in l_use],
                                 mc.parentConstraint,maxUse=3,maintainOffset=1)
    
        

    #Eye orbs -------------------------------------------------------------
    ml_l_eyeBits = BLOCKSHAPES.eyeOrb(self,md_handles['L_eyeAnchor'],mDefineNull, 'left') 
    ml_r_eyeBits = BLOCKSHAPES.eyeOrb(self,md_handles['R_eyeAnchor'],mDefineNull, 'right') 
    
    
    #Tag for mirror
    for i,mObj in enumerate(ml_l_eyeBits):
        l_tag = mObj.handleTag
        r_tag = ml_r_eyeBits[i].handleTag
        md_handles[l_tag] = mObj
        md_handles[r_tag] = ml_r_eyeBits[i]
        
        d_pairs[l_tag] = r_tag
        
        
        ml_handles.extend([mObj,  ml_r_eyeBits[i]])


    #Mirror setup...
    idx_ctr = 0
    idx_side = 0
    d = {}
        
    for tag,mHandle in md_handles.iteritems():
        mHandle._verifyMirrorable()
        _center = True
        for p1,p2 in d_pairs.iteritems():
            if p1 == tag or p2 == tag:
                _center = False
                break
        if _center:
            log.debug("|{0}| >>  Center: {1}".format(_str_func,tag))    
            mHandle.mirrorSide = 0
            mHandle.mirrorIndex = idx_ctr
            idx_ctr +=1
        mHandle.mirrorAxis = "translateX,rotateY,rotateZ"

    #Self mirror wiring -------------------------------------------------------
    for k,m in d_pairs.iteritems():
        md_handles[k].mirrorSide = 1
        md_handles[m].mirrorSide = 2
        md_handles[k].mirrorIndex = idx_side
        md_handles[m].mirrorIndex = idx_side
        md_handles[k].doStore('mirrorHandle',md_handles[m])
        md_handles[m].doStore('mirrorHandle',md_handles[k])
        idx_side +=1
        
    
    #Curves -------------------------------------------------------------------------
    log.debug("|{0}| >>  Make the curves...".format(_str_func))    
    md_resCurves = self.UTILS.create_defineCurve(self, d_curveCreation, md_handles, mNoTransformNull)
    self.msgList_connect('defineHandles',ml_handles)#Connect    
    #self.msgList_connect('defineSubHandles',ml_handles)#Connect
    self.msgList_connect('defineCurves',md_resCurves['ml_curves'])#Connect    
    
    md_curves = md_resCurves['md_curves']

    self.atUtils('controller_wireHandles',ml_handles,'define')
    return    
    
    
@cgmGEN.Timer
def defineBAK(self):
    d_defineScaleSpace = {'default':
                          {'R_browPeak_1': [-0.6713813499168115, 0.9811429697261111, 0.7239851128566311],
                           'R_browPeak_2': [-0.975582829228154,
                                            0.9292462342880228,
                                            -0.06630732811499518],
                           'R_brow_1': [-0.296678964755179, 0.6238101968178427, 1.2374333510236672],
                           'R_brow_2': [-0.6746586671748838, 0.6913925936975538, 0.9779912439843487],
                           'R_brow_3': [-0.8558618735550918, 0.6319769257756214, 0.6039768744968966],
                           'R_cheek': [-0.7937258239312499, -0.44134881404749393, 0.022774813563396945],
                           'R_cheekBack': [-1.08435503422675, 0.43200252871429257, -0.6647092625142361],
                           'R_cheekBone': [-0.9143956999602136,
                                           0.24937447365068266,
                                           0.19019182674534496],
                           'R_cheekFront': [-0.5800084295648364,
                                            0.05741114299616967,
                                            0.8169812818855758],
                           'R_cheekStart': [-0.6368880779821756,
                                            -0.5427476846630199,
                                            0.4622318304333529],
                           'R_chin': [-0.25934176974826384, -0.8201580995359059, 0.9731667681946202],
                           'R_earBottom': [-1.0783174987359372,
                                           -0.08624026718275957,
                                           -1.1995763804639146],
                           'R_earTop': [-1.1444148995425054, 0.3383959382276842, -1.0766615134510857],
                           'R_eyeAnchor': [-0.4664454973461831, 0.47394849201335276, 0.7477437370602481],
                           'R_jawCorner': [-0.9464050575538916,
                                           -0.3362372832936451,
                                           -1.0808767755983735],
                           'R_jawCornerAnchor': [-0.9464050575538916,
                                                 -0.3362372832936522,
                                                 -1.0808767755983735],
                           'R_jawFront': [-0.22414094211339675, -0.9932620486371135, 0.9227802213301418],
                           'R_jawUnder_1': [-0.6084799628382235,
                                            -0.8575730265172474,
                                            -0.5922238117367802],
                           'R_jawUnder_2': [-0.8602593133718259,
                                            -0.5542119790345517,
                                            -0.9519401543910275],
                           'R_jaw_1': [-0.5129767929405813, -0.799138414526972, 0.44464076618810855],
                           'R_jaw_2': [-0.7583590591562204, -0.6851224906224651, -0.15981019430820897],
                           'R_lidInner': [-0.3029570402922454, 0.4379300536754265, 0.6502626218897133],
                           'R_lidInnerOut': [-0.17672672978153947,
                                             0.4010449717869733,
                                             0.8413789507551926],
                           'R_lidLwr': [-0.528255603931568, 0.3865406964004521, 0.761007182505414],
                           'R_lidLwrOut': [-0.5361562658239293, 0.29866878972810085, 0.7135321923428891],
                           'R_lidOuter': [-0.6834834063494648, 0.45642595357777793, 0.6259167259566035],
                           'R_lidOuterOut': [-0.8220553927951387,
                                             0.4474897322766367,
                                             0.44154265761781863],
                           'R_lidUpr': [-0.48907145747431974, 0.5309936933601627, 0.8057133744200101],
                           'R_lidUprOut': [-0.4616043302747938, 0.6001000969734065, 0.8295343160021503],
                           'R_lipCorner': [-0.4074539939729345,
                                           -0.44691686813288456,
                                           0.8986685174598822],
                           'R_lipLwr': [-0.1939219722041378, -0.4840284915627855, 1.156996808696518],
                           'R_lipLwrBow': [-0.20427816885489, -0.6463295919508738, 1.0599307551557264],
                           'R_lipUpr': [-0.2116789641203703, -0.3935036149378277, 1.2114921421406075],
                           'R_neckCorner': [-0.8920030947084769,
                                            -0.7911289540772977,
                                            -1.4124202221274262],
                           'R_neckMid': [-0.6323231569209775, -1.181091197933835, -0.7744271466924437],
                           'R_noseBase': [-0.1407631922818084, -0.12837699389620028, 1.1843442536774735],
                           'R_noseBulb': [-0.13180994104456017, 0.00568692030633855, 1.5574745561698498],
                           'R_noseTop': [-0.09675033004195596, 0.42509394782153365, 1.1257566062097903],
                           'R_nostril': [-0.2709846143369321, -0.019148398268864497, 1.013497870905451],
                           'R_orbitOuter': [-0.9255948718732344,
                                            0.5201796111822112,
                                            0.09738985697345848],
                           'R_sideUprAnchor': [-1.1426325694896555,
                                               0.696103159964828,
                                               -0.9285849108478661],
                           'R_smileEnd': [-0.21037468867734357, 0.13608123598588762, 1.0490191715774957],
                           'R_smilePeak': [-0.41305022550414827,
                                           -0.017416572435340782,
                                           0.949934146203799],
                           'R_smileStart': [-0.5377998777885903,
                                            -0.4949121747497003,
                                            0.7585009932005266],
                           'R_sneer': [-0.24955410427517394, 0.2848984340461591, 0.9255073287535355],
                           'R_temple': [-1.1636325694896543, 0.6961031599648067, -0.9285849108478661],
                           'bottomAnchor': [-2.697495005143935e-16,
                                            -1.3264335108621275,
                                            -0.1506813856165703],
                           'browAnchor': [5.117434254131581e-17, 0.5699139046335482, 1.2618197021681716],
                           'browLwr': [5.204170427930421e-17, 0.5699139046335446, 1.2618197021681716],
                           'browPeak': [5.204170427930421e-18, 0.9749907754676599, 1.1631904897590082],
                           'chinAnchor': [2.6107588313450947e-16,
                                          -1.0324481185790013,
                                          0.9537196153513007],
                           'mouthAnchor': [1.5005358067199381e-16,
                                           -0.4269899985046166,
                                           1.145336506112777],
                           'neckJawMeet': [-2.714842239903703e-16,
                                           -1.014360367900128,
                                           -0.04835207949806697],
                           'neckLwr': [-2.706168622523819e-16, -1.3264335108621168, -0.1506813856165703],
                           'noseAnchor': [1.3530843112619095e-16,
                                          -0.1508926019765262,
                                          1.229154623585953],
                           'noseTip': [0.0042287310131365755, 0.001197278848103167, 1.6898677076170099],
                           'noseTopAnchor': [5.117434254131581e-17,
                                             0.3999999999999986,
                                             1.2618197021681716],
                           'topAnchor': [4.336808689942018e-18, 0.9749907754676599, 1.1631904897590046]}
                     
                     
                     }

    
    _str_func = 'define'    
    log.debug("|{0}| >>  ".format(_str_func)+ '-'*80)
    log.debug("{0}".format(self))
    
    _short = self.mNode
    
    #Attributes =========================================================
    ATTR.set_alias(_short,'sy','blockScale')    
    self.setAttrFlags(attrs=['sx','sz'])
    self.doConnectOut('sy',['sx','sz'])

    ATTR.set_min(_short, 'loftSplit', 1)
    
    
    #Cleaning =========================================================        
    _shapes = self.getShapes()
    if _shapes:
        log.debug("|{0}| >>  Removing old shapes...".format(_str_func))        
        mc.delete(_shapes)
        defineNull = self.getMessage('defineNull')
        if defineNull:
            log.debug("|{0}| >>  Removing old defineNull...".format(_str_func))
            mc.delete(defineNull)
    
    ml_handles = []
    
    #Make our handles creation data =======================================================
    d_pairs = {}
    d_creation = {}
    l_order = []
    d_curves = {}
    d_curveCreation = {}
    d_toParent = {}    
    
    #rigBlock Handle ===========================================================
    log.debug("|{0}| >>  RigBlock Handle...".format(_str_func))            
    _size = MATH.average(self.baseSize[1:])
    _crv = CURVES.create_fromName(name='locatorForm',#'axis3d',#'arrowsAxis', 
                                  direction = 'z+', size = _size/4)
    
    if self.jointRadius > _size/4:
        log.warning("|{0}| >> jointRadius too small. Reset".format(_str_func))   
        self.jointRadius = _size/4
        
        
    SNAP.go(_crv,self.mNode,)
    CORERIG.override_color(_crv, 'white')        
    CORERIG.shapeParent_in_place(self.mNode,_crv,False)
    mHandleFactory = self.asHandleFactory()
    self.addAttr('cgmColorLock',True,lock=True, hidden=True)
    mDefineNull = self.atUtils('stateNull_verify','define')
    
    mNoTransformNull = self.atUtils('noTransformNull_verify','define',forceNew=True,mVisLink=self)
    
    #Bounding Cube ==================================================================
    _bb_shape = CURVES.create_controlCurve(self.mNode,'cubeOpen', size = 1.0, sizeMode='fixed')
    mBBShape = cgmMeta.validateObjArg(_bb_shape, 'cgmObject',setClass=True)
    mBBShape.p_parent = mDefineNull    
    mBBShape.tz = -.5
    mBBShape.ty = .5
    
    
    CORERIG.copy_pivot(mBBShape.mNode,self.mNode)
    self.doConnectOut('baseSize', "{0}.scale".format(mBBShape.mNode))
    mHandleFactory.color(mBBShape.mNode,controlType='sub')
    mBBShape.setAttrFlags()
    
    mBBShape.doStore('cgmName', self)
    mBBShape.doStore('cgmType','bbVisualize')
    mBBShape.doName()    
    
    self.connectChildNode(mBBShape.mNode,'bbHelper')
    
    _d_pairs = {}
    _d = {}    
    _d_base = {'color':'yellowWhite','tagOnly':1,'arrow':0,'vectorLine':0}
    
    l_sideKeys = ['sideUprAnchor','eyeAnchor','jawCornerAnchor',
                  'browPeak_1','browPeak_2',
                  'brow_1','brow_2','brow_3',
                  'orbitOuter',
                  'temple',
                  'noseTop','noseBulb','nostril','sneer','noseBase',
                  
                  'lidInnerOut','lidInner','lidUpr','lidUprOut','lidOuter','lidOuterOut','lidLwr','lidLwrOut',
                  
                  'lipLwrBow','lipLwr','lipCorner','lipUpr',
                  
                  'smileStart','smilePeak','smileEnd',
                  'cheek','cheekFront','cheekBone','cheekBack','cheekStart','chin','jawCorner','jaw_1','jaw_2','neckMid','neckCorner',
                  
                  'jawUnder_1','jawUnder_2',
                  
                  'earTop','earBottom',
                  'jawFront',
                  ]

    for k in l_sideKeys:
        _d_pairs['L_'+k] = 'R_'+k

    d_pairs.update(_d_pairs)
    
    
    
    for k in 'top','brow','nose','mouth','bottom','chin','noseTop':
        _d[k+'Anchor'] = copy.copy(_d_base)
        
    for k in 'browLwr','browPeak','neckLwr','neckJawMeet','noseTip':
        _d[k] = copy.copy(_d_base)    
    
    #...build base dicts
    for k in l_sideKeys:
        _d['L_'+k] =  {'color':'blueWhite','tagOnly':1,'arrow':0,'vectorLine':0}
        _d['R_'+k] =  {'color':'redWhite','tagOnly':1,'arrow':0,'vectorLine':0}
        
    
    #We need to get our anchors for some processing help later
    l_anchors = _d.keys()
    #pprint.pprint(l_anchors)


    #Get poses
    _str_pose = 'default'

    
    
    _tmp = [.01,0,0]
    size_locForm = self.jointRadius * 2.0
    
    for k,d in _d.iteritems():
        if 'Anchor' in k:
            _d[k]['shape'] = 'defineAnchor'
            _d[k]['size'] = size_locForm
        else:
            _d[k]['jointScale'] = 1
            _d[k]['jointLabel'] = 1
            #_d[k]['size'] = size_locForm
            
            
        if 'eye' in k:
            _d[k]['jointScale'] = False
            
        
        _v = None
        if 'L_' in k:
            k_use = str(k).replace('L_','R_')
            _v = copy.copy(d_defineScaleSpace[_str_pose].get(k_use))
            if _v:
                _v[0] = -1 * _v[0]
        else:
            _v = d_defineScaleSpace[_str_pose].get(k)
            
        if _v is not None:
            _d[k]['scaleSpace'] = _v
        else:
            _d[k]['scaleSpace'] = _tmp
            _tmp = [v * 1.1 for v in _tmp]
            
    #Set directions for our anchor casts....................
    _d['L_jawCornerAnchor']['anchorDir'] = 'x+'
    _d['R_jawCornerAnchor']['anchorDir'] = 'x-'
    _d['R_sideUprAnchor']['anchorDir'] = 'x-'
    _d['L_sideUprAnchor']['anchorDir'] = 'x+'
    
    
    _keys = _d.keys()
    _keys.sort()
    l_order.extend(_keys)
    d_creation.update(_d)

    #pprint.pprint(d_creation)
    
    #'asdf':{'keys':[],'rebuild':0},
    
    _d_curveCreation = {
        'browLine':{'keys':['R_orbitOuter', 'R_brow_3', 'R_brow_2', 'R_brow_1', 'browLwr', 'L_brow_1', 'L_brow_2', 'L_brow_3', 'L_orbitOuter']
,'rebuild':0},
        'peakLine':{'keys':['R_temple', 'R_browPeak_2', 'R_browPeak_1', 'browPeak', 'L_browPeak_1', 'L_browPeak_2', 'L_temple'],'rebuild':0},
        
        'cheekLine':{'keys':['R_cheekBack', 'R_cheekBone', 'R_cheekFront', 'R_sneer', 'R_noseTop', 'L_noseTop', 'L_sneer', 'L_cheekFront', 'L_cheekBone', 'L_cheekBack']
,
                     'rebuild':0},
        
        
        'jaw':{'keys':['R_earBottom', 'R_jawCorner', 'R_jaw_2', 'R_jaw_1', 'R_jawFront',
                       'L_jawFront', 'L_jaw_1', 'L_jaw_2', 'L_jawCorner','L_earBottom',]
               ,'rebuild':0},
        'jawUnder':{'keys':['R_earBottom', 'R_jawUnder_2', 'R_jawUnder_1', 'neckJawMeet',
                            'L_jawUnder_1', 'L_jawUnder_2', 'L_earBottom']

               ,'rebuild':0},        
        
        
        
        
        'uprLip':{'keys':['R_earBottom', 'R_cheek','R_cheekStart', 'R_smileStart', 'R_lipCorner', 'R_lipUpr', 'L_lipUpr', 'L_lipCorner', 'L_smileStart', 'L_cheekStart', 'L_cheek','L_earBottom']
,'rebuild':0},
        'lwrLip':{'keys':['R_lipCorner', 'R_lipLwr', 'L_lipLwr', 'L_lipCorner']

,'rebuild':0},
        'noseUnder':{'keys':['R_nostril', 'R_noseBase','noseAnchor','L_noseBase', 'L_nostril'],'rebuild':0},
        
        'smileLine':{'keys':['R_smileEnd', 'R_smilePeak', 'R_smileStart', 'R_chin', 'L_chin', 'L_smileStart', 'L_smilePeak', 'L_smileEnd']
,
                     'rebuild':0},

        'noseOver':{'keys':['R_nostril', 'R_smileEnd', 'R_noseBulb', 'noseTip', 'L_noseBulb', 'L_smileEnd', 'L_nostril']
,'rebuild':0},
        'mouthTrace':{'keys':['R_sneer', 'R_smileEnd', 'R_nostril', 'R_lipCorner', 'R_lipLwrBow', 'L_lipLwrBow', 'L_lipCorner', 'L_nostril', 'L_smileEnd', 'L_sneer']

,'rebuild':0},
        'faceTrace':{'keys':['R_temple', 'R_earTop', 'R_earBottom', 'R_neckCorner', 'R_neckMid', 'neckLwr', 'L_neckMid', 'L_neckCorner', 'L_earBottom', 'L_earTop', 'L_temple']

,'rebuild':0},
        
        'neckLwrLidTrace':{'keys':['R_neckMid', 'R_jawUnder_1', 'R_jaw_2', 'R_cheek', 'R_cheekBone', 'R_lidOuterOut', 'R_lidLwrOut', 'R_lidInnerOut', 'R_noseTop', 'L_noseTop', 'L_lidInnerOut', 'L_lidLwrOut', 'L_lidOuterOut','L_cheekBone','L_cheek', 'L_jaw_2', 'L_jawUnder_1', 'L_neckMid']
,'rebuild':0},
        
        'L_noseLine':{'keys':['L_brow_1', 'L_noseTop', 'L_noseBulb', 'L_noseBase', 'L_lipUpr', 'L_lipLwr', 'L_lipLwrBow']

,'rebuild':0},

        'L_lid':{'keys':['L_lidInner','L_lidUpr', 'L_lidOuter', 'L_lidLwr', 'L_lidInner'],'rebuild':0},
        'L_eyeToNeck':{'keys':['L_lidLwr', 'L_lidLwrOut', 'L_cheekFront', 'L_cheekStart', 'L_jaw_1', 'L_jawFront']
,'rebuild':0},
        
        
        
        'R_noseLine':{'keys':['R_brow_1', 'R_noseTop', 'R_noseBulb', 'R_noseBase', 'R_lipUpr', 'R_lipLwr', 'R_lipLwrBow']

,'rebuild':0},

        'R_lid':{'keys':['R_lidInner','R_lidUpr', 'R_lidOuter', 'R_lidLwr', 'R_lidInner'],'rebuild':0},
        'R_eyeToNeck':{'keys':['R_lidLwr', 'R_lidLwrOut', 'R_cheekFront', 'R_cheekStart', 'R_jaw_1', 'R_jawFront']
,'rebuild':0},
        
        }
    d_curveCreation.update(_d_curveCreation)
    
    
    #pprint.pprint(vars())
        
        
    #make em...============================================================
    log.debug(cgmGEN.logString_sub(_str_func,'Make handles'))
    #for tag,d in d_creation.iteritems():
        #d_creation[tag]['jointScale'] = True
    
    #self,l_order,d_definitions,baseSize,mParentNull = None, mScaleSpace = None, rotVecControl = False,blockUpVector = [0,1,0] 
    md_res = self.UTILS.create_defineHandles(self, l_order, d_creation, self.jointRadius, mDefineNull, mBBShape,
                                             forceSize=1)

    md_handles = md_res['md_handles']
    ml_handles = md_res['ml_handles']
    
    
    for k,p in d_toParent.iteritems():
        md_handles[k].p_parent = md_handles[p]
        
        
    #Eye orbs -------------------------------------------------------------
    BLOCKSHAPES.eyeOrb(self,md_handles['L_eyeAnchor'],mDefineNull, 'left') 
    BLOCKSHAPES.eyeOrb(self,md_handles['R_eyeAnchor'],mDefineNull, 'right') 
    
    
    
    #Parent setup.....=============================================================================
    #                  'lidInnerOut','lidInner','lidUpr','lidUprOut','lidOuter','lidOuterOut','lidLwr','lidLwrOut',

    d_contraints = {'browPeak':['topAnchor'],
                    'L_browPeak_1':['topAnchor','L_sideUprAnchor'],
                    'L_browPeak_2':['topAnchor','L_sideUprAnchor'],
                    'L_temple':['L_sideUprAnchor'],
                    
                    'browLwr':['browAnchor'],
                    'L_brow_1':['browAnchor'],
                    'L_brow_2':['browAnchor','L_sideUprAnchor','L_eyeAnchor'],
                    'L_brow_3':['browAnchor','L_sideUprAnchor','L_eyeAnchor'],
                    'L_orbitOuter':['browAnchor','L_sideUprAnchor','L_eyeAnchor'],
                    
                    'L_noseTop':['noseTopAnchor'],
                    'L_sneer':['noseTopAnchor','L_eyeAnchor'],
                    
                    'L_noseBulb':['noseAnchor'],
                    'L_nostril':['noseAnchor'],
                    
                    'L_noseBase':['noseAnchor'],
                    'noseTip':['noseAnchor'],
                    
                    'L_earTop':['L_sideUprAnchor','L_jawCornerAnchor'],
                    'L_earBottom':['L_jawCornerAnchor'],
                    
                    
                    'neckJawMeet':['bottomAnchor','chinAnchor'],
                    'L_jawUnder_1':['bottomAnchor','chinAnchor'],
                    'L_jawUnder_2':['bottomAnchor','L_jawCornerAnchor'],
                    
                    'L_lidInnerOut':['L_eyeAnchor', 'noseTopAnchor'],
                    'L_lidInner':['L_eyeAnchor'],
                    'L_lidUpr':['L_eyeAnchor'],
                    'L_lidUprOut':['L_eyeAnchor'],
                    'L_lidOuter':['L_eyeAnchor'],
                    'L_lidOuterOut':['L_eyeAnchor'],
                    'L_lidLwr':['L_eyeAnchor'],
                    'L_lidLwrOut':['L_eyeAnchor'],
                    
                    
                    'L_lipLwrBow':['mouthAnchor','chinAnchor'],
                    'L_lipLwr':['mouthAnchor'],
                    'L_lipCorner':['mouthAnchor'],
                    'L_lipUpr':['mouthAnchor'],                    


                    'neckLwr':['bottomAnchor'],
                    'L_jawFront':['chinAnchor'],
                    
                    
                    'L_cheekFront':['mouthAnchor','noseAnchor','L_jawCornerAnchor'],
                    'L_cheekBone':['L_eyeAnchor','L_sideUprAnchor'],
                    'L_cheekBack':['L_sideUprAnchor','L_jawCornerAnchor'],
                    'L_cheekStart':['mouthAnchor','L_jawCornerAnchor'],
                    'L_cheek':['mouthAnchor','L_jawCornerAnchor'],
                    
                    'L_smileStart':['mouthAnchor'],
                    'L_smilePeak':['mouthAnchor','noseAnchor',],
                    'L_smileEnd':['noseAnchor'],
                    
                    'L_chin':['chinAnchor'],
                    'L_jawCorner':['L_jawCornerAnchor'],
                    'L_jaw_1':['L_jawCornerAnchor','chinAnchor'],
                    'L_jaw_2':['L_jawCornerAnchor','chinAnchor'],
                    'L_neckMid':['L_jawCornerAnchor','bottomAnchor'],
                    'L_neckCorner':['L_jawCornerAnchor']                    
                    
                    
    }
    
    for k,l in d_contraints.iteritems():
        if k.startswith('L_'):
            k_use = str(k).replace('L_','R_')
            l_use = []
            for i,k2 in enumerate(l):
                if k2.startswith('L'):
                    l_use.append(str(k2).replace('L_','R_'))
                else:
                    l_use.append(k2)
                    
            mGroup = md_handles[k_use].doGroup(True,True,asMeta=True,typeModifier = 'track',setClass='cgmObject')
            RIGCONSTRAINT.byDistance(mGroup,[md_handles[n] for n in l_use],
                                     mc.parentConstraint,maxUse=3,maintainOffset=1)            
            #after the other side, do the original
            k_use = k
            l_use = l
        else:
            k_use = k
            l_use = l            
            
        mGroup = md_handles[k_use].doGroup(True,True,asMeta=True,typeModifier = 'track',setClass='cgmObject')
        RIGCONSTRAINT.byDistance(mGroup,[md_handles[n] for n in l_use],
                                 mc.parentConstraint,maxUse=3,maintainOffset=1)
    
        

    #Mirror setup...
    idx_ctr = 0
    idx_side = 0
    d = {}
        
    for tag,mHandle in md_handles.iteritems():
        mHandle._verifyMirrorable()
        _center = True
        for p1,p2 in d_pairs.iteritems():
            if p1 == tag or p2 == tag:
                _center = False
                break
        if _center:
            log.debug("|{0}| >>  Center: {1}".format(_str_func,tag))    
            mHandle.mirrorSide = 0
            mHandle.mirrorIndex = idx_ctr
            idx_ctr +=1
        mHandle.mirrorAxis = "translateX,rotateY,rotateZ"

    #Self mirror wiring -------------------------------------------------------
    for k,m in d_pairs.iteritems():
        md_handles[k].mirrorSide = 1
        md_handles[m].mirrorSide = 2
        md_handles[k].mirrorIndex = idx_side
        md_handles[m].mirrorIndex = idx_side
        md_handles[k].doStore('mirrorHandle',md_handles[m])
        md_handles[m].doStore('mirrorHandle',md_handles[k])
        idx_side +=1
        
    
    #Curves -------------------------------------------------------------------------
    log.debug("|{0}| >>  Make the curves...".format(_str_func))    
    md_resCurves = self.UTILS.create_defineCurve(self, d_curveCreation, md_handles, mNoTransformNull)
    self.msgList_connect('defineHandles',ml_handles)#Connect    
    self.msgList_connect('defineSubHandles',ml_handles)#Connect
    self.msgList_connect('defineCurves',md_resCurves['ml_curves'])#Connect    
    
    md_curves = md_resCurves['md_curves']

    self.atUtils('controller_wireHandles',ml_handles,'define')
    return    
    
    
 
 

#=============================================================================================================
#>> Form
#=============================================================================================================
def mirror_self(self,primeAxis = 'Left'):
    _str_func = 'mirror_self'
    _idx_state = self.blockState
    
    log.debug("|{0}| >> define...".format(_str_func)+ '-'*80)
    ml_mirrorHandles = self.msgList_get('defineHandles')
    r9Anim.MirrorHierarchy().makeSymmetrical([mObj.mNode for mObj in ml_mirrorHandles],
                                             mode = '',primeAxis = primeAxis.capitalize() )        

    if _idx_state > 0:
        log.debug("|{0}| >> form...".format(_str_func)+ '-'*80)
        ml_mirrorHandles = self.msgList_get('formHandles')
        r9Anim.MirrorHierarchy().makeSymmetrical([mObj.mNode for mObj in ml_mirrorHandles],
                                                     mode = '',primeAxis = primeAxis.capitalize() )
    if _idx_state > 1:
        log.debug("|{0}| >> prerig...".format(_str_func)+ '-'*80)        
        ml_mirrorHandles = self.msgList_get('prerigHandles')
        r9Anim.MirrorHierarchy().makeSymmetrical([mObj.mNode for mObj in ml_mirrorHandles],
                                                 mode = '',primeAxis = primeAxis.capitalize() )        
    

def mirror_form(self,primeAxis = 'Left'):
    _str_func = 'mirror_form'    
    log.debug("|{0}| >>  ".format(_str_func)+ '-'*80)
    log.debug("{0}".format(self))
    
    ml_mirrorHandles = self.msgList_get('formHandles')
    
    r9Anim.MirrorHierarchy().makeSymmetrical([mObj.mNode for mObj in ml_mirrorHandles],
                                             mode = '',primeAxis = primeAxis.capitalize() )
    
def mirror_prerig(self,primeAxis = 'Left'):
    _str_func = 'mirror_form'    
    log.debug("|{0}| >>  ".format(_str_func)+ '-'*80)
    log.debug("{0}".format(self))
    
    ml_mirrorHandles = self.msgList_get('prerigHandles')
    
    r9Anim.MirrorHierarchy().makeSymmetrical([mObj.mNode for mObj in ml_mirrorHandles],
                                             mode = '',primeAxis = primeAxis.capitalize() )    

def formDelete(self):
    _str_func = 'formDelete'
    log.debug("|{0}| >> ...".format(_str_func)+ '-'*80)
    log.debug("{0}".format(self))
    ml_defSubHandles = self.msgList_get('defineSubHandles')
    for mObj in ml_defSubHandles:
        mObj.template = False    
        mObj.v=1
        
    for mObj in self.msgList_get('defineCurves'):
        mObj.template=0
        mObj.v=1
            
    try:self.defineLoftMesh.template = False
    except:pass
    self.bbHelper.v = True
    
@cgmGEN.Timer
def form(self):
    _str_func = 'form'
    log.debug("|{0}| >>  ".format(_str_func)+ '-'*80)
    log.debug("{0}".format(self))
    
    _short = self.p_nameShort
    _baseNameAttrs = ATTR.datList_getAttrs(self.mNode,'nameList')
    
    #Initial checks ===============================================================================
    log.debug("|{0}| >> Initial checks...".format(_str_func)+ '-'*40)    

    #Create temple Null  ==================================================================================
    mFormNull = BLOCKUTILS.formNull_verify(self)
    mNoTransformNull = self.atUtils('noTransformNull_verify','form')
    
    mHandleFactory = self.asHandleFactory()
    
    self.bbHelper.v = False
    _size = MATH.average(self.baseSize[1:]) * .2
    
    d_handleTags = {}
    md_loftCurves = {}
    md_curves = []
    
    #Brow Handles  ==================================================================================
    log.debug("|{0}| >> Brow Handles...".format(_str_func)+ '-'*40)

    
    if self.browType >=0:#Full brow
        log.debug("|{0}| >>  Full Brow...".format(_str_func))
        
        #Gather all our define dhandles and curves -----------------------------
        log.debug("|{0}| >> Get our define curves/handles...".format(_str_func)+ '-'*40)    

        md_handles = {}
        md_dCurves = {}
        d_defPos = {}
        
        ml_defineHandles = self.msgList_get('defineSubHandles')
        for mObj in ml_defineHandles:
            md_handles[mObj.handleTag] = mObj
            d_defPos[mObj.handleTag] = mObj.p_position
            mObj.v=0
            
        for mObj in self.msgList_get('defineCurves'):
            md_dCurves[mObj.handleTag] = mObj
            mObj.template=1
            mObj.v=0
        
        #
        d_pairs = {}
        d_creation = {}
        l_order = []
        d_curveCreation = {}
        ml_subHandles = []
        md_loftCreation = {}
        d_curveKeys = {}
        l_curveKeys = []
        d_sections = {'brow':{'crvs':['baseLine','browLine'],
                              'numAttr':'formBrowNum'},
                      'fore':{'crvs':['browLine','peakLine'],
                              'numAttr':'formForeheadNum'}}
        
        _done = []
        
        d_sectionPos = {}
        for iii,section in enumerate(['brow','fore']):
            log.debug(cgmGEN.logString_sub(_str_func,section + '...'))
            #We need to get positions lists per line
            l_posLists = []
            _d_section = d_sections[section]
            
            _res_tmp = mc.loft([md_dCurves[k].mNode for k in _d_section['crvs']],
                               o = True, d = 1, po = 0, c = False,u=False, autoReverse=0,ch=True)
                                
            str_meshShape = TRANS.shapes_get(_res_tmp[0])[0]
            l_knots = SURF.get_dat(str_meshShape, uKnots=True)['uKnots']
            
            _count = self.getMayaAttr(_d_section['numAttr'])
            
            if _count:
                l_uValues = MATH.get_splitValueList(l_knots[0],l_knots[1],2+_count)
            else:
                l_uValues = l_knots
            
            for v in l_uValues:
                if iii and v == l_uValues[0]:
                    continue
                
                _crv = mc.duplicateCurve("{0}.u[{1}]".format(str_meshShape,v), ch = 0, rn = 0, local = 0)[0]
                
                if iii:
                    _split = 7
                else:
                    _split = 11
                    
                _l_pos = CURVES.getUSplitList(_crv,_split,rebuild=1)
                    
                #_l_source = mc.ls("{0}.{1}[*]".format(_crv,'ep'),flatten=True,long=True)
                #_l_pos = []
                #for i,ep in enumerate(_l_source):
                    #p = POS.get(ep)
                    #_l_pos.append(p)
                    ##LOC.create(position=p,name='{0}_loc'.format(i))
                #_done.append(k)
                l_posLists.append(_l_pos)
                mc.delete(_crv)                
            
            """
            for k in _d_section['crvs']:
                if k in _done:
                    continue
                
                mCrv = md_dCurves[k]
                _l_source = mc.ls("{0}.{1}[*]".format(mCrv.mNode,'ep'),flatten=True,long=True)
                _l_pos = []
                for i,ep in enumerate(_l_source):
                    p = POS.get(ep)
                    _l_pos.append(p)
                    #LOC.create(position=p,name='{0}_loc'.format(i))
                _done.append(k)
                l_posLists.append(_l_pos)"""
            
            """
            if _count:
                log.debug(cgmGEN.logString_msg(_str_func,section + 'section split'))

                
                l_uValues.pop(0)
                l_uValues.pop(-1)
                
                for v in l_uValues:
                    _crv = mc.duplicateCurve("{0}.u[{1}]".format(str_meshShape,v), ch = 0, rn = 0, local = 0)[0]
                    
                    _l_source = mc.ls("{0}.{1}[*]".format(_crv,'ep'),flatten=True,long=True)
                    _l_pos = []
                    for i,ep in enumerate(_l_source):
                        p = POS.get(ep)
                        _l_pos.append(p)
                        #LOC.create(position=p,name='{0}_loc'.format(i))
                    _done.append(k)
                    l_posLists.insert(1,_l_pos)
                    mc.delete(_crv)"""
                    
            mc.delete(_res_tmp)
            
            #Now we have our positions, we need to setup our handle sets
            for i,l_pos in enumerate(l_posLists):
                _idx = MATH.get_midIndex(len(l_pos))
                _right = l_pos[:_idx]
                _left = l_pos[_idx+1:]
                _mid = l_pos[_idx]

                key_center = '{0}_{1}_center'.format(section,i+1)
                l_keys_left = []
                l_keys_right = []                   
                
                d_creation[key_center] =  {'color':'yellowWhite','tagOnly':1,'arrow':0,'jointLabel':1,'vectorLine':0,'pos':_mid}
                

                for ii,v in enumerate(_right):
                    k = '{0}_{1}_{2}'.format(section,i+1,ii+1)
                    
                    
                    d_creation[k+'_left'] =  {'color':'blueWhite','tagOnly':1,'arrow':0,'jointLabel':1,'vectorLine':0,'pos':_left[ii]}
                    d_creation[k+'_right'] =  {'color':'redWhite','tagOnly':1,'arrow':0,'jointLabel':1,'vectorLine':0,'pos':v}
                    
                    l_keys_right.append(k+'_right')
                    l_keys_left.append(k+'_left')
                    
                    #LOC.create(position=v,name=k+'_right_loc')
                    #LOC.create(position=_left[ii],name=k+'_left_loc')

                
                l_keys = l_keys_right + [key_center] + l_keys_left
                                       
                
                key_curve = '{0}_{1}'.format(section,i+1)
                d_curveKeys[key_curve]= l_keys
                l_curveKeys.append(key_curve)
                
                
                d_curveCreation[key_curve] = {'keys':l_keys,
                                              'rebuild':1}
                
                l_keys_left.reverse()
                for i,k in enumerate(l_keys_left):
                    d_pairs[k] = l_keys_right[i]                           
                
            d_sectionPos[section] = l_posLists
        
        l_order = d_creation.keys()

        #LoftDeclarations....
        md_loftCreation['brow'] = {'keys':l_curveKeys,
                                     'rebuild':{'spansU':5,'spansV':5},
                                     'kws':{'noRebuild':1}}
        
        for tag,d in d_creation.iteritems():
            d_creation[tag]['jointScale'] = True
            
        md_res = self.UTILS.create_defineHandles(self, l_order, d_creation, _size, 
                                                 mFormNull,statePlug = 'form',
                                                 forceSize=1)
        
        ml_subHandles.extend(md_res['ml_handles'])
        md_handles.update(md_res['md_handles'])
        

        md_res = self.UTILS.create_defineCurve(self, d_curveCreation, md_handles, mNoTransformNull,'formCurve')
        md_resCurves = md_res['md_curves']
        
        for k,d in md_loftCreation.iteritems():
            ml_curves = [md_resCurves[k2] for k2 in d['keys']]
            for mObj in ml_curves:
                mObj.v=False
            
            self.UTILS.create_simpleFormLoftMesh(self,
                                                 [mObj.mNode for mObj in ml_curves],
                                                 mFormNull,
                                                 polyType = 'faceLoft',
                                                 d_rebuild = d.get('rebuild',{}),
                                                 baseName = k,
                                                 transparent = False,
                                                 vDriver = "{0}.numSplit_v".format(_short),
                                                 uDriver = "{0}.numSplit_u".format(_short),
                                                 **d.get('kws',{}))
        
        
        ml_toDo = []
        for tag,mHandle in md_handles.iteritems():
            ml_toDo.append(mHandle)
            """if cgmGEN.__mayaVersion__ >= 2018:
                mController = mHandle.controller_get()
                
                try:
                    ATTR.connect("{0}.visProximityMode".format(self.mNode),
                             "{0}.visibilityMode".format(mController.mNode))    
                except Exception,err:
                    log.error(err)
                self.msgList_append('formStuff',mController)"""
        self.atUtils('controller_wireHandles',ml_toDo,'form')
        
        #Mirror indexing -------------------------------------
        log.debug("|{0}| >> Mirror Indexing...".format(_str_func)+'-'*40) 
        
        idx_ctr = 0
        idx_side = 0
        d = {}
        
        for tag,mHandle in md_handles.iteritems():
            if mHandle in ml_defineHandles:
                continue
            
            mHandle._verifyMirrorable()
            _center = True
            for p1,p2 in d_pairs.iteritems():
                if p1 == tag or p2 == tag:
                    _center = False
                    break
            if _center:
                log.debug("|{0}| >>  Center: {1}".format(_str_func,tag))    
                mHandle.mirrorSide = 0
                mHandle.mirrorIndex = idx_ctr
                idx_ctr +=1
            mHandle.mirrorAxis = "translateX,rotateY,rotateZ"
    
        #Self mirror wiring -------------------------------------------------------
        for k,m in d_pairs.iteritems():
            try:
                md_handles[k].mirrorSide = 1
                md_handles[m].mirrorSide = 2
                md_handles[k].mirrorIndex = idx_side
                md_handles[m].mirrorIndex = idx_side
                md_handles[k].doStore('mirrorHandle',md_handles[m])
                md_handles[m].doStore('mirrorHandle',md_handles[k])
                idx_side +=1        
            except Exception,err:
                log.error('Mirror error: {0}'.format(err))
                    
        self.msgList_connect('formHandles',ml_subHandles)#Connect
        self.msgList_connect('formCurves',md_res['ml_curves'])#Connect     
        

        
        return                        



#=============================================================================================================
#>> Prerig
#=============================================================================================================
def prerigDelete(self):
    try:self.moduleEyelid.delete()
    except:pass
    
    for a in 'blockScale','translate','rotate':
        ATTR.set_lock(self.mNode, a, False)    
    
    
def create_handle(self,tag,pos,mJointTrack=None,
                  trackAttr=None,visualConnection=True,
                  nameEnd = 'BrowHandle'):
    mHandle = cgmMeta.validateObjArg( CURVES.create_fromName('circle', size = _size_sub), 
                                      'cgmObject',setClass=1)
    mHandle.doSnapTo(self)

    mHandle.p_position = pos

    mHandle.p_parent = mStateNull
    mHandle.doStore('cgmName',tag)
    mHandle.doStore('cgmType','formHandle')
    mHandle.doName()

    mHandleFactory.color(mHandle.mNode,controlType='sub')

    self.connectChildNode(mHandle.mNode,'{0}nameEnd'.format(tag),'block')

    return mHandle

    #joinHandle ------------------------------------------------
    mJointHandle = cgmMeta.validateObjArg( CURVES.create_fromName('jack',
                                                                  size = _size_sub*.75),
                                           'cgmObject',
                                           setClass=1)

    mJointHandle.doStore('cgmName',tag)    
    mJointHandle.doStore('cgmType','jointHelper')
    mJointHandle.doName()                

    mJointHandle.p_position = pos
    mJointHandle.p_parent = mStateNull


    mHandleFactory.color(mJointHandle.mNode,controlType='sub')
    mHandleFactory.addJointLabel(mJointHandle,tag)
    mHandle.connectChildNode(mJointHandle.mNode,'jointHelper','handle')

    mTrackGroup = mJointHandle.doGroup(True,True,
                                       asMeta=True,
                                       typeModifier = 'track',
                                       setClass='cgmObject')

    if trackAttr and mJointTrack:
        mPointOnCurve = cgmMeta.asMeta(CURVES.create_pointOnInfoNode(mJointTrack.mNode,turnOnPercentage=True))

        mPointOnCurve.doConnectIn('parameter',"{0}.{1}".format(self.mNode,trackAttr))

        mTrackLoc = mJointHandle.doLoc()

        mPointOnCurve.doConnectOut('position',"{0}.translate".format(mTrackLoc.mNode))

        mTrackLoc.p_parent = mNoTransformNull
        mTrackLoc.v=False
        mc.pointConstraint(mTrackLoc.mNode,mTrackGroup.mNode)                    


    elif mJointTrack:
        mLoc = mHandle.doLoc()
        mLoc.v=False
        mLoc.p_parent = mNoTransformNull
        mc.pointConstraint(mHandle.mNode,mLoc.mNode)

        res = DIST.create_closest_point_node(mLoc.mNode,mJointTrack.mNode,True)
        #mLoc = cgmMeta.asMeta(res[0])
        mTrackLoc = cgmMeta.asMeta(res[0])
        mTrackLoc.p_parent = mNoTransformNull
        mTrackLoc.v=False
        mc.pointConstraint(mTrackLoc.mNode,mTrackGroup.mNode)


    mAimGroup = mJointHandle.doGroup(True,True,
                                     asMeta=True,
                                     typeModifier = 'aim',
                                     setClass='cgmObject')
    mc.aimConstraint(mLidRoot.mNode,
                     mAimGroup.mNode,
                     maintainOffset = False, weight = 1,
                     aimVector = [0,0,-1],
                     upVector = [0,1,0],
                     worldUpVector = [0,1,0],
                     worldUpObject = self.mNode,
                     worldUpType = 'objectRotation' )                          


    if visualConnection:
        log.debug("|{0}| >> visualConnection ".format(_str_func, tag))
        trackcrv,clusters = CORERIG.create_at([mLidRoot.mNode,
                                               mJointHandle.mNode],#ml_handleJoints[1]],
                                              'linearTrack',
                                              baseName = '{0}_midTrack'.format(tag))

        mTrackCrv = cgmMeta.asMeta(trackcrv)
        mTrackCrv.p_parent = mNoTransformNull
        mHandleFactory.color(mTrackCrv.mNode, controlType = 'sub')

        for s in mTrackCrv.getShapes(asMeta=True):
            s.overrideEnabled = 1
            s.overrideDisplayType = 2

    return mHandle

def prerig(self):
    try:
        _str_func = 'prerig'
        log.debug("|{0}| >>  {1}".format(_str_func,self)+ '-'*80)
        self.blockState = 'prerig'
        _side = self.UTILS.get_side(self)
        
        self.atUtils('module_verify')
        mStateNull = self.UTILS.stateNull_verify(self,'prerig')
        mNoTransformNull = self.atUtils('noTransformNull_verify','prerig')
        
        #mRoot = self.getMessageAsMeta('rootHelper')
        mHandleFactory = self.asHandleFactory()
        
        ml_handles = []
        md_handles = {'brow':{'center':[],
                              'left':[],
                              'right':[]}}
        md_jointHandles = {'brow':{'center':[],
                              'left':[],
                              'right':[]}}
        
        for a in 'blockScale','translate','rotate':
            ATTR.set_lock(self.mNode, a, True)
        
        #Get base dat =============================================================================    
        mBBHelper = self.bbHelper
        mBrowLoft = self.getMessageAsMeta('browFormLoft')
        
        _size = MATH.average(self.baseSize[1:])
        _size_base = _size * .25
        _size_sub = _size_base * .5
        
        idx_ctr = 0
        idx_side = 0
        
        d_baseHandeKWS = {'mStateNull' : mStateNull,
                          'mNoTransformNull' : mNoTransformNull,
                          'jointSize': self.jointRadius} 
        #Anchors =====================================================================================
        log.debug(cgmGEN.logString_sub('anchors'))
        
        def create_anchor(self, pos,mSurface,tag,k,side=None,controlType = 'main',nameDict=None, size = _size_sub):
            mHandle = cgmMeta.validateObjArg(self.doCreateAt(),'cgmControl',setClass=1)
            
            #Position 
            datClose = DIST.get_closest_point_data(mSurface.mNode, targetPoint=pos)
            pClose = datClose['position']
            
            mHandle.p_position = pClose
            
            mc.delete(mc.normalConstraint(mSurface.mNode, mHandle.mNode,
                                aimVector = [0,0,1], upVector = [0,1,0],
                                worldUpObject = self.mNode,
                                worldUpType = 'objectrotation', 
                                worldUpVector = [0,1,0]))
            
            pBall = DIST.get_pos_by_axis_dist(mHandle.mNode,'z+',self.controlOffset * 2)
            
            mBall = cgmMeta.validateObjArg( CURVES.create_fromName('semiSphere', size = size), 
                                              'cgmControl',setClass=1)
            mBall.doSnapTo(mHandle)
            mBall.p_position = pBall
            
            _crvLinear = CORERIG.create_at(create='curveLinear',
                                           l_pos=[pClose,pBall])
            
            CORERIG.shapeParent_in_place(mHandle.mNode, mBall.mNode,False)
            CORERIG.shapeParent_in_place(mHandle.mNode, _crvLinear,False)            
  
            mHandle._verifyMirrorable()
            
            mHandle.p_parent = mStateNull
            
            if nameDict:
                RIGGEN.store_and_name(mHandle,nameDict)
            else:
                mHandle.doStore('cgmName',tag)
                mHandle.doStore('cgmType','anchor')
                mHandle.doName()
                
            _key = tag
            if k:
                _key = _key+k.capitalize()
                
            mHandleFactory.color(mHandle.mNode, side = side, controlType=controlType)

            return mHandle
            
        #we need to generate some positions
        md_handles = {}
        ml_handlesAll = []
        md_mirrorDat = {'center':[],
                        'left':[],
                        'right':[]}
        md_dCurves = {}
        d_defPos = {}
        
        md_defineHandles = {}
        ml_defineHandles = self.msgList_get('defineSubHandles')
        for mObj in ml_defineHandles:
            md_defineHandles[mObj.handleTag] = mObj
            d_defPos[mObj.handleTag] = mObj.p_position
            mObj.v=0
            
        d_anchorDat = {'brow':{'center':{'main':['base','brow']}}}
        md_anchors = {}
        
        for side in 'left','right':
            d_anchorDat['brow'][side] = {}
            _d = d_anchorDat['brow'][side]
            _d["start"] = ['base_1_{0}'.format(side),'brow_1_{0}'.format(side)]
            _d["mid"] = ['base_2_{0}'.format(side),'brow_2_{0}'.format(side)]
            _d["end"] = ['base_3_{0}'.format(side),'brow_3_{0}'.format(side)]
            
            if self.controlTemple:
                _d["temple"]= ['base_4_{0}'.format(side),'brow_4_{0}'.format(side)]
            
            
        #pprint.pprint(d_anchorDat)
        #Get positions...
        _d = {'cgmName':'browCenter',
              'cgmType':'preHandle'}
        
        for section,sectionDat in d_anchorDat.iteritems():
            md_anchors[section] = {}
            for side,sideDat in sectionDat.iteritems():
                md_anchors[section][side] = {}
                for tag,dat in sideDat.iteritems():
                    _dUse = copy.copy(_d)
                    _dUse['cgmName'] = 'brow'+STR.capFirst(tag)
                    _dUse['cgmDirection'] = side
                    
                    l_pos = []
                    for key in dat:
                        l_pos.append(md_defineHandles[key].p_position)
                        
                    posBase = DIST.get_average_position(l_pos)
                    #LOC.create(position=posBase, name = tag+side)
                    
                    #md_anchors[section][side][tag] = create_anchor(self,posBase, mBrowLoft, tag, None, side,nameDict=_dUse,size= _size_sub/2)
                    
                    mAnchor = BLOCKSHAPES.create_face_anchor(self,posBase,
                                                             mBrowLoft,
                                                             tag,
                                                             None,
                                                             side,
                                                             nameDict=_dUse,
                                                             mStateNull=mStateNull,
                                                             size= _size_sub/2)                    
                    md_anchors[section][side][tag] = mAnchor
        
        #...get my anchors in lists...
        md_anchorsLists = {}
        
        for section,sectionDat in d_anchorDat.iteritems():
            md_anchorsLists[section] = {}
            
            for side,dat in sectionDat.iteritems():
                if side == 'center':
                    md_anchorsLists[section]['center'] =  [md_anchors[section][side]['main']]
                    md_mirrorDat['center'].extend(md_anchorsLists[section]['center'])
                    ml_handlesAll.extend(md_anchorsLists[section]['center'])
                    
                    mStateNull.msgList_connect('brow{0}Anchors'.format(STR.capFirst(side)),md_anchorsLists[section]['center'])
                else:
                    md_anchorsLists[section][side] =  [md_anchors[section][side]['start'],
                                              md_anchors[section][side]['mid'],
                                              md_anchors[section][side]['end']]
                    
                    md_mirrorDat[side].extend(md_anchorsLists[section][side])
                    ml_handlesAll.extend(md_anchorsLists[section][side])
                    
                    mStateNull.msgList_connect('brow{0}Anchors'.format(STR.capFirst(side)),md_anchorsLists[section][side])


        
        #...make our driver curves...
        log.debug(cgmGEN.logString_msg('driver curves'))
        d_curveCreation = {}
        for section,sectionDat in md_anchorsLists.iteritems():
            for side,dat in sectionDat.iteritems():
                if side == 'center':
                    pass
                else:
                    d_curveCreation[section+STR.capFirst(side)+'Driver'] = {'ml_handles': dat,
                                             'rebuild':1}
                
        md_res = self.UTILS.create_defineCurve(self, d_curveCreation, {}, mNoTransformNull,'preCurve')
        md_resCurves = md_res['md_curves']
        ml_resCurves = md_res['ml_curves']
        
        
        #Handles ====================================================================================
        log.debug(cgmGEN.logString_sub('Handles'))
        md_prerigDags = {}
        md_jointHelpers = {}
        
        _d = {'cgmName':''}
        
        #...get our driverSetup
        _mainShape = 'squareRounded'
        _sizeDirect = _size_sub * .4
        
        for section,sectionDat in md_anchorsLists.iteritems():
            log.debug(cgmGEN.logString_msg(section))
            
            md_handles[section] = {}
            md_prerigDags[section] = {}
            md_jointHelpers[section] = {}
            for side,dat in sectionDat.iteritems():
                log.debug(cgmGEN.logString_msg(side))
                
                md_handles[section][side] = []
                md_prerigDags[section][side] = []
                md_jointHelpers[side] = []
                
                _ml_shapes = []
                _ml_prerigDags = []
                _ml_jointShapes = []
                _ml_jointHelpers = []
                
                tag = section+STR.capFirst(side)
                
                if side == 'center':
                    d_use = copy.copy(_d)
                    d_use['cgmName'] = tag
                    d_use['cgmIterator'] = 0
                    mAnchor = md_anchorsLists[section][side][0]
                    p = mAnchor.p_position
                    
                    #mShape, mDag = create_faceHandle(p,mBrowLoft,tag,None,side,mDriver=mAnchor,controlType=_controlType, mode='handle', plugDag= 'preDag',plugShape= 'preShape',nameDict= d_use)
                    
                    
                    mShape, mDag = BLOCKSHAPES.create_face_handle(self,p,
                                                                  tag,
                                                                  None,
                                                                  side,
                                                                  mDriver=mAnchor,
                                                                  mSurface=mBrowLoft,
                                                                  mainShape=_mainShape,
                                                                  jointShape='locatorForm',
                                                                  controlType='main',#_controlType,
                                                                  mode='handle',
                                                                  depthAttr = 'jointDepth',
                                                                  plugDag= 'preDag',
                                                                  plugShape= 'preShape',
                                                                  attachToSurf=True,
                                                                  orientToDriver = True,
                                                                  nameDict= d_use,**d_baseHandeKWS)                    
                    
                    
                    
                    
                    
                    _ml_shapes.append(mShape)
                    _ml_prerigDags.append(mDag)
                    
                    #Joint stuff...
                    mShape, mDag = BLOCKSHAPES.create_face_handle(self,
                                                                  p,tag,None,side,
                                                                  mDriver=mDag,
                                                                  mSurface=mBrowLoft,
                                                                  mainShape='semiSphere',
                                                                  size= _sizeDirect,
                                                                  mode='joint',
                                                                  controlType='sub',
                                                                  plugDag= 'jointHelper',
                                                                  plugShape= 'directShape',
                                                                  attachToSurf=True,
                                                                  orientToDriver=True,
                                                                  offsetAttr='conDirectOffset',
                                                                  
                                                                  nameDict= d_use,**d_baseHandeKWS)                    
                    
                    
                    _ml_jointShapes.append(mShape)
                    _ml_jointHelpers.append(mDag)
                
                else:
                    mCrv = md_resCurves.get(tag+'Driver')
                    
                    #if mCrv:
                        #First do our controls....
                   #     l_pos = CURVES.getUSplitList(mCrv.mNode, self.numBrowControl)
                   #     mCrv.v=False
                    d_use = copy.copy(_d)
                    d_use['cgmName'] = tag

                    for i,mAnchor in enumerate(md_anchorsLists[section][side]):
                        d_use['cgmIterator'] = i
                        p = mAnchor.p_position
                        
                        if mAnchor not in [md_anchorsLists[section][side][0],md_anchorsLists[section][side][-1]]:
                            _controlType = 'sub'
                        else:
                            _controlType = 'main'
                        """
                        mDriver = self.doCreateAt(setClass=1)#self.doLoc()#
                        mDriver.rename("{0}_{1}_{2}_pre_driver".format(side,section,i))
                        mDriver.p_position = p
                        mDriver.p_parent = mStateNull
                        
                        _res = RIGCONSTRAINT.attach_toShape(mDriver.mNode,mCrv.mNode,'conPoint')
                        TRANS.parent_set(_res[0], mNoTransformNull.mNode)
                        """
                        
                        #mShape, mDag = create_faceHandle(p,mBrowLoft,tag,None,side,mDriver=mDriver,controlType=_controlType, mode='handle', plugDag= 'preDag',plugShape= 'preShape',nameDict= d_use)
                        mShape, mDag = BLOCKSHAPES.create_face_handle(self,p,
                                                                      tag,
                                                                      None,
                                                                      side,
                                                                      mDriver=mAnchor,
                                                                      mSurface=mBrowLoft,
                                                                      mainShape=_mainShape,
                                                                      jointShape='locatorForm',
                                                                      controlType=_controlType,
                                                                      mode='handle',
                                                                      depthAttr = 'jointDepth',
                                                                      plugDag= 'preDag',
                                                                      plugShape= 'preShape',
                                                                      attachToSurf=True,
                                                                      orientToDriver = True,
                                                                      nameDict= d_use,**d_baseHandeKWS)                            
                        _ml_shapes.append(mShape)
                        _ml_prerigDags.append(mDag)
                        
                    
                    #Now do our per joint handles
                    l_pos = CURVES.getUSplitList(mCrv.mNode, self.numBrowJoints)
                    _sizeDirect = _size_sub * .6
                    for i,p in enumerate(l_pos):
                        d_use['cgmIterator'] = i

                        
                        mDriver = self.doCreateAt(setClass=1)#self.doLoc()#
                        mDriver.rename("{0}_{1}_{2}_joint_driver".format(side,section,i))
                        mDriver.p_position = p
                        mDriver.p_parent = mStateNull
                        
                        _res = RIGCONSTRAINT.attach_toShape(mDriver.mNode,mCrv.mNode,'conPoint')
                        TRANS.parent_set(_res[0], mNoTransformNull.mNode)
                        """
                        mShape, mDag = create_faceHandle(p,mBrowLoft,tag,None,side,
                                                         mDriver=mDriver,
                                                         mainShape='semiSphere',
                                                         jointShape='sphere',
                                                         size= _sizeDirect,
                                                         mode='joint',
                                                         controlType='sub',
                                                         plugDag= 'jointHelper',
                                                         plugShape= 'directShape',
                                                         nameDict= d_use)"""
                        reload(BLOCKSHAPES)
                        mShape, mDag = BLOCKSHAPES.create_face_handle(self,
                                                                      p,tag,None,side,
                                                                      mDriver=mDriver,
                                                                      mSurface=mBrowLoft,
                                                                      mainShape='semiSphere',
                                                                      size= _sizeDirect,
                                                                      mode='joint',
                                                                      controlType='sub',
                                                                      plugDag= 'jointHelper',
                                                                      plugShape= 'directShape',
                                                                      attachToSurf=True,
                                                                      #orientToDriver=True,
                                                                      offsetAttr='conDirectOffset',
                                                                      
                                                                      nameDict= d_use,**d_baseHandeKWS)                        
                        
                        _ml_jointShapes.append(mShape)
                        _ml_jointHelpers.append(mDag)
                            
                mStateNull.msgList_connect('{0}PrerigShapes'.format(tag),_ml_shapes)
                mStateNull.msgList_connect('{0}PrerigHandles'.format(tag),_ml_prerigDags)
                mStateNull.msgList_connect('{0}JointHelpers'.format(tag),_ml_jointHelpers)
                mStateNull.msgList_connect('{0}JointShapes'.format(tag),_ml_jointShapes)                
                md_mirrorDat[side].extend(_ml_shapes + _ml_prerigDags)
                md_handles[section][side] = _ml_shapes
                md_prerigDags[section][side] = _ml_prerigDags
                md_jointHelpers[section][side] = _ml_jointHelpers
                ml_handlesAll.extend(_ml_shapes + _ml_prerigDags)
                if _ml_jointShapes:
                    ml_handlesAll.extend(_ml_jointShapes)
                    ml_handlesAll.extend(_ml_jointHelpers)
                    md_mirrorDat[side].extend(_ml_jointShapes + _ml_jointHelpers)
                
        
        #CURVES ==========================================================================
        log.debug(cgmGEN.logString_sub('curves'))
        
        #Make our visual joint curves for helping see things
        d_visCurves = {}
        md_browJointHelpers = md_jointHelpers['brow']
        for side in 'left','right':
            d_visCurves['brow'+STR.capFirst(side)] = {'ml_handles': md_jointHelpers['brow'][side],
                                                      'rebuild':0}            
        
        md_res = self.UTILS.create_defineCurve(self, d_visCurves, {}, mNoTransformNull,'preCurve')
        md_resCurves = md_res['md_curves']
        ml_resCurves = md_res['ml_curves']
        
        
        """
        log.debug(cgmGEN.logString_sub('joint handles'))
        
        for side in 'left','right':
            mCrv = d_visCurves['brow'+STR.capFirst(side)]         
            if mCrv:
                l_pos = CURVES.getUSplitList(mCrv.mNode, self.numBrowJoints)
                d_use = copy.copy(_d)
                d_use['cgmName'] = tag
                
                for i,p in enumerate(l_pos):
                    d_use['cgmIterator'] = i
                    
                    mDriver = self.doCreateAt(setClass=1)#self.doLoc()#
                    mDriver.rename("{0}_{1}_{2}_driver".format(side,section,i))
                    mDriver.p_position = p
                    mDriver.p_parent = mStateNull
                    
                    _res = RIGCONSTRAINT.attach_toShape(mDriver.mNode,mCrv.mNode,'conPoint')
                    TRANS.parent_set(_res[0], mNoTransformNull.mNode)
                    
                    mShape, mDag = create_handle(p,mBrowLoft,tag,None,side,mDriver=mDriver,nameDict= d_use)
                    
                    _ml_shapes.append(mShape)
                    _ml_prerigDags.append(mDag)  """              
        
                        
        
        #Mirror setup --------------------------------
        log.debug(cgmGEN.logString_sub('mirror'))
        idx_ctr = 0
        idx_side = 0
        
        log.debug(cgmGEN.logString_msg('mirror | center'))
        for mHandle in md_mirrorDat['center']:
            mHandle._verifyMirrorable()
            mHandle.mirrorSide = 0
            mHandle.mirrorIndex = idx_ctr
            idx_ctr +=1
            mHandle.mirrorAxis = "translateX,rotateY,rotateZ"

        log.debug(cgmGEN.logString_msg('mirror | sides'))
            
        for i,mHandle in enumerate(md_mirrorDat['left']):
            mLeft = mHandle 
            mRight = md_mirrorDat['right'][i]
            
            for mObj in mLeft,mRight:
                mObj._verifyMirrorable()
                mObj.mirrorAxis = "translateX,rotateY,rotateZ"
                mObj.mirrorIndex = idx_side
            mLeft.mirrorSide = 1
            mRight.mirrorSide = 2
            mLeft.doStore('mirrorHandle',mRight)
            mRight.doStore('mirrorHandle',mLeft)            
            idx_side +=1
 
        #Close out ======================================================================================
        self.msgList_connect('prerigHandles', ml_handlesAll)
        
        self.blockState = 'prerig'
        return
    
    
    except Exception,err:
        cgmGEN.cgmExceptCB(Exception,err)


def prerigBAK(self):
    try:
        _str_func = 'prerig'
        log.debug("|{0}| >>  {1}".format(_str_func,self)+ '-'*80)
        self.blockState = 'prerig'
        _side = self.UTILS.get_side(self)
        
        self.atUtils('module_verify')
        mStateNull = self.UTILS.stateNull_verify(self,'prerig')
        mNoTransformNull = self.atUtils('noTransformNull_verify','prerig')
        
        #mRoot = self.getMessageAsMeta('rootHelper')
        mHandleFactory = self.asHandleFactory()
        
        ml_handles = []
        md_handles = {'brow':{'center':[],
                              'left':[],
                              'right':[]}}
        md_jointHandles = {'brow':{'center':[],
                              'left':[],
                              'right':[]}}
        #Get base dat =============================================================================    
        mBBHelper = self.bbHelper
        mBrowLoft = self.getMessageAsMeta('browFormLoft')
        
        _size = MATH.average(self.baseSize[1:])
        _size_base = _size * .25
        _size_sub = _size_base * .5
        
        idx_ctr = 0
        idx_side = 0
        
        def create_handle(mHelper, mSurface, tag, k, side, controlType = 'main', aimGroup = 1,nameDict = None):
            mHandle = cgmMeta.validateObjArg( CURVES.create_fromName('squareRounded', size = _size_sub), 
                                              'cgmControl',setClass=1)
            mHandle._verifyMirrorable()
            
            mHandle.doSnapTo(self)
            mHandle.p_parent = mStateNull
            
            if nameDict:
                RIGGEN.store_and_name(mHandle,nameDict)
            else:
                mHandle.doStore('cgmName',tag)
                mHandle.doStore('cgmType','prerigHandle')
                mHandle.doName()
                
                
            _key = tag
            if k:
                _key = _key+k.capitalize()
            mMasterGroup = mHandle.doGroup(True,True,
                                           asMeta=True,
                                           typeModifier = 'master',
                                           setClass='cgmObject')
        
            mc.pointConstraint(mHelper.mNode,mMasterGroup.mNode,maintainOffset=False)
        
            mHandleFactory.color(mHandle.mNode,side = side, controlType=controlType)
            mStateNull.connectChildNode(mHandle, _key+'prerigHelper','block')
        
            mc.normalConstraint(mSurface.mNode, mMasterGroup.mNode,
                                aimVector = [0,0,1], upVector = [0,1,0],
                                worldUpObject = self.mNode,
                                worldUpType = 'objectrotation', 
                                worldUpVector = [0,1,0])
        
            if aimGroup:
                mHandle.doGroup(True,True,
                                asMeta=True,
                                typeModifier = 'aim',
                                setClass='cgmObject')
        
        
            mHandle.tz = _size_sub
            
            return mHandle
        
        def create_jointHelper(mPos, mSurface, tag, k, side, nameDict=None, aimGroup = 1):
            
            mHandle = cgmMeta.validateObjArg( CURVES.create_fromName('axis3d', size = _size_sub * .5), 
                                              'cgmControl',setClass=1)
            mHandle._verifyMirrorable()
            
            mHandle.doSnapTo(self)
            mHandle.p_parent = mStateNull
            if nameDict:
                RIGGEN.store_and_name(mHandle,nameDict)
                _dCopy = copy.copy(nameDict)
                _dCopy.pop('cgmType')
                mJointLabel = mHandleFactory.addJointLabel(mHandle,NAMETOOLS.returnCombinedNameFromDict(_dCopy))
                
            else:
                mHandle.doStore('cgmName',tag)
                mHandle.doStore('cgmType','jointHelper')
                mHandle.doName()
            
            _key = tag
            if k:
                _key = "{0}_{1}".format(tag,k)
            
            
            
            mMasterGroup = mHandle.doGroup(True,True,
                                           asMeta=True,
                                           typeModifier = 'master',
                                           setClass='cgmObject')
    
            mc.pointConstraint(mPos.mNode,mMasterGroup.mNode,maintainOffset=False)
    
            #mHandleFactory.color(mHandle.mNode,side = side, controlType='sub')
            mStateNull.connectChildNode(mHandle, _key+'prerigHelper','block')
    
            mc.normalConstraint(mSurface.mNode, mMasterGroup.mNode,
                                aimVector = [0,0,1], upVector = [0,1,0],
                                worldUpObject = self.mNode,
                                worldUpType = 'objectrotation', 
                                worldUpVector = [0,1,0])
    
            if aimGroup:
                mHandle.doGroup(True,True,
                                asMeta=True,
                                typeModifier = 'aim',
                                setClass='cgmObject')
    

            return mHandle        
        
        #Handles =====================================================================================
        log.debug("|{0}| >> Brow Handles..".format(_str_func)+'-'*40)
        
        _d = {'cgmName':'browCenter',
              'cgmType':'handleHelper'}
        
        mBrowCenterDefine = self.defineBrowcenterHelper
        md_handles['browCenter'] = [create_handle(mBrowCenterDefine,mBrowLoft,
                                                  'browCenter',None,'center',nameDict = _d)]
        md_handles['brow']['center'].append(md_handles['browCenter'])
        md_handles['browCenter'][0].mirrorIndex = idx_ctr
        idx_ctr +=1
        mStateNull.msgList_connect('browCenterPrerigHandles',md_handles['browCenter'])
        
        _d_nameHandleSwap = {'start':'inner',
                             'end':'outer'}
        for tag in ['browLeft','browRight']:
            _d['cgmName'] = tag
        
            for k in ['start','mid','end']:
                _d['cgmNameModifier'] = _d_nameHandleSwap.get(k,k)
                
                if 'Left' in tag:
                    _side = 'left'
                elif 'Right' in tag:
                    _side = 'right'
                else:
                    _side = 'center'
                
                if _side in ['left','right']:
                    _d['cgmDirection'] = _side
                    
                if k == 'mid':
                    _control = 'sub'
                else:
                    _control = 'main'
                    
                mFormHelper = self.getMessageAsMeta(tag+k.capitalize()+'formHelper')
                
                mHandle = create_handle(mFormHelper,mBrowLoft,tag,k,_side,controlType = _control,nameDict = _d)
                md_handles['brow'][_side].append(mHandle)
                ml_handles.append(mHandle)
            mStateNull.msgList_connect('{0}PrerigHandles'.format(tag),md_handles['brow'][_side])


        #Joint helpers ------------------------
        log.debug("|{0}| >> Joint helpers..".format(_str_func)+'-'*40)
        _d = {'cgmName':'brow',
              'cgmDirection':'center',
              'cgmType':'jointHelper'}        
        
        mFullCurve = self.getMessageAsMeta('browLineloftCurve')
        md_jointHandles['browCenter'] = [create_jointHelper(mBrowCenterDefine,mBrowLoft,'center',None,
                                                            'center',nameDict=_d)]
        md_jointHandles['brow']['center'].append(md_jointHandles['browCenter'])
        md_jointHandles['browCenter'][0].mirrorIndex = idx_ctr
        idx_ctr +=1
        mStateNull.msgList_connect('browCenterJointHandles',md_jointHandles['browCenter'])
        

        for tag in ['browLeft','browRight']:
            mCrv = self.getMessageAsMeta("{0}JointCurve".format(tag))
            if 'Left' in tag:
                _side = 'left'
            elif 'Right' in tag:
                _side = 'right'
            else:
                _side = 'center'            
            
            if _side in ['left','right']:
                _d['cgmDirection'] = _side
                
            _factor = 100/(self.numBrowJoints-1)
            
            for i in range(self.numBrowJoints):
                log.debug("|{0}| >>  Joint Handle: {1}|{2}...".format(_str_func,tag,i))            
                _d['cgmIterator'] = i
                
                mLoc = cgmMeta.asMeta(self.doCreateAt())
                mLoc.rename("{0}_{1}_jointTrackHelper".format(tag,i))
            
                #self.connectChildNode(mLoc, tag+k.capitalize()+'formHelper','block')
                mPointOnCurve = cgmMeta.asMeta(CURVES.create_pointOnInfoNode(mCrv.mNode,
                                                                             turnOnPercentage=True))
            
                mPointOnCurve.parameter = (_factor * i)/100.0
                mPointOnCurve.doConnectOut('position',"{0}.translate".format(mLoc.mNode))
            
                mLoc.p_parent = mNoTransformNull
                
            
                res = DIST.create_closest_point_node(mLoc.mNode,mFullCurve.mNode,True)
                #mLoc = cgmMeta.asMeta(res[0])
                mTrackLoc = cgmMeta.asMeta(res[0])
                mTrackLoc.p_parent = mNoTransformNull
                mTrackLoc.v=False
                
                mHandle = create_jointHelper(mTrackLoc,mBrowLoft,tag,i,_side,nameDict=_d)
                md_jointHandles['brow'][_side].append(mHandle)
                ml_handles.append(mHandle)
                
            
        
        #Aim pass ------------------------------------------------------------------------
        for side in ['left','right']:
            #Handles -------
            ml = md_handles['brow'][side]
            for i,mObj in enumerate(ml):
                mObj.mirrorIndex = idx_side + i
                mObj.mirrorAxis = "translateX,rotateY,rotateZ"
                
                if side == 'left':
                    _aim = [-1,0,0]
                    mObj.mirrorSide = 1                    
                else:
                    _aim = [1,0,0]
                    mObj.mirrorSide = 2
                    
                _up = [0,0,1]
                _worldUp = [0,0,1]
                
                if i == 0:
                    mAimGroup = mObj.aimGroup
                    mc.aimConstraint(md_handles['browCenter'][0].masterGroup.mNode,
                                     mAimGroup.mNode,
                                     maintainOffset = False, weight = 1,
                                     aimVector = _aim,
                                     upVector = _up,
                                     worldUpVector = _worldUp,
                                     worldUpObject = mObj.masterGroup.mNode,
                                     worldUpType = 'objectRotation' )                                
                else:

                    mAimGroup = mObj.aimGroup
                    mc.aimConstraint(ml[i-1].masterGroup.mNode,
                                     mAimGroup.mNode,
                                     maintainOffset = False, weight = 1,
                                     aimVector = _aim,
                                     upVector = _up,
                                     worldUpVector = _worldUp,
                                     worldUpObject = mObj.masterGroup.mNode,
                                     worldUpType = 'objectRotation' )
                    
            mStateNull.msgList_connect('brow{0}PrerigHandles'.format(side.capitalize()), ml)
            
        idx_side = idx_side + i + 1
        log.info(idx_side)
        
        for side in ['left','right']:
            #Joint Helpers ----------------
            ml = md_jointHandles['brow'][side]
            for i,mObj in enumerate(ml):
                if side == 'left':
                    _aim = [1,0,0]
                    mObj.mirrorSide = 1
                else:
                    _aim = [-1,0,0]
                    mObj.mirrorSide = 2
                    
                mObj.mirrorIndex = idx_side + i
                mObj.mirrorAxis = "translateX,rotateY,rotateZ"
                _up = [0,0,1]
                _worldUp = [0,0,1]
                if mObj == ml[-1]:
                    _vAim = [_aim[0]*-1,_aim[1],_aim[2]]
                    mAimGroup = mObj.aimGroup
                    mc.aimConstraint(ml[i-1].masterGroup.mNode,
                                     mAimGroup.mNode,
                                     maintainOffset = False, weight = 1,
                                     aimVector = _vAim,
                                     upVector = _up,
                                     worldUpVector = _worldUp,
                                     worldUpObject = mObj.masterGroup.mNode,
                                     worldUpType = 'objectRotation' )                    
                else:
                    mAimGroup = mObj.aimGroup
                    mc.aimConstraint(ml[i+1].masterGroup.mNode,
                                     mAimGroup.mNode,
                                     maintainOffset = False, weight = 1,
                                     aimVector = _aim,
                                     upVector = _up,
                                     worldUpVector = _worldUp,
                                     worldUpObject = mObj.masterGroup.mNode,
                                     worldUpType = 'objectRotation' )
                    
            mStateNull.msgList_connect('brow{0}JointHandles'.format(side.capitalize()), ml)
        
        #Mirror setup --------------------------------
        """
        for mHandle in ml_handles:
            mHandle._verifyMirrorable()
            _str_handle = mHandle.p_nameBase
            if 'Center' in _str_handle:
                mHandle.mirrorSide = 0
                mHandle.mirrorIndex = idx_ctr
                idx_ctr +=1
            mHandle.mirrorAxis = "translateX,rotateY,rotateZ"
    
        #Self mirror wiring -------------------------------------------------------
        for k,m in _d_pairs.iteritems():
            md_handles[k].mirrorSide = 1
            md_handles[m].mirrorSide = 2
            md_handles[k].mirrorIndex = idx_side
            md_handles[m].mirrorIndex = idx_side
            md_handles[k].doStore('mirrorHandle',md_handles[m])
            md_handles[m].doStore('mirrorHandle',md_handles[k])
            idx_side +=1        """
        
        #Close out ======================================================================================
        self.msgList_connect('prerigHandles', ml_handles)
        
        self.blockState = 'prerig'
        return
    
    
    except Exception,err:
        cgmGEN.cgmExceptCB(Exception,err)
        
#=============================================================================================================
#>> Skeleton
#=============================================================================================================
def skeleton_check(self):
    return True

def skeleton_build(self, forceNew = True):
    _short = self.mNode
    _str_func = '[{0}] > skeleton_build'.format(_short)
    log.debug("|{0}| >> ...".format(_str_func)) 
    
    _radius = self.atUtils('get_shapeOffset') * .25# or 1
    ml_joints = []
    
    mModule = self.atUtils('module_verify')
    
    mRigNull = mModule.rigNull
    if not mRigNull:
        raise ValueError,"No rigNull connected"
    
    mPrerigNull = self.prerigNull
    if not mPrerigNull:
        raise ValueError,"No prerig null"
    
    mRoot = self.UTILS.skeleton_getAttachJoint(self)
    
    #>> If skeletons there, delete -------------------------------------------------------------------------- 
    _bfr = mRigNull.msgList_get('moduleJoints',asMeta=True)
    if _bfr:
        log.debug("|{0}| >> Joints detected...".format(_str_func))            
        if forceNew:
            log.debug("|{0}| >> force new...".format(_str_func))                            
            mc.delete([mObj.mNode for mObj in _bfr])
        else:
            return _bfr
        
    _baseNameAttrs = ATTR.datList_getAttrs(self.mNode,'nameList')
    _l_baseNames = ATTR.datList_get(self.mNode, 'nameList')

    _browType = self.getEnumValueString('browType')
    if _browType in ['full','split']:#Full brow
        log.debug("|{0}| >>  {1} Brow...".format(_str_func,_browType))
        

        for side in 'left','right','center':
            _cap = side.capitalize()
            ml_new = []            
            if side == 'center':
                if not self.buildCenter:
                    continue
                ml_base = mPrerigNull.msgList_get('brow{0}JointHelpers'.format(_cap))
                for mObj in ml_base:
                    mJnt = mObj.doCreateAt('joint')
                    mJnt.doCopyNameTagsFromObject(mObj.mNode,ignore = ['cgmType'])
                    mJnt.doStore('cgmType','skinJoint')
                    mJnt.doName()
                    ml_new.append(mJnt)
                    ml_joints.append(mJnt)
                    JOINT.freezeOrientation(mJnt.mNode)
                    
                    mJnt.p_parent = mRoot

            else:
                #if self.numBrowControl != self.numBrowJoints:
                #    log.warning("differing browJoints to controls not supported yet")
                
                ml_base = mPrerigNull.msgList_get('brow{0}JointHelpers'.format(_cap))
                for mObj in ml_base:
                    mJnt = mObj.doCreateAt('joint')
                    mJnt.doCopyNameTagsFromObject(mObj.mNode,ignore = ['cgmType'])
                    mJnt.doStore('cgmType','skinJoint')
                    mJnt.doName()
                    ml_new.append(mJnt)
                    ml_joints.append(mJnt)
                    JOINT.freezeOrientation(mJnt.mNode)
                    
                    mJnt.p_parent = mRoot
                #else:
                    #mCrv = self.getMessageAsMeta("brow{0}PreCurve".format(_cap))
                    
            mPrerigNull.msgList_connect('brow{0}Joints'.format(_cap), ml_new)
            
                
    #>> ===========================================================================
    mRigNull.msgList_connect('moduleJoints', ml_joints)
    self.msgList_connect('moduleJoints', ml_joints)
    #self.atBlockUtils('skeleton_connectToParent')

    for mJnt in ml_joints:
        mJnt.displayLocalAxis = 1
        #mJnt.radius = _radius
        mJnt.doConnectIn('radius',self.asAttrString('jointRadius'))
        #self.doConnectOut('jointRadius',mJnt.asAttrString('radius'))
    for mJnt in ml_joints:mJnt.rotateOrder = 5
        
    return ml_joints    
    


#=============================================================================================================
#>> rig
#=============================================================================================================
#NOTE - self here is a rig Factory....

d_preferredAngles = {}#In terms of aim up out for orientation relative values, stored left, if right, it will invert
d_rotateOrders = {}

#Rig build stuff goes through the rig build factory ------------------------------------------------------
#@cgmGEN.Timer
def rig_prechecks(self):
    _str_func = 'rig_prechecks'
    log.debug(cgmGEN.logString_start(_str_func))
    
    mBlock = self.mBlock
    
    str_browSetup = mBlock.getEnumValueString('browSetup')
    if str_browSetup not in ['ribbon']:
        self.l_precheckErrors.append("Brow setup not completed: {0}".format(str_browSetup))
    
    str_browType = mBlock.getEnumValueString('browType')
    if str_browType not in ['full','split']:
        self.l_precheckErrors.append("Brow setup not completed: {0}".format(str_browType))
    
    if mBlock.scaleSetup:
        
        str_ribbonParam = mBlock.getEnumValueString('ribbonParam')
        str_squashMeasure = mBlock.getEnumValueString('squashMeasure')
        if str_squashMeasure in ['pointDist']:
            if str_ribbonParam in ['floating']:
                self.l_precheckErrors.append("Squash measure pointDist and floating ribbon param is pointless. Change ribbonParam to fixed or floating OR squashMeasure to arcLen")
        
        if str_browType in ['full']:
            if str_squashMeasure in ['arcLen']:
                self.l_precheckErrors.append("Full brow with arcLen setup not recommended")
    

#@cgmGEN.Timer
def rig_dataBuffer(self):
    _short = self.d_block['shortName']
    _str_func = 'rig_dataBuffer'
    log.debug("|{0}| >>  ".format(_str_func)+ '-'*80)
    log.debug("{0}".format(self))
    
    mBlock = self.mBlock
    mModule = self.mModule
    mRigNull = self.mRigNull
    mPrerigNull = mBlock.prerigNull
    self.mPrerigNull = mPrerigNull
    ml_handleJoints = mPrerigNull.msgList_get('handleJoints')
    mMasterNull = self.d_module['mMasterNull']
    
    mEyeFormHandle = mBlock.bbHelper
    
    self.mRootFormHandle = mEyeFormHandle
    ml_formHandles = [mEyeFormHandle]
    
    self.b_scaleSetup = mBlock.scaleSetup
    
    #self.str_browSetup = False
    #if mBlock.browSetup:
    #    self.str_browSetup  = mBlock.getEnumValueString('browSetup')
        
    for k in ['browSetup','buildSDK','browType']:
        self.__dict__['str_{0}'.format(k)] = ATTR.get_enumValueString(mBlock.mNode,k) or False
        
    self.b_SDKonly = False
    if self.str_buildSDK in ['only']:
        self.b_SDKonly = True
    
    #Logic checks ========================================================================
    l_handleKeys = (['center','left','right'])
    if not mBlock.buildCenter:
        l_handleKeys.remove('center')
    
    self.l_handleKeys = l_handleKeys
    
    
    #Squash stretch logic  =================================================================================
    log.debug("|{0}| >> Squash stretch..".format(_str_func))
    self.b_scaleSetup = mBlock.scaleSetup
    
    self.b_squashSetup = False
    
    self.d_squashStretch = {}
    
    _squashStretch = None
    if mBlock.squash:
        _squashStretch =  mBlock.getEnumValueString('squash')
        self.b_squashSetup = True
    self.d_squashStretch['squashStretch'] = _squashStretch
    
    _squashMeasure = None
    if mBlock.squashMeasure:
        _squashMeasure =  mBlock.getEnumValueString('squashMeasure')    
    self.d_squashStretch['squashStretchMain'] = _squashMeasure    

    _driverSetup = None
    if mBlock.ribbonAim:
        _driverSetup =  mBlock.getEnumValueString('ribbonAim')
    self.d_squashStretch['driverSetup'] = _driverSetup

    self.d_squashStretch['additiveScaleEnds'] = mBlock.scaleSetup
    self.d_squashStretch['extraSquashControl'] = mBlock.squashExtraControl
    self.d_squashStretch['squashFactorMax'] = mBlock.squashFactorMax
    self.d_squashStretch['squashFactorMin'] = mBlock.squashFactorMin
    
    log.debug("|{0}| >> self.d_squashStretch..".format(_str_func))    
    #pprint.pprint(self.d_squashStretch)
    

    #self.d_squashStretchIK['sectionSpans'] = 2

    
    log.debug("|{0}| >> self.b_scaleSetup: {1}".format(_str_func,self.b_scaleSetup))
    log.debug("|{0}| >> self.b_squashSetup: {1}".format(_str_func,self.b_squashSetup))
    #pprint.pprint(self.d_squashStretch)
    log.debug(cgmGEN._str_subLine)    
    

    #Offset ============================================================================ 
    self.v_offset = self.mPuppet.atUtils('get_shapeOffset')
    """
    str_offsetMode = ATTR.get_enumValueString(mBlock.mNode,'offsetMode')
    
    if not mBlock.getMayaAttr('offsetMode'):
        log.debug("|{0}| >> default offsetMode...".format(_str_func))
        self.v_offset = self.mPuppet.atUtils('get_shapeOffset')
    else:
        str_offsetMode = ATTR.get_enumValueString(mBlock.mNode,'offsetMode')
        log.debug("|{0}| >> offsetMode: {1}".format(_str_func,str_offsetMode))
        
        l_sizes = []
        for mHandle in ml_formHandles:
            _size_sub = POS.get_bb_size(mHandle,True)
            l_sizes.append( MATH.average(_size_sub) * .1 )            
        self.v_offset = MATH.average(l_sizes)"""
    log.debug("|{0}| >> self.v_offset: {1}".format(_str_func,self.v_offset))    
    log.debug(cgmGEN._str_subLine)
    
    #Size =======================================================================================
    self.v_baseSize = [mBlock.blockScale * v for v in mBlock.baseSize]
    self.f_sizeAvg = MATH.average(self.v_baseSize)
    log.debug("|{0}| >> size | self.v_baseSize: {1} | self.f_sizeAvg: {2}".format(_str_func,
                                                                                  self.v_baseSize,
                                                                                  self.f_sizeAvg ))
    
    #Settings =============================================================================
    mModuleParent =  self.d_module['mModuleParent']
    if mModuleParent:
        mSettings = mModuleParent.rigNull.settings
    else:
        log.debug("|{0}| >>  using puppet...".format(_str_func))
        mSettings = self.d_module['mMasterControl'].controlVis

    log.debug("|{0}| >> mSettings | self.mSettings: {1}".format(_str_func,mSettings))
    self.mSettings = mSettings
    
    log.debug("|{0}| >> self.mPlug_visSub_moduleParent: {1}".format(_str_func,
                                                                    self.mPlug_visSub_moduleParent))
    log.debug("|{0}| >> self.mPlug_visDirect_moduleParent: {1}".format(_str_func,
                                                                       self.mPlug_visDirect_moduleParent))
    
    #DynParents =============================================================================
    #self.UTILS.get_dynParentTargetsDat(self)
    #log.debug(cgmGEN._str_subLine)
    
    #rotateOrder =============================================================================
    _str_orientation = self.d_orientation['str']
    _l_orient = [_str_orientation[0],_str_orientation[1],_str_orientation[2]]
    self.ro_base = "{0}{1}{2}".format(_str_orientation[1],_str_orientation[2],_str_orientation[0])
    self.ro_head = "{2}{0}{1}".format(_str_orientation[0],_str_orientation[1],_str_orientation[2])
    self.ro_headLookAt = "{0}{2}{1}".format(_str_orientation[0],_str_orientation[1],_str_orientation[2])
    log.debug("|{0}| >> rotateOrder | self.ro_base: {1}".format(_str_func,self.ro_base))
    log.debug("|{0}| >> rotateOrder | self.ro_head: {1}".format(_str_func,self.ro_head))
    log.debug("|{0}| >> rotateOrder | self.ro_headLookAt: {1}".format(_str_func,self.ro_headLookAt))
    log.debug(cgmGEN._str_subLine)
    

    return True


#@cgmGEN.Timer
def rig_skeleton(self):
    _short = self.d_block['shortName']
    
    _str_func = 'rig_skeleton'
    log.debug("|{0}| >>  ".format(_str_func)+ '-'*80)
    log.debug("{0}".format(self))
        
    mBlock = self.mBlock
    mRigNull = self.mRigNull
    mPrerigNull = mBlock.prerigNull
    
    ml_jointsToConnect = []
    ml_jointsToHide = []
    ml_joints = mRigNull.msgList_get('moduleJoints')
    self.d_joints['ml_moduleJoints'] = ml_joints
    
    
    BLOCKUTILS.skeleton_pushSettings(ml_joints, self.d_orientation['str'],
                                     self.d_module['mirrorDirection'])
                                     #d_rotateOrders, d_preferredAngles)
    
    
    #Rig Joints =================================================================================
    ml_rigJoints = BLOCKUTILS.skeleton_buildDuplicateChain(mBlock,
                                                           ml_joints,
                                                           'rig',
                                                           self.mRigNull,
                                                           'rigJoints',
                                                           'rig',
                                                           cgmType = False,
                                                           blockNames=False)
    
    
    if not self.b_SDKonly:
        ml_segmentJoints = BLOCKUTILS.skeleton_buildDuplicateChain(mBlock,ml_joints, None,
                                                                   mRigNull,'segmentJoints','seg',
                                                                   cgmType = 'segJnt')    
        ml_jointsToHide.extend(ml_segmentJoints)
    else:
        for mJnt in ml_rigJoints:
            mJnt.p_parent = False
    
    #Brow joints ================================================================================
    log.debug("|{0}| >> Brow Joints...".format(_str_func)+ '-'*40)
    
    #Need to sort our joint lists:
    md_skinJoints = {'brow':{}}
    md_rigJoints = {'brow':{}}
    md_segJoints = {'brow':{}}
    md_directShapes = {'brow':{}}
    

    
    for k in self.l_handleKeys:
        log.debug("|{0}| >> {1}...".format(_str_func,k))        
        ml_skin = self.mPrerigNull.msgList_get('brow{0}Joints'.format(k.capitalize()))
        ml_directShapes = self.mPrerigNull.msgList_get('brow{0}JointShapes'.format(k.capitalize()))            
        md_skinJoints['brow'][k] = ml_skin
        ml_rig = []
        ml_seg = []
        
        for mJnt in ml_skin:
            mRigJoint = mJnt.getMessageAsMeta('rigJoint')
            ml_rig.append(mRigJoint)
            
            if not self.b_SDKonly:
                mSegJoint = mJnt.getMessageAsMeta('segJoint')
                ml_seg.append(mSegJoint)
                mSegJoint.p_parent = False
            
                mRigJoint.p_parent = mSegJoint
            
        md_rigJoints['brow'][k] = ml_rig
        md_segJoints['brow'][k] = ml_seg
        md_directShapes['brow'][k] = ml_directShapes
        
    """
    for i,mJnt in enumerate(ml_rigJoints):
        mJnt.parent = ml_segmentJoints[i]
        mJnt.connectChildNode(ml_segmentJoints[i],'driverJoint','sourceJoint')#Connect
    ml_jointsToHide.extend(ml_segmentJoints)        
        """
    log.debug(cgmGEN._str_subLine)
    md_handles = {'brow':{}}
    md_handleShapes = {'brow':{}}    
    if not self.b_SDKonly:
    
        #Brow Handles ================================================================================
        log.debug("|{0}| >> Brow Handles...".format(_str_func)+ '-'*40)    
        #mBrowCurve = mBlock.getMessageAsMeta('browLineloftCurve')
        #_BrowCurve = mBrowCurve.getShapes()[0]

        
        #if self.str_browType == 'full':
        #    else:
        #    l_handleKeys = ['left','right']
        
        for k in self.l_handleKeys:
            log.debug("|{0}| >> {1}...".format(_str_func,k))        
            ml_helpers = self.mPrerigNull.msgList_get('brow{0}PrerigHandles'.format(k.capitalize()))
            ml_handleShapes = self.mPrerigNull.msgList_get('brow{0}PrerigShapes'.format(k.capitalize()))
            
            ml_new = []
            for mHandle in ml_helpers:
                mJnt = mHandle.doCreateAt('joint')
                mJnt.doCopyNameTagsFromObject(mHandle.mNode,ignore = ['cgmType'])
                #mJnt.doStore('cgmType','dag')
                mJnt.doName()
                ml_new.append(mJnt)
                ml_joints.append(mJnt)
                JOINT.freezeOrientation(mJnt.mNode)
                mJnt.p_parent = False
                mJnt.p_position = mHandle.p_position
                #DIST.get_closest_point(mHandle.mNode,_BrowCurve,True)[0]
    
            md_handles['brow'][k] = ml_new
            md_handleShapes['brow'][k] = ml_handleShapes
            
            ml_jointsToHide.extend(ml_new)
        log.debug(cgmGEN._str_subLine)
    
    self.md_rigJoints = md_rigJoints
    self.md_skinJoints = md_skinJoints
    self.md_segJoints = md_segJoints
    self.md_handles = md_handles
    self.md_handleShapes = md_handleShapes
    self.md_directShapes = md_directShapes
    #...joint hide -----------------------------------------------------------------------------------
    for mJnt in ml_jointsToHide:
        try:mJnt.drawStyle =2
        except:mJnt.radius = .00001
            
    #...connect... 
    self.fnc_connect_toRigGutsVis( ml_jointsToConnect )        
    return

#@cgmGEN.Timer
def rig_shapes(self):
    try:
        _short = self.d_block['shortName']
        _str_func = 'rig_shapes'
        log.debug("|{0}| >>  ".format(_str_func)+ '-'*80)
        log.debug("{0}".format(self))
        
    
        mBlock = self.mBlock
        #_baseNameAttrs = ATTR.datList_getAttrs(mBlock.mNode,'nameList')    
        mHandleFactory = mBlock.asHandleFactory()
        mRigNull = self.mRigNull
        mPrerigNull = self.mPrerigNull
        
        ml_rigJoints = mRigNull.msgList_get('rigJoints')
        
        if not self.b_SDKonly:
            #Brow center ================================================================================
            if self.str_browType == 'full':
                mBrowCenter = self.md_handles['brow']['center'][0].doCreateAt()
                mBrowCenterShape = self.md_handleShapes['brow']['center'][0].doDuplicate(po=False)
                mBrowCenterShape.scale = [1.5,1.5,1.5]
                
                mBrowCenter.doStore('cgmName','browMain')
                mBrowCenter.doName()
                
                CORERIG.shapeParent_in_place(mBrowCenter.mNode,
                                             mBrowCenterShape.mNode,False)
                
                mRigNull.connectChildNode(mBrowCenter,'browMain','rigNull')#Connect
                
                
            
            
            #Handles ================================================================================
            log.debug("|{0}| >> Handles...".format(_str_func)+ '-'*80)
            for k,d in self.md_handles.iteritems():
                log.debug("|{0}| >> {1}...".format(_str_func,k)+ '-'*40)
                for side,ml in d.iteritems():
                    log.debug("|{0}| >> {1}...".format(_str_func,side)+ '-'*10)
                    
                    if self.str_browType == 'split':
                        if side != 'center':
                            log.info("|{0}| >> split...".format(_str_func))
                            _tmpKey = 'brow{0}Main'.format( STR.capFirst(side))
                            mSide = ml[0].doCreateAt()
                            mSideShape = self.md_handleShapes['brow'][side][0].doDuplicate(po=False)
                            mSideShape.scale = [v * 2.0 for v in mSideShape.scale]
                            
                            
                            mSide.doStore('cgmName',_tmpKey)
                            mSide.doName()
                            
                            CORERIG.shapeParent_in_place(mSide.mNode,
                                                         mSideShape.mNode,False)
                            mRigNull.connectChildNode(mSide,_tmpKey,'rigNull')#Connect                        
                        

                    
                    for i,mHandle in enumerate(ml):
                        log.debug("|{0}| >> {1}...".format(_str_func,mHandle))
                        CORERIG.shapeParent_in_place(mHandle.mNode,
                                                     self.md_handleShapes[k][side][i].mNode)
                        
                        if side == 'center':
                            mHandleFactory.color(mHandle.mNode,side='center',controlType='sub')
                        
            

        #Direct ================================================================================
        log.debug("|{0}| >> Direct...".format(_str_func)+ '-'*80)
        
        for k,d in self.md_rigJoints.iteritems():
            log.debug("|{0}| >> {1}...".format(_str_func,k)+ '-'*40)
            for side,ml in d.iteritems():
                log.debug("|{0}| >> {1}...".format(_str_func,side)+ '-'*10)
                for i,mHandle in enumerate(ml):
                    log.debug("|{0}| >> {1}...".format(_str_func,mHandle))
                    CORERIG.shapeParent_in_place(mHandle.mNode,
                                                 self.md_directShapes[k][side][i].mNode)                    
                    """
                    crv = CURVES.create_fromName(name='cube',
                                                 direction = 'z+',
                                                 size = mHandle.radius*2)
                    SNAP.go(crv,mHandle.mNode)
                    mHandleFactory.color(crv,side=side,controlType='sub')
                    CORERIG.shapeParent_in_place(mHandle.mNode,
                                                 crv,keepSource=False)"""
        for mJnt in ml_rigJoints:
            try:
                mJnt.drawStyle =2
            except:
                mJnt.radius = .00001                
        return
    except Exception,error:
        cgmGEN.cgmExceptCB(Exception,error,msg=vars())


#@cgmGEN.Timer
def rig_controls(self):
    try:
        _short = self.d_block['shortName']
        _str_func = 'rig_controls'
        log.debug("|{0}| >>  ".format(_str_func)+ '-'*80)
        log.debug("{0}".format(self))
      
        mRigNull = self.mRigNull
        mBlock = self.mBlock
        ml_controlsAll = []#we'll append to this list and connect them all at the end
        mRootParent = self.mDeformNull
        ml_segmentHandles = []
        
        #mPlug_visSub = self.atBuilderUtils('build_visSub')
        mPlug_visDirect = self.mPlug_visDirect_moduleParent
        mPlug_visSub = self.mPlug_visSub_moduleParent
        self.atBuilderUtils('build_visModuleProxy')#...proxyVis wiring
        
        #ATTR.connect(self.mPlug_visModule.p_combinedShortName, 
        #             "{0}.visibility".format(self.mDeformNull.mNode))
        
        self.mDeformNull.overrideEnabled = 1
        ATTR.connect(self.mPlug_visModule.p_combinedShortName,
                     "{0}.overrideVisibility".format(self.mDeformNull.mNode))
        
        
        """
        cgmMeta.cgmAttr(self.mSettings,'visDirect_{0}'.format(self.d_module['partName']),
                                          value = True,
                                          attrType='bool',
                                          defaultValue = False,
                                          keyable = False,hidden = False)"""        
        
        b_sdk = False
        if self.str_buildSDK == 'dag':
            b_sdk = True
            
        if not self.b_SDKonly:
            if self.str_browType == 'full':
                mBrowMain = mRigNull.browMain
                _d = MODULECONTROL.register(mBrowMain,
                                            mirrorSide= self.d_module['mirrorDirection'],
                                            mirrorAxis="translateX,rotateY,rotateZ",
                                            makeAimable = False)
                ml_controlsAll.append(_d['mObj'])
                ml_segmentHandles.append(_d['mObj'])
            
        
                

                
            #Handles ================================================================================
            log.debug("|{0}| >> Handles...".format(_str_func)+ '-'*80)
            for k,d in self.md_handles.iteritems():
                log.debug("|{0}| >> {1}...".format(_str_func,k)+ '-'*40)
                for side,ml in d.iteritems():
                    log.debug("|{0}| >> {1}...".format(_str_func,side)+ '-'*10)
                    
                    if self.str_browType == 'split':
                        if side != 'center':
                            log.info("|{0}| >> split...".format(_str_func))
                            _tmpKey = 'brow{0}Main'.format( STR.capFirst(side))
                            mHandle = mRigNull.getMessageAsMeta(_tmpKey)
                            if mHandle:
                                _d = MODULECONTROL.register(mHandle,
                                                            mirrorSide= side,
                                                            addSDKGroup=b_sdk,
                                                            mirrorAxis="translateX,rotateY,rotateZ",
                                                            makeAimable = False)
                                
                                ml_controlsAll.append(_d['mObj'])
                                ml_segmentHandles.append(_d['mObj'])
                                
                                if side == 'right':
                                    log.debug("|{0}| >> mirrorControl connect".format(_str_func))                        
                                    mTarget = mRigNull.getMessageAsMeta('brow{0}Main'.format( STR.capFirst('left')))
                                    _d['mObj'].doStore('mirrorControl',mTarget)
                                    mTarget.doStore('mirrorControl',_d['mObj'])                                   
                    
                    
                    for i,mHandle in enumerate(ml):
                        log.debug("|{0}| >> {1}...".format(_str_func,mHandle))
                        _d = MODULECONTROL.register(mHandle,
                                                    mirrorSide= side,
                                                    addSDKGroup=b_sdk,
                                                    mirrorAxis="translateX,rotateY,rotateZ",
                                                    makeAimable = False)
                        
                        ml_controlsAll.append(_d['mObj'])
                        ml_segmentHandles.append(_d['mObj'])
                        
                        if side == 'right':
                            log.debug("|{0}| >> mirrorControl connect".format(_str_func))                        
                            mTarget = d['left'][i]
                            _d['mObj'].doStore('mirrorControl',mTarget)
                            mTarget.doStore('mirrorControl',_d['mObj'])                    
                    
        #Direct ================================================================================
        log.debug("|{0}| >> Direct...".format(_str_func)+ '-'*80)
        for k,d in self.md_rigJoints.iteritems():
            log.debug("|{0}| >> {1}...".format(_str_func,k)+ '-'*40)
            for side,ml in d.iteritems():
                log.debug("|{0}| >> {1}...".format(_str_func,side)+ '-'*10)
                for i,mHandle in enumerate(ml):
                    log.debug("|{0}| >> {1}...".format(_str_func,mHandle))
                    _d = MODULECONTROL.register(mHandle,
                                                typeModifier='direct',
                                                addSDKGroup= self.b_SDKonly,
                                                mirrorSide= side,
                                                mirrorAxis="translateX,rotateY,rotateZ",
                                                makeAimable = False)
                    
                    mObj = _d['mObj']
                    
                    ml_controlsAll.append(_d['mObj'])
                    
                    ATTR.set_hidden(mObj.mNode,'radius',True)        
                    if mObj.hasAttr('cgmIterator'):
                        ATTR.set_hidden(mObj.mNode,'cgmIterator',True)        
                
                    for mShape in mObj.getShapes(asMeta=True):
                        ATTR.connect(mPlug_visDirect.p_combinedShortName, "{0}.overrideVisibility".format(mShape.mNode))
                        
                    
                    if side == 'right':
                        log.debug("|{0}| >> mirrorControl connect".format(_str_func))                        
                        mTarget = d['left'][i]
                        mObj.doStore('mirrorControl',mTarget)
                        mTarget.doStore('mirrorControl',mObj)

       
        

            
        #Close out...
        mHandleFactory = mBlock.asHandleFactory()
        for mCtrl in ml_controlsAll:
            ATTR.set(mCtrl.mNode,'rotateOrder',self.ro_base)
            
            if mCtrl.hasAttr('radius'):
                ATTR.set(mCtrl.mNode,'radius',0)        
            
            ml_pivots = mCtrl.msgList_get('spacePivots')
            if ml_pivots:
                log.debug("|{0}| >> Coloring spacePivots for: {1}".format(_str_func,mCtrl))
                for mPivot in ml_pivots:
                    mHandleFactory.color(mPivot.mNode, controlType = 'sub')            
        """
        if mHeadIK:
            ATTR.set(mHeadIK.mNode,'rotateOrder',self.ro_head)
        if mHeadLookAt:
            ATTR.set(mHeadLookAt.mNode,'rotateOrder',self.ro_headLookAt)
            """
        mRigNull.msgList_connect('controlsFace',ml_controlsAll)
        mRigNull.msgList_connect('handleJoints',ml_segmentHandles,'rigNull')        
        mRigNull.msgList_connect('controlsAll',ml_controlsAll)
        mRigNull.moduleSet.extend(ml_controlsAll)
        mRigNull.faceSet.extend(ml_controlsAll)
        
    except Exception,error:
        cgmGEN.cgmExceptCB(Exception,error,msg=vars())


#@cgmGEN.Timer
def rig_frame(self):
    _short = self.d_block['shortName']
    _str_func = ' rig_rigFrame'
    
    log.debug("|{0}| >>  ".format(_str_func)+ '-'*80)
    log.debug("{0}".format(self))    

    mBlock = self.mBlock
    mRigNull = self.mRigNull
    mRootParent = self.mDeformNull
    mModule = self.mModule
    md_browMains = {}
    
    if self.b_SDKonly:
        for k,d in self.md_rigJoints.iteritems():
            log.debug("|{0}| >> {1}...".format(_str_func,k)+ '-'*40)
            for side,ml in d.iteritems():
                log.debug("|{0}| >> {1}...".format(_str_func,side)+ '-'*10)
                for i,mHandle in enumerate(ml):
                    log.debug("|{0}| >> {1}...".format(_str_func,mHandle))
                    mHandle.masterGroup.p_parent = mRootParent
        
        return
    
    if self.str_browType == 'full':
        mBrowMain = mRigNull.browMain
        mBrowMain.masterGroup.p_parent = self.mDeformNull
    elif self.str_browType == 'split':
        log.info("|{0}| >> split...".format(_str_func))
        
        
        for side in 'left','right':
            mHandle = mRigNull.getMessageAsMeta('brow{0}Main'.format( STR.capFirst(side)))
            md_browMains[side] = mHandle

            mHandle.masterGroup.p_parent = mRootParent

            
        
    #Parenting ============================================================================
    log.debug("|{0}| >>Parenting...".format(_str_func)+ '-'*80)
    
    for k,d in self.md_handles.iteritems():
        log.debug("|{0}| >> {1}...".format(_str_func,k)+ '-'*40)
        for side,ml in d.iteritems():
            log.debug("|{0}| >> {1}...".format(_str_func,side)+ '-'*10)
            for i,mHandle in enumerate(ml):
                mHandle.masterGroup.p_parent = self.mDeformNull
                
    for k,d in self.md_segJoints.iteritems():
        log.debug("|{0}| >> {1}...".format(_str_func,k)+ '-'*40)
        for side,ml in d.iteritems():
            log.debug("|{0}| >> {1}...".format(_str_func,side)+ '-'*10)
            for i,mHandle in enumerate(ml):
                mHandle.p_parent = self.mDeformNull
        
    
    #Brow Ribbon ============================================================================
    log.debug("|{0}| >> Brow ribbon...".format(_str_func)+ '-'*80)
    
    md_seg = self.md_segJoints
    md_brow = md_seg['brow']
    ml_right = copy.copy(md_brow['right'])
    if mBlock.buildCenter:
        ml_center = md_brow['center']
    else:
        ml_center = False
        
    ml_left = md_brow['left']

    md_handles = self.md_handles
    md_brow = md_handles['brow']
    ml_rightHandles = copy.copy(md_brow['right'])
    ml_leftHandles = md_brow['left']
    
    ml_centerHandles = False
    if mBlock.buildCenter:
        ml_centerHandles = md_brow['center']
    
    
    if self.b_scaleSetup:
        res_segScale = self.UTILS.get_blockScale(self,'segMeasure')
        mPlug_masterScale = res_segScale[0]
        mMasterCurve = res_segScale[1]
        
        mMasterCurve.p_parent = mRootParent
    
    
    if self.str_browType == 'split':
        d_sides = {'left':{'ribbonJoints':ml_left,
                           'skinDrivers':ml_leftHandles},
                   'right':{'ribbonJoints':ml_right,
                           'skinDrivers':ml_rightHandles}}
        
        for _side,dat in d_sides.iteritems():
            d_ik = {'jointList':[mObj.mNode for mObj in dat['ribbonJoints']],
                    'baseName' : self.d_module['partName'] + "_{0}".format(_side) + '_ikRibbon',
                    'extendEnds':True,
                    'attachEndsToInfluences':1,
                    'orientation':'xyz',
                    'loftAxis' : 'z',
                    'tightenWeights':False,
                    'driverSetup':'stable',#'stableBlend',
                    'squashStretch':None,
                    'settingsControl': self.mSettings.mNode,
                    'connectBy':'constraint',
                    'squashStretchMain':'arcLength',
                    'paramaterization':mBlock.getEnumValueString('ribbonParam'),
                    #masterScalePlug:mPlug_masterScale,
                    #'settingsControl': mSettings.mNode,
                    'extraSquashControl':True,
                    'influences':dat['skinDrivers'],
                    'moduleInstance' : self.mModule}    
            
            if self.b_scaleSetup:
                d_ik['masterScalePlug'] = mPlug_masterScale                
                d_ik.update(self.d_squashStretch)
            
            res_ribbon = IK.ribbon(**d_ik)
            
            
            if ml_center:
                mc.pointConstraint([md_brow['left'][0].mNode, md_brow['right'][0].mNode],
                                   ml_centerHandles[0].masterGroup.mNode,
                                   skip = 'z',
                                   maintainOffset=True)
                
                mc.parentConstraint([ml_centerHandles[0].mNode],
                                   ml_center[0].mNode,
                                   maintainOffset=True)            
        
    else:
        ml_right.reverse()
        ml_rightHandles.reverse()    
        
        if ml_center:
            ml_ribbonJoints = ml_right + ml_center + ml_left
            ml_skinDrivers = ml_rightHandles + ml_centerHandles + ml_leftHandles
            
        else:
            ml_ribbonJoints = ml_right + ml_left
            ml_skinDrivers = ml_rightHandles + ml_leftHandles
            
        
        d_ik = {'jointList':[mObj.mNode for mObj in ml_ribbonJoints],
                'baseName' : self.d_module['partName'] + '_ikRibbon',
                'orientation':'xyz',
                'loftAxis' : 'z',
                'tightenWeights':False,
                'driverSetup':'stable',#'stableBlend',
                'squashStretch':None,
                'settingsControl': self.mSettings.mNode,
                'connectBy':'constraint',
                'squashStretchMain':'arcLength',
                'paramaterization':mBlock.getEnumValueString('ribbonParam'),
                #masterScalePlug:mPlug_masterScale,
                #'settingsControl': mSettings.mNode,
                'extraSquashControl':True,
                'influences':ml_skinDrivers,
                'moduleInstance' : self.mModule}    
        
        if self.b_scaleSetup:
            d_ik['masterScalePlug'] = mPlug_masterScale
            d_ik.update(self.d_squashStretch)
            
        res_ribbon = IK.ribbon(**d_ik)
    
    #Setup some constraints============================================================================
    if self.str_browType == 'full':
        md_brow['center'][0].masterGroup.p_parent = mBrowMain
        
        if ml_center:
            mc.pointConstraint([md_brow['left'][0].mNode, md_brow['right'][0].mNode],
                               md_brow['center'][0].masterGroup.mNode,
                               skip = 'z',
                               maintainOffset=True)
            
    
    for side in ['left','right']:
        ml = md_brow[side]
        if self.str_browType == 'full':
            ml[0].masterGroup.p_parent = mBrowMain
            
        if self.str_browType == 'split':
            for mObj in ml:
                if not mObj.getConstraintsTo():
                    mObj.masterGroup.p_parent = md_browMains[side]
                    
                    
        mc.pointConstraint([ml[0].mNode, ml[-1].mNode],
                           ml[1].masterGroup.mNode,
                           maintainOffset=True)
        
        if side == 'left':
            _v_aim = [-1,0,0]
        else:
            _v_aim = [1,0,0]
            
        mc.aimConstraint([ml[-1].mNode],
                         ml[1].masterGroup.mNode,
                         maintainOffset = True, weight = 1,
                         aimVector = _v_aim,
                         upVector = [0,1,0],
                         worldUpVector = [0,1,0],
                         worldUpObject = ml[-1].masterGroup.mNode,
                         worldUpType = 'objectRotation')            
        
        

        
    #pprint.pprint(vars())

    return


#@cgmGEN.Timer
def rig_cleanUp(self):
    _short = self.d_block['shortName']
    _str_func = 'rig_cleanUp'
    log.debug("|{0}| >>  ".format(_str_func)+ '-'*80)
    log.debug("{0}".format(self))
    
    mBlock = self.mBlock
    mRigNull = self.mRigNull
    
    mMasterControl= self.d_module['mMasterControl']
    mMasterDeformGroup= self.d_module['mMasterDeformGroup']    
    mMasterNull = self.d_module['mMasterNull']
    mModuleParent = self.d_module['mModuleParent']
    mPlug_globalScale = self.d_module['mPlug_globalScale']
    

    #Settings =================================================================================
    #log.debug("|{0}| >> Settings...".format(_str_func))
    #mSettings.visDirect = 0
    
    #mPlug_FKIK = cgmMeta.cgmAttr(mSettings,'FKIK')
    #mPlug_FKIK.p_defaultValue = 1
    #mPlug_FKIK.value = 1
        
    #Lock and hide =================================================================================
    ml_controls = mRigNull.msgList_get('controlsAll')
    self.UTILS.controls_lockDown(ml_controls)
    
    if not mBlock.scaleSetup:
        log.debug("|{0}| >> No scale".format(_str_func))
        ml_controlsToLock = copy.copy(ml_controls)
        for mCtrl in ml_controlsToLock:
            ATTR.set_standardFlags(mCtrl.mNode, ['scale'])
    else:
        log.debug("|{0}| >>  scale setup...".format(_str_func))
        
        
    self.mDeformNull.dagLock(True)

    #Close out ===============================================================================================
    mRigNull.version = self.d_block['buildVersion']
    mBlock.blockState = 'rig'
    mBlock.UTILS.set_blockNullFormState(mBlock)
    self.UTILS.rigNodes_store(self)


def create_simpleMesh(self,  deleteHistory = True, cap=True):
    _str_func = 'create_simpleMesh'
    log.debug("|{0}| >>  ".format(_str_func)+ '-'*80)
    log.debug("{0}".format(self))
    
    #>> Head ===================================================================================
    log.debug("|{0}| >> Head...".format(_str_func))
    
    mGroup = self.msgList_get('headMeshProxy')[0].getParent(asMeta=True)
    l_headGeo = mGroup.getChildren(asMeta=False)
    ml_headStuff = []
    for i,o in enumerate(l_headGeo):
        log.debug("|{0}| >> geo: {1}...".format(_str_func,o))                    
        if ATTR.get(o,'v'):
            log.debug("|{0}| >> visible head: {1}...".format(_str_func,o))            
            mObj = cgmMeta.validateObjArg(mc.duplicate(o, po=False, ic = False)[0])
            ml_headStuff.append(  mObj )
            mObj.p_parent = False
        

    if self.neckBuild:#...Neck =====================================================================
        log.debug("|{0}| >> neckBuild...".format(_str_func))    
        ml_neckMesh = self.UTILS.create_simpleLoftMesh(self,deleteHistory,cap)
        ml_headStuff.extend(ml_neckMesh)
        
    _mesh = mc.polyUnite([mObj.mNode for mObj in ml_headStuff],ch=False)
    _mesh = mc.rename(_mesh,'{0}_0_geo'.format(self.p_nameBase))
    
    return cgmMeta.validateObjListArg(_mesh)

def asdfasdfasdf(self, forceNew = True, skin = False):
    """
    Build our proxyMesh
    """
    _short = self.d_block['shortName']
    _str_func = 'build_proxyMesh'
    log.debug("|{0}| >>  ".format(_str_func)+ '-'*80)
    log.debug("{0}".format(self))
    
    mBlock = self.mBlock
    mRigNull = self.mRigNull
    mHeadIK = mRigNull.headIK
    mSettings = mRigNull.settings
    mPuppetSettings = self.d_module['mMasterControl'].controlSettings
    
    ml_rigJoints = mRigNull.msgList_get('rigJoints',asMeta = True)
    if not ml_rigJoints:
        raise ValueError,"No rigJoints connected"

    #>> If proxyMesh there, delete --------------------------------------------------------------------------- 
    _bfr = mRigNull.msgList_get('proxyMesh',asMeta=True)
    if _bfr:
        log.debug("|{0}| >> proxyMesh detected...".format(_str_func))            
        if forceNew:
            log.debug("|{0}| >> force new...".format(_str_func))                            
            mc.delete([mObj.mNode for mObj in _bfr])
        else:
            return _bfr
        
    #>> Head ===================================================================================
    log.debug("|{0}| >> Head...".format(_str_func))
    if directProxy:
        log.debug("|{0}| >> directProxy... ".format(_str_func))
        _settings = self.mRigNull.settings.mNode
        
    
    mGroup = mBlock.msgList_get('headMeshProxy')[0].getParent(asMeta=True)
    l_headGeo = mGroup.getChildren(asMeta=False)
    l_vis = mc.ls(l_headGeo, visible = True)
    ml_headStuff = []
    
    for i,o in enumerate(l_vis):
        log.debug("|{0}| >> visible head: {1}...".format(_str_func,o))
        
        mObj = cgmMeta.validateObjArg(mc.duplicate(o, po=False, ic = False)[0])
        ml_headStuff.append(  mObj )
        mObj.parent = ml_rigJoints[-1]
        
        ATTR.copy_to(ml_rigJoints[-1].mNode,'cgmName',mObj.mNode,driven = 'target')
        mObj.addAttr('cgmIterator',i)
        mObj.addAttr('cgmType','proxyGeo')
        mObj.doName()
        
        if directProxy:
            CORERIG.shapeParent_in_place(ml_rigJoints[-1].mNode,mObj.mNode,True,False)
            CORERIG.colorControl(ml_rigJoints[-1].mNode,_side,'main',directProxy=True)        
        
    if mBlock.neckBuild:#...Neck =====================================================================
        log.debug("|{0}| >> neckBuild...".format(_str_func))


def build_proxyMesh(self, forceNew = True, puppetMeshMode = False):
    """
    Build our proxyMesh
    """
    _str_func = 'build_proxyMesh'
    log.debug("|{0}| >>  ".format(_str_func)+ '-'*80)
    log.debug("{0}".format(self))
    
     
    mBlock = self
    mModule = self.moduleTarget
    mRigNull = mModule.rigNull
    mDeformNull = mModule.deformNull
    #mSettings = mRigNull.settings
    
    mPuppet = self.atUtils('get_puppet')
    mMaster = mPuppet.masterControl    
    mPuppetSettings = mMaster.controlSettings
    str_partName = mModule.get_partNameBase()
    mPrerigNull = mBlock.prerigNull
    
    _side = BLOCKUTILS.get_side(self)
    
    ml_rigJoints = mRigNull.msgList_get('rigJoints',asMeta = True)
    if not ml_rigJoints:
        raise ValueError,"No rigJoints connected"
    
    #self.v_baseSize = [mBlock.blockScale * v for v in mBlock.baseSize]
    
    #>> If proxyMesh there, delete --------------------------------------------------------------------------- 
    if puppetMeshMode:
        _bfr = mRigNull.msgList_get('puppetProxyMesh',asMeta=True)
        if _bfr:
            log.debug("|{0}| >> puppetProxyMesh detected...".format(_str_func))            
            if forceNew:
                log.debug("|{0}| >> force new...".format(_str_func))                            
                mc.delete([mObj.mNode for mObj in _bfr])
            else:
                return _bfr        
    else:
        _bfr = mRigNull.msgList_get('proxyMesh',asMeta=True)
        if _bfr:
            log.debug("|{0}| >> proxyMesh detected...".format(_str_func))            
            if forceNew:
                log.debug("|{0}| >> force new...".format(_str_func))                            
                mc.delete([mObj.mNode for mObj in _bfr])
            else:
                return _bfr
        
    ml_proxy = []
    ml_curves = []
    
    
    #Get our brow geo
    mBrowLoft = self.getMessageAsMeta('browFormLoft')
    
    d_kws = {'mode':'default',
             'uNumber':self.numSplit_u,
             'vNumber':self.numSplit_v,
             }
    mMesh = RIGCREATE.get_meshFromNurbs(mBrowLoft,**d_kws)    
    ml_proxy.append(mMesh)
    
    #Get our rig joints =====================================================================
    ml_exists = mRigNull.msgList_get('proxyJoints',asMeta=0)
    if ml_exists:
        mc.delete(ml_exists)
        
    md_defineObjs = {}
    
    ml_defineHandles = self.msgList_get('defineSubHandles')
    for mObj in ml_defineHandles:
        md_defineObjs[mObj.handleTag] = mObj
        
    l_toDo = ['peak']#'base'

    l_sideKeys = ['peak_2','peak_3',
                  'brow_4',
                  #'base_1','base_2','base_3','base_4'
                  'base_3','base_4'
                  ]
    for k in l_sideKeys:
        l_toDo.append(k+'_left')
        l_toDo.append(k+'_right')
        
    ml_proxyJoints= []
    for k in l_toDo:
        mJoint = self.doCreateAt('joint')
        mJoint.p_position = md_defineObjs[k].p_position
        mJoint.p_parent = mDeformNull
        mJoint.v=False
        mJoint.dagLock()
        ml_proxyJoints.append(mJoint)

    mRigNull.msgList_connect('proxyJoints', ml_proxyJoints)

    #Create new rig joints
    #Skin them all to the brow
    
    
    """
    #Brow -------------
    mUprCurve = mBlock.getMessageAsMeta('browUprloftCurve')
    mUprUse = mUprCurve.doDuplicate(po=False)
    mUprUse.p_parent = mRigNull.constrainNull
    mUprCurve.v=False
    ml_curves.append(mUprUse)
    md_rigJoints = {'brow':{}}
    for k in ['center','left','right']:
        log.debug("|{0}| >> {1}...".format(_str_func,k))        
        ml_skin = mPrerigNull.msgList_get('brow{0}Joints'.format(k.capitalize()))
        ml_rig = []
        for mJnt in ml_skin:
            mRigJoint = mJnt.getMessageAsMeta('rigJoint')
            ml_rig.append(mRigJoint)        
        md_rigJoints['brow'][k] = ml_rig
        
    ml_right = copy.copy(md_rigJoints['brow']['right'])
    ml_right.reverse()
    ml_followJoints = ml_right + md_rigJoints['brow']['center'] + md_rigJoints['brow']['left']

    
    _crv = mc.curve(d=1,p=[mObj.p_position for mObj in ml_followJoints])
    mCrv = cgmMeta.validateObjArg(_crv,'cgmObject',setClass=True)
    mCrv.p_parent = mRigNull
    mCrv.rename('{0}_proxyBrowCurve'.format(self.d_module['partName']))            
    mCrv.v=False
    ml_curves.append(mCrv)

    l_clusters = []
    for i,cv in enumerate(mCrv.getComponents('cv')):
        _res = mc.cluster(cv, n = 'test_{0}_{1}_pre_cluster'.format(self.d_module['partName'],i))
        TRANS.parent_set( _res[1],ml_followJoints[i].mNode)
        l_clusters.append(_res)
        ATTR.set(_res[1],'visibility',False)

    #pprint.pprint(l_clusters)
    mc.rebuildCurve(mCrv.mNode, d=3, keepControlPoints=False,ch=1,s=8,
                    n="{0}_reparamRebuild".format(self.d_module['partName']))    

    #Loft ------------------------------------------------
    _res_body = mc.loft([mCrv.mNode,mUprUse.mNode], 
                        o = True, d = 1, po = 3, c = False,ch=True,autoReverse=False)
    mLoftSurface = cgmMeta.validateObjArg(_res_body[0],'cgmObject',setClass= True)
    _loftNode = _res_body[1]
    _inputs = mc.listHistory(mLoftSurface.mNode,pruneDagObjects=True)
    _rebuildNode = _inputs[0]            
    mLoftSurface = cgmMeta.validateObjArg(_res_body[0],'cgmObject',setClass= True)

    #if polyType == 'bezier':
    mc.reverseSurface(mLoftSurface.mNode, direction=1,rpo=True)

    _d = {'keepCorners':False}#General}


    mLoftSurface.overrideEnabled = 1
    mLoftSurface.overrideDisplayType = 2

    mLoftSurface.p_parent = self.mModule
    mLoftSurface.resetAttrs()

    mLoftSurface.doStore('cgmName',"{0}_{1}brow".format(self.d_module['partName'],k),attrType='string')
    mLoftSurface.doStore('cgmType','proxy')
    mLoftSurface.doName()
    log.info("|{0}| loft node: {1}".format(_str_func,_loftNode))             



    #mLoft = mBlock.getMessageAsMeta('{0}LidFormLoft'.format(tag))
    #mMesh = mLoft.doDuplicate(po=False, ic=False)
    #mDag = mRigJoint.doCreateAt(setClass='cgmObject')
    #CORERIG.shapeParent_in_place(mDag.mNode, mMesh.mNode,False)
    #mDag.p_parent = mRigJoint
    ml_proxy.append(mLoftSurface)
        
    """


    for mProxy in ml_proxy:
        CORERIG.colorControl(mProxy.mNode,_side,'main',transparent=False,proxy=True)
        mc.makeIdentity(mProxy.mNode, apply = True, t=1, r=1,s=1,n=0,pn=1)

        #Vis connect -----------------------------------------------------------------------
        mProxy.overrideEnabled = 1
        ATTR.connect("{0}.proxyVis_out".format(mRigNull.mNode),"{0}.visibility".format(mProxy.mNode) )
        ATTR.connect("{0}.proxyLock".format(mPuppetSettings.mNode),"{0}.overrideDisplayType".format(mProxy.mNode) )
        for mShape in mProxy.getShapes(asMeta=1):
            str_shape = mShape.mNode
            mShape.overrideEnabled = 0
            #ATTR.connect("{0}.proxyVis".format(mPuppetSettings.mNode),"{0}.visibility".format(str_shape) )
            ATTR.connect("{0}.proxyLock".format(mPuppetSettings.mNode),"{0}.overrideDisplayTypes".format(str_shape) )
            
    #if directProxy:
    #    for mObj in ml_rigJoints:
    #        for mShape in mObj.getShapes(asMeta=True):
                #mShape.overrideEnabled = 0
    #            mShape.overrideDisplayType = 0
    #            ATTR.connect("{0}.visDirect".format(_settings), "{0}.overrideVisibility".format(mShape.mNode))
    """
    reload(MRSPOST)
    MRSPOST.skin_mesh(mMesh,ml_rigJoints+ml_proxyJoints,**{'maximumInfluences':6,'heatmapFalloff':10,'dropoffRate':2.5})"""
    
    
    mc.skinCluster ([mJnt.mNode for mJnt in ml_rigJoints + ml_proxyJoints],
                    mMesh.mNode,
                    tsb=True,
                    bm=1,
                    sm=0,
                    maximumInfluences = 5,
                    normalizeWeights = 1, dropoffRate=4)

    
    mRigNull.msgList_connect('proxyMesh', ml_proxy + ml_curves)
    """
    _sl = []
    for mObj in ml_proxyJoints + ml_rigJoints:
        _sl.append(mObj.mNode)
    mc.select(_sl)"""
# ======================================================================================================
# UI 
# -------------------------------------------------------------------------------------------------------

def uiBuilderMenu(self,parent = None):
    #uiMenu = mc.menuItem( parent = parent, l='Head:', subMenu=True)
    _short = self.p_nameShort
    
    mc.menuItem(en=False,divider=True,
                label = "Brow")
    
    #mc.menuItem(ann = '[{0}] Snap state handles to surface'.format(_short),
    #            c = cgmGEN.Callback(uiFunc_snapStateHandles,self),
    #            label = "Snap state handles")
    
    mc.menuItem(ann = '[{0}] Snap state handles objects to the selected'.format(_short),
                c = cgmGEN.Callback(uiFunc_snapStateHandles,self),
                label = "Snap State Handles")
    
    mc.menuItem(ann = '[{0}] Get define space'.format(_short),
                c = cgmGEN.Callback(uiFunc_getDefineScaleSpace,self),
                label = "Get DefineScaleSpace")    

    
    
    #mc.menuItem(en=True,divider = True,
    #            label = "Utilities")
    
    #_sub = mc.menuItem(en=True,subMenu = True,tearOff=True,
    #                   label = "State Picker")
    
    #self.atUtils('uiStatePickerMenu',parent)
    
    #self.UTILS.uiBuilderMenu(self,parent)
    
    return

_handleKey = {'define':'defineSubHandles',
              'form':'formHandles',
              'prerig':'prerigHandles'}



def uiFunc_snapStateHandles(self,ml=None):
    if not ml:
        ml = cgmMeta.asMeta(mc.ls(sl=1))
    
    if not ml:
        log.warning("Nothing Selected")
        return False
    
    _state = self.p_blockState    
    ml_handles = self.msgList_get(_handleKey.get(_state))
    
    for mObj in ml_handles:
        try:mObj.p_position = DIST.get_closest_point(mObj.mNode, ml[0].mNode)[0]
        except Exception,err:
            log.warning("Failed to snap: {0} | {1}".format(mObj.mNode,err))

def uiFunc_getDefineScaleSpace(self):
    ml_handles = self.msgList_get('defineHandles')
    for mObj in ml_handles:
        if 'Left' in mObj.handleTag:
            ml_handles.remove(mObj)
            
    self.atUtils('get_handleScaleSpace',ml_handles)
    














