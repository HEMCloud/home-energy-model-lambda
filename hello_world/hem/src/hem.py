#!/usr/bin/env python3

"""
This module provides the entry point to the program and defines the command-line interface.
"""

# Standard library imports
import argparse
import csv
import json
import os
import re
import shutil
from math import floor
from typing import List
import datetime

# Third-party imports
import numpy as np

# Local imports
import core.units as units
from core.project import Project, calc_HTC_HLP
from read_CIBSE_weather_file import CIBSE_weather_data_to_dict
from read_weather_file import weather_data_to_dict
from wrappers.future_homes_standard.future_homes_standard import (
    apply_fhs_postprocessing, apply_fhs_preprocessing)
from wrappers.future_homes_standard.future_homes_standard_FEE import (
    apply_fhs_FEE_postprocessing, apply_fhs_FEE_preprocessing)
from wrappers.future_homes_standard.future_homes_standard_notional import \
    apply_fhs_not_preprocessing
from copy import deepcopy
from core.simulation_time import SimulationTime


# Ensure numpy errors get raised properly
# np.seterr('raise')


class CsvWriter:
    def __init__(self,f):
        self.writer = csv.writer(f)

    def writerow(self,row:list):
        # Round any floating point numbers to 6 decimals places
        def format(v):
            if type(v) in (float, np.float64):
                v = round(v, 6)
                return v if v else 0  # Avoids '0.0' being output in the .csv files
            return v
        self.writer.writerow(map(format, row))

    def writerows(self,rows:List[list]):
        for row in rows:
            self.writerow(row)


def run_project(
        inp_filename,
        external_conditions_dict,
        preproc_only=False,
        fhs_assumptions=False,
        fhs_FEE_assumptions=False,
        fhs_notA_assumptions=False,
        fhs_notB_assumptions=False,
        fhs_FEE_notA_assumptions=False,
        fhs_FEE_notB_assumptions=False,
        heat_balance=False,
        detailed_output_heating_cooling=False,
        use_fast_solver=True,
        tariff_data_filename=None,
        display_progress=False,
        ):
    file_name = os.path.splitext(os.path.basename(inp_filename))[0]
    file_path = os.path.splitext(os.path.abspath(inp_filename))[0]
    results_folder = os.path.join(file_path + '__results', '')
    os.makedirs(results_folder, exist_ok=True)
    if fhs_assumptions:
        output_file_run_name = 'FHS'
    elif fhs_FEE_assumptions:
        output_file_run_name = 'FHS_FEE'
    elif fhs_notA_assumptions:
        output_file_run_name = 'FHS_notA'
    elif fhs_notB_assumptions:
        output_file_run_name = 'FHS_notB'
    elif fhs_FEE_notA_assumptions:
        output_file_run_name = 'FHS_FEE_notA'
    elif fhs_FEE_notB_assumptions:
        output_file_run_name = 'FHS_FEE_notB'
    else:
        output_file_run_name = 'core'
    output_file_name_stub = results_folder + file_name + '__' + output_file_run_name + '__'
    output_file_detailed = output_file_name_stub + 'results.csv'
    output_file_static = output_file_name_stub + 'results_static.csv'
    output_file_summary = output_file_name_stub + 'results_summary.csv'

    with open(inp_filename) as json_file:
        project_dict = json.load(json_file)

    if external_conditions_dict is not None:
        # Note: Shading segments are an assessor input regardless, so save them
        # before overwriting the ExternalConditions and re-insert after
        shading_segments = project_dict["ExternalConditions"]["shading_segments"]
        project_dict["ExternalConditions"] = external_conditions_dict
        project_dict["ExternalConditions"]["shading_segments"] = shading_segments

    # Apply required preprocessing steps, if any
    # TODO Implement notional runs (the below treats them the same as the
    #      equivalent non-notional runs)
    if fhs_notA_assumptions or fhs_notB_assumptions \
    or fhs_FEE_notA_assumptions or fhs_FEE_notB_assumptions:
        project_dict = apply_fhs_not_preprocessing(project_dict, 
                                                   fhs_notA_assumptions, 
                                                   fhs_notB_assumptions,
                                                   fhs_FEE_notA_assumptions,
                                                   fhs_FEE_notB_assumptions)
    if fhs_assumptions or fhs_notA_assumptions or fhs_notB_assumptions:
        project_dict = apply_fhs_preprocessing(project_dict, sim_settings = [heat_balance, detailed_output_heating_cooling, use_fast_solver, tariff_data_filename])
    elif fhs_FEE_assumptions or fhs_FEE_notA_assumptions or fhs_FEE_notB_assumptions:
        project_dict = apply_fhs_FEE_preprocessing(project_dict)

    if preproc_only:
        preproc_file_name = output_file_name_stub + 'preproc.json'
        with open(preproc_file_name, 'w') as preproc_file:
            json.dump(project_dict, preproc_file, sort_keys=True, indent=4)
        shutil.copy2(inp_filename, results_folder)
        return # Skip actual calculation if preproc only option has been selected

    # Create a deep copy as init_resistance_or_uvalue() will add u_value & r_c
    # which will raise warning when called second time
    project_dict_copy = deepcopy(project_dict)

    project = Project(project_dict, heat_balance, detailed_output_heating_cooling, use_fast_solver, tariff_data_filename, display_progress)

    # Calculate static parameters and output
    heat_trans_coeff, heat_loss_param, HTC_dict, HLP_dict = calc_HTC_HLP(project_dict_copy)

    heat_capacity_param = project.calc_HCP()
    heat_loss_form_factor = project.calc_HLFF()
    write_static_output_file(
        output_file_static,
        heat_trans_coeff,
        heat_loss_param,
        heat_capacity_param,
        heat_loss_form_factor,
        temp_internal_air=project_dict["temp_internal_air_static_calcs"],
        temp_external_air=project.external_conditions().air_temp_annual_daily_average_min()
        )

    # Run main simulation
    timestep_array, results_totals, results_end_user, \
        energy_import, energy_export, energy_generated_consumed, \
        energy_to_storage, energy_from_storage, storage_from_grid, battery_state_of_charge, energy_diverted, betafactor, \
        zone_dict, zone_list, hc_system_dict, hot_water_dict, \
        heat_cop_dict, cool_cop_dict, dhw_cop_dict, \
        ductwork_gains, heat_balance_dict, heat_source_wet_results_dict, \
        heat_source_wet_results_annual_dict, \
        emitters_output_dict, esh_output_dict, vent_output_list, hot_water_source_results_dict = project.run()

    write_core_output_file(
        output_file_detailed,
        timestep_array,
        results_totals,
        results_end_user,
        energy_import,
        energy_export,
        energy_generated_consumed,
        energy_to_storage,
        energy_from_storage,
        storage_from_grid,
        battery_state_of_charge,        
        energy_diverted,
        betafactor,
        zone_dict,
        zone_list,
        hc_system_dict,
        hot_water_dict,
        ductwork_gains
        )

    if heat_balance:
        hour_per_step = project_dict['SimulationTime']['step']
        for hb_name, hb_dict in heat_balance_dict.items():
            heat_balance_output_file = output_file_name_stub + 'results_heat_balance_' + hb_name + '.csv'
            write_heat_balance_output_file(
                heat_balance_output_file,
                timestep_array,
                hour_per_step,
                hb_dict,
                )

    if detailed_output_heating_cooling:
        for heat_source_wet_name, heat_source_wet_results in heat_source_wet_results_dict.items():
            heat_source_wet_output_file \
                = output_file_name_stub + 'results_heat_source_wet__' \
                + heat_source_wet_name + '.csv'
            write_heat_source_wet_output_file(
                heat_source_wet_output_file,
                timestep_array,
                heat_source_wet_results,
                )
        for heat_source_wet_name, heat_source_wet_results_annual \
            in heat_source_wet_results_annual_dict.items():
            heat_source_wet_output_file \
                = output_file_name_stub + 'results_heat_source_wet_summary__' \
                + heat_source_wet_name + '.csv'
            write_heat_source_wet_summary_output_file(
                heat_source_wet_output_file,
                heat_source_wet_results_annual,
                )
        # Function call to write detailed ventilation results
        vent_output_file = output_file_name_stub + 'ventilation_results.csv'
        write_ventilation_detailed_output(vent_output_file, vent_output_list)
        for hot_water_source_name, hot_water_source_results in hot_water_source_results_dict.items():
            hot_water_source_file \
                = output_file_name_stub + 'results_hot_water_source_summary__' \
                + re.sub(r' ', r'_', hot_water_source_name) + '.csv'
            write_hot_water_source_summary_output_file(
                hot_water_source_file,
                hot_water_source_results,
                )

    # Sum per-timestep figures as needed
    space_heat_demand_total = sum(sum(h_dem) for h_dem in zone_dict['space heat demand'].values())
    space_cool_demand_total = sum(sum(c_dem) for c_dem in zone_dict['space cool demand'].values())
    total_floor_area = project.total_floor_area()
    daily_hw_demand = units.convert_profile_to_daily(
        hot_water_dict['Hot water energy demand incl pipework_loss']['energy_demand_incl_pipework_loss'],
        project_dict['SimulationTime']['step'],
        )
    daily_hw_demand_75th_percentile = np.percentile(daily_hw_demand, 75)

    write_core_output_file_summary(
        output_file_summary,
        project_dict,
        timestep_array,
        results_end_user,
        energy_generated_consumed,
        energy_to_storage,
        energy_from_storage,
        storage_from_grid,
        energy_diverted,
        energy_import,
        energy_export,
        space_heat_demand_total,
        space_cool_demand_total,
        total_floor_area,
        heat_cop_dict,
        cool_cop_dict,
        dhw_cop_dict,
        daily_hw_demand_75th_percentile,
        )
    
    #Create a file for emitters detailed ouput and write
    if detailed_output_heating_cooling:
        emitters_detailed_output = output_file_name_stub + 'results_emitters_.csv'
        write_emitters_detailed_output_file(results_folder,\
                                            emitters_detailed_output,\
                                            emitters_output_dict)

    #Create a file for esh detailed ouput and write
    if detailed_output_heating_cooling:
        esh_detailed_output = output_file_name_stub + 'results_esh_.csv'
        write_esh_detailed_output_file(results_folder,\
                                            esh_detailed_output,\
                                            esh_output_dict)


    # Apply required postprocessing steps, if any
    if fhs_assumptions or fhs_notA_assumptions or fhs_notB_assumptions:
        if fhs_notA_assumptions or fhs_notB_assumptions:
            notional = True
        else:
            notional = False
        apply_fhs_postprocessing(
            project_dict,
            results_totals,
            energy_import,
            energy_export,
            results_end_user,
            timestep_array,
            output_file_name_stub,
            notional,
            )
    elif fhs_FEE_assumptions or fhs_FEE_notA_assumptions or fhs_FEE_notB_assumptions:
        postprocfile = output_file_name_stub + 'postproc.csv'
        apply_fhs_FEE_postprocessing(
            postprocfile,
            total_floor_area,
            space_heat_demand_total,
            space_cool_demand_total,
            )

    shutil.copy2(inp_filename, results_folder)

def write_static_output_file(
        output_file,
        heat_trans_coeff,
        heat_loss_param,
        heat_capacity_param,
        heat_loss_form_factor,
        temp_internal_air,
        temp_external_air
        ):
    # Note: need to specify newline='' below, otherwise an extra carriage return
    # character is written when running on Windows
    with open(output_file, 'w', newline='') as f:
        writer = CsvWriter(f)
        writer.writerow(['Heat transfer coefficient', 'W / K', heat_trans_coeff])
        writer.writerow(['Heat loss parameter', 'W / m2.K', heat_loss_param])
        writer.writerow(['Heat capacity parameter', 'kJ / m2.K', heat_capacity_param])
        writer.writerow(['Heat loss form factor', '', heat_loss_form_factor])
        writer.writerow(['Assumptions used for HTC/HLP calculation:'])
        writer.writerow(['Internal air temperature', 'Celsius', temp_internal_air])
        writer.writerow(['External air temperature', 'Celsius', temp_external_air])

def write_heat_balance_output_file(
        heat_balance_output_file,
        timestep_array,
        hour_per_step,
        heat_balance_dict,
        ):
    # Note: need to specify newline='' below, otherwise an extra carriage return
    # character is written when running on Windows
    with open(heat_balance_output_file, 'w', newline='') as f:
        writer = CsvWriter(f)
        headings = ['Timestep']
        units_row = ['index']
        rows = ['']

        headings_annual = ['']
        units_annual = ['']

        nbr_of_zones = 0
        for z_name, heat_loss_gain_dict in heat_balance_dict.items():
            for heat_loss_gain_name in heat_loss_gain_dict.keys():
                headings.append(z_name+': '+heat_loss_gain_name)
                units_row.append('[W]')
            nbr_of_zones += 1

        for z_name, heat_loss_gain_dict in heat_balance_dict.items():
            annual_totals = [0]*(len(heat_loss_gain_dict.keys())*nbr_of_zones)
            annual_totals.insert(0,'')
            for heat_loss_gain_name in heat_loss_gain_dict.keys():
                headings_annual.append(z_name+': total '+heat_loss_gain_name)
                units_annual.append('[kWh]')

        for t_idx, timestep in enumerate(timestep_array):
            row = [t_idx]
            annual_totals_index = 1
            for z_name, heat_loss_gain_dict in heat_balance_dict.items():
                for heat_loss_gain_name in heat_loss_gain_dict.keys():
                    row.append(heat_loss_gain_dict[heat_loss_gain_name][t_idx])
                    annual_totals[annual_totals_index] += \
                        heat_loss_gain_dict[heat_loss_gain_name][t_idx]*hour_per_step/units.W_per_kW
                    annual_totals_index += 1
            rows.append(row)

        writer.writerow(headings_annual)
        writer.writerow(units_annual)
        writer.writerow(annual_totals)
        writer.writerow([''])
        writer.writerow(headings)
        writer.writerow(units_row)
        writer.writerows(rows)

def write_heat_source_wet_output_file(output_file, timestep_array, heat_source_wet_results):

    # Repeat column headings for each service
    col_headings = ['Timestep']
    col_units_row = ['count']
    columns = {}
    for service_name, service_results in heat_source_wet_results.items():
        columns[service_name] = [col for col in service_results.keys()]
        col_headings += [f"{service_name}: {col_heading}" for col_heading, _ in columns[service_name]]
        col_units_row += [col_unit for _, col_unit in columns[service_name]]

    # Note: need to specify newline='' below, otherwise an extra carriage return
    # character is written when running on Windows
    with open(output_file, 'w', newline='') as f:
        writer = CsvWriter(f)

        # Write column headings and units
        writer.writerow(col_headings)
        writer.writerow(col_units_row)

        # Write rows
        for t_idx in range(0, len(timestep_array)):
            row = [t_idx]
            for service_name, service_results in heat_source_wet_results.items():
                row += [service_results[col][t_idx] for col in columns[service_name]]
            writer.writerow(row)

def write_heat_source_wet_summary_output_file(output_file, heat_source_wet_results_annual):
    # Note: need to specify newline='' below, otherwise an extra carriage return
    # character is written when running on Windows
    with open(output_file, 'w', newline='') as f:
        writer = CsvWriter(f)

        for service_name, service_results in heat_source_wet_results_annual.items():
            writer.writerow((service_name,))
            for name, value in service_results.items():
                writer.writerow((name[0], name[1], value))
            writer.writerow('')


def write_emitters_detailed_output_file(results_folder,emitters_detailed_output,\
                                            emitters_output_dict):
    ''' The function writes detailed emitter output results in csv format.
        Specific file is created for every heat_system'''
    

    for emitter,emitter_output in emitters_output_dict.items() : 
        #Create CSV file with specified emitter name  
        original_file_name = emitters_detailed_output.split(".csv")
        specific_file_name = original_file_name[0]+'_'+ emitter + '.csv'  

        with open(specific_file_name, 'w', newline='') as f:
            writer = CsvWriter(f)
            headings = ['timestep','demand_energy','temp_emitter_req',
                        'time_before_heating_start','energy_provided_by_heat_source',
                        'temp_emitter','temp_emitter_max','energy_released_from_emitters',
                        'temp_flow_target','temp_return_target',
                        'temp_emitter_max_is_final_temp','energy_req_from_heat_source',
                        'fan_energy_kWh']
            units_row = ['[count]','[kWh]','[Celsius]','[hours]','[kWh]','[Celsius]','[Celsius]','[kWh]','[Celsius]',
                         '[Celsius]','[Boolean]','[kWh]','[kWh]']
            writer.writerow(headings)
            writer.writerow(units_row)
            for timestep, emitter_results in emitter_output.items():
                writer.writerow((emitter_results))


def write_esh_detailed_output_file(results_folder,esh_detailed_output,\
                                            esh_output_dict):
    ''' The function writes detailed esh output results in csv format.
        Specific file is created for every heat_system'''
    

    for esh,esh_output in esh_output_dict.items() : 
        #Create CSV file with specified emitter name  
        original_file_name = esh_detailed_output.split(".csv")
        specific_file_name = original_file_name[0]+'_'+ esh + '.csv'  

        with open(specific_file_name, 'w', newline='') as f:
            writer = CsvWriter(f)
            headings = ['timestep','n_units','demand_energy',
                        'energy_delivered','energy_instant',
                        'energy_charged','energy_for_fan',
                        'state_of_charge','final_soc_ivp','time_used_max']
            units_row = ['[count]','[count]','[kWh]','[kWh]','[kWh]','[kWh]','[kWh]','[ratio]','[ratio]','[hours]']
            writer.writerow(headings)
            writer.writerow(units_row)
            for timestep, esh_results in esh_output.items():
                writer.writerow((esh_results))

def write_ventilation_detailed_output(vent_output_file, vent_output_list):
    '''The function writed detailed ventilation output in csv format'''
    
    with open(vent_output_file, 'w', newline='') as f:
        writer = CsvWriter(f)
        headings = ['Timestep', 'Incoming air changes per hour', 'Vent opening ratio',
                    'incoming air flow', 'total_volume', 'air changes per hour',
                    'Internal temperature','Internal reference pressure',
                    'Air mass flow rate entering through window opening',
                    'Air mass flow rate leaving through window opening', 
                    'Air mass flow rate entering through vents (openings in the external envelope)',
                    'Air mass flow rate leaving through vents (openings in the external envelope)',
                    'Air mass flow rate entering through envelope leakage',
                    'Air mass flow rate leaving through envelope leakage',
                    'Air mass flow rate entering through combustion appliances',
                    'Air mass flow rate leaving through combustion appliances',
                    'Air mass flow rate entering through passive or hybrid duct',
                    'Air mass flow rate leaving through passive or hybrid duct',
                    'Supply air mass flow rate going to ventilation zone',
                    'Extract air mass flow rate from a ventilation zone',
                    'Extract air mass flow rate from heat recovery',
                    'Total air mass flow rate entering the zone',
                    'Total air mass flow rate leaving the zone']
        units_row = ['[count]', '[indicator]', '[ratio]',
                     '[m3/h]','[m3]','[ACH]',
                     '[Celsius]', '[Pa]',
                     '[kg/h]','[kg/h]', '[kg/h]','[kg/h]', '[kg/h]','[kg/h]','[kg/h]',
                     '[kg/h]', '[kg/h]', '[kg/h]', '[kg/h]', '[kg/h]', '[kg/h]' ,'[kg/h]', '[kg/h]']
        writer.writerow(headings)
        writer.writerow(units_row)
        for ventilation_results in vent_output_list:
            writer.writerow(ventilation_results)            
        
def write_hot_water_source_summary_output_file(output_file, hot_water_source_results):
    # Note: need to specify newline='' below, otherwise an extra carriage return
    # character is written when running on Windows
    with open(output_file, 'w', newline='') as f:
        writer = CsvWriter(f)

        for row in hot_water_source_results:
            writer.writerow(row)


def write_core_output_file(
        output_file,
        timestep_array,
        results_totals,
        results_end_user,
        energy_import,
        energy_export,
        energy_generated_consumed,
        energy_to_storage,
        energy_from_storage,
        storage_from_grid,
        battery_state_of_charge,
        energy_diverted,
        betafactor,
        zone_dict,
        zone_list,
        hc_system_dict,
        hot_water_dict,
        ductwork_gains
        ):
    # Note: need to specify newline='' below, otherwise an extra carriage return
    # character is written when running on Windows
    with open(output_file, 'w', newline='') as f:
        writer = CsvWriter(f)
        headings = ['Timestep']
        units_row = ['[count]']
        
        # Dictionary for most of the units (future output headings need respective units)
        unitsDict = {
            'internal gains': '[W]',
            'solar gains': '[W]',
            'operative temp': '[deg C]',
            'internal air temp': '[deg C]',
            'space heat demand': '[kWh]',
            'space cool demand': '[kWh]',
            'DHW: demand volume (including distribution pipework losses)': '[litres]',           
            'DHW: demand energy (including distribution pipework losses)': '[kWh]',
            'DHW: demand energy (excluding distribution pipework losses)': '[kWh]',
            'DHW: total event duration': '[mins]',
            'DHW: number of events': '[count]',
            'DHW: distribution pipework losses': '[kWh]',
            'DHW: primary pipework losses': '[kWh]',
            'DHW: storage losses': '[kWh]'
        }
        
        #Hot_water_dict headings
        for system in hot_water_dict:                
            if system == 'Hot water demand':
                system = 'DHW: demand volume (including distribution pipework losses)'
            if system == 'Hot water energy demand':
                system = 'DHW: demand energy (excluding distribution pipework losses)'
            if system == 'Hot water energy demand incl pipework_loss':
                system = 'DHW: demand energy (including distribution pipework losses)'
            if system == 'Hot water duration':
                system = 'DHW: total event duration'
            if system == 'Hot Water Events':
                system = 'DHW: number of events'
            if system == 'Pipework losses':
                system = 'DHW: distribution pipework losses'
            if system == 'Primary pipework losses':
                system = 'DHW: primary pipework losses'
            if system == 'Storage losses':
                system = 'DHW: storage losses'
            headings.append(system)        
            if system in unitsDict:
                units_row.append(unitsDict.get(system))
            else:
                this_filename = os.path.basename(__file__)
                units_row.append('Unit not defined (add to unitsDict ' + this_filename + ')')

        headings.append('Ventilation: Ductwork gains')
        units_row.append('[kWh]')

        for zone in zone_list:
            for zone_outputs in zone_dict.keys():
                zone_headings = zone + ': ' + zone_outputs
                headings.append(zone_headings)
                if zone_outputs in unitsDict:
                    units_row.append(unitsDict.get(zone_outputs))
                else:
                    this_filename = os.path.basename(__file__)
                    units_row.append('Unit not defined (unitsDict ' + this_filename + ')')
                    
        # hc_system_dict holds heating demand and output as first level keys
        # and the system name as second level keys.
        # Reorganising this dictionary so system names can be grouped together     

        # Initialize the reorganized dictionary for grouping systems in hc_system_dict
        reorganized_dict = {}

        # Iterate over the original dictionary 
        for key, value in hc_system_dict.items():
            # Iterate over the nested dictionary 
            for nested_key, nested_value in value.items():
                # Check if the nested_key already exists in reorganized_dict
                if nested_key not in reorganized_dict:
                    # If not, create a new entry
                    reorganized_dict[nested_key] = {}
                # Add the nested_value to the corresponding entry in reorganized_dict
                reorganized_dict[nested_key][key] = nested_value
 
        # Loop over reorganised dictionary to add  column and unit headers  
        # Check if the system name is set ,else add a designated empty 'None' string      
        for system in reorganized_dict:
            if system is not None:         
                for hc_name in reorganized_dict[system].keys():
                    if hc_name == 'Heating system output' or hc_name =='Cooling system output':
                        alternate_name = 'energy output'
                        hc_system = system + ': ' + alternate_name
                    else:
                        hc_system = system + ': ' + hc_name  
                    headings.append(hc_system)
                    units_row.append('[kWh]')  
            else:
                for hc_name in reorganized_dict[system].keys():
                    if hc_name == 'Heating system output' or hc_name =='Cooling system output':
                        alternate_name = 'energy output'
                        hc_system = 'None' + ': ' + alternate_name
                    else:
                        hc_system = 'None' + ': ' + hc_name
                    headings.append(hc_system)
                    units_row.append('[kWh]')   

        for totals_key in results_totals.keys():
            totals_header = str(totals_key)
            totals_header = totals_header + ': total'
            headings.append(totals_header)
            units_row.append('[kWh]')
            for end_user_key in results_end_user[totals_key].keys():
                headings.append(str(totals_key)+ ': '+ str(end_user_key))
                units_row.append('[kWh]')
            headings.append(str(totals_key) + ': import')
            units_row.append('[kWh]')
            headings.append(str(totals_key) + ': export')
            units_row.append('[kWh]')
            headings.append(str(totals_key) + ': generated and consumed')
            units_row.append('[kWh]')
            headings.append(str(totals_key) + ': beta factor')
            units_row.append('[ratio]')
            headings.append(str(totals_key) + ': generation to storage')
            units_row.append('[kWh]')
            headings.append(str(totals_key) + ': from storage')
            units_row.append('[kWh]')
            headings.append(str(totals_key) + ': grid to storage')
            units_row.append('[kWh]')
            headings.append(str(totals_key) + ': battery charge level')
            units_row.append('[ratio]')
            headings.append(str(totals_key) + ': diverted')
            units_row.append('[kWh]')                        
        
        # Write headings & units to output file
        writer.writerow(headings)
        writer.writerow(units_row)

        for t_idx, timestep in enumerate(timestep_array):
            energy_use_row = []
            zone_row = []
            hc_system_row = []
            hw_system_row = []
            hw_system_row_energy = []
            hw_system_row_energy_with_pipework_losses = []
            hw_system_row_duration = []
            hw_system_row_events = []
            pw_losses_row = []
            primary_pw_losses_row = []
            storage_losses_row = []
            ductwork_row = []
            energy_shortfall = []
            i = 0
            # Loop over end use totals
            for totals_key in results_totals:
                energy_use_row.append(results_totals[totals_key][t_idx])
                for end_user_key in results_end_user[totals_key]:
                    energy_use_row.append(results_end_user[totals_key][end_user_key][t_idx])
                energy_use_row.append(energy_import[totals_key][t_idx])
                energy_use_row.append(energy_export[totals_key][t_idx])
                energy_use_row.append(energy_generated_consumed[totals_key][t_idx])
                energy_use_row.append(betafactor[totals_key][t_idx])
                energy_use_row.append(energy_to_storage[totals_key][t_idx])
                energy_use_row.append(energy_from_storage[totals_key][t_idx])
                energy_use_row.append(storage_from_grid[totals_key][t_idx])
                energy_use_row.append(battery_state_of_charge[totals_key][t_idx])
                energy_use_row.append(energy_diverted[totals_key][t_idx])

                # Loop over results separated by zone
            for zone in zone_list:
                for zone_outputs in zone_dict:
                    zone_row.append(zone_dict[zone_outputs][zone][t_idx])
                # Loop over system names and print the heating and cooling enery demand and output
            for system in reorganized_dict:
                for hc_name in reorganized_dict[system]:
                    hc_system_row.append(reorganized_dict[system][hc_name][t_idx])

            # loop over hot water demand
            hw_system_row.append(hot_water_dict['Hot water demand']['demand'][t_idx])
            hw_system_row_energy.append(hot_water_dict['Hot water energy demand']['energy_demand'][t_idx])
            hw_system_row_energy_with_pipework_losses.append(hot_water_dict['Hot water energy demand incl pipework_loss']['energy_demand_incl_pipework_loss'][t_idx])
            hw_system_row_duration.append(hot_water_dict['Hot water duration']['duration'][t_idx])
            pw_losses_row.append(hot_water_dict['Pipework losses']['pw_losses'][t_idx])
            primary_pw_losses_row.append(hot_water_dict['Primary pipework losses']['primary_pw_losses'][t_idx])
            storage_losses_row.append(hot_water_dict['Storage losses']['storage_losses'][t_idx])
            hw_system_row_events.append(hot_water_dict['Hot Water Events']['no_events'][t_idx])
            ductwork_row.append(ductwork_gains['ductwork_gains'][t_idx])
            
          
            row = [t_idx] + hw_system_row + hw_system_row_energy_with_pipework_losses + hw_system_row_energy + \
                  hw_system_row_duration + hw_system_row_events +  pw_losses_row + primary_pw_losses_row + \
                  storage_losses_row + ductwork_row + energy_shortfall + zone_row + hc_system_row + energy_use_row 
 
            
            writer.writerow(row)

def write_core_output_file_summary(
        output_file_summary,
        project_dict,
        timestep_array,
        results_end_user,
        energy_generated_consumed,
        energy_to_storage,
        energy_from_storage,
        storage_from_grid,
        energy_diverted,
        energy_import,
        energy_export,
        space_heat_demand_total,
        space_cool_demand_total,
        total_floor_area,
        heat_cop_dict,
        cool_cop_dict,
        dhw_cop_dict,
        daily_hw_demand_75th_percentile,
        ):
    stats = {}
    # Energy Supply breakdown for all EnergySupply objects  
    for key, value in results_end_user.items():  
        elec_generated = 0
        elec_consumed = 0
        for end_use, arr in results_end_user[key].items():
            if sum(arr)<0:
                elec_generated+=abs(sum(arr))
            else:
                elec_consumed+=sum(arr)
        
        grid_to_consumption = sum(energy_import[key])
        generation_to_grid = abs(sum(energy_export[key]))
        gen_to_storage = sum(energy_to_storage[key])
        storage_to_consumption = abs(sum(energy_from_storage[key]))
        gen_to_diverter = sum(energy_diverted[key])
        if gen_to_storage > 0.0:
            storage_eff = storage_to_consumption / ( gen_to_storage + sum(storage_from_grid[key]))
        else:
            storage_eff = 'DIV/0'
            
        stats[key] = {
                'elec_generated': elec_generated,
                'elec_consumed': elec_consumed,
                'gen_to_consumption': sum(energy_generated_consumed[key]),
                'grid_to_consumption': grid_to_consumption,
                'generation_to_grid': generation_to_grid,
                'net_import': grid_to_consumption - generation_to_grid,
                'gen_to_storage': gen_to_storage,
                'storage_to_consumption': storage_to_consumption,
                'storage_from_grid': abs(sum(storage_from_grid[key])),
                'gen_to_diverter': gen_to_diverter,
                'storage_eff': storage_eff
                }

    #get peak electrcitiy consumption, and when it happens
    # Initialize the SimulationTime object   
    start_timestep = project_dict['SimulationTime']['start']
    end_timestep = project_dict['SimulationTime']['end']
    stepping = project_dict['SimulationTime']['step']
    sim_time = SimulationTime(starttime=start_timestep, endtime=end_timestep, step=stepping)

    # Get Energy Supply objects with fuel type 'electricity'
    electricity_keys = [key for key, value in project_dict['EnergySupply'].items() 
                        if value['fuel'] == 'electricity']
    # Calculate net import per timestep by adding gross import and export figures.
    # Add because export figures already negative
    net_import_per_timestep = [
        sum(energy_import[key][i] + energy_export[key][i] for key in electricity_keys)
        for i in range(len(timestep_array))
        ]
    
    # Find peak electricity consumption
    peak_elec_consumption = max(net_import_per_timestep)
    index_peak_elec_consumption = net_import_per_timestep.index(peak_elec_consumption)
    #must reflect hour or half hour in the year (hour 0 to hour 8759)
    #to work with the dictionary below timestep_to_date
    #hence + start_timestep
    step_peak_elec_consumption = index_peak_elec_consumption + start_timestep    
    
    # Initialize the dictionary to store the results
    timestep_to_date = {}
    
    #Set the base for any non-leap year
    base_time = datetime.datetime(year=2023, month=1, day=1, hour=0)
    #the step must reflect hour or half hour in the year (hour 0 to hour 8759)
    #step starts on the start_timestep 
    step = start_timestep
    for count, t in enumerate(timestep_array):
        current_time = base_time + datetime.timedelta(hours=t)
        timestep_to_date[step] = {
            'month': current_time.strftime('%b').upper(),
            'day': current_time.day,
            'hour': (step % (24 / stepping)) * stepping + 1
        }
        step +=1
            
    # Delivered energy by end-use and by fuel
    delivered_energy_dict = {'total':{'total':0}}
    for fuel,end_uses in results_end_user.items():
        if fuel not in ['_unmet_demand','hw cylinder']:
            delivered_energy_dict[fuel]={}
            delivered_energy_dict[fuel]['total'] = 0
            for end_use,delivered_energy in end_uses.items():
                if sum(delivered_energy)>=0:
                    delivered_energy_dict[fuel][end_use]=sum(delivered_energy)
                    delivered_energy_dict[fuel]['total'] +=sum(delivered_energy)
                    if end_use not in delivered_energy_dict['total'].keys():
                        delivered_energy_dict['total'][end_use] = sum(delivered_energy)
                    else:
                        delivered_energy_dict['total'][end_use] += sum(delivered_energy)
                    delivered_energy_dict['total']['total'] +=sum(delivered_energy)
    
    delivered_energy_rows_title = ['Delivered energy by end-use (below) and fuel (right) [kWh/m2]']
    delivered_energy_rows = [['total']]
    for fuel, end_uses in delivered_energy_dict.items():
        delivered_energy_rows_title.append(fuel)
        for row in delivered_energy_rows:
            row.append(0)
        for end_use,value in end_uses.items():
            end_use_found = False
            for row in delivered_energy_rows:
                if end_use in row:
                    end_use_found = True
                    row[delivered_energy_rows_title.index(fuel)] = value/total_floor_area
            if not end_use_found:
                new_row = [0]*len(delivered_energy_rows_title)
                new_row[0] = end_use
                new_row[delivered_energy_rows_title.index(fuel)] = value/total_floor_area
                delivered_energy_rows.append(new_row)

    heat_cop_rows = [(h_name, h_cop) for h_name, h_cop in heat_cop_dict.items()]
    cool_cop_rows = [(c_name, c_cop) for c_name, c_cop in cool_cop_dict.items()]
    dhw_cop_rows = [[hw_name, hw_cop] for hw_name, hw_cop in dhw_cop_dict.items()]

    # Note: need to specify newline='' below, otherwise an extra carriage return
    # character is written when running on Windows
    with open(output_file_summary, 'w', newline='') as f:
        writer = CsvWriter(f)
        writer.writerow(['Energy Demand Summary'])
        writer.writerow(['', '', 'Total'])
        writer.writerow(['Space heat demand', 'kWh/m2', space_heat_demand_total/total_floor_area])
        writer.writerow(['Space cool demand', 'kWh/m2', space_cool_demand_total/total_floor_area])
        writer.writerow([])
        writer.writerow(['Energy Supply Summary'])
        writer.writerow(['','kWh','timestep','month','day','hour of day'])
        writer.writerow(['Peak half-hour consumption (electricity)',
                         peak_elec_consumption,
                         index_peak_elec_consumption,
                         timestep_to_date[step_peak_elec_consumption]['month'],
                         timestep_to_date[step_peak_elec_consumption]['day'],
                         timestep_to_date[step_peak_elec_consumption]['hour']
                         ])
        writer.writerow([])
        header_row = ['', 'Total' ]
        for key in stats:
            header_row.append(key)
        writer.writerow(header_row)
        fields = [
                ('Consumption', 'kWh', 'elec_consumed'),
                ('Generation', 'kWh', 'elec_generated'),
                ('Generation to consumption (immediate excl. diverter)', 'kWh', 'gen_to_consumption'),
                ('Generation to storage', 'kWh', 'gen_to_storage'),
                ('Generation to diverter', 'kWh', 'gen_to_diverter'),
                ('Generation to grid (export)', 'kWh', 'generation_to_grid'),
                ('Storage to consumption', 'kWh', 'storage_to_consumption'),
                ('Grid to storage', 'kWh', 'storage_from_grid'),
                ('Grid to consumption (import)', 'kWh', 'grid_to_consumption'),
                ('Net import', 'kWh', 'net_import'),
                ('Storage round-trip efficiency', 'ratio', 'storage_eff')
                ]
        for field in fields:
            row = [field[0], field[1]]
            for key in stats:
                row.append(stats[key][field[2]])
            writer.writerow(row)
        writer.writerow([])
        writer.writerow(['Delivered Energy Summary'])
        writer.writerow(delivered_energy_rows_title)
        writer.writerows(delivered_energy_rows)
        if dhw_cop_rows:
            writer.writerow([])
            writer.writerow([
                'Hot water system',
                'Overall CoP',
                'Daily HW demand ([kWh] 75th percentile)',
                'HW cylinder volume (litres)',
                ])
            for row in dhw_cop_rows:
                row.append(daily_hw_demand_75th_percentile)
                if project_dict['HotWaterSource'][row[0]]['type'] == 'StorageTank':
                    row.append(project_dict['HotWaterSource'][row[0]]['volume'])
                else:
                    row.append('N/A')
            writer.writerows(dhw_cop_rows)
        if heat_cop_rows:
            writer.writerow([])
            writer.writerow(['Space heating system', 'Overall CoP'])
            writer.writerows(heat_cop_rows)
        if cool_cop_rows:
            writer.writerow([])
            writer.writerow(['Space cooling system', 'Overall CoP'])
            writer.writerows(cool_cop_rows)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Home Energy Model (HEM)')
    parser.add_argument(
        '--epw-file', '-w',
        action='store',
        default=None,
        help=('path to weather file in .epw format'),
        )
    parser.add_argument(
        '--CIBSE-weather-file',
        action='store',
        default=None,
        help=('path to CIBSE weather file in .csv format'),
        )
    parser.add_argument(
        '--tariff-file',
        action='store',
        default=None,
        help=('path to tariff data file in .csv format'),
        )
    parser.add_argument(
        'input_file',
        nargs='+',
        help=('path(s) to file(s) containing building specifications to run'),
        )
    parser.add_argument(
        '--parallel', '-p',
        action='store',
        type=int,
        default=0,
        help=('run calculations for different input files in parallel'
              '(specify no of files to run simultaneously)'),
        )
    parser.add_argument(
        '--preprocess-only',
        action='store_true',
        default=False,
        help='run prepocessing step only',
        )
    wrapper_options = parser.add_mutually_exclusive_group()
    wrapper_options.add_argument(
        '--future-homes-standard',
        action='store_true',
        default=False,
        help='use Future Homes Standard calculation assumptions',
        )
    wrapper_options.add_argument(
        '--future-homes-standard-FEE',
        action='store_true',
        default=False,
        help='use Future Homes Standard Fabric Energy Efficiency assumptions',
        )
    wrapper_options.add_argument(
        '--future-homes-standard-notA',
        action='store_true',
        default=False,
        help='use Future Homes Standard calculation assumptions for notional option A',
        )
    wrapper_options.add_argument(
        '--future-homes-standard-notB',
        action='store_true',
        default=False,
        help='use Future Homes Standard calculation assumptions for notional option B',
        )
    wrapper_options.add_argument(
        '--future-homes-standard-FEE-notA',
        action='store_true',
        default=False,
        help='use Future Homes Standard Fabric Energy Efficiency assumptions for notional option A',
        )
    wrapper_options.add_argument(
        '--future-homes-standard-FEE-notB',
        action='store_true',
        default=False,
        help='use Future Homes Standard Fabric Energy Efficiency assumptions for notional option B',
        )
    parser.add_argument(
        '--heat-balance',
        action='store_true',
        default=False,
        help='output heat balance for each zone',
        )
    parser.add_argument(
        '--detailed-output-heating-cooling',
        action='store_true',
        default=False,
        help=('output detailed calculation results for heating and cooling '
              'system objects (including HeatSourceWet objects) where the '
              'relevant objects have this functionality'
              )
        )
    parser.add_argument(
        '--no-fast-solver',
        action='store_true',
        default=False,
        help=('disable optimised solver (results may differ slightly due '
              'to reordering of floating-point ops); this option is '
              'provided to facilitate verification and debugging of the '
              'optimised version')
        )
    parser.add_argument(
        '--display-progress',
        action='store_true',
        default=False,
        help=('display progress for the json input file currently running')
        )
    cli_args = parser.parse_args()

    inp_filenames = cli_args.input_file
    epw_filename = cli_args.epw_file
    cibse_weather_filename = cli_args.CIBSE_weather_file
    tariff_data_filename = cli_args.tariff_file
    fhs_assumptions = cli_args.future_homes_standard
    fhs_FEE_assumptions = cli_args.future_homes_standard_FEE
    fhs_notA_assumptions = cli_args.future_homes_standard_notA
    fhs_notB_assumptions = cli_args.future_homes_standard_notB
    fhs_FEE_notA_assumptions = cli_args.future_homes_standard_FEE_notA
    fhs_FEE_notB_assumptions = cli_args.future_homes_standard_FEE_notB
    preproc_only = cli_args.preprocess_only
    heat_balance = cli_args.heat_balance
    detailed_output_heating_cooling = cli_args.detailed_output_heating_cooling
    use_fast_solver = not cli_args.no_fast_solver
    display_progress = cli_args.display_progress
    
    if epw_filename is not None:
        external_conditions_dict = weather_data_to_dict(epw_filename)
    elif cibse_weather_filename is not None:
        external_conditions_dict = CIBSE_weather_data_to_dict(cibse_weather_filename)
    
    else:
        external_conditions_dict = None

    if cli_args.parallel == 0:
        print('Running '+str(len(inp_filenames))+' cases in series')
        for inpfile in inp_filenames:
            if cli_args.display_progress:
                print(inpfile)
            run_project(
                inpfile,
                external_conditions_dict,
                preproc_only,
                fhs_assumptions,
                fhs_FEE_assumptions,
                fhs_notA_assumptions,
                fhs_notB_assumptions,
                fhs_FEE_notA_assumptions,
                fhs_FEE_notB_assumptions,
                heat_balance,
                detailed_output_heating_cooling,
                use_fast_solver,
                tariff_data_filename,
                display_progress
                )
    else:
        import multiprocessing as mp
        print('Running '+str(len(inp_filenames))+' cases in parallel'
              ' ('+str(cli_args.parallel)+' at a time)')
        run_project_args = [
            ( inpfile,
              external_conditions_dict,
              preproc_only,
              fhs_assumptions,
              fhs_FEE_assumptions,
              fhs_notA_assumptions,
              fhs_notB_assumptions,
              fhs_FEE_notA_assumptions,
              fhs_FEE_notB_assumptions,
              heat_balance,
              detailed_output_heating_cooling,
              use_fast_solver,
              tariff_data_filename,
            )
            for inpfile in inp_filenames
            ]
        with mp.Pool(processes=cli_args.parallel) as p:
            p.starmap(run_project, run_project_args)

