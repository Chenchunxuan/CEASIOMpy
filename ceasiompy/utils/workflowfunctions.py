"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Module containing the utilitary functions for the workflowcreator and optimization modules

Python version: >=3.6

| Author: Aidan Jungo
| Creation: 2020-02-25
| Last modifiction: 2020-12-01

TODO:

    * ...

"""


#==============================================================================
#   IMPORTS
#==============================================================================

import os
import subprocess
import shutil

import ceasiompy.utils.moduleinterfaces as mi

from ceasiompy.SettingsGUI.settingsgui import create_settings_gui

from ceasiompy.utils.ceasiomlogger import get_logger
log = get_logger(__file__.split('.')[0])

import ceasiompy.__init__
LIB_DIR = os.path.dirname(ceasiompy.__init__.__file__)


#==============================================================================
#   FUNCTIONS
#==============================================================================

def get_list_from_config(config_value):
    """ Return a list of module name (string)

    Function 'get_list_config_value' transform the string imput from the  config
    dictionary into a list of string with the correct format to be use by
    'WorkflowCreator'

    Args:
        config_value (str): String from the config dictionary
        module_list (list): List of modules

    """

    if config_value == 'NONE':
        return

    module_list = [x.strip() for x in config_value.split(',')]

    return module_list


def copy_module_to_module(module_from, io_from, module_to, io_to):
    """ Transfer CPACS file from one module to another.

    Function 'copy_module_to_module' copy the CPACS file form ToolInput or
    ToolOutput of 'module_from' to ToolInput or ToolOutput of 'module_to'

    Args:
        module_from (str): Name of the module the CPACS file is copy from
        io_from (str): "in" or "out", for ToolInput or ToolOutput
        module_to (str): Name of the module where the CPACS file will be copy
        io_to (str): "in" or "out", for ToolInput or ToolOutput

    """

    in_list = ['in','In','IN','iN','input','Input','INPUT','ToolInput','toolinput']

    if io_from in in_list:
        file_copy_from = mi.get_toolinput_file_path(module_from)
    else: # 'out' or anything else ('out' by default)
        file_copy_from = mi.get_tooloutput_file_path(module_from)
    log.info('Copy CPACS from:'+ file_copy_from)

    if io_to in in_list:
        file_copy_to = mi.get_toolinput_file_path(module_to)
    else: # 'out' or anything else ('out' by default)
        file_copy_to = mi.get_tooloutput_file_path(module_to)

    log.info('Copy CPACS to:'+ file_copy_to)

    shutil.copy(file_copy_from,file_copy_to)


def run_subworkflow(module_to_run,cpacs_path_in='',cpacs_path_out=''):
    """Function to run a list of module in order.

    Function 'run_subworkflow' will exectute in order all the module contained
    in 'module_to_run' list. Every time the resuts of one module (generaly CPACS
    file) will be copied as input for the next module.

    Args:
        module_to_run (list): List of mododule to run (in order)
        cpacs_path_in (str): Path of the CPACS file use, if not already in the
                             ToolInput folder of the first submodule
        cpacs_path_out (str): Path of the output CPACS file use, if not already
                              in the ToolInput folder of the first submodule

    """

    if not module_to_run:
        log.info('No module to run')
        return 0

    # Check non existing module
    submodule_list = mi.get_submodule_list()
    for module in module_to_run:
        if module not in submodule_list:
            raise ValueError('No module named "' + module + '"!')

    # Copy the cpacs file in the first module
    if cpacs_path_in:
        shutil.copy(cpacs_path_in,mi.get_toolinput_file_path(module_to_run[0]))

    log.info('The following modules will be executed: ')
    for module in module_to_run:
        log.info(module)

    for m, module in enumerate(module_to_run):

        log.info('######################################################################################')
        log.info('Run module: ' + module)
        log.info('######################################################################################')

        # Go to the module directory
        module_path = os.path.join(LIB_DIR,module)
        log.info('Going to ' + module_path)
        os.chdir(module_path)

        # Copy CPACS file from previous module to this one
        if m > 0:
            copy_module_to_module(module_to_run[m-1],'out',module,'in')

        if module == 'SettingsGUI':
            cpacs_path = mi.get_toolinput_file_path(module)
            cpacs_out_path = mi.get_tooloutput_file_path(module)

            # Check if there is at least one other 'SettingsGUI' after this one
            if 'SettingsGUI' in module_to_run[m+1:] and m+1 != len(module_to_run):
                idx = module_to_run.index('SettingsGUI', m+1)
                create_settings_gui(cpacs_path,cpacs_out_path,module_to_run[m:idx])
            else:
                create_settings_gui(cpacs_path,cpacs_out_path,module_to_run[m:])
        else:
            # Find the python file to run
            for file in os.listdir(module_path):
                if file.endswith('.py'):
                    if not file.startswith('__'):
                        main_python = file

            # Run the module
            error = subprocess.call(['python',main_python])

            if error:
                raise ValueError('An error ocured in the module '+ module)

    # Copy the cpacs file in the first module
    if cpacs_path_out:
        shutil.copy(mi.get_tooloutput_file_path(module_to_run[-1]),cpacs_path_out)


#==============================================================================
#    MAIN
#==============================================================================

if __name__ == '__main__':

    log.info('Nothing to execute!')
