"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Module to run SU2 Calculation in CEASIOMpy

Python version: >=3.6

| Author : Aidan Jungo
| Creation: 2018-11-06
| Last modifiction: 2019-08-21

TODO:

    * Add possibility of using SSH
    * Save all results in CPACS output file (AeroMap)
    * Change su2 log file (for each case and wetted_area)
    * Add checks on the code
    * Create test functions
    * chech input and output in __specs__

"""

#==============================================================================
#   IMPORTS
#==============================================================================

import os
import sys
import math
import shutil
from shutil import ignore_patterns

from ceasiompy.utils.ceasiomlogger import get_logger
from ceasiompy.utils.cpacsfunctions import open_tixi, close_tixi, \
                                           create_branch, get_value
from ceasiompy.utils.apmfunctions import save_aero_coef, get_apm_xpath, AeroCoefficient

log = get_logger(__file__.split('.')[0])

MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
TMP_DIR = MODULE_DIR + '/tmp'

SU2_XPATH = '/cpacs/toolspecific/CEASIOMpy/aerodynamics/su2'
SU2_LOGFILE_PATH = MODULE_DIR + '/tmp/logSU2calculation.log'

#==============================================================================
#   CLASSES
#==============================================================================


#==============================================================================
#   FUNCTIONS
#==============================================================================

# Maybe make that a general function
def save_timestamp(tixi, xpath):
    """Function to get start and end time of an SU2 calculation.

    Function 'get_efficiency' the CL/CD ratio in the results file
    (forces_breakdown.dat)

    Args:
        tixi (handles): TIXI Handle of the CPACS file
        xpath (str): XPath where start and end time will be stored

    Returns:
        tixi (handles): Modified TIXI Handle

    """

    logfile_name = __file__.split('.')[0] + '.log'

    start_time = None
    end_time = None

    with open(logfile_name) as f:
        for line in f.readlines():
            if '>>> SU2 Start Time' in line:
                start_time = line.split(' - ')[0]
            if '>>> SU2 End Time' in line:
                end_time = line.split(' - ')[0]

    if start_time == None:
        log.warning("SU2 Start time has not been found in the logfile!")
    if end_time == None:
        log.warning("SU2 End time has not been found in the logfile!")

    tixi = create_branch(tixi,xpath+'/startTime')
    tixi.updateTextElement(xpath+'/startTime',start_time)
    tixit = create_branch(tixi,xpath+'/endTime')
    tixi.updateTextElement(xpath+'/endTime',end_time)

    return tixi


# Maybe could be remove or modified when aeroMap works
def get_efficiency(force_path):
    """Function to get efficiency (CL/CD)

    Function 'get_efficiency' the CL/CD ratio in the results file
    (forces_breakdown.dat)

    Args:
        force_path (str): Path to the Force Breakdown result file

    Returns:
        cl_cd (float): CL/CD ratio [-]

    """

    cl_cd = None

    with open(force_path) as f:
        for line in f.readlines():
            if 'CL/CD' in line:
                cl_cd = float(line.split(':')[1].split('|')[0])
                break
    if cl_cd is None:
        raise ValueError('No value has been found for the CL/CD ratio!')
    else:
        log.info('CL/CD ratio has been found and is equal to: ' \
                  + str(cl_cd) + '[-]')
        return cl_cd


def get_wetted_area():
    """ Function save wetted area calculated by SU2

    Function 'get_wetted_area' reads the wetted area value in the logfile
    generated by SU2 at each calculations.

    Returns:
        wetted_area (float): Wetted area calculated by SU2 [m^2]

    """

    wetted_area = None

    with open(SU2_LOGFILE_PATH) as f:
        for line in f.readlines():
            if 'Wetted area =' in line:
                wetted_area = float(line.split(' ')[3])
                break

    if wetted_area is None:
        raise ValueError('No value has been found for the wetted area!')
    else:
        log.info('Wetted area value has been found and is equal to '
                  + str(wetted_area) + ' [m^2]')
        return wetted_area


def run_SU2(mesh_path, config_path):
    """ Function to run SU2 calculation

    Function 'run_SU2' runs a SU2 calculation with an SU2 Mesh (.su2) and an
    SU2 configuration file (.cfg)

    Source :
        * SU2 Turorials : https://su2code.github.io/tutorials/home/

    Args:
        mesh_path (str): Path to the mesh file
        config_path (str): Path to the config file

    """

    # Define paths

    config_name = 'ToolOutput.cfg'
    force_path = MODULE_DIR + '/ToolOutput/forces_breakdown.dat'

    # Remove /tmp directory
    if os.path.exists(TMP_DIR):
        shutil.rmtree(TMP_DIR)
        log.info('The /tmp directory has been removed.')

    # Copy SU2 config files (.cfg) in the temp directory
    shutil.copytree(config_path, TMP_DIR, ignore=ignore_patterns('*.xml'))
    if os.path.isdir(TMP_DIR):
        log.info('The input SU2 config file has been copied in /tmp ')
    else:
        raise OSError('No config directory has been copied in /temp')

    # Check intallation of SU2 and MPI
    su2_run_install_path = shutil.which("SU2_CFD")
    su2_sol_install_path = shutil.which("SU2_SOL")
    mpi_install_path = shutil.which('mpirun')

    if  su2_run_install_path:
        log.info('"SU2_CFD" is intall in: ' + su2_run_install_path)
    else:
        raise RuntimeError('"SU2_CFD" is not install on your computer')

    if su2_sol_install_path:
        log.info('"SU2_SOL" is intall in: ' + su2_sol_install_path)
    else:
        raise RuntimeError('"SU2_SOL" is not install on your computer_')

    if mpi_install_path:
        log.info('"mpirun" is intall in: ' + mpi_install_path)

        proc_nb = os.cpu_count()
        log.info('Number of proc on your computer: ' + str(proc_nb))

        su2_command = 'mpirun -np ' + str(proc_nb) + ' ' + su2_run_install_path + ' '
    else:
        log.warning('"mpirun" is not install on your computeur!')
        log.info('SU2 will be executed only on 1 proc')

        su2_command = su2_run_install_path + ' '

    logfile = ' > ' + SU2_LOGFILE_PATH
    command_line = [su2_command, config_name, logfile]

    # Run the command from the /tmp directory
    os.chdir(TMP_DIR)
    log.info('>>> SU2 Start Time')
    config_dir_list = os.listdir(TMP_DIR)
    for config_dir in config_dir_list:
        os.chdir(config_dir)
        os.system(''.join(command_line))
        os.system('/soft/SU2/bin/SU2_SOL ' + config_name)

        # force_file_name = 'forces_breakdown.dat'
        # if os.path.isfile(force_file_name):
        #     shutil.copy(force_tmp_path, force_path)
        #     log.info('The Force Breakdown file has been copied in /ToolOutput ')
        # else:
        #     log.error('The Force Breakdown file cannot be found!')
        #     return None
        # TODO: don't need to copy, get results with take care of that

        os.chdir(TMP_DIR)

    log.info('>>> SU2 End Time')

    os.chdir(MODULE_DIR)



def get_su2_results(cpacs_path,cpacs_out_path):
    """ Function to write SU2 results in a CPACS file.

    Function 'get_su2_results' get available results from the latest SU2
    calculation and put it at the correct place in the CPACS file.

    '/cpacs/vehicles/aircraft/model/analyses/aeroPerformance/aerpMap[n]/aeroPerformanceMap'

    Args:
        cpacs_path (str): Path to input CPACS file
        cpacs_out_path (str): Path to output CPACS file

    """

    tixi = open_tixi(cpacs_path)
    print('=======')
    print(cpacs_path)

    tixi = save_timestamp(tixi,SU2_XPATH)

    # Get and save Wetted area
    wetted_area = get_wetted_area()
    wetted_area_xpath = '/cpacs/toolspecific/CEASIOMpy/geometry/analysis/wettedArea'
    tixi = create_branch(tixi, wetted_area_xpath)
    tixi.updateDoubleElement(wetted_area_xpath,wetted_area,'%g')

    # Get and save CL/CD ratio
    # TODO: only if fixed CL mode
    # force_path = MODULE_DIR + '/ToolOutput/forces_breakdown.dat' # TODO: global ?
    # cl_cd = get_efficiency(force_path)
    # lDRatio_xpath = '/cpacs/toolspecific/CEASIOMpy/ranges/lDRatio' # TODO: probalby change xpath and name
    # tixi = create_branch(tixi, lDRatio_xpath)
    # tixi.updateDoubleElement(lDRatio_xpath,cl_cd,'%g')

    # Save aeroPerformanceMap
    active_aeroMap_xpath = SU2_XPATH + '/aeroMapUID'
    apm_xpath = get_apm_xpath(tixi,active_aeroMap_xpath)

    # Create an oject to store the aerodynamic coefficients
    Coef = AeroCoefficient()

    os.chdir(TMP_DIR)
    config_dir_list = os.listdir(TMP_DIR)
    for config_dir in config_dir_list:
        if os.path.isdir(config_dir):
            os.chdir(config_dir)
            force_file_name = 'forces_breakdown.dat'
            if not os.path.isfile(force_file_name):
                raise OSError('No result force file have been found!')

            # Read result file
            with open(force_file_name) as f:
                for line in f.readlines():
                    if 'Total CL:' in line:
                        cl = float(line.split(':')[1].split('|')[0])
                    if 'Total CD:' in line:
                        cd = float(line.split(':')[1].split('|')[0])
                    if 'Total CSF:' in line:
                        cs = float(line.split(':')[1].split('|')[0])
                    # TODO: Check which axis name corespond to waht: cml, cmd, cms
                    if 'Total CMx:' in line:
                        cml = float(line.split(':')[1].split('|')[0])
                    if 'Total CMy:' in line:
                        cmd = float(line.split(':')[1].split('|')[0])
                    if 'Total CMz:' in line:
                        cms = float(line.split(':')[1].split('|')[0])

            # Add new coefficients into the object Coef
            Coef.add_coefficients(cl,cd,cs,cml,cmd,cms)

            os.chdir(TMP_DIR)


    # Save object Coef in the CPACS file
    tixi = save_aero_coef(tixi,apm_xpath,Coef)

    print('=======')
    print(cpacs_out_path)
    close_tixi(tixi,cpacs_out_path)


#==============================================================================
#    MAIN
#==============================================================================


if __name__ == '__main__':

    log.info('----- Start of ' + os.path.basename(__file__) + ' -----')

    cpacs_path = MODULE_DIR + '/ToolInput/ToolInput.xml'
    mesh_path = MODULE_DIR + '/ToolInput/ToolInput.su2'

    force_path = MODULE_DIR + '/ToolOutput/forces_breakdown.dat'
    cpacs_out_path = MODULE_DIR + '/ToolOutput/ToolOutput.xml'

    # config_path = MODULE_DIR + '/ToolInput/ToolInput.cfg'
    tixi = open_tixi(cpacs_path)
    config_path_xpath = SU2_XPATH + '/configPath'
    config_path = get_value(tixi,config_path_xpath)

    run_SU2(mesh_path, config_path)

    get_su2_results(cpacs_path,cpacs_out_path)


    log.info('----- End of ' + os.path.basename(__file__) + ' -----')
