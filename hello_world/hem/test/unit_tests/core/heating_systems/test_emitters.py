#!/usr/bin/env python3

"""
This module contains unit tests for the Instant Electric Heater module
"""

# Standard library imports
import unittest
import numpy as np
from unittest.mock import Mock

# Set path to include modules to be tested (must be before local imports)
from unit_tests.common import test_setup
test_setup()

# Local imports
from core.simulation_time import SimulationTime
from core.energy_supply.energy_supply import EnergySupplyConnection, EnergySupply
from core.heating_systems.emitters import Emitters
from core.external_conditions import ExternalConditions

class TestEmitters(unittest.TestCase):
    """ Unit tests for InstantElecHeater class """

    def setUp(self):
        """ Create InstantElecHeater object to be tested """
        self.simtime = SimulationTime(0, 2, 0.25)

        # Create simple HeatSource object implementing required interface to run tests
        class HeatSource:
            def energy_output_max(self, temp_flow, temp_return, time_start):
                return 2.5
            def demand_energy(self, energy_req_from_heating_system, temp_flow, temp_return, time_start, update_heat_source_state=True):
                return max(0, min(2.5, energy_req_from_heating_system))
            def running_time_throughput_factor(self,space_heat_running_time_cumulative,
                                               energy_req_from_heat_source,
                                               temp_flow_target,
                                               temp_return_target,
                                               time_start,
                                               ):
                return 'Heat source throughput function called with ' \
                    + str(space_heat_running_time_cumulative) + ', ' \
                    + str(energy_req_from_heat_source) + ', ' \
                    + str(temp_flow_target) + ', ' \
                    + str(temp_return_target) + ', ' \
                    + str(time_start)
            
        self.heat_source = HeatSource()

        # Create simple Zone object implementing required interface to run tests
        class Zone:
            def area(self):
                return 80.0
            def temp_internal_air(self):
                return 20.0

        self.zone = Zone()
        self.airtemp = [0.0, 2.5, 5.0, 7.5, 10.0, 12.5, 15.0, 20.0]
        self.windspeed = [3.7, 3.8, 3.9, 4.0, 4.1, 4.2, 4.3, 4.4]
        self.wind_direction = [200, 220, 230, 240, 250, 260, 260, 270]
        energy_supply_conn_name_auxiliary = 'Boiler_auxiliary'
        self.airtemp = [0.0, 2.5, 5.0, 7.5, 10.0, 12.5, 15.0, 20.0]
        self.diffuse_horizontal_radiation = [333, 610, 572, 420, 0, 10, 90, 275]
        self.direct_beam_radiation = [420, 750, 425, 500, 0, 40, 0, 388]
        self.solar_reflectivity_of_ground = [0.2] * 8760
        self.latitude = 51.42
        self.longitude = -0.75
        self.timezone = 0
        self.start_day = 0
        self.end_day = 0
        self.time_series_step = 1
        self.january_first = 1
        self.daylight_savings = "not applicable"
        self.leap_day_included = False
        self.direct_beam_conversion_needed = False
        self.shading_segments = [
            {"number": 1, "start": 180, "end": 135},
            {"number": 2, "start": 135, "end": 90},
            {"number": 3, "start": 90, "end": 45},
            {"number": 4, "start": 45, "end": 0},
            {"number": 5, "start": 0, "end": -45},
            {"number": 6, "start": -45, "end": -90},
            {"number": 7, "start": -90, "end": -135},
            {"number": 8, "start": -135, "end": -180}
        ]
        self.ext_cond = ExternalConditions(
            self.simtime,
            self.airtemp,
            self.windspeed,
            self.wind_direction,
            self.diffuse_horizontal_radiation,
            self.direct_beam_radiation,
            self.solar_reflectivity_of_ground,
            self.latitude,
            self.longitude,
            self.timezone,
            self.start_day,
            self.end_day,
            self.time_series_step,
            self.january_first,
            self.daylight_savings,
            self.leap_day_included,
            self.direct_beam_conversion_needed,
            self.shading_segments
            )
        
        self.ecodesign_controller = {
                "ecodesign_control_class": 2,
                "min_outdoor_temp": -4,
                "max_outdoor_temp": 20,
                "min_flow_temp": 30}

        self.emitters = Emitters(0.14,
                                 [
                                  {
                                   "wet_emitter_type": "radiator",
                                   "c": 0.08,
                                   "n": 1.2,
                                   "frac_convective": 0.4
                                  }
                                 ],
                                 10.0,
                                 True, 
                                 None, 
                                 3, 
                                 18,
                                 0.0, 
                                 self.heat_source,
                                 self.zone,
                                 self.ext_cond, self.ecodesign_controller, 55.0, self.simtime)
        
        self.energysupply     = EnergySupply("electricity", self.simtime)
        self.energysupplyconn = self.energysupply.connection("main")
        
        self.fancoil = Emitters(None, [
                                        {
                                        "wet_emitter_type": "fancoil",
                                        "n_units": 1,
                                        "frac_convective": 0.4,
                                        "fancoil_test_data": {
                                            "fan_speed_data": [
                                                {
                                                "temperature_diff": 80.0,
                                                "power_output": [2.7, 3.6, 5, 5.3, 6.2, 7.4]
                                                },
                                                {
                                                "temperature_diff": 70.0,
                                                "power_output": [2.3, 3.1, 4.2, 4.5, 5.3, 6.3]
                                                },
                                                {
                                                "temperature_diff": 60.0,
                                                "power_output": [1.9, 2.6, 3.5, 3.8, 4.4, 5.3]
                                                },
                                                {
                                                "temperature_diff": 50.0,
                                                "power_output": [1.5, 2, 2.8, 3, 3.5, 4.2]
                                                },
                                                {
                                                "temperature_diff": 40.0,
                                                "power_output": [1.1, 1.5, 2.05, 2.25, 2.6, 3.15]
                                                },
                                                {
                                                "temperature_diff": 30.0,
                                                "power_output": [0.7, 0.97, 1.32, 1.49, 1.7, 2.09]
                                                },
                                                {
                                                "temperature_diff": 20.0,
                                                "power_output": [0.3, 0.44, 0.59, 0.73, 0.8, 1.03]
                                                },
                                                {
                                                "temperature_diff": 10.0,
                                                "power_output": [0, 0, 0, 0, 0, 0]
                                                }    
                                            ],
                                            "fan_power_W": [15, 19, 25, 33, 43, 56]
                                            }
                                        }
                                       ],
                                        10.0, True, None, 3, 18, 0.0, self.heat_source, self.zone,
                                        self.ext_cond, self.ecodesign_controller, 55.0, self.simtime,self.energysupplyconn)
    
    def test_demand_energy(self):
        """ Test that Emitter object returns correct energy supplied """
        energy_demand_list = [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.0, 0.0]
        energy_demand = 0.0
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                energy_demand += energy_demand_list[t_idx]
                energy_provided = self.emitters.demand_energy(energy_demand)
                energy_demand -= energy_provided
                self.assertAlmostEqual(
                    energy_provided,
                    [0.26481930394248643, 0.8203297684307538, 0.9900258469156371, 0.9900258469156371,
                     0.8941786531029309, 0.8715059403189445, 0.8715059403189445, 0.7471884447241743]
                    [t_idx],
                    msg='incorrect energy provided by emitters',
                    )
                self.assertAlmostEqual(
                    self.emitters._Emitters__temp_emitter_prev,
                    [35.96557640041081, 45.833333333333336, 45.833333333333336, 45.833333333333336,
                     43.22916666666667, 43.22916666666667, 43.22916666666667, 37.89210634720828]
                    [t_idx],
                    msg='incorrect emitter temperature calculated'
                    )
    
    def test_demand_energy_fancoil(self):
        """ Test that fancoil returns correct energy supplied """
        energy_demand_list = [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.0, 0.0]
        energy_demand = 0.0
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                energy_demand += energy_demand_list[t_idx]
                energy_provided = self.fancoil.demand_energy(energy_demand)
                energy_demand -= energy_provided
                self.assertAlmostEqual(
                    energy_provided,
                    [0.43450355962369697, 0.43450355962369697, 0.43450355962369697, 0.43450355962369697,
                     0.37944261695906434, 0.37944261695906434, 0.37944261695906434, 0.37944261695906434]
                    [t_idx],
                    msg='incorrect energy provided by emitters',
                    )
                self.assertAlmostEqual(
                    self.fancoil._Emitters__temp_emitter_prev,
                    [20.0, 20.0, 20.0, 20.0,
                     20.0, 20.0, 20.0, 20.0]
                    [t_idx],
                    msg='incorrect emitter temperature calculated'
                    )
    
    def test_temp_flow_return(self):
        ''' Test flow and return temperature based on ecodesign control class'''
        flow_temp,return_temp = self.emitters.temp_flow_return()
        self.assertAlmostEqual(flow_temp, 50.8333, 3)
        self.assertAlmostEqual(return_temp, 43.5714, 3)
    
        #Test with different outdoor temp
        self.ecodesign_controller = {
                "ecodesign_control_class": 2,
                "min_outdoor_temp": 10,
                "max_outdoor_temp": 15,
                "min_flow_temp": 30}
    
        self.emitters = Emitters(0.14, [
                                        {"wet_emitter_type": "radiator", "c": 0.08, "n": 1.2, "frac_convective": 0.4}
                                       ],
                                       10.0, True, None, 3, 18, 0.0, self.heat_source, self.zone,
                                       self.ext_cond, self.ecodesign_controller, 55.0, self.simtime)
    
        flow_temp,return_temp = self.emitters.temp_flow_return()
        self.assertAlmostEqual(flow_temp, 55.0, 3)
        self.assertAlmostEqual(return_temp, 47.1428, 3)
    
        #Test with different control class
        self.ecodesign_controller = {
                "ecodesign_control_class": 4,
                "min_outdoor_temp": -4,
                "max_outdoor_temp": 20,
                "min_flow_temp": 30}
    
        self.emitters = Emitters(0.14, [
                                        {"wet_emitter_type": "radiator", "c": 0.08, "n": 1.2, "frac_convective": 0.4}
                                       ],
                                       10.0, True, None, 3, 18, 0.0, self.heat_source, self.zone, 
                                       self.ext_cond, self.ecodesign_controller, 55.0, self.simtime)
    
        flow_temp,return_temp = self.emitters.temp_flow_return()
        self.assertAlmostEqual(flow_temp, 55.0)
        self.assertAlmostEqual(return_temp, 47.14285714)
    
        #Test with different control class and ufh
        self.ecodesign_controller = {
                "ecodesign_control_class": 4,
                "min_outdoor_temp": -4,
                "max_outdoor_temp": 20,
                "min_flow_temp": 30}
    
        self.emitters = Emitters(0.14, [
                                        {
                                        "wet_emitter_type": "ufh",
                                        "equivalent_specific_thermal_mass": 80,
                                        "system_performance_factor": 5,
                                        "emitter_floor_area": 80.0, 
                                        "frac_convective": 0.43
                                        }
                                       ],
                                       10.0, True, None, 3, 18, 0.0, self.heat_source, self.zone, 
                                       self.ext_cond, self.ecodesign_controller, 55.0, self.simtime)
    
        flow_temp,return_temp = self.emitters.temp_flow_return()
        self.assertAlmostEqual(flow_temp, 55.0)
        self.assertAlmostEqual(return_temp, 47.14285714)
    
    def test_temp_flow_return_invalid_value(self):
        # Use an invalid ecodesign_control_class value (e.g., 11)
        self.ecodesign_controller = {
                "ecodesign_control_class": 11,
                "min_outdoor_temp": -4,
                "max_outdoor_temp": 20,
                "min_flow_temp": 30}
        with self.assertRaises(SystemExit):

            self.emitters = Emitters(0.14, [
                                            {"wet_emitter_type": "radiator", "c": 0.08, "n": 1.2, "frac_convective": 0.4}
                                           ],
                                           10.0, True, None, 3, 18, 0.0, self.heat_source, self.zone,
                                           self.ext_cond, self.ecodesign_controller, 55.0, self.simtime)
    
    
    def test_power_output_emitter(self):
        '''Test emitter output at given emitter and room temp'''
        self.ecodesign_controller = {
                "ecodesign_control_class": 2,
                "min_outdoor_temp": -4,
                "max_outdoor_temp": 20,
                "min_flow_temp": 30}
    
        self.emitters = Emitters(0.14, [
                                        {"wet_emitter_type": "radiator", "c": 0.08, "n": 1.2, "frac_convective": 0.4}
                                       ],
                                        10.0, True, None, 3, 18, 0.0, self.heat_source, self.zone,
                                        self.ext_cond, self.ecodesign_controller, 55.0, self.simtime)
        temp_emitter = 15.0
        temp_rm = 10.0        
        self.assertAlmostEqual(self.emitters.power_output_emitter(temp_emitter, temp_rm), 0.55189186)
    
    def test_power_output_emitter_ufh(self):
        '''Test ufh emitter output at given emitter and room temp'''
        self.ecodesign_controller = {
                "ecodesign_control_class": 2,
                "min_outdoor_temp": -4,
                "max_outdoor_temp": 20,
                "min_flow_temp": 30}
    
        self.emitters = Emitters(0.14, [
                                        {
                                        "wet_emitter_type": "ufh",
                                        "equivalent_specific_thermal_mass": 80,
                                        "system_performance_factor": 5,
                                        "emitter_floor_area": 80.0,
                                        "frac_convective": 0.43
                                        }
                                       ],
                                        10.0, True, None, 3, 18, 0.0, self.heat_source, self.zone,
                                        self.ext_cond, self.ecodesign_controller, 55.0, self.simtime)
        temp_emitter = 15.0
        temp_rm = 10.0        
        self.assertAlmostEqual(self.emitters.power_output_emitter(temp_emitter, temp_rm), 2.0)
    
    def test_temp_emitter_req(self):
        ''' Test emitter temperature that gives required power output at given room temp'''
        power_emitter_req = 0.22
        temp_rm = 2.0
    
        self.assertAlmostEqual(self.emitters.temp_emitter_req(power_emitter_req, temp_rm), 4.32332827)
    
    def test_func_temp_emitter_change_rate(self):
        ''' Test Differential eqn is formed for change rate of emitter temperature'''
    
        func = self.emitters._Emitters__func_temp_emitter_change_rate(5)
        # Check if the returned value is a lambda function
        self.assertTrue(callable(func))
        self.assertEqual(func.__name__, '<lambda>')
    
    def test_temp_emitter(self):
        ''' Test function calculates emitter temperature after specified time with specified power input'''
        # Check None conditions  are invoked
        temp_emitter, time_temp_diff_max_reached = self.emitters.temp_emitter( time_start = 0,
                                                                              time_end = 2,
                                                                              temp_emitter_start= 5,
                                                                              temp_rm = 10,
                                                                              power_input = 0.2,
                                                                              temp_emitter_max=None,
                                                                              )
        self.assertAlmostEqual(temp_emitter, 7.85714285)
        self.assertEqual(time_temp_diff_max_reached, None)
    
        #Check not None conditions are invoked        
        temp_emitter, time_temp_diff_max_reached = self.emitters.temp_emitter( time_start = 0,
                                                                              time_end = 2,
                                                                              temp_emitter_start= 70,
                                                                              temp_rm = 10,
                                                                              power_input = 0.2,
                                                                              temp_emitter_max= 25,
                                                                              )
    
        self.assertAlmostEqual(temp_emitter, 25.0)
        self.assertAlmostEqual(time_temp_diff_max_reached, 1.29981138)
    
    def test_format_fancoil_manufacturer_data(self):
        ''' Test the function accepts test data and 
        returns fancoil manufacturer data in expected numpy format'''
        test_data = {   
            'fan_speed_data': [
                {'temperature_diff': 80.0, 'power_output': [2.7, 3.6, 5, 5.3, 6.2, 7.4]},
                {'temperature_diff': 70.0, 'power_output': [2.3, 3.1, 4.2, 4.5, 5.3, 6.3]}
            ],
            'fan_power_W': [15, 19, 25, 33, 43, 56]
        }
        
        fc_temperature_data, fc_fan_power_data = self.emitters.format_fancoil_manufacturer_data(test_data)
        
        expected_temperature = np.array([
            [80.0, 2.7, 3.6, 5.0, 5.3, 6.2, 7.4],
            [70.0, 2.3, 3.1, 4.2, 4.5, 5.3, 6.3]
        ])
        
        expected_fan_power = np.array([
            ["Fan power (W)", 15, 19, 25, 33, 43, 56]
        ])
        
        # Use np.testing.assert_array_equal for better diagnostics
        np.testing.assert_array_equal(fc_temperature_data.astype(float), expected_temperature, 
                                      err_msg="Temperature Arrays are not equal")
        
        # Reshape fc_fan_power_data to match the shape of expected_fan_power
        np.testing.assert_array_equal(fc_fan_power_data.reshape(1, -1), expected_fan_power, 
                                      err_msg="Fan power Arrays are not equal")
        
        # Test the function does a system exit if the fan_speeds list differ in length
        test_data_invalid = {
            'fan_speed_data': [
                {'temperature_diff': 80.0, 'power_output': [2, 4, 6, 8, 9, 11]},
                {'temperature_diff': 70.0, 'power_output': [2, 4, 6, 8, 9]}
            ],
            'fan_power_W': [15, 19, 25, 33, 43, 56]
        }
        
        with self.assertRaises(SystemExit):    
            self.emitters.format_fancoil_manufacturer_data(test_data_invalid)
    
    def test_energy_required_from_heat_source(self):
        
        energy_demand_list = [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]
        energy_demand = 0.0
        timestep = 1.0
        temp_rm_prev = 10.0
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                energy_demand += energy_demand_list[t_idx]
                power_emitter_req = energy_demand / timestep
                temp_emitter_req = self.emitters.temp_emitter_req(power_emitter_req, temp_rm_prev)
                energy_req, temp_emitter_max_is_final_temp, __ = self.emitters._Emitters__energy_required_from_heat_source(
                                                                        energy_demand,
                                                                        timestep = timestep,
                                                                        temp_rm_prev = temp_rm_prev,
                                                                        temp_emitter_max = 25,
                                                                        temp_return = 30,
                                                                        time_heating_start = 0,
                                                                        temp_emitter_heating_start = self.emitters._Emitters__temp_emitter_prev,
                                                                        temp_emitter_req = temp_emitter_req,
                                                                        )

            self.assertAlmostEqual(
                    energy_req,
                    [0.7487346289045738, 2.458950517761754, 2.458950517761754, 2.458950517761754,
                     2.458950517761754, 2.458950517761754, 2.458950517761754,2.458950517761754]
                    [t_idx],
                    )
            self.assertEqual(
                    temp_emitter_max_is_final_temp,
                    [False, False, True, True, True, True, True, True]
                    [t_idx],
                    )

        
    # def test_running_time_throughput_factor(self):
    #     ''' Test appropriate heat source function and arguments are called to calculate throughput factor''' 
    #     #Check for conditionals when energy demand is greater than 0.0
    #     msg = self.emitters.running_time_throughput_factor(energy_demand = 0.5,
    #                                                        space_heat_running_time_cumulative =  5)
    #
    #     self.assertEqual('Heat source throughput function called with 5, 2.5, 50.833333333333336, 43.57142857142857, 0.0', msg)
    #
    #     #Check for conditionals when energy demand is 0.0 
    #     msg = self.emitters.running_time_throughput_factor(energy_demand = 0.0,
    #                                                        space_heat_running_time_cumulative =  5)
    #
    #     self.assertEqual('Heat source throughput function called with 5, 0.0, 50.833333333333336, 43.57142857142857, 0.0', msg)

    def test_energy_output_min(self):
        mockzone = Mock()
        mockzone.temp_internal_air.return_value = 10.0
        mockzone.area.return_value = 80
        self.emitters = Emitters(0.14,
                                 [
                                  {
                                   "wet_emitter_type": "radiator",
                                   "c": 0.08,
                                   "n": 1.2,
                                   "frac_convective": 0.4
                                  }
                                 ],
                                 10.0, True, None, 3, 18, 0.0, self.heat_source, mockzone,
                                 self.ext_cond, self.ecodesign_controller, 55.0, self.simtime)
        self.assertAlmostEqual(self.emitters.energy_output_min(), 0.2780866841016483)
