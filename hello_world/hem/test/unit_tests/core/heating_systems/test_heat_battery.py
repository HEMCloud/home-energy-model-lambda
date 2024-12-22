#!/usr/bin/env python3

"""
This module contains unit tests for the heat_battery module
"""

# Standard library imports
import unittest
from unittest.mock import patch,MagicMock

# Set path to include modules to be tested (must be before local imports)
from unit_tests.common import test_setup
test_setup()

# Local imports
from core.schedule import expand_schedule
from core.simulation_time import SimulationTime
from core.external_conditions import ExternalConditions
from core.heating_systems.heat_battery import *
from core.energy_supply.energy_supply import EnergySupply, EnergySupplyConnection
from core.controls.time_control import SetpointTimeControl,ChargeControl

def contains_value(dicts, key, value):
    '''Function to determine the list of dict has a specific value'''    
    return any(d.get(key) == value for d in dicts)

class TestHeatBatteryService(unittest.TestCase):

    def setUp(self):
        self.mock_heat_battery = MagicMock()
        self.service_name = "TestService"
        self.simtime = SimulationTime(0, 2, 1)

    def test_service_is_on_with_control(self):
        ''' Test a HeatBatteryService object control'''
        # Test when control is provided and returns True
        self.ctrl_true = SetpointTimeControl([21.0],
                                        self.simtime,
                                        0, #start_day
                                        1.0, #time_series_step
                                        )
        self.heat_battery_service = HeatBatteryService(
                        heat_battery=self.mock_heat_battery,
                        service_name=self.service_name,
                        control=self.ctrl_true
                        )
        self.assertTrue(self.heat_battery_service.is_on())

        # Test when control is provided and returns False
        self.ctrl_false = SetpointTimeControl([None],
                                        self.simtime,
                                        0, #start_day
                                        1.0, #time_series_step
                                        )

        self.heat_battery_service = HeatBatteryService(
                            heat_battery=self.mock_heat_battery,
                            service_name=self.service_name,
                            control=self.ctrl_false
                            )

        self.assertFalse(self.heat_battery_service.is_on())

    def test_service_is_on_without_control(self):
        # Create a service without control
        self.heat_battery_service_no_control = HeatBatteryService(
                            heat_battery=self.mock_heat_battery,
                            service_name=self.service_name
                            )
        self.assertTrue(self.heat_battery_service_no_control.is_on())


class TestHeatBatteryServiceWaterRegular(unittest.TestCase):

    def setUp(self):
        self.mock_heat_battery      = MagicMock()
        self.mock_heat_battery_data = MagicMock()
        self.mock_cold_feed         = MagicMock()
        self.mock_simulation_time   = MagicMock()
        self.mock_control           = MagicMock()
        self.service_name           = "WaterHeating"
        self.controlmin = SetpointTimeControl(
                               [52.0, None, None, None, 52.0, 52.0, 52.0, 52.0],
                               self.mock_simulation_time,
                               0,
                               1
                               )
        self.controlmax = SetpointTimeControl(
                               [55.0, 55.0, 55.0, 55.0, 55.0, 55.0, 55.0, 55.0],
                               self.mock_simulation_time,
                               0,
                               1
                               )
        self.heat_battery_service = HeatBatteryServiceWaterRegular(
                    heat_battery=self.mock_heat_battery,
                    heat_battery_data=self.mock_heat_battery_data,
                    service_name=self.service_name,
                    cold_feed=self.mock_cold_feed,
                    simulation_time=self.mock_simulation_time,
                    controlmin=self.controlmin,
                    controlmax=self.controlmax,
                    )

    @patch.object(HeatBatteryServiceWaterRegular, 'is_on', return_value=True)
    def test_demand_energy(self, mock_is_on):
        ''' Test demand energy with service on'''
        energy_demand = 10.0  
        temp_return = 40.0  
        # Call the method under test
        result = self.heat_battery_service.demand_energy(energy_demand, temp_return)
        # Check if the heat battery's demand_energy method was called correctly
        self.mock_heat_battery._HeatBattery__demand_energy.assert_called_once_with(
                        self.service_name,
                        ServiceType.WATER_REGULAR,
                        energy_demand,
                        temp_return
                        )    

    @patch.object(HeatBatteryServiceWaterRegular, 'is_on', return_value=False)
    def test_demand_energy_service_off(self, mock_is_on):
        ''' Test demand energy with service off'''
        energy_demand = 10.0  
        temp_return = 40.0  
        # Call the method under test
        result = self.heat_battery_service.demand_energy(energy_demand, temp_return)
        # Check if the heat battery's demand_energy method was called with zero energy demand
        self.mock_heat_battery._HeatBattery__demand_energy.assert_called_once_with(
                        self.service_name,
                        ServiceType.WATER_REGULAR,
                        0.0,
                        temp_return
                        )

    @patch.object(HeatBatteryServiceWaterRegular, 'is_on', return_value=True)
    def test_energy_output_max_service_on(self, mock_is_on):
        ''' Test maximum energy output function is called with correct arguments'''
        temp_return = 40.0
        # Call the method under test
        self.heat_battery_service.energy_output_max(temp_return)
        # Check if the heat battery's __energy_output_max method was called correctly
        self.mock_heat_battery.\
                _HeatBattery__energy_output_max.assert_called_once_with(55)


    @patch.object(HeatBatteryServiceWaterRegular, 'is_on', return_value=False)
    def test_energy_output_max_service_off(self, mock_is_on):
        ''' Test maximum energy output function when service is off'''
        temp_return = 40.0
        # Call the method under test
        result = self.heat_battery_service.energy_output_max(temp_return)
        # Check the result
        self.assertEqual(result, 0.0)

class TestHeatBatteryServiceSpace(unittest.TestCase):
    def setUp(self):
        self.simtime            = SimulationTime(0, 2, 1)
        self.sched              = [21.0, 21.0]
        self.setptctrl          = SetpointTimeControl(self.sched,
                                              self.simtime,
                                              start_day = 0,
                                              time_series_step = 1,
                                              setpoint_min=None,
                                              setpoint_max=None,
                                              default_to_max=None,
                                              duration_advanced_start=0.0,
                                              )
        self.heat_battery       = MagicMock()
        self.service_name       = 'service_space'
        self.heat_battery_space = HeatBatteryServiceSpace(self.heat_battery,
                                                          self.service_name,
                                                          self.setptctrl
                                                          )


    def test_temp_setpnt(self):
        self.assertAlmostEqual(self.heat_battery_space.temp_setpnt(), 21.0)

    def test_in_required_period(self):
        self.assertTrue(self.heat_battery_space.in_required_period())

    @patch.object(HeatBatteryServiceSpace, 'is_on', return_value=True)
    def test_demand_energy(self, mock_is_on):
        ''' Test demand energy with service on'''
        energy_demand = 10.0  
        temp_return = 40.0 
        temp_flow = 1.0
        # Call the method under test
        result = self.heat_battery_space.demand_energy(energy_demand, 
                                                       temp_flow, 
                                                       temp_return)
        # Check if the heat battery's demand_energy method was called correctly
        update_heat_source_state = True
        self.heat_battery._HeatBattery__demand_energy.assert_called_once_with(
                        self.service_name,
                        ServiceType.SPACE,
                        energy_demand,
                        temp_return,
                        update_heat_source_state
                        )    

    @patch.object(HeatBatteryServiceSpace, 'is_on', return_value=False)
    def test_demand_energy_service_off(self, mock_is_on):
        ''' Test demand energy with service off'''
        energy_demand = 10.0  
        temp_return = 40.0 
        temp_flow = 1.0 
        # Call the method under test
        result = self.heat_battery_space.demand_energy(energy_demand,
                                                       temp_flow, 
                                                       temp_return)
        # Check the result
        self.assertEqual(result, 0.0)

    @patch.object(HeatBatteryServiceSpace, 'is_on', return_value=True)
    def test_energy_output_max_service_on(self, mock_is_on):
        ''' Test maximum energy output function is called with correct arguments'''
        temp_output = 70
        temp_return_feed = 40 
        time_start = 0.1
        # Call the method under test
        result = self.heat_battery_space.energy_output_max(
            temp_output,
            temp_return_feed,
            time_start,
            )
        # Check if the heat battery's __energy_output_max method was called correctly
        self.heat_battery._HeatBattery__energy_output_max.assert_called_once_with(temp_output, time_start)

    @patch.object(HeatBatteryServiceSpace, 'is_on', return_value=False)
    def test_energy_output_max_service_off(self, mock_is_on):
        ''' Test maximum energy output function when service is off'''
        temp_output = 70
        temp_return_feed = 40
        # Call the method under test
        result = self.heat_battery_space.energy_output_max(temp_output,
                                                           temp_return_feed)
        # Check the result
        self.assertEqual(result, 0.0)


class TestHeatBattery(unittest.TestCase):
    def setUp(self):
        self.heat_dict  = {
                          'type': 'HeatBattery',
                          'EnergySupply': 'mains elec',
                          'heat_battery_location': 'internal', 
                          'electricity_circ_pump': 0.06, 
                          'electricity_standby': 0.0244,
                          'rated_charge_power': 20.0, 
                          'heat_storage_capacity': 80.0, 
                          'max_rated_heat_output': 15.0, 
                          'max_rated_losses': 0.22, 
                          'number_of_units': 1, 
                          'ControlCharge': 'hb_charge_control',
                          'labs_tests_rated_output' : [
                                    [0.0, 0],
                                    [0.08, 0.00],
                                    [0.16, 0.03],
                                    [0.17, 0.05],
                                    [0.19, 0.10],
                                    [0.21, 0.15],
                                    [0.23, 0.21],
                                    [0.25, 0.23],
                                    [0.28, 0.26],
                                    [0.31, 0.29],
                                    [0.34, 0.32],
                                    [0.38, 0.36],
                                    [0.42, 0.41],
                                    [0.47, 0.45],
                                    [0.52, 0.51],
                                    [0.58, 0.57],
                                    [0.64, 0.64],
                                    [0.72, 0.71],
                                    [0.8, 0.8],
                                    [0.89, 0.89],
                                    [1.0, 1.0]
                                ],
                          'labs_tests_rated_output_enhanced' : [
                                    [0.0, 0.0],
                                    [0.101, 0.0],
                                    [0.12, 0.18],
                                    [0.144, 0.235],
                                    [0.175, 0.313],
                                    [0.215, 0.391],
                                    [0.266, 0.486],
                                    [0.328, 0.607],
                                    [0.406, 0.728],
                                    [0.494, 0.795],
                                    [0.587, 0.825],
                                    [0.683, 0.875],
                                    [0.781, 0.906],
                                    [0.891, 0.953],
                                    [0.981, 0.992],
                                    [1.0, 1.0]
                            ],
                          'labs_tests_losses' : [
                                    [0.0, 0],
                                    [0.16, 0.13],
                                    [0.17, 0.15],
                                    [0.19, 0.17],
                                    [0.21, 0.18],
                                    [0.23, 0.21],
                                    [0.25, 0.23],
                                    [0.28, 0.26],
                                    [0.31, 0.29],
                                    [0.34, 0.32],
                                    [0.38, 0.36],
                                    [0.42, 0.41],
                                    [0.47, 0.45],
                                    [0.52, 0.51],
                                    [0.58, 0.57],
                                    [0.64, 0.64],
                                    [0.72, 0.71],
                                    [0.8, 0.8],
                                    [0.89, 0.89],
                                    [1.0, 1.0]
                            ]
                          }
        self.simtime    = SimulationTime(0, 2, 1)
        self.sched      = expand_schedule(bool,
                                          {'main':[{'repeat': 1, 'value': False}]}, 
                                           "main", False)

        self.energysupply       = EnergySupply("mains_gas", self.simtime)
        self.energysupplyconn = self.energysupply.connection("WaterHeating")
        self.windspeed = [3.7, 3.8]
        self.wind_direction = [200, 220]
        self.airtemp = [0.0, 2.5]
        self.diffuse_horizontal_radiation = [333, 610]
        self.direct_beam_radiation = [420, 750]
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
        ]
        
        self.extcond = ExternalConditions(
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
        self.external_sensor = {
                "correlation": [
                    {"temperature": 0.0, "max_charge": 1.0},
                    {"temperature": 10.0, "max_charge": 0.9},
                    {"temperature": 18.0, "max_charge": 0.0}
                ]
            }
        self.ctrl       = ChargeControl( "Manual",
                                            self.sched,
                                            self.simtime,
                                            0,
                                            1,
                                            0.2,
                                            None, None,
                                            None, None,
                                            self.extcond, self.external_sensor)
        self.heatbattery = HeatBattery(
                self.heat_dict,
                self.ctrl,
                self.energysupply,
                self.energysupplyconn,
                self.simtime,
                self.extcond
                )

    def test_create_service_connection(self):
        ''' Test creation of EnergySupplyConnection for the service name given''' 
        self.service_name = 'new_service'
        # Ensure the service name does not exist in __energy_supply_connections
        self.assertNotIn(self.service_name, 
                         self.heatbattery._HeatBattery__energy_supply_connections)
        # Call the method under test
        self.heatbattery._HeatBattery__create_service_connection(self.service_name)
        # Check that the service name was added to __energy_supply_connections
        self.assertIn(self.service_name,
                      self.heatbattery._HeatBattery__energy_supply_connections)
        # Check system exit when connection is created with exiting service name
        with self.assertRaises(SystemExit):
            self.heatbattery._HeatBattery__create_service_connection(self.service_name)

    def test_convert_to_energy(self):
        ''' Test to check conversion of power value supplied to the correct units'''

        power = 10.0
        timestep = 0.25
        self.assertAlmostEqual(self.heatbattery._HeatBattery__convert_to_energy(power,timestep),2.5)

    def test_electric_charge(self):
        ''' Test to check calculation of power required '''
        # __charge_control is off
        self.assertAlmostEqual(self.heatbattery._HeatBattery__electric_charge(3600), 0.0)

        self.sched  = expand_schedule(bool, {'main':[{'repeat': 1, 'value': True}]}, 
                                      "main", False)
        self.ctrl   = ChargeControl(
                                        "Manual",
                                        self.sched,
                                        self.simtime,
                                        0,
                                        1,
                                        [0.2, 0.2],
                                        None, None,
                                        None, None,
                                        self.extcond, self.external_sensor)
        self.heatbattery = HeatBattery(
                            self.heat_dict,
                            self.ctrl,
                            self.energysupply,
                            self.energysupplyconn,
                            self.simtime,
                            self.extcond
                            ) 
        # __charge_control is on
        self.assertAlmostEqual(self.heatbattery._HeatBattery__electric_charge(10),20.0)

    def test_lab_test_rated_output(self):

        self.assertAlmostEqual(self.heatbattery._HeatBattery__lab_test_rated_output(5.0),15.0)

    def test_lab_test_losses(self):

        self.assertAlmostEqual(self.heatbattery._HeatBattery__lab_test_losses(5.0),0.22)

    def test_first_call(self):
        self.sched  = expand_schedule(bool, {"main": [{"value": True, "repeat":2},
                                                     {"value": True, "repeat": 1}]},
                                            "main", True)
        self.ctrl   = ChargeControl( "Manual",
                                        self.sched,
                                        self.simtime,
                                        0,
                                        1,
                                        [0.2 ,1],
                                        None, None,
                                        None, None,
                                        self.extcond, self.external_sensor)

        self.heatbattery = HeatBattery(
                            self.heat_dict,
                            self.ctrl,
                            self.energysupply,
                            self.energysupplyconn,
                            self.simtime,
                            self.extcond
                            ) 
        
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):        
                # Call the method under test
                self.heatbattery._HeatBattery__first_call()
                # Assertions to check if the internal state was updated correctly
                self.assertFalse(self.heatbattery._HeatBattery__flag_first_call)
                self.assertAlmostEqual(self.heatbattery._HeatBattery__Q_in_ts,
                                       [20.0, 20.0][t_idx])
                self.assertAlmostEqual(self.heatbattery._HeatBattery__Q_out_ts,
                                       [4.358566028225806, 4.358566028225806][t_idx])
                self.assertAlmostEqual(self.heatbattery._HeatBattery__Q_loss_ts,
                                       [0.031277812499999995, 0.031277812499999995][t_idx])   
            self.heatbattery.timestep_end()

    def test_demand_energy(self):
        self.sched  = expand_schedule(bool, {"main": [{"value": True, "repeat": 1},
                                                      {"value": True, "repeat": 2}]},
                                             "main", True)
        self.ctrl   = ChargeControl("Manual",
                                       self.sched,
                                       self.simtime,
                                       0,
                                       1,
                                       [0.2, 0.3],
                                       None, None,
                                       None, None,
                                       self.extcond, self.external_sensor)

        self.heatbattery = HeatBattery(
                            self.heat_dict,
                            self.ctrl,
                            self.energysupply,
                            self.energysupplyconn,
                            self.simtime,
                            self.extcond
                            ) 
        
        self.heatbattery._HeatBattery__create_service_connection('new_service')
        
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):        
                self.assertAlmostEqual(self.heatbattery._HeatBattery__demand_energy(
                                       'new_service', 
                                       ServiceType.WATER_REGULAR,
                                       5.0,
                                       40.0),
                                       [4.358566028225806, 4.358566028225806][t_idx])
                self.assertTrue(contains_value(self.heatbattery._HeatBattery__service_results, 
                                       'service_name',
                                       'new_service'))
                self.assertAlmostEqual(self.heatbattery._HeatBattery__charge_level, 
                                       [0.19512695199092742, 0.2][t_idx])
                self.assertAlmostEqual(self.heatbattery._HeatBattery__total_time_running_current_timestep, 
                                       [1.0,1.0][t_idx])
            self.heatbattery.timestep_end()


    def test_calc_auxiliary_energy(self):  
        """Check heat battery auxilary energy consumption"""
        
        self.heatbattery._HeatBattery__energy_supply_conn = MagicMock()        
        self.heatbattery._HeatBattery__calc_auxiliary_energy(1.0, 0.5)

        time_remaining_current_timestep = 0.5
        expected_energy_aux = (
            self.heatbattery._HeatBattery__total_time_running_current_timestep
            * self.heatbattery._HeatBattery__power_circ_pump
        ) + (
            self.heatbattery._HeatBattery__power_standby
            * time_remaining_current_timestep
        )
        
        self.heatbattery._HeatBattery__energy_supply_conn.\
                                        demand_energy.assert_called_once_with(expected_energy_aux)

    def test_timestep_end(self):
        self.sched  = expand_schedule(bool, {"main": [{"value": True, "repeat": 1},
                                                      {"value": True, "repeat": 2}]},
                                             "main", True)
        self.ctrl   = ChargeControl( "Manual",
                                        self.sched,
                                        self.simtime,
                                        0,
                                        1,
                                        [1.0, 1.5],
                                        None, None,
                                        None, None,
                                        self.extcond, self.external_sensor)

        self.heatbattery = HeatBattery(
                            self.heat_dict,
                            self.ctrl,
                            self.energysupply,
                            self.energysupplyconn,
                            self.simtime,
                            self.extcond
                            )
        
        self.heatbattery._HeatBattery__create_service_connection('new_timestep_end_service')
        
        # Change the state of HeatBattery object parameters
        self.heatbattery._HeatBattery__demand_energy('new_timestep_end_service', 
                                       ServiceType.WATER_REGULAR,
                                       5.0,
                                       40.0)
        
        # Assertions to check the internal state 
        self.assertAlmostEqual(self.heatbattery._HeatBattery__Q_in_ts,20.0)
        self.assertAlmostEqual(self.heatbattery._HeatBattery__Q_out_ts,5.637774816176471)
        self.assertAlmostEqual(self.heatbattery._HeatBattery__Q_loss_ts,0.03929547794117647) 
        self.assertAlmostEqual(self.heatbattery._HeatBattery__total_time_running_current_timestep,
                               0.8868747268254661)
        self.assertTrue(contains_value(self.heatbattery._HeatBattery__service_results, 
                                       'service_name',
                                       'new_timestep_end_service'))
        
        # Call the method under test
        self.heatbattery.timestep_end()   

        # Assertions to check if the internal state was updated correctly
        self.assertFalse(self.heatbattery._HeatBattery__flag_first_call)
        self.assertAlmostEqual(self.heatbattery._HeatBattery__Q_in_ts,20.0)
        self.assertAlmostEqual(self.heatbattery._HeatBattery__Q_out_ts,10.001923317091928)
        self.assertAlmostEqual(self.heatbattery._HeatBattery__Q_loss_ts,0.07624000227068732) 
        self.assertAlmostEqual(self.heatbattery._HeatBattery__total_time_running_current_timestep,
                                0.0)
        self.assertEqual(self.heatbattery._HeatBattery__service_results,[])
            

    def test_energy_output_max(self):

        self.sched  = expand_schedule(bool, {"main": [{"value": True, "repeat": 1},
                                                      {"value": True, "repeat": 1}]},
                                             "main", True)
        self.ctrl   = ChargeControl( "Manual",
                                        self.sched,
                                        self.simtime,
                                        0,
                                        1,
                                        [1.5, 1.6],
                                        None, None,
                                        None, None,
                                        self.extcond, self.external_sensor)
        self.heatbattery = HeatBattery(
                            self.heat_dict,
                            self.ctrl,
                            self.energysupply,
                            self.energysupplyconn,
                            self.simtime,
                            self.extcond
                            )        
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):        
                self.assertAlmostEqual(self.heatbattery._HeatBattery__energy_output_max(0.0),
                                       [5.637774816176471,  11.13482970854502][t_idx])  
            
            self.heatbattery.timestep_end() 


if __name__ == '__main__':
    unittest.main()