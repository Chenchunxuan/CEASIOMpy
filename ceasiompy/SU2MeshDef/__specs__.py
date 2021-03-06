#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from ceasiompy.utils.moduleinterfaces import CPACSInOut, AIRCRAFT_XPATH, CEASIOM_XPATH, SU2_XPATH


# ===== RCE integration =====

RCE = {
    "name": "SU2MeshDef",
    "description": "Module to create new deformed meshes with SU2 mesh deformation",
    "exec": "pwd\npython su2meshdef.py",
    "author": "Aidan Jungo",
    "email": "aidan.jungo@cfse.ch",
}

# ===== CPACS inputs and outputs =====

cpacs_inout = CPACSInOut()

# ----- Input -----

cpacs_inout.add_input(
    var_name='nb_proc',
    var_type=int,
    default_value=1,
    unit='1',
    descr='Number of proc to use to run SU2',
    xpath=CEASIOM_XPATH + '/aerodynamics/su2/settings/nbProc',
    gui=True,
    gui_name='Nb of processor',
    gui_group='CPU',
)

cpacs_inout.add_input(
    var_name='su2_mesh_path',
    var_type='pathtype',
    default_value='-',
    unit='1',
    descr='Absolute path of the SU2 mesh',
    xpath=CEASIOM_XPATH + '/filesPath/su2Mesh',
    gui=True,
    gui_name='SU2 Mesh',
    gui_group='Inputs',
)

cpacs_inout.add_input(
    var_name='control_surf',
    var_type=bool,
    default_value=False,
    unit='1',
    descr='To check if control surfaces deflections should be calculated or not',
    xpath=CEASIOM_XPATH + '/aerodynamics/su2/options/clalculateCotrolSurfacesDeflections',
    gui=True,
    gui_name='Control Surfaces',
    gui_group='Inputs',
)

# TODO: add TED,deflection and symetry selection

cpacs_inout.add_input(
    var_name='ref_len',
    var_type=float,
    default_value=None,
    unit='m',
    descr='Reference length of the aircraft',
    xpath=AIRCRAFT_XPATH + '/model/reference/length',
    gui=False,
    gui_name=None,
    gui_group=None,
)

cpacs_inout.add_input(
    var_name='ref_area',
    var_type=float,
    default_value=None,
    unit='m^2',
    descr='Reference area of the aircraft',
    xpath=AIRCRAFT_XPATH + '/model/reference/area',
    gui=False,
    gui_name=None,
    gui_group=None,
)

for direction in ['x', 'y', 'z']:
    cpacs_inout.add_input(
        var_name=f'ref_ori_moment_{direction}',
        var_type=float,
        default_value=0.0,
        unit='m',
        descr=f"Fuselage scaling on {direction} axis",
        xpath=AIRCRAFT_XPATH + f'/model/reference/point/{direction}',
        gui=False,
        gui_name=None,
        gui_group=None,
    )



# ----- Output -----

# TODO: add it or not?
# cpacs_inout.add_output(
#     var_name='wetted_area',
#     var_type=float,
#     default_value=None,
#     unit='m^2',
#     descr='Aircraft wetted area calculated by SU2',
#     xpath=CEASIOM_XPATH + '/geometry/analyses/wettedArea',
# )

cpacs_inout.add_output(
    var_name='su2_def_mesh_list',
    var_type=list,
    default_value=None,
    unit='1',
    descr='List of SU2 deformed meshes generated by SU2MeshDef',
    xpath=SU2_XPATH + '/availableDeformedMesh',
)

cpacs_inout.add_output(
    var_name='bc_wall_list',
    var_type=list,
    default_value=None,
    unit='1',
    descr='Wall boundary conditions found in the SU2 mesh',
    xpath=CEASIOM_XPATH + '/aerodynamics/su2/boundaryConditions/wall'
)
