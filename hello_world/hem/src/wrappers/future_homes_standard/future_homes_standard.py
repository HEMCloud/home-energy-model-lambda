#!/usr/bin/env python3

"""
This module provides functions to implement pre- and post-processing
steps for the Future Homes Standard.
"""

import math
import sys
import os
import json
import csv
from fractions import Fraction
from core import project, schedule, units
from core.water_heat_demand.misc import frac_hot_water
from core.simulation_time import SimulationTime
from core.external_conditions import ExternalConditions,\
    create_external_conditions
from core.space_heat_demand.building_element import WindowTreatmentCtrl
from cmath import log
import numpy as np
from wrappers.future_homes_standard.FHS_HW_events import HW_event_adjust_allocate, HW_events_generator
from copy import deepcopy
from wrappers.future_homes_standard.FHS_appliance import FHS_appliance
from core.units import W_per_kW, days_per_year
from copy import deepcopy

this_directory = os.path.dirname(os.path.relpath(__file__))
FHSEMISFACTORS =  os.path.join(this_directory, "FHS_emisPEfactors_05-08-2024.csv")
FHSEMISFACTORS_ELEC =  os.path.join(this_directory, "DEMO_variable_grid_model.csv")
emis_factor_name = 'Emissions Factor kgCO2e/kWh'
emis_oos_factor_name = 'Emissions Factor kgCO2e/kWh including out-of-scope emissions'
PE_factor_name = 'Primary Energy Factor kWh/kWh delivered'

energysupplyname_gas = 'mains gas'
energysupplyname_electricity = 'mains elec'

appl_obj_name = 'appliances'
elec_cook_obj_name = 'Eleccooking'
gas_cook_obj_name = 'Gascooking'
hw_timer_main_name = "hw timer"
hw_timer_hold_at_setpnt_name = "hw timer eco7"
randomseed = 37

livingroom_setpoint_fhs = 21.0
restofdwelling_setpoint_fhs = 20.0

simtime_start = 0
simtime_end = 8760
simtime_step = 0.5
simtime = SimulationTime(simtime_start, simtime_end, simtime_step)

total_steps = simtime.total_steps()

# Central point for hot water temperature (temp_hot_water) across the code
HW_temperature = 52.0
HW_setpoint_max = 60.0

#Occupant sleep+wake hours as per Part O
occupant_waking_hr = 7
occupant_sleeping_hr = 23

def apply_fhs_preprocessing(project_dict, is_FEE=False, sim_settings = [False, False, False, None]):
    """ Apply assumptions and pre-processing steps for the Future Homes Standard """
    appliance_propensities_file = os.path.join(this_directory, 'appliance_propensities.csv')
    with open(appliance_propensities_file,'r') as appfile:
        appfilereader = csv.DictReader(appfile)
        appliance_propensities = {fieldname:[] for fieldname in appfilereader.fieldnames}
        for row in appfilereader:
            for key in row.keys():
                appliance_propensities[key].append(float(row[key]))
        #normalise appliance propensities, but not occupancy
        for key in list(appliance_propensities.keys())[2:]:
            sumcol = sum(appliance_propensities[key])
            appliance_propensities[key] = [ x / sumcol for x in appliance_propensities[key]]
    
    evap_profile_data = load_evaporative_profile('evap_loss_profile.csv')
    cold_water_loss_profile_data = load_evaporative_profile('cold_water_loss_profile.csv')       
    project_dict['SimulationTime']["start"] = simtime_start
    project_dict['SimulationTime']["end"] = simtime_end
    project_dict['SimulationTime']["step"] = simtime_step

    
    project_dict['InternalGains']={}
    
    TFA = calc_TFA(project_dict)
    
    nbeds = calc_nbeds(project_dict)
    
    try:
        N_occupants = calc_N_occupants(TFA, nbeds)
    except ValueError as e:
        sys.exit("Invalid data used in occupancy calculation. {0}".format(e))
    
    #construct schedules
    schedule_occupancy_weekday, schedule_occupancy_weekend =\
        create_occupancy(N_occupants, 
                         appliance_propensities['Occupied prop ( Chance the house is occupied)'])
    create_metabolic_gains(
        N_occupants,
        project_dict,
        schedule_occupancy_weekday, 
        schedule_occupancy_weekend)

    create_water_heating_pattern(project_dict)
    create_heating_pattern(project_dict)
    create_evaporative_losses(project_dict, TFA, N_occupants, evap_profile_data)
    create_cold_water_losses(project_dict, TFA, N_occupants, cold_water_loss_profile_data)
    create_lighting_gains(project_dict, TFA, N_occupants)
    create_appliance_gains(project_dict, TFA, N_occupants, appliance_propensities)
    
    for hwsource in project_dict["HotWaterSource"]:
        if project_dict["HotWaterSource"][hwsource]["type"] == "StorageTank":
            project_dict["HotWaterSource"][hwsource]["init_temp"] = HW_setpoint_max
        elif project_dict["HotWaterSource"][hwsource]["type"] == "PointOfUse":
            project_dict["HotWaterSource"][hwsource]["setpoint_temp"] = HW_temperature
        elif project_dict["HotWaterSource"][hwsource]["type"] == "CombiBoiler":
            project_dict["HotWaterSource"][hwsource]["setpoint_temp"] = HW_temperature
        elif project_dict["HotWaterSource"][hwsource]["type"] == "HIU":
            project_dict["HotWaterSource"][hwsource]["setpoint_temp"] = HW_temperature
        
    cold_water_feed_temps = create_cold_water_feed_temps(project_dict)
    create_hot_water_use_pattern(project_dict, TFA, N_occupants, cold_water_feed_temps)
    create_cooling(project_dict)
    create_window_opening_schedule(project_dict)
    create_vent_opening_schedule(project_dict)
    window_treatment(project_dict)
    if not is_FEE:
        calc_SFP_mech_vent(project_dict)
    if project_dict['InfiltrationVentilation'].get('MechanicalVentilation') is not None:
        create_MEV_pattern(project_dict)
    
    set_temp_internal_static_calcs(project_dict)
    if "loadshifting" in project_dict["Control"]:
        #run project for 24 hours to obtain initial estimate for daily heating demand
        sim_24h(project_dict, sim_settings)

    return project_dict

def set_temp_internal_static_calcs(project_dict):
    project_dict["temp_internal_air_static_calcs"] = livingroom_setpoint_fhs

def load_emisPE_factors():
    """ Load emissions factors and primary energy factors from data file """
    
    emisPE_factors = {}
    with open(FHSEMISFACTORS, 'r') as emisPE_factors_csv:
        emisPE_factors_reader = csv.DictReader(emisPE_factors_csv, delimiter=',')

        for row in emisPE_factors_reader:
            if row["Fuel Code"]!= "":
                fuel_code = row["Fuel Code"]
                emisPE_factors[fuel_code] = row
                # Remove keys that aren't factors to be applied to results
                emisPE_factors[fuel_code].pop("Fuel Code")
                emisPE_factors[fuel_code].pop("Fuel")

    return emisPE_factors

def load_emisPE_factors_elec():
    """ Load emissions factors and primary energy factors from data file for electricity"""
    emisPE_factors_elec = {}
    with open(FHSEMISFACTORS_ELEC, 'r') as emisPE_factors_csv:
        emisPE_factors_reader = csv.DictReader(emisPE_factors_csv, delimiter=',')        
        for row in emisPE_factors_reader:
            emisPE_factors_elec[row['Timestep']] = row    
    return emisPE_factors_elec

def apply_energy_factor_series(energy_data, factors):
    if len(energy_data) != len(factors):
        raise ValueError("Both energy_data and factors list must be of the same length.") 
    return [energy * factor for energy, factor in zip(energy_data, factors)]

def apply_fhs_postprocessing(
        project_dict,
        results_totals,
        energy_import,
        energy_export,
        results_end_user,
        timestep_array,
        file_path,
        notional,
        ):
    """ Post-process core simulation outputs as required for Future Homes Standard """
    no_of_timesteps = len(timestep_array)

    # Read factors from csv
    emisPE_factors = load_emisPE_factors()
    emisPE_factors_elec = load_emisPE_factors_elec()

    # Add unmet demand to list of EnergySupply objects
    project_dict["EnergySupply"]['_unmet_demand'] = {"fuel": "unmet_demand"}

    # For each EnergySupply object:
    # - look up relevant factors for import/export from csv or custom factors
    #   from input file
    # - look up relevant factors for generation from csv
    # - apply relevant factors for import, export and generation
    # Applying factors in this way rather than applying a net export factor to
    # exported energy accounts for energy generated and used on site and also
    # accounts for battery storage losses
    emis_results = {}
    emis_oos_results = {}
    PE_results = {}
    for energy_supply in project_dict["EnergySupply"]:
        emis_results[energy_supply] = {}
        emis_oos_results[energy_supply] = {}
        PE_results[energy_supply] = {}

        fuel_code = project_dict["EnergySupply"][energy_supply]["fuel"]

        # Get emissions/PE factors for import/export
        if fuel_code == "custom":
            emis_factor_import_export \
                = float(project_dict["EnergySupply"][energy_supply]["factor"][emis_factor_name])
            emis_oos_factor_import_export \
                = float(project_dict["EnergySupply"][energy_supply]["factor"][emis_oos_factor_name])
            PE_factor_import_export \
                = float(project_dict["EnergySupply"][energy_supply]["factor"][PE_factor_name])
        elif fuel_code == "electricity":
            emis_factor_import_export \
                = [float(value[emis_factor_name]) for value in emisPE_factors_elec.values()]
            emis_oos_factor_import_export \
                = [float(value[emis_oos_factor_name]) for value in emisPE_factors_elec.values()]
            PE_factor_import_export \
                = [float(value[PE_factor_name]) for value in emisPE_factors_elec.values()]
        else:
            emis_factor_import_export = float(emisPE_factors[fuel_code][emis_factor_name])
            emis_oos_factor_import_export = float(emisPE_factors[fuel_code][emis_oos_factor_name])
            PE_factor_import_export = float(emisPE_factors[fuel_code][PE_factor_name])

        # Calculate energy imported and associated emissions/PE
        if fuel_code == 'electricity':
            emis_results[energy_supply]['import']       = apply_energy_factor_series(energy_import[energy_supply],
                                                                                    emis_factor_import_export)
            emis_oos_results[energy_supply]['import']   = apply_energy_factor_series(energy_import[energy_supply], 
                                                                                    emis_oos_factor_import_export)
            PE_results[energy_supply]['import']         = apply_energy_factor_series(energy_import[energy_supply], 
                                                                                    PE_factor_import_export)

        else:    
            emis_results[energy_supply]['import'] = [
                x * emis_factor_import_export for x in energy_import[energy_supply]
                ]            
            emis_oos_results[energy_supply]['import'] = [
                x * emis_oos_factor_import_export for x in energy_import[energy_supply]
                ]
            PE_results[energy_supply]['import'] = [
                x * PE_factor_import_export for x in energy_import[energy_supply]
                ]

        # If there is any export, Calculate energy exported and associated emissions/PE
        # Note that by convention, exported energy is negative
        if sum(energy_export[energy_supply]) < 0:
            if fuel_code == 'electricity':
                emis_results[energy_supply]['export']       = apply_energy_factor_series(energy_export[energy_supply], 
                                                                                        emis_factor_import_export)
                emis_oos_results[energy_supply]['export']   = apply_energy_factor_series(energy_export[energy_supply], 
                                                                                        emis_oos_factor_import_export)
                PE_results[energy_supply]['export']         = apply_energy_factor_series(energy_export[energy_supply], 
                                                                                        PE_factor_import_export)

            else: 
                emis_results[energy_supply]['export'] = [
                    x * emis_factor_import_export for x in energy_export[energy_supply]
                    ]
                emis_oos_results[energy_supply]['export'] = [
                    x * emis_oos_factor_import_export for x in energy_export[energy_supply]
                    ]
                PE_results[energy_supply]['export'] = [
                    x * PE_factor_import_export for x in energy_export[energy_supply]
                    ]
        else:
            emis_results[energy_supply]['export'] = [0.0] * no_of_timesteps
            emis_oos_results[energy_supply]['export'] = [0.0] * no_of_timesteps
            PE_results[energy_supply]['export'] = [0.0] * no_of_timesteps

        # Calculate energy generated and associated emissions/PE
        energy_generated = [0.0] * no_of_timesteps
        for end_user_name, end_user_energy in results_end_user[energy_supply].items():
            # If there is energy generation (represented as negative demand)
            if sum(end_user_energy) < 0.0:
                for t_idx in range(0, no_of_timesteps):
                    # Subtract here because generation is represented as negative demand
                    energy_generated[t_idx] -= end_user_energy[t_idx]

        if sum(energy_generated) > 0.0:
            # TODO Allow custom (user-defined) factors for generated energy?
            fuel_code_generated = fuel_code + '_generated'
            emis_factor_generated = float(emisPE_factors[fuel_code_generated][emis_factor_name])
            emis_oos_factor_generated = float(emisPE_factors[fuel_code_generated][emis_oos_factor_name])
            PE_factor_generated = float(emisPE_factors[fuel_code_generated][PE_factor_name])

            emis_results[energy_supply]['generated'] = [
                x * emis_factor_generated for x in energy_generated
                ]
            emis_oos_results[energy_supply]['generated'] = [
                x * emis_oos_factor_generated for x in energy_generated
                ]
            PE_results[energy_supply]['generated'] = [
                x * PE_factor_generated for x in energy_generated
                ]
        else:
            emis_results[energy_supply]['generated'] = [0.0] * no_of_timesteps
            emis_oos_results[energy_supply]['generated'] = [0.0] * no_of_timesteps
            PE_results[energy_supply]['generated'] = [0.0] * no_of_timesteps

        # Calculate unregulated energy demand and associated emissions/PE
        energy_unregulated = [0.0] * no_of_timesteps
        for end_user_name, end_user_energy in results_end_user[energy_supply].items():
            if end_user_name in (appl_obj_name, elec_cook_obj_name, gas_cook_obj_name):
                for t_idx in range(0, no_of_timesteps):
                    energy_unregulated[t_idx] += end_user_energy[t_idx]
                    
        if fuel_code == 'electricity':
            emis_results[energy_supply]['unregulated']      = apply_energy_factor_series(energy_unregulated, 
                                                                                        emis_factor_import_export)
            emis_oos_results[energy_supply]['unregulated']  = apply_energy_factor_series(energy_unregulated, 
                                                                                        emis_oos_factor_import_export)
            PE_results[energy_supply]['unregulated']        = apply_energy_factor_series(energy_unregulated, 
                                                                                        PE_factor_import_export)
        else:
            emis_results[energy_supply]['unregulated'] = [
                x * emis_factor_import_export for x in energy_unregulated
                ]
            emis_oos_results[energy_supply]['unregulated'] = [
                x * emis_oos_factor_import_export for x in energy_unregulated
                ]
            PE_results[energy_supply]['unregulated'] = [
                x * PE_factor_import_export for x in energy_unregulated
                ]

        # Calculate total CO2/PE for each EnergySupply based on import and export,
        # subtracting unregulated
        emis_results[energy_supply]['total'] = [0.0] * no_of_timesteps
        emis_oos_results[energy_supply]['total'] = [0.0] * no_of_timesteps
        PE_results[energy_supply]['total'] = [0.0] * no_of_timesteps
        for t_idx in range(0, no_of_timesteps):
            emis_results[energy_supply]['total'][t_idx] \
                = emis_results[energy_supply]['import'][t_idx] \
                + emis_results[energy_supply]['export'][t_idx] \
                + emis_results[energy_supply]['generated'][t_idx] \
                - emis_results[energy_supply]['unregulated'][t_idx]
            emis_oos_results[energy_supply]['total'][t_idx] \
                = emis_oos_results[energy_supply]['import'][t_idx] \
                + emis_oos_results[energy_supply]['export'][t_idx] \
                + emis_oos_results[energy_supply]['generated'][t_idx] \
                - emis_oos_results[energy_supply]['unregulated'][t_idx]
            PE_results[energy_supply]['total'][t_idx] \
                = PE_results[energy_supply]['import'][t_idx] \
                + PE_results[energy_supply]['export'][t_idx] \
                + PE_results[energy_supply]['generated'][t_idx] \
                - PE_results[energy_supply]['unregulated'][t_idx]

    # Calculate summary results
    TFA = calc_TFA(project_dict)
    total_emissions_rate = sum([sum(emis['total']) for emis in emis_results.values()]) / TFA
    total_PE_rate = sum([sum(PE['total']) for PE in PE_results.values()]) / TFA

    # Write results to output files
    write_postproc_file(file_path, "emissions", emis_results, no_of_timesteps)
    write_postproc_file(file_path, "emissions_incl_out_of_scope", emis_oos_results, no_of_timesteps)
    write_postproc_file(file_path, "primary_energy", PE_results, no_of_timesteps)
    write_postproc_summary_file(file_path, total_emissions_rate, total_PE_rate, notional)

def write_postproc_file(file_path, results_type, results, no_of_timesteps):
    file_name = file_path + 'postproc' + '_'+ results_type + '.csv'

    row_headers = []
    rows_results = []

    # Loop over each EnergySupply object and add headers and results to rows
    for energy_supply, energy_supply_results in results.items():
        for result_name in energy_supply_results.keys():
            # Create header row
            row_headers.append(energy_supply + ' ' + result_name)

    # Create results rows
    for t_idx in range(0, no_of_timesteps):
        row = []
        for energy_supply, energy_supply_results in results.items():
            for result_name, result_values in energy_supply_results.items():
                row.append(result_values[t_idx])
        rows_results.append(row)

    # Note: need to specify newline='' below, otherwise an extra carriage return
    # character is written when running on Windows
    with open(file_name, 'w', newline='') as postproc_file:
        writer = csv.writer(postproc_file)
        writer.writerow(row_headers)
        writer.writerows(rows_results)

def write_postproc_summary_file(file_path, total_emissions_rate, total_PE_rate, notional):
    if notional:
        emissions_rate_name = 'TER'
        pe_rate_name = 'TPER'
    else:
        emissions_rate_name = 'DER'
        pe_rate_name = 'DPER'

    # Note: need to specify newline='' below, otherwise an extra carriage return
    # character is written when running on Windows
    with open(file_path + 'postproc_summary.csv', 'w', newline='') as postproc_file:
        writer = csv.writer(postproc_file)
        writer.writerow(['','','Total'])
        writer.writerow([emissions_rate_name, 'kgCO2/m2', total_emissions_rate])
        writer.writerow([pe_rate_name,'kWh/m2',total_PE_rate])

def calc_TFA(project_dict):
     
    TFA = 0.0
    
    for zones in project_dict["Zone"].keys():
        TFA += project_dict["Zone"][zones]["area"]
        
    return TFA

def calc_nbeds(project_dict):
    if "NumberOfBedrooms" in project_dict:
        nbeds = int(project_dict["NumberOfBedrooms"])
    else:
        sys.exit("missing NumberOfBedrooms - required for FHS calculation")
    
    nbeds = min(nbeds,5)
    return nbeds

def calc_N_occupants(TFA, nbeds):
    
    if (TFA <= 0):
        # assume if floor area less than or equal to zero, TFA is not valid
        raise ValueError("Invalid floor area: {0}".format(TFA))
    
    # sigmoid curve is only used for one bedroom occupancy.
    # Therefore sigmoid parameters only listed if there is one bedroom
    sigmoid_params =   {1 :
                            {'j': 0.4373, 'k': -0.001902}
                        }
    
    # constant values are used to look up occupancy against the number of bedrooms
    TWO_BED_OCCUPANCY = 2.2472
    THREE_BED_OCCUPANCY = 2.9796
    FOUR_BED_OCCUPANCY = 3.3715
    FIVE_BED_OCCUPANCY = 3.8997
             
    if (nbeds == 1):
        N = 1 + sigmoid_params[nbeds]['j'] * (1 - math.exp(sigmoid_params[nbeds]['k'] * (TFA)**2))
    elif (nbeds == 2):
        N = TWO_BED_OCCUPANCY
    elif (nbeds == 3):
        N = THREE_BED_OCCUPANCY 
    elif (nbeds == 4):
        N = FOUR_BED_OCCUPANCY
    elif (nbeds >= 5):
        # 5 bedrooms or more are assumed to all have same occupancy
        N = FIVE_BED_OCCUPANCY
    else:
        # invalid number of bedrooms, raise ValueError exception
        raise ValueError("Invalid number of bedrooms: {0}".format(nbeds))
            
    return N

def create_occupancy(N_occupants, occupancy_FHS):
    #in number of occupants
    
    schedule_occupancy_weekday = [
        x * N_occupants for x in occupancy_FHS
    ]
    schedule_occupancy_weekend = [
        x * N_occupants for x in occupancy_FHS
    ]
    
    return schedule_occupancy_weekday, schedule_occupancy_weekend

def create_metabolic_gains(N_occupants,
                           project_dict, 
                           schedule_occupancy_weekday, 
                           schedule_occupancy_weekend):
    # Calculate total body surface area of occupants
    a = 2.0001
    b = 0.8492
    total_body_surface_area_occupants = a * N_occupants ** b

    # Read metabolic gains profile from CSV
    metabolic_gains_weekday = []
    metabolic_gains_weekend = [] 
    
    met_gain_csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dry_metabolic_gains_profile_Wperm2.csv')
     
    with open(met_gain_csv_path, 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            metabolic_gains_weekday.append(float(row['Weekday']))
            metabolic_gains_weekend.append(float(row['Weekend']))

    # Multiply metabolic gains by total body surface area for each half hour
    metabolic_gains_weekday_absolute = [gains * total_body_surface_area_occupants for gains in metabolic_gains_weekday]
    metabolic_gains_weekend_absolute = [gains * total_body_surface_area_occupants for gains in metabolic_gains_weekend]

    project_dict['InternalGains']['metabolic gains'] = {
        "start_day": 0,
        "time_series_step": 0.5,
        "schedule": {
            #watts
            "main": [{"repeat": 53, "value": "week"}],
            "week": [{"repeat": 5, "value": "weekday"},
                     {"repeat": 2, "value": "weekend"}],
            "weekday": metabolic_gains_weekday_absolute,
            "weekend": metabolic_gains_weekend_absolute
        }
    }

    return project_dict

def create_heating_pattern(project_dict):
    '''
    space heating
    '''

    #07:00-09:30 and then 16:30-22:00
    heating_fhs_weekday = (
        [False for x in range(14)] +
        [True for x in range(5)] +
        [False for x in range(14)] +
        [True for x in range(11)] +
        [False for x in range(4)])
    # Start all-day HW schedule 1 hour before space heating
    hw_sched_allday_weekday \
        = ( [False for x in range(13)]
          + [True for x in range(31)]
          + [False for x in range(4)]
        )

    #07:00-09:30 and then 18:30-22:00
    heating_nonlivingarea_fhs_weekday = (
        [False for x in range(14)] +
        [True for x in range(5)] +
        [False for x in range(18)] +
        [True for x in range(7)] +
        [False for x in range(4)])

    #08:30 - 22:00
    heating_fhs_weekend = (
        [False for x in range(17)] +
        [True for x in range(27)] +
        [False for x in range(4)])
    # Start all-day HW schedule 1 hour before space heating
    hw_sched_allday_weekend \
        = ( [False for x in range(15)]
          + [True for x in range(29)]
          + [False for x in range(4)]
        )

    '''
    if there is not separate time control of the non-living rooms
    (i.e. control type 3 in SAP 10 terminology),
    the heating times are necessarily the same as the living room,
    so the evening heating period would also start at 16:30 on weekdays.
    '''
    controltype = 0
    if project_dict["HeatingControlType"]:
        if project_dict["HeatingControlType"] =="SeparateTimeAndTempControl":
            controltype = 3
        elif project_dict["HeatingControlType"] =="SeparateTempControl":
            controltype = 2
        else:
            sys.exit("invalid HeatingControlType (SeparateTempControl or SeparateTimeAndTempControl)")
    else:
        sys.exit("missing HeatingControlType (SeparateTempControl or SeparateTimeAndTempControl)")
    
    
    for zone in project_dict['Zone']:
        if "SpaceHeatControl" in project_dict["Zone"][zone].keys():
            if project_dict['Zone'][zone]["SpaceHeatControl"] == "livingroom":
                project_dict['Zone'][zone]['temp_setpnt_init'] = livingroom_setpoint_fhs

                project_dict['Control']['HeatingPattern_LivingRoom'] = {
                    "type": "SetpointTimeControl",
                    "start_day" : 0,
                    "time_series_step":0.5,
                    "schedule": {
                        "main": [{"repeat": 53, "value": "week"}],
                        "week": [{"repeat": 5, "value": "weekday"},
                                 {"repeat": 2, "value": "weekend"}],
                        "weekday": [livingroom_setpoint_fhs if x
                                    else None
                                    for x in heating_fhs_weekday],
                        "weekend": [livingroom_setpoint_fhs if x
                                    else None
                                    for x in heating_fhs_weekend],
                    }
                }
                if "SpaceHeatSystem" in project_dict["Zone"][zone].keys():
                    spaceheatsystem = project_dict["Zone"][zone]["SpaceHeatSystem"]
                    project_dict["SpaceHeatSystem"][spaceheatsystem]["Control"] = "HeatingPattern_LivingRoom"
                    if 'temp_setback' in project_dict["SpaceHeatSystem"][spaceheatsystem].keys():
                        project_dict['Control']['HeatingPattern_LivingRoom']['setpoint_min'] \
                            = project_dict["SpaceHeatSystem"][spaceheatsystem]['temp_setback']
                    if 'advanced_start' in project_dict["SpaceHeatSystem"][spaceheatsystem].keys():
                        project_dict['Control']['HeatingPattern_LivingRoom']['advanced_start'] \
                            = project_dict["SpaceHeatSystem"][spaceheatsystem]['advanced_start']
            
            elif project_dict['Zone'][zone]["SpaceHeatControl"] == "restofdwelling" \
            and controltype == 2:
                project_dict['Zone'][zone]['temp_setpnt_init'] = restofdwelling_setpoint_fhs

                project_dict['Control']['HeatingPattern_RestOfDwelling'] =  {
                    "type": "SetpointTimeControl",
                    "start_day" : 0,
                    "time_series_step":0.5,
                    "schedule":{
                        "main": [{"repeat": 53, "value": "week"}],
                        "week": [{"repeat": 5, "value": "weekday"},
                                 {"repeat": 2, "value": "weekend"}],
                        "weekday": [restofdwelling_setpoint_fhs if x
                                    else None
                                    for x in heating_fhs_weekday],
                        "weekend": [restofdwelling_setpoint_fhs if x
                                    else None
                                    for x in heating_fhs_weekend],
                    }
                }
                if "SpaceHeatSystem" in project_dict["Zone"][zone].keys():
                    spaceheatsystem = project_dict["Zone"][zone]["SpaceHeatSystem"]
                    project_dict["SpaceHeatSystem"][spaceheatsystem]["Control"] = "HeatingPattern_RestOfDwelling"
                    if 'temp_setback' in project_dict["SpaceHeatSystem"][spaceheatsystem].keys():
                        project_dict['Control']['HeatingPattern_RestOfDwelling']['setpoint_min'] \
                            = project_dict["SpaceHeatSystem"][spaceheatsystem]['temp_setback']
                    if 'advanced_start' in project_dict["SpaceHeatSystem"][spaceheatsystem].keys():
                        project_dict['Control']['HeatingPattern_RestOfDwelling']['advanced_start'] \
                            = project_dict["SpaceHeatSystem"][spaceheatsystem]['advanced_start']
            
            elif project_dict['Zone'][zone]["SpaceHeatControl"] == "restofdwelling" \
            and controltype == 3:
                project_dict['Zone'][zone]['temp_setpnt_init'] = restofdwelling_setpoint_fhs

                project_dict['Control']['HeatingPattern_RestOfDwelling'] =  {
                    "type": "SetpointTimeControl",
                    "start_day" : 0,
                    "time_series_step":0.5,
                    "schedule":{
                        "main": [{"repeat": 53, "value": "week"}],
                        "week": [{"repeat": 5, "value": "weekday"},
                                 {"repeat": 2, "value": "weekend"}],
                        "weekday": [restofdwelling_setpoint_fhs if x
                                    else None
                                    for x in heating_nonlivingarea_fhs_weekday],
                        "weekend": [restofdwelling_setpoint_fhs if x
                                    else None
                                    for x in heating_fhs_weekend],
                    }
                }
                if "SpaceHeatSystem" in project_dict["Zone"][zone].keys():
                    spaceheatsystem = project_dict["Zone"][zone]["SpaceHeatSystem"]
                    project_dict["SpaceHeatSystem"][spaceheatsystem]["Control"] = "HeatingPattern_RestOfDwelling"
                    if 'temp_setback' in project_dict["SpaceHeatSystem"][spaceheatsystem].keys():
                        project_dict['Control']['HeatingPattern_RestOfDwelling']['setpoint_min'] \
                            = project_dict["SpaceHeatSystem"][spaceheatsystem]['temp_setback']
                    if 'advanced_start' in project_dict["SpaceHeatSystem"][spaceheatsystem].keys():
                        project_dict['Control']['HeatingPattern_RestOfDwelling']['advanced_start'] \
                            = project_dict["SpaceHeatSystem"][spaceheatsystem]['advanced_start']
        #todo: else condition to deal with zone that doesnt have specified livingroom/rest of dwelling

def create_water_heating_pattern(project_dict):
    '''
    water heating pattern - if system is not instantaneous, hold at setpoint
    00:00-02:00 and then reheat as necessary 24/7
    Note: Holding at setpoint for two hours has been chosen because
    typical setting is for sterilisation cycle to last one hour, but the
    model can only set a maximum and minimum setpoint temperaure, not
    guarantee that the temperature is actually reached. Therefore, setting
    the minimum to the maximum for two hours allows time for the tank
    to heat up to the required temperature before being held there
    '''
    HW_min_temp = "_HW_min_temp"
    HW_max_temp = "_HW_max_temp"

    project_dict['Control'][HW_min_temp] = {
        "type": "SetpointTimeControl",
        "start_day": 0,
        "time_series_step": 0.5,
        "schedule": {
            "main": [{"value": "day", "repeat": 365}],
            "day": [
                {"value": HW_setpoint_max, "repeat": 4},
                {"value": HW_temperature, "repeat": 44}
            ]
        }
    }
    project_dict['Control'][HW_max_temp] = {
        "type": "SetpointTimeControl",
        "start_day": 0,
        "time_series_step": 0.5,
        "schedule": {
            "main": [{"value": "day", "repeat": 365}],
            "day": [
                {"value": HW_setpoint_max, "repeat": 48}
            ]
        }
    }

    for hwsource in project_dict['HotWaterSource']:
        hw_source_type = project_dict['HotWaterSource'][hwsource]["type"]
        if hw_source_type == "StorageTank":
            for heatsource in project_dict['HotWaterSource'][hwsource]["HeatSource"]:
                project_dict['HotWaterSource'][hwsource]["HeatSource"][heatsource]["Controlmin"] \
                    = HW_min_temp
                project_dict['HotWaterSource'][hwsource]["HeatSource"][heatsource]["Controlmax"] \
                    = HW_max_temp

        elif hw_source_type in ("CombiBoiler", "PointOfUse", "HIU"):
            # Instantaneous water heating systems must be available 24 hours a day
            pass
        else:
            sys.exit("Standard water heating schedule not defined for HotWaterSource type"
                      + hw_source_type)

def load_evaporative_profile(filename):
    """
    Load the daily evaporative profile from a CSV file.
    
    This function reads a CSV file containing time-of-day factors for evaporative losses
    for each day of the week. It constructs a dictionary mapping days of the week to
    lists of evaporative loss factors.

    Args:
        filename (str): The name of the CSV file containing the evaporative profile data.

    Returns:
        dict: A dictionary with days of the week as keys and lists of float factors as values.
    """
    # Determine the path of the CSV file relative to the current file
    this_directory = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(this_directory, filename)

    # Open the file and read the data
    with open(file_path, mode='r') as infile:
        reader = csv.DictReader(infile)
        evap_profile_data = {day: [] for day in reader.fieldnames[1:]}  # Exclude 'Half_hour' field
        for row in reader:
            for day in evap_profile_data:
                evap_profile_data[day].append(float(row[day]))
    return evap_profile_data

def create_evaporative_losses(project_dict, TFA, N_occupants, evap_profile_data):
    """
    Apply the evaporative loss profile to modify the base evaporative loss across a full year.
    
    This function takes the base evaporative loss and modifies it according to the provided
    daily profile for each day of the week. It extends this profile throughout the year,
    adjusting for any discrepancies in the week cycle (e.g., leap years).

    Args:
        project_dict (dict): The main project dictionary where results are stored.
        TFA (float): Total floor area used in the base loss calculation.
        N_occupants (int): Number of occupants used in the base loss calculation.
        evap_profile_data (dict): Daily evaporative loss profiles loaded from a CSV file.

    Effects:
        Modifies the project_dict in-place by setting a detailed schedule for evaporative losses.
    """
    # Base evaporative loss calculation
    evaporative_losses_fhs = -25 * N_occupants
    
    # Prepare to populate a full-year schedule of gains adjusted by the profile
    evaporative_losses_schedule = []
    days_of_week = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    
    # Repeat for each week in a standard year
    for week in range(52):
        for day in days_of_week:
            for factor in evap_profile_data[day]:
                adjusted_loss = evaporative_losses_fhs * factor
                evaporative_losses_schedule.append(adjusted_loss)
    
    # Handle the extra days in the year not covered by the full weeks
    last_week_days = days_of_week[:1]  # Adjust based on the year (e.g., extra Monday for leap years)
    for day in last_week_days:
        for factor in evap_profile_data[day]:
            adjusted_loss = evaporative_losses_fhs * factor
            evaporative_losses_schedule.append(adjusted_loss)

    # Assign the calculated schedule to the project dictionary under the appropriate key
    project_dict['InternalGains']['EvaporativeLosses'] = {
        "start_day": 0,
        "time_series_step": 0.5,  # Each time step corresponds to half an hour
        "schedule": {"main": evaporative_losses_schedule}
    }
    
def load_cold_water_loss_profile(filename):
    """
    Load the daily cold water loss profile from a CSV file.
    
    This function reads a CSV file that contains time-of-day factors for cold water losses
    for each day of the week. It creates a dictionary with days of the week as keys and lists
    of float factors as values, representing the cold water loss factors for different times of the day.

    Args:
        filename (str): The name of the CSV file containing the cold water loss profile data.

    Returns:
        dict: A dictionary with days of the week as keys and lists of float factors as values.
    """
    # Determine the path of the CSV file relative to the current file
    this_directory = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(this_directory, filename)

    # Open and read the CSV file
    with open(file_path, mode='r') as infile:
        reader = csv.DictReader(infile)
        cold_water_loss_profile_data = {day: [] for day in reader.fieldnames[1:]}  # Exclude the 'Half_hour' field
        for row in reader:
            for day in cold_water_loss_profile_data:
                cold_water_loss_profile_data[day].append(float(row[day]))
    return cold_water_loss_profile_data

def create_cold_water_losses(project_dict, TFA, N_occupants, cold_water_loss_profile_data):
    """
    Apply the cold water loss profile to modify the base cold water loss across a full year.
    
    This function takes the base cold water loss and modifies it according to the provided
    daily profile for each day of the week. It extends this profile throughout the year,
    adjusting for any discrepancies in the weekly cycle (e.g., leap years).

    Args:
        project_dict (dict): The main project dictionary where results are stored.
        TFA (float): Total floor area used in the base loss calculation.
        N_occupants (int): Number of occupants used in the base loss calculation.
        cold_water_loss_profile_data (dict): Daily cold water loss profiles loaded from a CSV file.

    Effects:
        Modifies the project_dict in-place by setting a detailed schedule for cold water losses.
    """
    # Base cold water loss calculation
    cold_water_losses_fhs = -20 * N_occupants
    
    # Prepare to populate a full-year schedule of gains adjusted by the profile
    cold_water_losses_schedule = []
    days_of_week = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    
    # Repeat for each week in a standard year
    for week in range(52):
        for day in days_of_week:
            for factor in cold_water_loss_profile_data[day]:
                adjusted_loss = cold_water_losses_fhs * factor
                cold_water_losses_schedule.append(adjusted_loss)
    
    # Handle the extra days in the year not covered by the full weeks
    last_week_days = days_of_week[:1]  # Example: Just handle an extra Monday
    for day in last_week_days:
        for factor in cold_water_loss_profile_data[day]:
            adjusted_loss = cold_water_losses_fhs * factor
            cold_water_losses_schedule.append(adjusted_loss)

    # Assign the calculated schedule to the project dictionary under the appropriate key
    project_dict['InternalGains']['ColdWaterLosses'] = {
        "start_day": 0,
        "time_series_step": 0.5,  # Each time step corresponds to half an hour
        "schedule": {"main": cold_water_losses_schedule}
    }

def create_lighting_gains(project_dict, TFA, N_occupants):
    '''
    Calculate the annual energy requirement in kWh using the procedure described in SAP 10.2 up to and including step 9.
    Divide this by 365 to get the average daily energy use.
    Multiply the daily energy consumption figure by the following profiles to
    create a daily profile for each month of the year (to be applied to all days in that month).
    Multiply by the daylighting at each half hourly timestep to correct for incidence of daylight.
    '''

    '''
    here we calculate an overall lighting efficacy as
    the average of zone lighting efficacies weighted by zone
    floor area.
    '''
    lighting_efficacy = 0
    for zone in project_dict["Zone"]:
        if "Lighting"  not in project_dict["Zone"][zone].keys():
            sys.exit("missing lighting in zone "+ zone)
        if "efficacy" not in project_dict["Zone"][zone]["Lighting"].keys():
            sys.exit("missing lighting efficacy in zone "+ zone)
        lighting_efficacy += project_dict["Zone"][zone]["Lighting"]["efficacy"] * project_dict["Zone"][zone]["area"] / TFA
        
    if lighting_efficacy == 0:
        sys.exit('invalid/missing lighting efficacy for all zones')
        
    
    # TODO Consider defining large tables like this in a separate file rather than inline
    avg_monthly_halfhr_profiles = [
        [0.029235831, 0.02170637, 0.016683155, 0.013732757, 0.011874713, 0.010023118, 0.008837131, 0.007993816,
         0.007544302, 0.007057335, 0.007305208, 0.007595198, 0.009170401, 0.013592425, 0.024221707, 0.034538234,
         0.035759809, 0.02561524, 0.019538678, 0.017856399, 0.016146846, 0.014341097, 0.013408345, 0.013240894,
         0.013252628, 0.013314013, 0.013417126, 0.01429735, 0.014254224, 0.014902582, 0.017289786, 0.023494947,
         0.035462982, 0.050550653, 0.065124006, 0.072629223, 0.073631053, 0.074451912, 0.074003097, 0.073190397,
         0.071169797, 0.069983033, 0.06890179, 0.066130187, 0.062654436, 0.056634675, 0.047539646, 0.037801233],
        [0.026270349, 0.01864863, 0.014605535, 0.01133541, 0.009557625, 0.008620514, 0.007385915, 0.00674999,
         0.006144089, 0.005812534, 0.005834644, 0.006389013, 0.007680219, 0.013106226, 0.021999709, 0.027144574,
         0.02507541, 0.0179487, 0.014855879, 0.012930469, 0.011690622, 0.010230198, 0.00994897, 0.009668602,
         0.00969183, 0.010174279, 0.011264866, 0.011500069, 0.011588248, 0.011285427, 0.012248949, 0.014420402,
         0.01932017, 0.027098032, 0.044955369, 0.062118024, 0.072183735, 0.075100799, 0.075170654, 0.072433133,
         0.070588417, 0.069756433, 0.068356831, 0.06656098, 0.06324827, 0.055573729, 0.045490296, 0.035742204],
        [0.02538112, 0.018177936, 0.012838313, 0.00961673, 0.007914015, 0.006844738, 0.00611386, 0.005458354,
         0.00508359, 0.004864933, 0.004817922, 0.005375289, 0.006804643, 0.009702514, 0.013148583, 0.013569968,
         0.01293754, 0.009183378, 0.007893734, 0.00666975, 0.006673791, 0.006235776, 0.006096299, 0.006250229,
         0.006018285, 0.00670324, 0.006705105, 0.006701531, 0.006893458, 0.006440525, 0.006447363, 0.007359989,
         0.009510975, 0.011406472, 0.017428875, 0.026635564, 0.042951415, 0.057993474, 0.066065305, 0.067668248,
         0.067593187, 0.067506237, 0.065543759, 0.063020652, 0.06004127, 0.052838397, 0.043077683, 0.033689246],
        [0.029044978, 0.020558675, 0.014440871, 0.010798435, 0.008612364, 0.007330799, 0.006848797, 0.006406058,
         0.00602619, 0.005718987, 0.005804901, 0.006746423, 0.007160898, 0.008643678, 0.010489867, 0.011675722,
         0.011633729, 0.008939881, 0.007346857, 0.007177037, 0.007113926, 0.007536109, 0.007443049, 0.006922747,
         0.00685514, 0.006721853, 0.006695838, 0.005746367, 0.005945173, 0.005250153, 0.005665752, 0.006481695,
         0.006585193, 0.00751989, 0.009038481, 0.009984259, 0.011695555, 0.014495872, 0.018177089, 0.027110627,
         0.042244993, 0.056861545, 0.064008071, 0.062680016, 0.060886258, 0.055751568, 0.048310205, 0.038721632],
        [0.023835444, 0.016876637, 0.012178456, 0.009349274, 0.007659691, 0.006332517, 0.005611274, 0.005650048,
         0.005502101, 0.005168442, 0.005128425, 0.005395259, 0.004998272, 0.005229362, 0.006775116, 0.007912694,
         0.008514274, 0.006961449, 0.00630672, 0.00620858, 0.005797218, 0.005397357, 0.006006318, 0.005593869,
         0.005241095, 0.005212189, 0.00515531, 0.004906504, 0.004757624, 0.004722969, 0.004975738, 0.005211879,
         0.005684004, 0.006331507, 0.007031149, 0.008034144, 0.008731998, 0.010738922, 0.013170262, 0.016638631,
         0.021708313, 0.0303703, 0.043713685, 0.051876584, 0.054591464, 0.05074126, 0.043109775, 0.033925231],
        [0.023960632, 0.016910619, 0.012253193, 0.009539031, 0.007685214, 0.006311553, 0.00556675, 0.005140391,
         0.004604673, 0.004352551, 0.004156956, 0.004098101, 0.00388452, 0.00433039, 0.005658606, 0.006828804,
         0.007253075, 0.005872749, 0.004923197, 0.004521087, 0.004454765, 0.004304616, 0.004466648, 0.004178716,
         0.004186183, 0.003934784, 0.004014114, 0.003773073, 0.003469885, 0.003708517, 0.003801095, 0.004367245,
         0.004558263, 0.005596378, 0.005862632, 0.006068665, 0.006445161, 0.007402661, 0.007880006, 0.009723385,
         0.012243076, 0.016280074, 0.023909324, 0.03586776, 0.046595858, 0.047521241, 0.041417407, 0.03322265],
        [0.024387138, 0.017950032, 0.01339296, 0.010486231, 0.008634325, 0.00752814, 0.006562675, 0.006180296,
         0.00566116, 0.005092682, 0.004741384, 0.004680853, 0.00479228, 0.004921812, 0.005950605, 0.007010479,
         0.007057257, 0.005651136, 0.004813649, 0.00454666, 0.004121156, 0.003793481, 0.004122788, 0.004107635,
         0.004363668, 0.004310674, 0.004122943, 0.004014391, 0.004009496, 0.003805058, 0.004133355, 0.004188447,
         0.005268291, 0.005964825, 0.005774607, 0.006292344, 0.006813734, 0.007634982, 0.008723529, 0.009855823,
         0.012318322, 0.017097237, 0.026780014, 0.037823534, 0.046797578, 0.045940354, 0.039472789, 0.033058217],
        [0.023920296, 0.01690733, 0.012917415, 0.010191735, 0.008787867, 0.007681138, 0.006600128, 0.006043227,
         0.005963814, 0.005885256, 0.006164212, 0.005876554, 0.005432168, 0.00580157, 0.00641092, 0.007280576,
         0.00811752, 0.007006283, 0.006505718, 0.005917892, 0.005420978, 0.005527121, 0.005317478, 0.004793601,
         0.004577663, 0.004958332, 0.005159584, 0.004925386, 0.005192686, 0.0054453, 0.005400465, 0.005331386,
         0.005994507, 0.006370203, 0.006800758, 0.007947816, 0.009005592, 0.010608225, 0.012905449, 0.015976909,
         0.024610768, 0.036414926, 0.04680022, 0.050678553, 0.051188831, 0.046725936, 0.03998602, 0.032496965],
        [0.022221313, 0.016428778, 0.01266253, 0.010569518, 0.008926713, 0.007929788, 0.007134802, 0.006773883,
         0.006485147, 0.006766094, 0.007202971, 0.007480145, 0.008460127, 0.011414527, 0.014342431, 0.01448993,
         0.012040415, 0.008520428, 0.0077578, 0.006421555, 0.005889369, 0.005915144, 0.006229011, 0.005425193,
         0.005094464, 0.005674584, 0.005898523, 0.006504338, 0.005893063, 0.005967896, 0.0061056, 0.006017598,
         0.007500459, 0.008041236, 0.0099079, 0.012297435, 0.01592606, 0.021574549, 0.032780393, 0.04502082,
         0.054970312, 0.05930568, 0.060189471, 0.057269758, 0.05486585, 0.047401041, 0.038520417, 0.029925316],
        [0.023567522, 0.016304584, 0.012443113, 0.009961033, 0.008395854, 0.007242191, 0.006314956, 0.005722235,
         0.005385313, 0.005197814, 0.005444756, 0.0064894, 0.008409762, 0.015347201, 0.025458901, 0.028619409,
         0.023359044, 0.014869014, 0.011900433, 0.010931316, 0.010085903, 0.009253621, 0.008044246, 0.007866149,
         0.007665985, 0.007218414, 0.00797338, 0.008005782, 0.007407311, 0.008118996, 0.008648934, 0.010378068,
         0.013347814, 0.018541666, 0.026917161, 0.035860046, 0.049702909, 0.063560224, 0.069741764, 0.070609245,
         0.069689625, 0.069439031, 0.068785313, 0.065634051, 0.062207874, 0.053986076, 0.043508937, 0.033498873],
        [0.025283869, 0.018061868, 0.013832406, 0.01099122, 0.009057752, 0.007415348, 0.006415533, 0.006118688,
         0.005617255, 0.005084989, 0.005552217, 0.006364787, 0.00792208, 0.014440148, 0.02451, 0.02993728,
         0.024790064, 0.016859553, 0.013140437, 0.012181571, 0.010857371, 0.010621789, 0.010389982, 0.010087677,
         0.00981219, 0.0097001, 0.01014589, 0.01052881, 0.01044948, 0.011167223, 0.013610154, 0.02047533,
         0.035335895, 0.05409712, 0.067805633, 0.074003571, 0.077948793, 0.078981046, 0.077543712, 0.074620225,
         0.072631194, 0.070886175, 0.06972224, 0.068354439, 0.063806373, 0.055709895, 0.045866391, 0.035248054],
        [0.030992394, 0.022532047, 0.016965296, 0.013268634, 0.010662773, 0.008986943, 0.007580978, 0.006707669,
         0.00646337, 0.006180296, 0.006229094, 0.006626391, 0.00780049, 0.013149437, 0.022621172, 0.033064744,
         0.035953213, 0.029010413, 0.023490829, 0.020477646, 0.018671663, 0.017186751, 0.016526661, 0.015415424,
         0.014552683, 0.014347935, 0.014115058, 0.013739051, 0.014944386, 0.017543021, 0.021605977, 0.032100988,
         0.049851633, 0.063453382, 0.072579104, 0.076921792, 0.079601317, 0.079548711, 0.078653413, 0.076225647,
         0.073936893, 0.073585752, 0.071911165, 0.069220452, 0.065925982, 0.059952377, 0.0510938, 0.041481111]]

    #from analysis of EFUS 2017 data (updated to derive from harmonic mean)
    lumens = 1139 * (TFA * N_occupants) ** 0.39

    topup = top_up_lighting(project_dict, lumens)
    
    topup = topup / 21.3 #assumed efficacy of top up lighting
    topupperday = topup / 365

    #dropped 1/3 - 2/3 split based on SAP2012 assumptions about portable lighting
    kWhperyear = lumens/lighting_efficacy
    kWhperday = kWhperyear / 365
    factor = daylight_factor(project_dict,TFA) 

    lighting_gains_W = []
    topup_gains_W = []
    #Need to expand the monthly profiles to get an annual profile 
    annual_halfhr_profile = []
    for month in range(len(units.days_in_month)):
        for day in range(units.days_in_month[month]):
            annual_halfhr_profile.extend(avg_monthly_halfhr_profiles[month])
    
    #for each half hour time step in annual_halfhr_profiles:
    for frac in range(len(annual_halfhr_profile)):
        '''
        To obtain the lighting gains,
        the above should be converted to Watts by multiplying the individual half-hourly figure by (2 x 1000).
        Since some lighting energy will be used in external light
        (e.g. outdoor security lights or lights in unheated spaces like garages and sheds)
        a factor of 0.85 is also applied to get the internal gains from lighting.
        '''
        lighting_gains_W.append((annual_halfhr_profile[frac] * kWhperday * factor[frac]) * 2 * 1000)
        topup_gains_W.append((annual_halfhr_profile[frac] * topupperday * factor[frac]) * 2 * 1000)
    project_dict['ApplianceGains']={}
    project_dict['ApplianceGains']['lighting'] = {
        "type": "lighting",
        "start_day": 0,
        "time_series_step" : 0.5,
        "gains_fraction": 0.85,
        "EnergySupply": energysupplyname_electricity,
        "schedule": {
            "main": lighting_gains_W
            },
        "priority": -1
    }
    project_dict['ApplianceGains']['topup'] = {
        "type": "lighting",
        "start_day": 0,
        "time_series_step" : 0.5,
        "gains_fraction": 0.85,
        "EnergySupply": energysupplyname_electricity,
        "schedule": {
            "main": topup_gains_W
            }
    }

def create_appliance_gains(project_dict,TFA,N_occupants, appliance_propensities):
    #derived from EFUS 2017 total energy demand profiles
    avg_monthly_hr_profiles = [
        [0.025995114, 0.023395603, 0.022095847, 0.020796091, 0.019496336, 0.022095847, 0.02729487, 0.040292427, 0.048090962, 0.049390717, 0.050690473, 0.049390717, 0.053289984, 0.049390717, 0.050690473, 0.053289984, 0.074086076, 0.087083633, 0.08188461, 0.070186809, 0.064987786, 0.057189252, 0.046791206, 0.033793649],
        [0.025995114, 0.023395603, 0.022095847, 0.020796091, 0.019496336, 0.022095847, 0.02729487, 0.032493893, 0.046791206, 0.051990229, 0.049390717, 0.046791206, 0.048090962, 0.046791206, 0.04549145, 0.049390717, 0.062388274, 0.074086076, 0.080584854, 0.067587297, 0.059788763, 0.050690473, 0.044191694, 0.032493893],
        [0.024695359, 0.020796091, 0.020796091, 0.019496336, 0.020796091, 0.022095847, 0.029894381, 0.041592183, 0.04549145, 0.048090962, 0.04549145, 0.04549145, 0.049390717, 0.048090962, 0.048090962, 0.049390717, 0.057189252, 0.070186809, 0.07278632, 0.067587297, 0.061088519, 0.051990229, 0.041592183, 0.029894381],
        [0.022095847, 0.022095847, 0.022095847, 0.022095847, 0.023395603, 0.029894381, 0.038992672, 0.046791206, 0.046791206, 0.044191694, 0.046791206, 0.048090962, 0.044191694, 0.042891939, 0.044191694, 0.051990229, 0.062388274, 0.061088519, 0.058489007, 0.057189252, 0.050690473, 0.041592183, 0.033793649, 0.024695359],
        [0.024695359, 0.022095847, 0.020796091, 0.020796091, 0.023395603, 0.031194137, 0.038992672, 0.044191694, 0.048090962, 0.046791206, 0.044191694, 0.04549145, 0.041592183, 0.037692916, 0.038992672, 0.049390717, 0.05458974, 0.058489007, 0.051990229, 0.055889496, 0.050690473, 0.041592183, 0.031194137, 0.024695359],
        [0.022095847, 0.020796091, 0.020796091, 0.019496336, 0.020796091, 0.024695359, 0.032493893, 0.042891939, 0.044191694, 0.041592183, 0.040292427, 0.042891939, 0.040292427, 0.038992672, 0.040292427, 0.044191694, 0.053289984, 0.057189252, 0.048090962, 0.048090962, 0.04549145, 0.041592183, 0.031194137, 0.024695359],
        [0.022095847, 0.020796091, 0.020796091, 0.019496336, 0.020796091, 0.024695359, 0.032493893, 0.041592183, 0.042891939, 0.042891939, 0.041592183, 0.041592183, 0.040292427, 0.037692916, 0.037692916, 0.044191694, 0.051990229, 0.05458974, 0.046791206, 0.046791206, 0.04549145, 0.042891939, 0.031194137, 0.024695359],
        [0.022095847, 0.020796091, 0.020796091, 0.019496336, 0.020796091, 0.024695359, 0.032493893, 0.044191694, 0.044191694, 0.044191694, 0.044191694, 0.044191694, 0.042891939, 0.040292427, 0.041592183, 0.044191694, 0.051990229, 0.055889496, 0.050690473, 0.051990229, 0.049390717, 0.042891939, 0.031194137, 0.024695359],
        [0.022095847, 0.020796091, 0.020796091, 0.019496336, 0.023395603, 0.029894381, 0.040292427, 0.041592183, 0.044191694, 0.044191694, 0.04549145, 0.044191694, 0.042891939, 0.042891939, 0.042891939, 0.051990229, 0.059788763, 0.064987786, 0.061088519, 0.058489007, 0.051990229, 0.038992672, 0.031194137, 0.023395603],
        [0.022095847, 0.020796091, 0.019496336, 0.022095847, 0.023395603, 0.029894381, 0.040292427, 0.046791206, 0.049390717, 0.04549145, 0.046791206, 0.049390717, 0.04549145, 0.044191694, 0.04549145, 0.053289984, 0.067587297, 0.07278632, 0.066287542, 0.059788763, 0.053289984, 0.042891939, 0.031194137, 0.023395603],
        [0.024695359, 0.022095847, 0.020796091, 0.020796091, 0.020796091, 0.024695359, 0.029894381, 0.042891939, 0.048090962, 0.049390717, 0.04549145, 0.04549145, 0.046791206, 0.046791206, 0.044191694, 0.051990229, 0.064987786, 0.08188461, 0.076685587, 0.067587297, 0.061088519, 0.05458974, 0.04549145, 0.032493893],
        [0.025995114, 0.023395603, 0.022095847, 0.020796091, 0.019496336, 0.022095847, 0.02729487, 0.032493893, 0.048090962, 0.053289984, 0.051990229, 0.05458974, 0.057189252, 0.051990229, 0.055889496, 0.058489007, 0.075385832, 0.083184366, 0.08188461, 0.068887053, 0.062388274, 0.055889496, 0.046791206, 0.033793649]]
    
    #create flattened yearlong versions of energy use profiles
    flatEFUSprofile = []
    for month in range(len(units.days_in_month)):
        for day in range(units.days_in_month[month]):
            flatEFUSprofile.extend(avg_monthly_hr_profiles[month]) 
    
    flat_annual_propensities = {}
    for key in appliance_propensities.keys():
        flat_annual_propensities.update({key:[]})
        for month in range(len(units.days_in_month)):
            for day in range(units.days_in_month[month]):
                flat_annual_propensities[key].extend(appliance_propensities[key]) 
                
    #add any missing required appliances to the assessment,
    #get default demand figures for any unknown appliances
    appliance_cooking_defaults(project_dict, N_occupants, TFA)
    cookparams = cooking_demand(project_dict, N_occupants)
    
    
    #todo - change to enum
    #todo - check appliances are named correctly and what to do if not?
    appliancemap = { 
        "Fridge": {
            "util_unit": 1,
            "use": None,
            "standby": 0,
            "gains_frac": 1.0,
            "prof": flatEFUSprofile
        },
        "Freezer": {
            "util_unit": 1,
            "use": None,
            "standby": 0,
            "gains_frac": 1.0,
            "prof": flatEFUSprofile
        },
        "Fridge-Freezer": {
            "util_unit": 1,
            "use": None,
            "standby": 0,
            "gains_frac": 1.0,
            "prof": flatEFUSprofile
        },
        "Otherdevices": {
            "util_unit": 1,
            "use": None,
            "standby": 0,
            "gains_frac": 1.0,
            "prof": flat_annual_propensities['Consumer Electronics']
        },
        "Dishwasher": {
            "util_unit":N_occupants,
             "use": 132,         #HES 2012 final report table 22
             "standard_use": 280, #EU standard
             "standby": 0.75,
             "gains_frac": 0.3,
             "prof": flat_annual_propensities['Cleaning Dishwasher'],
             "dur": 1.5,
             "dur_devation": 0,
        },
        "Clothes_washing": {
            "util_unit":N_occupants, 
            "use": 174,         #HES 2012 final report table 22
            "standard_use": 220, #EU standard
            "standard_load_kg": 7,
            "standby": 0.75,
            "gains_frac": 0.3,
            "prof": flat_annual_propensities['Cleaning Washing machine Prop'],
            "dur": 2.5,
            "dur_devation": 0,
        },
        "Clothes_drying": {
            "util_unit":N_occupants,
            "use": 145,         #HES 2012 final report table 22
            "standard_use": 160,  #EU standard
            "standard_load_kg": 7,
            "standby": 0.50,
            "gains_frac": 0.7,
            "prof": flat_annual_propensities['Cleaning Tumble dryer'],
            "dur": 0.75,
            "dur_devation": 0,
        },
        "Oven": {
            "util_unit":1,
            "use":  cookparams["Oven"]["eventcount"],         #analysis of HES - see folder
            "standby": 0.50,
            "gains_frac": 0.5,
            "prof": flat_annual_propensities['Cooking Electric Oven'],
            "dur": 0.5,
            "dur_devation": 0.7,
        },
        "Hobs": {
            "util_unit":1,
            "use": cookparams["Hobs"]["eventcount"],         #analysis of HES - see folder
            "standby": 0.50,
            "gains_frac": 0.5,
            "prof": flat_annual_propensities['Cooking Gas Cooker'],
            "dur": 0.1,
            "dur_devation": 0.7,
        },
        "Microwave": {
            "util_unit":1,
            "use": cookparams["Microwave"]["eventcount"],         #analysis of HES - see folder
            "standby": 0.50,
            "gains_frac": 1.,
            "prof": flat_annual_propensities['Cooking Microwave'],
            "dur": 0.05,
            "dur_devation": 0.3,
        },
        "Kettle": {
            "util_unit":1,
            "use":  cookparams["Kettle"]["eventcount"],         #analysis of HES - see folder
            "standby": 0.50,
            "gains_frac": 1.,
            "prof": flat_annual_propensities['Cooking Kettle'],
            "dur": 0.05,
            "dur_devation": 0.3,
        },
    }
    
    
    #add any missing required appliances to the assessment,
    #get default demand figures for any unknown appliances
    priority = {}
    power_scheds = {}
    weight_scheds = {}
    #loop through appliances in the assessment.
    for appliancename in project_dict["Appliances"]:
        #if it needs to be modelled per use
        if isinstance(appliancemap[appliancename]["use"], int) or isinstance(appliancemap[appliancename]["use"], float):
            #value on energy label is defined differently between appliance types
            #todo - translation of efficiencies should be its own function
            kWhcycle, loadingfactor = appliance_kWhcycle_loadingfactor(project_dict, appliancename, appliancemap)
            
            
            app = FHS_appliance(appliancemap[appliancename]["util_unit"], 
                                        appliancemap[appliancename]["use"] * loadingfactor,
                                        kWhcycle,
                                        appliancemap[appliancename]["dur"],
                                        appliancemap[appliancename]["standby"],
                                        appliancemap[appliancename]["gains_frac"],
                                        appliancemap[appliancename]['prof'],
                                        duration_std_dev = appliancemap[appliancename]['dur_devation'])
            
            project_dict['ApplianceGains'][appliancename] = {
                "type": appliancename,
                "EnergySupply": project_dict["Appliances"][appliancename]["Energysupply"]\
                    if appliancename in ["Hobs", "Oven"] else energysupplyname_electricity,
                "start_day": 0,
                #TODO - variable timestep
                "time_series_step": 1,
                "gains_fraction": app.gains_frac,
                "Events": app.eventlist,
                "Standby": app.standby_W
            }
            #if the appliance specifies load shifting, add it to the dict
            if "loadshifting" in project_dict["Appliances"][appliancename].keys():
                
                if project_dict["Appliances"][appliancename]["loadshifting"]["max_shift_hrs"] >= 24:
                    #could instead change length of buffers/initial simulation match this, but unclear what benefit this would have
                    sys.exit(appliancename + " max_shift_hrs too high, FHS wrapper cannot handle max shift >= 24 hours")
                
                #establish priority between appliances based on user defined priority,
                #and failing that, demand per cycle
                if "priority" in project_dict["Appliances"][appliancename]["loadshifting"]:
                    priority[appliancename] = [project_dict["Appliances"][appliancename]["loadshifting"]["priority"], kWhcycle]
                else:
                    priority[appliancename] = [None, kWhcycle]
                
                project_dict['ApplianceGains'][appliancename].update({"loadshifting":project_dict["Appliances"][appliancename]["loadshifting"]})
                
                #create year long cost profile
                #loadshifting is also intended to respond to CO2, primary energy factors instead of cost, for example
                #so the weight timeseries is generic.
                #TODO - create weight timeseries as combination of PE, CO2, cost factors.
                #could also multiply by propensity factor
                
                weight_timeseries = schedule.expand_schedule(float, project_dict[project_dict["Appliances"][appliancename]["loadshifting"]["weight"]]["schedule"], "main", False)
                project_dict['ApplianceGains'][appliancename]["loadshifting"].update({
                        "weight_timeseries": weight_timeseries
                    }
                )
                weight_scheds.update({appliancename:weight_timeseries})
            else:
                #only add demand from appliances that DO NOT have loadshifting to the demands
                power_scheds.update({appliancename:app.flatschedule})
                priority[appliancename] = [None, kWhcycle]
            
        else:
            #model as yearlong time series schedule of demand in W
            if "kWh_per_annum" in project_dict["Appliances"][appliancename]:
                annualkWh = project_dict["Appliances"][appliancename]["kWh_per_annum"] *\
                            appliancemap[appliancename]["util_unit"]
            else:
                continue
            #todo - check normalisation of flat profile here
            flatschedule = [W_per_kW /days_per_year * frac * annualkWh for frac in flatEFUSprofile]
            power_scheds.update({appliancename:flatschedule})
            priority[appliancename] = [None, kWhcycle]
            project_dict['ApplianceGains'][appliancename] = {
                "type": appliancename,
                "EnergySupply": energysupplyname_gas if "Gas" in appliancename else energysupplyname_electricity,
                "start_day": 0,
                "time_series_step": 1,
                "gains_fraction": appliancemap[appliancename]["gains_frac"],
                "schedule": {
                    #watts
                    "main": flatschedule
                }
            }
    
    #sum schedules for use with loadshifting
    #will this work with variable timestep?
    
    sched_len = len(list(power_scheds.values())[0])
    main_power_sched = {
        energysupplyname:[0 for x in range(sched_len)]
         for energysupplyname in [energysupplyname_gas, energysupplyname_electricity]
    }
    main_weight_sched = {
        energysupplyname:[0 for x in range(sched_len)]
         for energysupplyname in [energysupplyname_gas, energysupplyname_electricity]
    }
    for sched in power_scheds.keys():
        energysupplyname = project_dict['ApplianceGains'][sched]["EnergySupply"]
        main_power_sched[energysupplyname] = [main_power_sched[energysupplyname][i] + power_scheds[sched][i] for i in range(sched_len)]
    
    for sched in weight_scheds.keys():
        energysupplyname = project_dict['ApplianceGains'][sched]["EnergySupply"]
        main_weight_sched[energysupplyname] = [main_weight_sched[energysupplyname][i] + weight_scheds[sched][i] for i in range(sched_len)]
    
    
    project_dict["Control"]["loadshifting"] = {
        "type":"smartappliance",
        "power_timeseries":main_power_sched,
        "weight_timeseries":main_weight_sched,
        "time_series_step": 1,
    }
    
    #work out order in which to process loadshifting appliances
    defined_priority = [app for app, x in priority.items() if x[0] is not None]
    lowest_priority = max([priority[p][0] for p in defined_priority] + [0])
    priority_kWhcycle = [
        x[0]for x in
        sorted(priority.items(),
            key = lambda d: d[1][1],
            reverse = True
        )
        if x[1][0] is None
    ]
    for appliance in priority.keys():
        if appliance in defined_priority:
            project_dict["ApplianceGains"][appliance]["priority"] =\
             defined_priority.index(appliance)
        else:
            project_dict["ApplianceGains"][appliance]["priority"] =\
             priority_kWhcycle.index(appliance) + lowest_priority


def cooking_demand(project_dict, N_occupants):
    
    cookparams = {"Oven":
     {"mean_annual_demand":285.14,
      "mean_annual_events":441.11,
      "mean_event_demand": 0.762,
      "fuel": project_dict["EnergySupply"][project_dict["Appliances"]["Oven"]["Energysupply"]]["fuel"]\
            if "Oven" in project_dict["Appliances"] else None},
     "Hobs":
     {"mean_annual_demand": 352.53,
      "mean_annual_events":520.86,
      "mean_event_demand":0.810,
      "fuel":project_dict["EnergySupply"][project_dict["Appliances"]["Hobs"]["Energysupply"]]["fuel"]\
            if "Hobs" in project_dict["Appliances"] else None},
    "Microwave":
     {"mean_annual_demand": 44.11,
      "mean_annual_events":710.65,
      "mean_event_demand":0.0772,
      "fuel": "electricity" if "Microwave" in project_dict["Appliances"] else None},
    "Kettle":
     {"mean_annual_demand": 173.03,
      "mean_annual_events":1782.5,
      "mean_event_demand":0.0985,
      "fuel": "electricity" if "Kettle" in project_dict["Appliances"] else None},
    }
    gastot = 0
    electot = 0
    for cook in cookparams.keys():
        if cookparams[cook]["fuel"] == "electricity":
            electot += cookparams[cook]["mean_annual_demand"]
        elif cookparams[cook]["fuel"] == "mains_gas":
            gastot += cookparams[cook]["mean_annual_demand"]
    
    #top down cooking demand estimate based on analysis of EFUS 2017 electricity monitoring data
    #and HES 2012
    annual_cooking_elec_kWh = 448 * 0.8 + (171 + 98 * N_occupants) * 0.2

    for cook in cookparams.keys():
        #for each appliance, work out number of usage events based on
        #average HES annual demand and demand per cycle
        #do not consider gas and electricity separately for this purpose
        demandprop = cookparams[cook]["mean_annual_demand"]/(electot + gastot)
        annualkWh = demandprop * annual_cooking_elec_kWh
        events = annualkWh / cookparams[cook]["mean_event_demand"]
        cookparams[cook]["eventcount"] = events
        
    return cookparams

def appliance_cooking_defaults(project_dict, N_occupants, TFA):
    #From the cooking energy supplies, need to find the associated fuel they use
    cookingfuels=[]
    for energysupply in project_dict["EnergySupply"].keys():
        fuel_type = project_dict["EnergySupply"][energysupply]["fuel"]
        cookingfuels.append(fuel_type)
    
    #also check gas/elec cooker/oven  together - better to have energysupply as a dict entry?    
    if "electricity" in cookingfuels and "mains_gas" in cookingfuels:
        cookingdefaults = {
            "Oven":{
                "Energysupply": "mains elec",
                "kWh_per_cycle": 0.59
            },
            "Hobs":{
                "Energysupply": "mains gas",
                "kWh_per_cycle": 0.72
            }
        }
    elif "mains_gas" in cookingfuels:
        cookingdefaults = {
            "Oven":{
                "Energysupply": "mains gas",
                "kWh_per_cycle": 1.57
            },
            "Hobs":{
                "Energysupply": "mains gas",
                "kWh_per_cycle": 0.72
            }
        }
    elif "electricity" in cookingfuels:
        cookingdefaults = {
            "Oven":{
                "Energysupply": "mains elec",
                "kWh_per_cycle": 0.59
            },
            "Hobs":{
                "Energysupply": "mains elec",
                "kWh_per_cycle": 0.72
            }
        }
    else:
        cookingdefaults = {
            "Oven":{
                "Energysupply": "mains elec",
                "kWh_per_cycle": 0.59
            },
            "Hobs":{
                "Energysupply": "mains elec",
                "kWh_per_cycle": 0.72
            }
        }
    additional_cookingdefaults = {
        "Kettle":{
            "kWh_per_cycle": 0.1
        },
        "Microwave":{
            "kWh_per_cycle": 0.08
        }
    }
    
    appliancedefaults  = { 
        "Otherdevices": {
            "kWh_per_annum": 30.0  * (N_occupants * TFA) ** 0.49
        },
        "Dishwasher":{
            "kWh_per_100cycle" : 53.0
        },
        "Clothes_washing":{
            "kWh_per_100cycle" : 53.0,
            "kg_load": 7.0
        },
        "Clothes_drying":{
            "kWh_per_100cycle" : 98.0,
            "kg_load": 7.0
        },
        "Fridge":{
            "kWh_per_annum" : 76.7
        },
        "Freezer":{
            "kWh_per_annum" : 128.2
        },
        "Fridge-Freezer":{
            "kWh_per_annum" : 137.4
        }
    }
    
    if "Appliances" not in project_dict.keys():
        project_dict.update({"Appliances": appliancedefaults})
        project_dict["Appliances"].update(cookingdefaults)
        project_dict["Appliances"].update(additional_cookingdefaults)
    else:
        for appliancename in appliancedefaults:
            if appliancename not in project_dict["Appliances"].keys()\
                or project_dict["Appliances"][appliancename] == "Default":
                project_dict["Appliances"].update({appliancename:appliancedefaults[appliancename]})
            elif project_dict["Appliances"][appliancename] == "Not Installed":
                project_dict["Appliances"].pop(appliancename)
            else:
                #user has specified appliance efficiency, overwrite efficiency with default
                if "loadshifting" in project_dict["Appliances"][appliancename]:
                    #do not overwrite user defined load shifting
                    ls = project_dict["Appliances"][appliancename]["loadshifting"]
                    project_dict["Appliances"].update({appliancename:appliancedefaults[appliancename]}
                    )
                    project_dict["Appliances"][appliancename].update({"loadshifting":ls})
                else:
                    project_dict["Appliances"].update({appliancename:appliancedefaults[appliancename]}
                    )
        if not any(cookdefault in project_dict["Appliances"]\
            for cookdefault in cookingdefaults):
            #neither cooker or oven specified, add cooker as minimum requirement
            project_dict["Appliances"].update({"Hobs":cookingdefaults["Hobs"]})
        cookingdefaults.update(additional_cookingdefaults)
        for cookingname in cookingdefaults:
            if cookingname not in project_dict["Appliances"].keys()\
                or project_dict["Appliances"][cookingname] == "Default":
                project_dict["Appliances"].update({cookingname:cookingdefaults[cookingname]})
            elif project_dict["Appliances"][cookingname] == "Not Installed":
                project_dict["Appliances"].pop(cookingname)
            else:
                #user has specified appliance efficiency, overwrite with default
                project_dict["Appliances"].update({appliancename:cookingdefaults[cookingname]})
    return appliancedefaults, cookingdefaults

def appliance_kWhcycle_loadingfactor(project_dict, appliancename, appliancemap):
    #value on energy label is defined differently between appliance types,
    #convert any different input types to simple kWh per cycle
    
    if "kWh_per_cycle" in project_dict["Appliances"][appliancename]:
        kWhcycle = project_dict["Appliances"][appliancename]["kWh_per_cycle"]
    elif "kWh_per_100cycle" in project_dict["Appliances"][appliancename]:
        kWhcycle = project_dict["Appliances"][appliancename]["kWh_per_100cycle"] /100
    elif "kWh_per_annum" in project_dict["Appliances"][appliancename]:
        #standard use is the number of cycles per annum dictated by EU standard for energy label
        kWhcycle = project_dict["Appliances"][appliancename]["kWh_per_annum"]\
                    /project_dict["Appliances"][appliancename]["standard_use"]
    else:
        sys.exit(appliancename, "demand must be specified as one of 'kWh_per_cycle', 'kWh_per_100cycle' or 'kWh_per_annum'")
    
    if "Clothes" in appliancename:
        #additionally, laundry appliances have variable load size,
        #which affects the required number of uses to do all the occupants' laundry for the year
        loadingfactor = appliancemap[appliancename]["standard_load_kg"] / project_dict["Appliances"][appliancename]["kg_load"]
        
        #EU Spin-drying efficiency classes and respective residual moisture contents
        spin_eff_class_to_res_moisture = {'A': 0.45,
        'B': 0.54,
        'C': 0.63,
        'D': 0.72,
        'E': 0.81,
        'F': 0.90,
        'G': 1.00}
        if "Drying" in appliancename:
            if "Clothes Washing" in project_dict["Appliances"].keys()\
             and "spin_dry_efficiency_class" in project_dict["Appliances"]["Clothes Washing"]:
                #in accordance with section 14 of Article 2 in EU regulation 2023/2533,
                #  ‘eco programme’ means a programme which is able to dry cotton laundry 
                #  from an initial moisture content of the load of 60 % 
                #  down to a final moisture content of the load of 0 %;
                residual_moisture_adjustment = (spin_eff_class_to_res_moisture[\
                    project_dict["Appliances"]["Clothes Washing"]["spin_dry_efficiency_class"]\
                    ]) / 0.6
            else:
                #if spin drying efficiency of clothes washing is not provided assume
                #60% residual moisture, so no correction
                residual_moisture_adjustment = 1.
            kWhcycle = kWhcycle * residual_moisture_adjustment
    else:
        loadingfactor = 1.0
    
    return kWhcycle, loadingfactor

def sim_24h(project_dict, sim_settings = [False, False, False, None]):
    
    heat_balance, detailed_output_heating_cooling, use_fast_solver, tariff_data_filename = sim_settings
    _24h_proj_dict = deepcopy(project_dict)
    _24h_0s_by_supply = {energysupplyname_electricity:[0 for x in range(math.ceil(units.hours_per_day / simtime_step))],
                                                                    energysupplyname_gas:[0 for x in range(math.ceil(units.hours_per_day / simtime_step))]}
    
    _24h_proj_dict["Control"]["loadshifting"]["non_appliance_demand_24hr"] = _24h_0s_by_supply
    _24h_proj_dict["Control"]["loadshifting"]["battery24hr"] = {
        "energy_into_battery_from_generation":_24h_0s_by_supply,
        "energy_out_of_battery":_24h_0s_by_supply,
        "energy_into_battery_from_grid":_24h_0s_by_supply,
        "battery_state_of_charge":_24h_0s_by_supply
        
    }
    
    _24h_proj_dict['SimulationTime']["start"] = simtime_start
    _24h_proj_dict['SimulationTime']["end"] = simtime_start + units.hours_per_day
    _24h_proj_dict['SimulationTime']["step"] = simtime_step
    
    proj = project.Project(_24h_proj_dict, heat_balance, detailed_output_heating_cooling, use_fast_solver, tariff_data_filename)
    # Run main simulation
    timestep_array, results_totals, results_end_user, \
        energy_import, energy_export, energy_generated_consumed, \
        energy_to_storage, energy_from_storage, storage_from_grid, battery_state_of_charge, energy_diverted, betafactor, \
        zone_dict, zone_list, hc_system_dict, hot_water_dict, \
        heat_cop_dict, cool_cop_dict, dhw_cop_dict, \
        ductwork_gains_dict, heat_balance_all_dict, \
        heat_source_wet_results_dict, heat_source_wet_results_annual_dict, \
        emitters_output_dict, esh_output_dict, vent_output_list, hot_water_source_results_dict = proj.run()
    
    #sum results for electricity demand other than appliances to get 24h demand buffer for loadshifting
    project_dict["Control"]["loadshifting"]["non_appliance_demand_24hr"] = {
        energysupplyname_electricity:[sum(timestep) for timestep in zip(*[
            user for (name,user) in results_end_user[energysupplyname_electricity].items()
            if name not in project_dict["Appliances"].keys()
        ])],
        energysupplyname_gas:[0 for x in range(math.ceil(units.hours_per_day / simtime_step))]
    }
    
    project_dict["Control"]["loadshifting"]["battery24hr"] = {
                    "energy_into_battery_from_generation":energy_to_storage,
                    "energy_out_of_battery":energy_from_storage,
                    "energy_into_battery_from_grid":storage_from_grid,
                    "battery_state_of_charge":battery_state_of_charge
                    
                }
    

# check whether the shower flowrate is not less than the minimum allowed    
def check_shower_flowrate(project_dict):
    
    MIN_FLOWRATE = 8.0 # minimum flow allowed. Return False if below minimum.
    showers = project_dict['HotWaterDemand']['Shower']
  
    for name, shower in showers.items():
        if 'flowrate' in shower:
            flowrate = shower['flowrate']
            if flowrate < MIN_FLOWRATE:
                print("Invalid flow rate: {0} l/s in shower with name {1}".format(flowrate, name), 
                      file=sys.stderr)
                return False
    return True
        
def create_hot_water_use_pattern(project_dict, TFA, N_occupants, cold_water_feed_temps):
    
    if not (check_shower_flowrate(project_dict)):
        sys.exit("Exited: invalid flow rate")    
    
    #temperature of mixed hot water for event
    event_temperature_showers = 41.0
    event_temperature_bath = 41.0
    event_temperature_others = 41.0
    
    mean_feedtemp = sum(cold_water_feed_temps) / len(cold_water_feed_temps)
    mean_delta_T = HW_temperature - mean_feedtemp
    
    annual_HW_events = []
    annual_HW_events_energy = []
    startmod = 0 #this changes which day of the week we start on. 0 is monday.

    #SAP 2012 relation
    #vol_daily_average = (25 * N_occupants) + 36
    
    #new relation based on Boiler Manufacturer data and EST surveys
    #reduced by 30% to account for pipework losses present in the source data
    vol_HW_daily_average =  0.70 * 60.3 * N_occupants ** 0.71
    
    # The hot water data set only included hot water use via the central hot water system
    # Electric showers are common in the UK, sometimes in addition to a central shower.
    # It is therefore very likely more showers were taken than are recorded in our main dataset.
    # To attempt to correct for this additional shower events (and their equivalent volume)
    # need to be added for use in generating the correct list of water use events.
    # It was assumed that 30% of the homes had an additional electric shower and these were
    # used half as often as showers from the central water heating system (due to lower flow).
    # This would mean that about 15% of showers taken were missing from the data.
    # The proportion of total hot water volume due to with showers in the original sample
    # was 60.685%. Increasing this by 15%, then re-adding it to the non-shower total gives
    # 109.10%. So we need to multiply the hot water use by 1.0910 to correct for the missing showers. 
    # (Note that this is only being used to generate the correct events list so does not assume
    # the dwelling being modelled actually has an electric shower, or a central shower. Allocation
    # of events to the actual showers types present in the home is done later.) 
    prop_with_elec_shower = 0.3 # 30% of homes had an additional electric shower
    elec_shower_use_prop_of_main = 0.5 # they are used half as often as the main shower
    correction_for_missing_elec_showers = 1 + prop_with_elec_shower * elec_shower_use_prop_of_main # 1.15
    original_prop_hot_water_showers = 0.60685 # from original data set
    uplifted_prop_hot_water_showers = original_prop_hot_water_showers * correction_for_missing_elec_showers
    elec_shower_correction_factor = 1 - original_prop_hot_water_showers + uplifted_prop_hot_water_showers
    vol_HW_daily_average *= elec_shower_correction_factor
    
    HWeventgen = HW_events_generator(vol_HW_daily_average)
    ref_eventlist = HWeventgen.build_annual_HW_events(startmod)
    ref_HW_vol = 0
    for event in ref_eventlist:  
        '''
        NB while calibration is done by event volumes we use the event durations from the HW csv data for showers
        so the actual hw use predicted by sap depends on shower flowrates in dwelling, but this value does not
        '''
        ref_HW_vol += float(event["vol"])
    # Add daily average hot water use to hot water only heat pump (HWOHP) object, if present
    # TODO This is probably only valid if HWOHP is the only heat source for the
    #      storage tank. Make this more robust/flexible in future.
    for hw_source_obj in project_dict['HotWaterSource'].values():
        if hw_source_obj['type'] == 'StorageTank':
            for heat_source_obj in hw_source_obj['HeatSource'].values():
                if heat_source_obj['type'] == 'HeatPump_HWOnly':
                    heat_source_obj['vol_hw_daily_average'] = vol_HW_daily_average

    FHW = (365 * vol_HW_daily_average) / ref_HW_vol



    '''
    if part G has been complied with, apply 5% reduction to duration of Other events
    '''
    partGbonus = 1.0
    if "PartGcompliance" in project_dict:
        if project_dict["PartGcompliance"] == True:
            partGbonus = 0.95
            #adjusting the size of the bath here as bath duration is not utilised by engine,
            #only bath size
    else:
        sys.exit("Part G compliance missing from input file")
    
    HW_event_aa = HW_event_adjust_allocate(N_occupants,
                    project_dict,
                     FHW,
                     event_temperature_others, 
                     HW_temperature, 
                     cold_water_feed_temps,
                     partGbonus
                     )
    
    '''
    now create lists of events
    Shower events should be  evenly spread across all showers in dwelling
    and so on for baths etc.
    '''
    hrlyevents = [[] for x in range(8760)]
    for i, event in enumerate(ref_eventlist):
        #assign HW usage events to end users and work out their durations
        #note that if there are no baths in the dwelling "bath" events are
        #assigned to showers, and vice versa (see HW_event_aa class)
        if event["type"] != "None":
            if event["type"].find("shower")!=-1:
                eventtype, name, durationfunc = HW_event_aa.get_shower()
            elif event["type"].find("bath")!=-1:
                eventtype, name, durationfunc = HW_event_aa.get_bath()
            else:
                eventtype, name, durationfunc = HW_event_aa.get_other()
            duration = durationfunc(event)
            
            eventstart = event["time"]
            
                
            if not (name in project_dict['HotWaterDemand']["Shower"] and project_dict['HotWaterDemand']["Shower"][name]["type"] == "InstantElecShower"):
                #IES can overlap with anything so ignore them entirely
                #TODO - implies 2 uses of the same IES may overlap, could check them separately
                HWeventgen.overlap_check(hrlyevents, ["Shower", "Bath"], eventstart, duration)
                hrlyevents[math.floor(eventstart)].append({"type":"Shower",
                                                           "eventstart": eventstart,
                                                           "eventend": eventstart + duration / 60.0})
                
            if event["type"].find("shower")!=-1:
                project_dict["Events"][eventtype][name].append(
                    {"start": eventstart,
                    "duration": duration, 
                    "temperature": event_temperature_showers}
                    )
            elif event["type"].find("bath")!=-1:
                if "flowrate" in project_dict["HotWaterDemand"][eventtype][name]:
                    #if the end user the event is being assigned to has a defined flowrate
                    #we are able to supply a volume
                    volume = duration * project_dict["HotWaterDemand"][eventtype][name]["flowrate"]
                    project_dict["Events"][eventtype][name].append(
                        {"start": eventstart,
                        "volume": volume, 
                        "duration": duration,
                        "temperature": event_temperature_bath}
                        )
                else:
                    #the end user does not have a defined flowrate - for example an IES
                    project_dict["Events"][eventtype][name].append(
                        {"start": eventstart,
                        "duration": duration,
                        "temperature": event_temperature_bath}
                        )
            else:
                project_dict["Events"][eventtype][name].append(
                    {"start": eventstart,
                    "duration": duration, 
                    "temperature": event_temperature_others}
                    )

def window_treatment(project_dict):

    simtime = SimulationTime(simtime_start, simtime_end, simtime_step)
    extcond = create_external_conditions(project_dict['ExternalConditions'], simtime)
    curtain_opening_sched_manual = []
    curtain_opening_sched_auto = []
    blinds_closing_irrad_manual= []
    blinds_opening_irrad_manual = []
    for _, _, _ in simtime:
        # TODO Are these waking hours correct? Check consistency with other parts of calculation
        waking_hours = (simtime.hour_of_day() >= occupant_waking_hr and simtime.hour_of_day()< occupant_sleeping_hr)
        sun_above_horizon = extcond.sun_above_horizon()
        curtain_opening_sched_manual.append(
            True if waking_hours and sun_above_horizon           # Open during waking hours after sunrise
            else False if waking_hours and not sun_above_horizon # Close during waking hours after sunset
            else None                                            # Do not adjust outside waking hours
            )
        curtain_opening_sched_auto.append(sun_above_horizon)
        blinds_closing_irrad_manual.append(300.0 if waking_hours else None)
        blinds_opening_irrad_manual.append(200.0 if waking_hours else None)

    project_dict['Control']['_curtains_open_manual'] = {
        "type": "OnOffTimeControl",
        "allow_null": True,
        "start_day": 0,
        "time_series_step": simtime_step,
        "schedule": {
            "main": curtain_opening_sched_manual
            }
        }
    project_dict['Control']['_curtains_open_auto'] = {
        "type": "OnOffTimeControl",
        "start_day": 0,
        "time_series_step": simtime_step,
        "schedule": {
            "main": curtain_opening_sched_auto
            }
        }

    project_dict['Control']['_blinds_closing_irrad_manual'] = {
        "type": "SetpointTimeControl",
        "start_day": 0,
        "time_series_step": simtime_step,
        "schedule": {
            "main": blinds_closing_irrad_manual
            }
        }
    project_dict['Control']['_blinds_closing_irrad_auto'] = {
        "type": "SetpointTimeControl",
        "start_day": 0,
        "time_series_step": 1.0,
        "schedule": {
            "main": [{"repeat": simtime_end, "value": 200.0}]
            }
        }
    project_dict['Control']['_blinds_opening_irrad_manual'] = {
        "type": "SetpointTimeControl",
        "start_day": 0,
        "time_series_step": simtime_step,
        "schedule": {
            "main": blinds_opening_irrad_manual
            }
        }
    project_dict['Control']['_blinds_opening_irrad_auto'] = {
        "type": "SetpointTimeControl",
        "start_day": 0,
        "time_series_step": 1.0,
        "schedule": {
            "main": [{"repeat": simtime_end, "value": 200.0}]
            }
        }

    for zone in project_dict["Zone"]:
        for _, BuildingElement in project_dict["Zone"][zone]["BuildingElement"].items():
            if BuildingElement["type"] == "BuildingElementTransparent" and "treatment" in BuildingElement.keys():
                for treatment in BuildingElement["treatment"]:
                    treatment['is_open'] = False # Initial condition

                    if treatment["type"] == "curtains":
                        if WindowTreatmentCtrl.is_manual(treatment["controls"]):
                            treatment["Control_open"] = '_curtains_open_manual'
                        elif WindowTreatmentCtrl.is_automatic(treatment["controls"]):
                            treatment["Control_open"] = '_curtains_open_auto'
                        else:
                            raise ValueError("Unknown control type for window treatment: " + str(treatment["controls"]))

                    #blinds are opened and closed in response to solar irradiance incident upon them
                    elif treatment["type"] == "blinds":
                        if WindowTreatmentCtrl.is_manual(treatment["controls"]):
                            #manual control - Table B.24 in BS EN ISO 52016-1:2017.
                            treatment["Control_closing_irrad"] = '_blinds_closing_irrad_manual'
                            treatment["Control_opening_irrad"] = '_blinds_opening_irrad_manual'
                        elif WindowTreatmentCtrl.is_automatic(treatment["controls"]):
                            #automatic control - Table B.24 in BS EN ISO 52016-1:2017.
                            treatment["Control_closing_irrad"] = '_blinds_closing_irrad_auto'
                            treatment["Control_opening_irrad"] = '_blinds_opening_irrad_auto'
                            treatment["opening_delay_hrs"] = 2.
                        else:
                            raise ValueError("Unknown control type for window treatment: " + str(treatment["controls"]))

                    else:
                        raise ValueError("Unknown window treatment type: " + str(treatment["type"]))

def create_window_opening_schedule(project_dict):

    window_opening_setpoint = 22.0

    project_dict['Control']["_window_opening_adjust"] = {
        "type": "SetpointTimeControl",
        "start_day": 0,
        "time_series_step": 1.0,
        "schedule": {
            "main": [{"repeat": simtime_end, "value": window_opening_setpoint}]
            }
        }
    project_dict['InfiltrationVentilation']['Control_WindowAdjust'] = "_window_opening_adjust"
 
    project_dict['Control']["_window_opening_openablealways"] = {
        "type": "OnOffTimeControl",
        "start_day": 0,
        "time_series_step": 1.0,
        "schedule": {
            "main": [{"repeat": simtime_end, "value": True}]
            }
        }
 
    project_dict['Control']["_window_opening_closedsleeping"] = {
        "type": "OnOffTimeControl",
        "start_day": 0,
        "time_series_step": 1.0,
        "schedule": {
            "main": [{"repeat": 365, "value": "day"}],
            "day": [
                    {"repeat": occupant_waking_hr, "value": False},
                    {"repeat": occupant_sleeping_hr - occupant_waking_hr, "value": True},
                    {"repeat": 24 - occupant_sleeping_hr, "value": False}
                    ]
            }
        }
    
    noise_nuisance = project_dict['InfiltrationVentilation']["noise_nuisance"]

    for z_name in project_dict['Zone'].values():
        if z_name["BuildingElement"] is not None:
            for build_components,build_elements in z_name["BuildingElement"].items():                 
                if build_elements['type'] == 'BuildingElementTransparent':
                    if noise_nuisance is True or build_elements['security_risk'] is True:
                        build_elements['Control_WindowOpenable'] = "_window_opening_closedsleeping"
                    else:
                        build_elements['Control_WindowOpenable'] = "_window_opening_openablealways"                                       

def minimum_air_change_rate(project_dict, TFA,total_volume, bedroom_number):
    """ Calculate effective air change rate accoring to according to Part F 1.24 a """
    
    # minimum ventilation rates method B
    min_ventilation_rates_b = [19, 25, 31, 37, 43]
    
    #Calculate minimum whole dwelling ventilation rate l/s method A
    min_ventilation_rate_a = TFA * 0.3

    #Calculate minimum whole dwelling ventilation rate l/s method B
    if bedroom_number <= 5:
        min_ventilation_rate_b = min_ventilation_rates_b[bedroom_number -1]
    elif bedroom_number > 6:
        min_ventilation_rate_b = min_ventilation_rates_b[-1] + (bedroom_number - 5) * 6

    # Calculate air change rate ACH
    minimum_ach = ( max(min_ventilation_rate_a, min_ventilation_rate_b) / total_volume ) \
                    * units.seconds_per_hour / units.litres_per_cubic_metre

    return minimum_ach

def create_vent_opening_schedule(project_dict):
    """ Set min and max vent opening thresholds """
    TFA = calc_TFA(project_dict)
    bedroom_number = project_dict['NumberOfBedrooms']
    total_volume = 0
    for zones, zone_data in project_dict['Zone'].items():
        total_volume += zone_data['volume']

    vent_adjust_min_ach = minimum_air_change_rate(
        project_dict,
        TFA,
        total_volume,
        bedroom_number,
        )
    vent_adjust_max_ach = 2.0

    project_dict['Control']["_vent_adjust_min_ach"] = {
        "type": "SetpointTimeControl",
        "start_day": 0,
        "time_series_step": 1.0,
        "schedule": {
            "main": [{"repeat": simtime_end - simtime_start, "value": vent_adjust_min_ach}]
            }
        }
    project_dict['InfiltrationVentilation']['Control_VentAdjustMin'] = "_vent_adjust_min_ach"

    project_dict['Control']["_vent_adjust_max_ach"] = {
        "type": "SetpointTimeControl",
        "start_day": 0,
        "time_series_step": 1.0,
        "schedule": {
            "main": [{"repeat": simtime_end - simtime_start, "value": vent_adjust_max_ach}]
            }
        }
    project_dict['InfiltrationVentilation']['Control_VentAdjustMax'] = "_vent_adjust_max_ach"

def create_MEV_pattern(proj_dict):
    #intermittent extract fans are assumed to turn on whenever cooking, bath or shower events occur
    
    intermittent_mev = {}
    for vent in proj_dict['InfiltrationVentilation']['MechanicalVentilation'].keys():
        if proj_dict['InfiltrationVentilation']['MechanicalVentilation'][vent]['vent_type'] == "Intermittent MEV":
            intermittent_mev[vent] = [0 for x in range(math.ceil((simtime_end - simtime_start) / simtime_step))]
    
    mevnames = list(intermittent_mev.keys())
    if mevnames == []:
        return
    
    class _cycle_mev:
        #if there are multiple extract fans they are cycled sequentially
        #in order that they all be used an approximately equal amount,
        #so a different extract fan could be activated by the same shower,
        #and likewise the same extract fan could be activated by cooking as by a shower
        def __init__(self, mevnames):
            self.mevnames = mevnames
            self.cycle_count = 0
        def getmev(self):
            res = self.mevnames[self.cycle_count]
            self.cycle_count  = (self.cycle_count  + 1) % len(self.mevnames)
            return res
    
    cycle_mev = _cycle_mev(mevnames)
    
    for HW_enduse in ["Shower", "Bath"]:
        for eventtype in proj_dict["Events"][HW_enduse]:
            for event in proj_dict["Events"][HW_enduse][eventtype]:
                mevname = cycle_mev.getmev()
                idx = math.floor(event["start"] / simtime_step)
                tsfrac = event["duration"] / (units.minutes_per_hour * simtime_step)
                #add fraction of the timestep for which appliance is turned on
                #to the fraction of the timestep for which the fan is turned on,
                #and cap that fraction at 1.
                integralx = 0.0
                startoffset = event["start"] / simtime_step - idx
                while integralx < tsfrac:
                    segment = min(math.ceil(startoffset) - startoffset, tsfrac - integralx)
                    _idx = (idx + math.floor(startoffset + integralx)) % len(intermittent_mev[mevname])
                    intermittent_mev[mevname][_idx] = min(intermittent_mev[mevname][_idx] + segment, 1)
                    integralx += segment
    
    #these names are the same as those already defined in create_appliance_gains
    #TODO - define them at top level of wrapper
    #kettles and microwaves are assumed not to activate the extract fan
    for cook_enduse in ["Oven","Hobs"]:
        if cook_enduse in proj_dict["ApplianceGains"].keys():
            for event in proj_dict["ApplianceGains"][cook_enduse]["Events"]:
                mevname = cycle_mev.getmev()
                idx = math.floor(event["start"] / simtime_step)
                #appliance/cooking event durations are in hours, not minutes
                tsfrac = event["duration"] / simtime_step
                #add fraction of the timestep for which appliance is turned on
                #to the fraction of the timestep for which the fan is turned on,
                #and cap that fraction at 1.
                integralx = 0.0
                startoffset = event["start"] / simtime_step - idx
                while integralx < tsfrac:
                    segment = min(math.ceil(startoffset) - startoffset, tsfrac - integralx)
                    _idx = (idx + math.floor(startoffset + integralx)) % len(intermittent_mev[mevname])
                    intermittent_mev[mevname][_idx] = min(intermittent_mev[mevname][_idx] + segment, 1)
                    integralx += segment
    
    for vent in intermittent_mev.keys():
        controlname = "_intermittent_MEV_control: " + str(vent)
        proj_dict['InfiltrationVentilation']['MechanicalVentilation'][vent]['Control'] = controlname
        proj_dict['Control'][controlname] = {
            "type": "SetpointTimeControl",
            "start_day": 0,
            "time_series_step": simtime_step,
            "schedule": {
                "main": intermittent_mev[vent]
            }
        }



def calc_SFP_mech_vent(project_dict):
    if project_dict['InfiltrationVentilation'].get('MechanicalVentilation') is not None:
        for mech_vents_name, mech_vents_data in project_dict['InfiltrationVentilation']['MechanicalVentilation'].items():
            if mech_vents_data['vent_type'] in ('Centralised continuous MEV', 'MVHR'):
                measured_fan_power = mech_vents_data['measured_fan_power'] # in W
                measured_air_flow_rate = mech_vents_data['measured_air_flow_rate'] # in l/s
                # Specific fan power is total measured electrical power in Watts divided by air flow rate  
                measured_sfp = measured_fan_power / measured_air_flow_rate # in W/l/s
                mech_vents_data['SFP'] = measured_sfp
            elif mech_vents_data['vent_type'] in ('Decentralised continuous MEV', 'Intermittent MEV'):
                pass
            else:
                sys.exit("Mechanical ventilation type not recognised")

def create_cooling(project_dict):
    cooling_setpoint = 24.0

    #07:00-09:30 and then 18:30-22:00
    cooling_subschedule_livingroom_weekday = (
        [None for x in range(14)] +
        [cooling_setpoint for x in range(5)] +
        [None for x in range(18)] +
        [cooling_setpoint for x in range(7)] +
        [None for x in range(4)])

    #08:30 - 22:30
    cooling_subschedule_livingroom_weekend = (
        [None for x in range(17)] +
        [cooling_setpoint for x in range(28)] +
        [None for x in range(3)])

    cooling_subschedule_restofdwelling = (
        #22:00-07:00 - ie nighttime only
        [cooling_setpoint for x in range(14)] +
        [None for x in range(30)] +
        [cooling_setpoint for x in range(4)]
    )
    
    for zone in project_dict['Zone']:
        if "SpaceHeatControl" in project_dict['Zone'][zone]:
            if project_dict['Zone'][zone]["SpaceHeatControl"] == "livingroom" and "SpaceCoolSystem" in project_dict['Zone'][zone]:
                project_dict['Control']['Cooling_LivingRoom'] = {
                    "type": "SetpointTimeControl",
                    "start_day" : 0,
                    "time_series_step":0.5,
                    "schedule": {
                        "main": [{"repeat": 53, "value": "week"}],
                        "week": [{"repeat": 5, "value": "weekday"},
                                 {"repeat": 2, "value": "weekend"}],
                        "weekday": cooling_subschedule_livingroom_weekday,
                        "weekend": cooling_subschedule_livingroom_weekend,
                    }
                }
                spacecoolsystem = project_dict["Zone"][zone]["SpaceCoolSystem"]
                project_dict["SpaceCoolSystem"][spacecoolsystem]["Control"] = "Cooling_LivingRoom"
                if 'temp_setback' in project_dict["SpaceCoolSystem"][spacecoolsystem].keys():
                    project_dict['Control']['Cooling_LivingRoom']['setpoint_max'] \
                        = project_dict["SpaceCoolSystem"][spacecoolsystem]['temp_setback']
                if 'advanced_start' in project_dict["SpaceCoolSystem"][spacecoolsystem].keys():
                    project_dict['Control']['Cooling_LivingRoom']['advanced_start'] \
                        = project_dict["SpaceCoolSystem"][spacecoolsystem]['advanced_start']

            elif project_dict['Zone'][zone]["SpaceHeatControl"] == "restofdwelling" and "SpaceCoolSystem" in project_dict['Zone'][zone]:
                project_dict['Control']['Cooling_RestOfDwelling'] = {
                    "type": "SetpointTimeControl",
                    "start_day" : 0,
                    "time_series_step":0.5,
                    "schedule": {
                        "main": [{"repeat": 365, "value": "day"}],
                        "day": cooling_subschedule_restofdwelling
                    }
                }
        
                spacecoolsystem = project_dict["Zone"][zone]["SpaceCoolSystem"]
                project_dict["SpaceCoolSystem"][spacecoolsystem]["Control"] = "Cooling_RestOfDwelling"
                if 'temp_setback' in project_dict["SpaceCoolSystem"][spacecoolsystem].keys():
                    project_dict['Control']['Cooling_RestOfDwelling']['setpoint_max'] \
                        = project_dict["SpaceCoolSystem"][spacecoolsystem]['temp_setback']
                if 'advanced_start' in project_dict["SpaceCoolSystem"][spacecoolsystem].keys():
                    project_dict['Control']['Cooling_RestOfDwelling']['advanced_start'] \
                        = project_dict["SpaceCoolSystem"][spacecoolsystem]['advanced_start']

def create_cold_water_feed_temps(project_dict):
    
    #24 hour average feed temperature (degreees Celsius) per month m. SAP 10.2 Table J1
    T24m_header_tank = [11.1, 11.3, 12.3, 14.5, 16.2, 18.8, 21.3, 19.3, 18.7, 16.2, 13.2, 11.2]
    T24m_mains = [8, 8.2, 9.3, 12.7, 14.6, 16.7, 18.4, 17.6, 16.6, 14.3, 11.1, 8.5]
    T24m=[]
    feedtype=""
    #typical fall in feed temp from midnight to 6am
    delta = 1.5
    
    if "header tank" in project_dict["ColdWaterSource"]:
        T24m = T24m_header_tank
        feedtype="header tank"
    else:
        T24m = T24m_mains
        feedtype="mains water"
    
    cold_feed_schedulem=[]
    
    for T in T24m:
        #typical cold feed temp between 3pm and midnight
        Teveningm = T + (delta * 15 /48)
        
        #variation throughout the day
        cold_feed_schedulem += [[
        Teveningm - delta * t/6 for t in range(0,6)]+
        [Teveningm - (15-t) * delta /9 for t in range(6,15)]+
        [Teveningm for t in range(15,24)]]
        
    outputfeedtemp=[]
    for i in range(31):
        outputfeedtemp.extend(cold_feed_schedulem[0])
    for i in range(28):
        outputfeedtemp.extend(cold_feed_schedulem[1])
    for i in range(31):
        outputfeedtemp.extend(cold_feed_schedulem[2])
    for i in range(30):
        outputfeedtemp.extend(cold_feed_schedulem[3])
    for i in range(31):
        outputfeedtemp.extend(cold_feed_schedulem[4])
    for i in range(30):
        outputfeedtemp.extend(cold_feed_schedulem[5])
    for i in range(31):
        outputfeedtemp.extend(cold_feed_schedulem[6])
    for i in range(31):
        outputfeedtemp.extend(cold_feed_schedulem[7])
    for i in range(30):
        outputfeedtemp.extend(cold_feed_schedulem[8])
    for i in range(31):
        outputfeedtemp.extend(cold_feed_schedulem[9])
    for i in range(30):
        outputfeedtemp.extend(cold_feed_schedulem[10])
    for i in range(31):
        outputfeedtemp.extend(cold_feed_schedulem[11])
    
    project_dict['ColdWaterSource'][feedtype] = {
        "start_day": 0,
        "time_series_step": 1,
        "temperatures": outputfeedtemp
    }
    return outputfeedtemp

def daylight_factor(project_dict,TFA):
    
    total_area = [0] * total_steps
    data=[]
    df = []
    
    for zone in project_dict['Zone']:
        for element in project_dict["Zone"][zone]["BuildingElement"]:
            if project_dict["Zone"][zone]["BuildingElement"][element]["type"] =="BuildingElementTransparent":
                #retrieve window properties of each window
                ff = project_dict["Zone"][zone]["BuildingElement"][element]["frame_area_fraction"]
                g_val = project_dict["Zone"][zone]["BuildingElement"][element]["g_value"]
                width = project_dict["Zone"][zone]["BuildingElement"][element]["width"]
                height = project_dict["Zone"][zone]["BuildingElement"][element]["height"]
                base_height = project_dict["Zone"][zone]["BuildingElement"][element]["base_height"]
                orientation = project_dict["Zone"][zone]["BuildingElement"][element]["orientation360"]
                shading = project_dict["Zone"][zone]["BuildingElement"][element]["shading"]
                w_area = float(width) * float(height)
                #retrieve half hourly shading factor
                direct = shading_factor(project_dict,base_height, height, width, orientation, shading)
                area = (0.9 * w_area * (1 - float(ff)) * float(g_val))
                w_tot = [factor * area for factor in direct]
                
                data.append(w_tot)
    
    
    for idx in data:
        for t,gl in enumerate(idx):
            total_area[t] += gl
            
    #calculate Gl for each half hourly timestep 
    for i in range(len(total_area)):
        Gl = total_area[i] / TFA
    
        if Gl > 0.095:
            df.append(0.96)
        else:
            factor = 52.2 * Gl**2 - 9.94 * Gl + 1.433
            df.append(factor)
    return df
    
def shading_factor(project_dict,base_height, height, width, orientation, shading):
    def __init_orientation(orientation360):
        """ Convert orientation from 0-360 (clockwise) to -180 to +180 (anticlockwise) """
        return 180 - orientation360
    def convert_shading(shading_segments):
        """ Function to convert orientation from -180 to +180 (anticlockwise) to 0-360 (clockwise) """
        for element in shading_segments:
            element["start"] = __init_orientation(element["start360"])
            element["end"] = __init_orientation(element["end360"])
        return shading_segments
    
    time = deepcopy(simtime)
    dir_shade = []
    
    if project_dict['ExternalConditions']['direct_beam_conversion_needed']:
            dir_beam_conversion = project_dict['ExternalConditions']['direct_beam_conversion_needed']
    else:
            dir_beam_conversion = False
            
    conditions = ExternalConditions(
            time,
            project_dict['ExternalConditions']['air_temperatures'],
            project_dict['ExternalConditions']['wind_speeds'],
            project_dict['ExternalConditions']['wind_directions'],
            project_dict['ExternalConditions']['diffuse_horizontal_radiation'],
            project_dict['ExternalConditions']['direct_beam_radiation'],
            project_dict['ExternalConditions']['solar_reflectivity_of_ground'],
            project_dict['ExternalConditions']['latitude'],
            project_dict['ExternalConditions']['longitude'],
            0,
            0,
            365,
            1,
            None,
            None,
            None,
            dir_beam_conversion,
            convert_shading(project_dict['ExternalConditions']['shading_segments']),
            )
            
    #for each half hourly timestep get the shading factor
    for t_idx, _, _ in time: 
        direct = conditions.direct_shading_reduction_factor(base_height, height, width, orientation, shading)
        dir_shade.append(direct)
    
    return dir_shade

def top_up_lighting (project_dict, l_req):
    
    capacity_tot = 0
    
    for zone in project_dict["Zone"]:
        if "bulbs"  not in project_dict["Zone"][zone]["Lighting"].keys():
            sys.exit("missing light bulbs in zone "+ zone)
            
        for bulb in project_dict["Zone"][zone]["Lighting"]["bulbs"].keys():
            capacity = \
            (project_dict["Zone"][zone]["Lighting"]["bulbs"][bulb]["count"] * \
            project_dict["Zone"][zone]["Lighting"]["bulbs"][bulb]["power"] * \
            project_dict["Zone"][zone]["Lighting"]["bulbs"][bulb]["efficacy"])
            capacity_tot += capacity
            
    TFA = calc_TFA(project_dict)
    capacity_ref = 330 * TFA 
    
    l_prov = l_req * (capacity_tot / capacity_ref)
    
    l_topup = 0
    if l_prov < (l_req / 3):
        l_topup = (l_req / 3) - l_prov
    else:
        l_topup = 0
        
    return l_topup

