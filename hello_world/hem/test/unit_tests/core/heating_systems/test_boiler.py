#!/usr/bin/env python3

"""
This module contains unit tests for the boiler module
"""

# Standard library imports
import unittest
from unittest.mock import patch,MagicMock

# Set path to include modules to be tested (must be before local imports)
from unit_tests.common import test_setup
test_setup()

# Local imports
from core.simulation_time import SimulationTime
from core.external_conditions import ExternalConditions
from core.controls.time_control import SetpointTimeControl
from core.heating_systems.boiler import Boiler, BoilerServiceWaterCombi,\
        BoilerServiceWaterRegular, BoilerServiceSpace, ServiceType
from core.water_heat_demand.cold_water_source import ColdWaterSource
from core.energy_supply.energy_supply import EnergySupply
from core.material_properties import WATER, MaterialProperties

class TestBoiler(unittest.TestCase):
    """ Unit tests for Combi Boiler class """

    def setUp(self):
        """ Create Boiler object to be tested """
        boiler_dict = {"type": "Boiler",
                       "rated_power": 24.0,
                       "EnergySupply": "mains_gas",
                       "efficiency_full_load": 0.88,
                       "efficiency_part_load": 0.986,
                       "boiler_location": "internal",
                       "modulation_load" : 0.2,
                       "electricity_circ_pump": 0.0600,
                       "electricity_part_load" : 0.0131,
                       "electricity_full_load" : 0.0388,
                       "electricity_standby" : 0.0244
                      }
        self.simtime = SimulationTime(0, 2, 1)
        self.energysupply = EnergySupply("mains_gas", self.simtime)
        self.energy_output_required = [2.0, 10.0]
        self.temp_return_feed = [51.05, 60.00]

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
        extcond = ExternalConditions(
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

        self.boiler = Boiler(
            boiler_dict,
            self.energysupply,
            energy_supply_conn_name_auxiliary,
            self.simtime,
            extcond
            )
        self.boiler._Boiler__create_service_connection("boiler_test")

    def test_energy_output_provided(self):
        """ Test that Boiler object returns correct energy and fuel demand """
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                self.assertAlmostEqual(
                    self.boiler._Boiler__demand_energy(
                        "boiler_test",
                        ServiceType.WATER_COMBI,
                        self.energy_output_required[t_idx],
                        self.temp_return_feed[t_idx]
                        ),
                    [2.0, 10.0][t_idx],
                    msg="incorrect energy_output_provided"
                    )
                self.assertAlmostEqual(
                    self.energysupply.results_by_end_user()["boiler_test"][t_idx],
                    [2.2843673926764496, 11.5067107][t_idx],
                    msg="incorrect fuel demand"
                    )

    def test_effvsreturntemp(self):
        """ Test that Boiler object returns correct theoretical efficiencies """
        self.return_temp = [30, 60]
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                self.assertEqual(
                    self.boiler.effvsreturntemp(self.return_temp[t_idx], 0),
                    [0.967, 0.8769][t_idx],
                    "incorrect theoretical boiler efficiency returned",
                    )

    def test_high_value_correction(self):
        """ Test that Boiler object corrects for high boiler efficiencies """
        self.assertEqual(
            self.boiler.high_value_correction_full_load(0.980),
            0.963175,
            "incorrect high_value_correction",
            )
        self.assertEqual(
            self.boiler.high_value_correction_part_load(1.081),
            1.056505,
            "incorrect high_value_correction",
            )

    def test_net2gross(self):
        """ Test that Boiler object selects correct net2gross conversion factor """
        self.__fuel_code = "mains_gas"
        self.assertEqual(
            self.boiler.net_to_gross(),
            0.901,
            "incorrect net_to_gross",
            )

class TestBoilerServiceWaterCombi(unittest.TestCase):
    """ Unit tests for Boiler class """

    def setUp(self):
        """ Create Boiler object to be tested """
        boiler_dict = {
            "type": "Boiler",
            "rated_power": 16.85,
            "EnergySupply": "mains_gas",
            "efficiency_full_load": 0.868,
            "efficiency_part_load": 0.952,
            "boiler_location": "internal",
            "modulation_load" : 1,
            "electricity_circ_pump": 0.0600,
            "electricity_part_load" : 0.0131,
            "electricity_full_load" : 0.0388,
            "electricity_standby" : 0.0244
            }
        
        boilerservicewatercombi_dict = {
            "separate_DHW_tests": "M&L",
            "fuel_energy_1": 7.099,
            "rejected_energy_1": 0.0004,
            "storage_loss_factor_1": 0.98328,
            "fuel_energy_2": 13.078,
            "rejected_energy_2": 0.0004,
            "storage_loss_factor_2": 0.91574,
            "rejected_factor_3": 0,
            "daily_HW_usage" : 132.5802
            }
        self.simtime = SimulationTime(0, 2, 1)
        self.energysupply = EnergySupply("mains_gas", self.simtime)
        self.volume_demanded = [{'41.0': {'warm_temp': 41.0, 'warm_vol': 48.0},
                                 '43.0': {'warm_temp': 43.0, 'warm_vol': 100.0}, 
                                 '40.0': {'warm_temp': 40.0, 'warm_vol': 0.0}, 
                                 'temp_hot_water': {'warm_temp': 55.0, 'warm_vol': 110.59194954841298}},
                                {'41.0': {'warm_temp': 41.0, 'warm_vol': 48.0},
                                 'temp_hot_water': {'warm_temp': 55.0, 'warm_vol': 32.60190808710678}}]
                                 
        self.temp_return_feed = [51.05, 60.00]

        self.windspeed = [3.7, 3.8, 3.9, 4.0, 4.1, 4.2, 4.3, 4.4]
        self.wind_direction = [200, 220, 230, 240, 250, 260, 260, 270]
        self.airtemp = [0.0, 2.5, 5.0, 7.5, 10.0, 12.5, 15.0, 20.0]
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
        extcond = ExternalConditions(
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

        self.boiler = Boiler(
            boiler_dict,
            self.energysupply,
            energy_supply_conn_name_auxiliary,
            self.simtime,
            extcond
            )
        self.boiler._Boiler__create_service_connection("boiler_test")

        coldwatertemps = [1.0, 1.2]
        coldfeed = ColdWaterSource(coldwatertemps, self.simtime, 0, 1)
        return_temp = 60
        self.boiler_service_water = BoilerServiceWaterCombi(
            self.boiler,
            boilerservicewatercombi_dict,
            "boiler_test", 
            return_temp,
            coldfeed,
            self.simtime)

    def test_boiler_service_water(self):
        """ Test that Boiler object returns correct hot water energy demand """
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                self.assertAlmostEqual(
                    self.boiler_service_water.demand_hot_water(self.volume_demanded[t_idx]),
                    [7.624602058956146, 2.267017951167212][t_idx],
                    msg="incorrect energy_output_provided"
                    )

class TestBoilerServiceWaterRegular(unittest.TestCase):
    """ Unit tests for Regular Boiler class """

    def setUp(self):
        """ Create Regular Boiler object to be tested """
        boiler_dict = {
            "type": "Boiler",
            "EnergySupply": "mains gas",
            "rated_power": 24.0,
            "temperature_return_": 60,
            "efficiency_full_load": 0.891,
            "efficiency_part_load": 0.991,
            "boiler_location": "internal",
            "modulation_load": 0.3,
            "electricity_circ_pump": 0.0600,
            "electricity_part_load" : 0.0131,
            "electricity_full_load" : 0.0388,
            "electricity_standby" : 0.0244
            }
        
        boilerservicewaterregular_dict = {
            "temp_return": 60
            }
        
        self.simtime = SimulationTime(0, 2, 1)
        self.energysupply = EnergySupply("mains_gas", self.simtime)
        self.volume_demanded = [10, 2]
        self.temp_return_feed = [51.05, 60.00]

        self.windspeed = [3.7, 3.8, 3.9, 4.0, 4.1, 4.2, 4.3, 4.4]
        self.wind_direction = [200, 220, 230, 240, 250, 260, 260, 270]
        self.airtemp = [0.0, 2.5, 5.0, 7.5, 10.0, 12.5, 15.0, 20.0]
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
        extcond = ExternalConditions(
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
        
        controlmin = SetpointTimeControl([52, 52], self.simtime, 0, 1)
        controlmax = SetpointTimeControl([60, 60], self.simtime, 0, 1)

        self.boiler = Boiler(
            boiler_dict,
            self.energysupply,
            energy_supply_conn_name_auxiliary,
            self.simtime,
            extcond
            )
        self.boiler._Boiler__create_service_connection("boiler_test")
        coldwatertemps = [1.0, 1.2]
        coldfeed = ColdWaterSource(coldwatertemps, self.simtime, 0, 1)
        return_temp = 60
        self.boiler_service_water = BoilerServiceWaterRegular(
            self.boiler,
            "boiler_test",
            coldfeed,
            self.simtime,
            controlmin,
            controlmax
            )

    def test_boiler_service_water(self):
        """ Test that Regular Boiler object returns correct hot water energy demand """
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                self.assertAlmostEqual(
                    self.boiler._Boiler__demand_energy(
                        "boiler_test",
                        ServiceType.WATER_REGULAR,
                        [0.7241412, 0.1748878][t_idx],
                        self.temp_return_feed[t_idx]
                        ),
                    [0.7241412, 0.1748878][t_idx],
                    msg="incorrect energy_output_provided"
                    )

    def test_temp_setpnt(self):
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                self.assertAlmostEqual(
                    self.boiler_service_water.temp_setpnt(),
                    (52, 60)
                    )
                                       
    
class TestBoilerServiceSpace(unittest.TestCase):
    """ Unit tests for Boiler class """

    def setUp(self):
        """ Create Boiler object to be tested """
        boiler_dict = {"type": "Boiler",
                       "rated_power": 16.85,
                       "EnergySupply": "mains_gas",
                       "efficiency_full_load": 0.868,
                       "efficiency_part_load": 0.952,
                       "boiler_location": "internal",
                       "modulation_load" : 1,
                       "electricity_circ_pump": 0.0600,
                       "electricity_part_load" : 0.0131,
                       "electricity_full_load" : 0.0388,
                       "electricity_standby" : 0.0244,
                      }
        self.simtime = SimulationTime(0, 3, 1)
        self.energysupply = EnergySupply("mains_gas", self.simtime)
        self.energy_demanded = [10.0, 2.0, 2.0]
        self.temp_flow = [55.0, 65.0, 65.0]
        self.temp_return_feed = [50.0, 60.0, 60.0]
        self.airtemp = [0.0, 2.5, 5.0, 7.5, 10.0, 12.5, 15.0, 20.0]
        energy_supply_conn_name_auxiliary = 'Boiler_auxiliary'
        self.windspeed = [3.7, 3.8, 3.9, 4.0, 4.1, 4.2, 4.3, 4.4]
        self.wind_direction = [200, 220, 230, 240, 250, 260, 260, 270]
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
        extcond = ExternalConditions(
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
        self.boiler = Boiler(
            boiler_dict,
            self.energysupply,
            energy_supply_conn_name_auxiliary,
            self.simtime,
            extcond
            )
        self.boiler._Boiler__create_service_connection("boiler_test")
        ctrl = SetpointTimeControl(
            [21.0, 21.0, None],
            self.simtime,
            0, # start_day
            1.0, # time_series_step
            )
        self.boiler_service_space = BoilerServiceSpace(self.boiler, "boiler_test", ctrl)

    def test_boiler_service_space(self):
        """ Test that Boiler object returns correct space heating energy demand """
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                self.assertAlmostEqual(
                    self.boiler_service_space.demand_energy(
                        self.energy_demanded[t_idx],
                        self.temp_flow[t_idx],
                        self.temp_return_feed[t_idx]
                    ),
                    [10.0, 2.0, 0.0][t_idx],
                    msg="incorrect energy_output_provided"
                    )
                
                
class TestBoiler(unittest.TestCase):
    """ Unit tests for Combi Boiler class """

    def setUp(self):
        """ Create Boiler object to be tested """
        self.boiler_dict = {"type": "Boiler",
                       "rated_power": 24.0,
                       "EnergySupply": "mains_gas",
                       "efficiency_full_load": 0.88,
                       "efficiency_part_load": 0.986,
                       "boiler_location": "internal",
                       "modulation_load" : 0.2,
                       "electricity_circ_pump": 0.0600,
                       "electricity_part_load" : 0.0131,
                       "electricity_full_load" : 0.0388,
                       "electricity_standby" : 0.0244
                      }
        self.simtime = SimulationTime(0, 2, 1)
        self.energysupply = EnergySupply("mains_gas", self.simtime)
        self.energy_supply_conn_auxiliary = MagicMock()
        self.energy_output_required = [2.0, 10.0]
        self.temp_return_feed = [51.05, 60.00]
        self.windspeed = [3.7, 3.8, 3.9, 4.0, 4.1, 4.2, 4.3, 4.4]
        self.wind_direction = [200, 220, 230, 240, 250, 260, 260, 270]
        self.airtemp = [0.0, 2.5, 5.0, 7.5, 10.0, 12.5, 15.0, 20.0]
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

        self.boiler = Boiler(
            self.boiler_dict,
            self.energysupply,
            self.energy_supply_conn_auxiliary,
            self.simtime,
            self.extcond
            )
    def test_create_service_connection(self):
        ''' Test creation of EnergySupplyConnection for the service name given''' 
        self.service_name = 'new_service'
        # Ensure the service name does not exist in __energy_supply_connections
        self.assertNotIn(self.service_name, 
                         self.boiler._Boiler__energy_supply_connections)
        # Call the method under test
        self.boiler._Boiler__create_service_connection(self.service_name)
        # Check that the service name was added to __energy_supply_connections
        self.assertIn(self.service_name,
                      self.boiler._Boiler__energy_supply_connections)
        # Check system exit when connection is created with existing service name
        with self.assertRaises(SystemExit):
            self.boiler._Boiler__create_service_connection(self.service_name)
            
    def test_create_service_hot_water_combi(self):
        ''' Check BoilerServiceWaterCombi object is created correctly'''
        
        self.service_name = 'service_hot_water_combi'
        self.coldfeed = ColdWaterSource([1.0, 1.2], self.simtime, 0, 1)
        self.temp_hot_water = 50
        self.boiler_data = {'type': 'CombiBoiler',
                             'ColdWaterSource': 'mains water', 
                             'HeatSourceWet': 'hp', 
                             'Control': 'hw timer', 
                             'separate_DHW_tests': 'M&L', 
                             'rejected_energy_1': 0.0004, 
                             'fuel_energy_2': 13.078, 
                             'rejected_energy_2': 0.0004, 
                             'storage_loss_factor_2': 0.91574, 
                             'rejected_factor_3': 0, 
                             'daily_HW_usage': 120, 
                             'setpoint_temp': 60.0}


        boiler_service_WaterCombi_obj = self.boiler.create_service_hot_water_combi( 
                                                       self.boiler_data,
                                                       self.service_name,
                                                       self.temp_hot_water,
                                                       self.coldfeed)
        
        self.assertTrue(isinstance(boiler_service_WaterCombi_obj,
                                   BoilerServiceWaterCombi))
            
    def test_create_service_hot_water_regular(self):
        ''' Check the function returns BoilerServiceWaterRegular object'''

        self.service_name = 'service_hot_water_regular'
        self.coldfeed = ColdWaterSource([1.0, 1.2], self.simtime, 0, 1)
        self.temp_hot_water = 50
        self.controlmin = SetpointTimeControl(
                               [None, None],
                               self.simtime,
                               0,
                               1
                               )
        self.controlmax = SetpointTimeControl(
                               [None, None],
                               self.simtime,
                               0,
                               1
                               )
        boiler_hotwater_regular = self.boiler.create_service_hot_water_regular(self.service_name,
                                                self.coldfeed,
                                                self.controlmin,
                                                self.controlmax,
                                                )
        
        self.assertTrue(isinstance(boiler_hotwater_regular, 
                                   BoilerServiceWaterRegular))
        
    
    def test_create_service_space_heating(self):
        ''' Check the function returns BoilerServiceSpace object'''
        
        boiler_create_service_space_heating = self.boiler.create_service_space_heating(
                                                            service_name = 'BoilerServiceSpace',
                                                            control = MagicMock()
                                                            )
        self.assertTrue(isinstance(boiler_create_service_space_heating, 
                                   BoilerServiceSpace))
        
    def test_cycling_adjustment(self):
        
        self.assertAlmostEqual(self.boiler._Boiler__cycling_adjustment(temp_return_feed = 40.0,
                                                 standing_loss = 0.05,
                                                 prop_of_timestep_at_min_rate = 0.5,
                                                 temp_boiler_loc = 20),
                                0.030120066786994828) 
        
    def test_location_adjustment(self):
        #Internal boiler settings
        self.assertAlmostEqual(self.boiler.location_adjustment(
                                                temp_return_feed = 30,
                                                standing_loss = 5,
                                                temp_boiler_loc = 20),
                              76.72260667117162)
        #External boiler settings
        self.boiler_dict_external = {"type": "Boiler",
                       "rated_power": 24.0,
                       "EnergySupply": "mains_gas",
                       "efficiency_full_load": 0.88,
                       "efficiency_part_load": 0.986,
                       "boiler_location": "external",
                       "modulation_load" : 0.2,
                       "electricity_circ_pump": 0.0600,
                       "electricity_part_load" : 0.0131,
                       "electricity_full_load" : 0.0388,
                       "electricity_standby" : 0.0244
                      }
        self.boiler_external = Boiler(
            self.boiler_dict_external,
            self.energysupply,
            self.energy_supply_conn_auxiliary,
            self.simtime,
            self.extcond
            )
        
        self.assertAlmostEqual(self.boiler_external.location_adjustment(
                                                temp_return_feed = 30,
                                                standing_loss = 5,
                                                temp_boiler_loc = 2.5),
                              31.530735570835994)
        
    def test_calc_current_boiler_power(self):

        self.assertAlmostEqual(self.boiler._Boiler__calc_current_boiler_power(energy_output_provided = 10 ,
                                                                               time_available = 0),
                                0.0)
        
        self.assertAlmostEqual(self.boiler._Boiler__calc_current_boiler_power(energy_output_provided = 10 ,
                                                                               time_available = 3),
                                4.800000000000001)
        
    def test_calc_boiler_eff(self):
        # Check with loaction 'internal'
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                self.assertAlmostEqual(self.boiler.calc_boiler_eff(service_type = ServiceType.SPACE, 
                                                           temp_return_feed = 37,
                                                           energy_output_required = 3,
                                                           time_elapsed_hp = 0),
                              [0.8619648380446757, 0.8619648380446757 ][t_idx])

        
        #Check with location 'external'
        boiler_dict_external = {"type": "Boiler",
                       "rated_power": 24.0,
                       "EnergySupply": "mains_gas",
                       "efficiency_full_load": 0.88,
                       "efficiency_part_load": 0.986,
                       "boiler_location": "external",
                       "modulation_load" : 0.2,
                       "electricity_circ_pump": 0.0600,
                       "electricity_part_load" : 0.0131,
                       "electricity_full_load" : 0.0388,
                       "electricity_standby" : 0.0244
                      }
        
        energy_supply_conn_name_auxiliary = 'Boiler_external'
        self.boiler_external = Boiler(
                        boiler_dict_external,
                        self.energysupply,
                        energy_supply_conn_name_auxiliary,
                        self.simtime,
                        self.extcond
                        )
        self.simtime.reset()   
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):        
                self.assertAlmostEqual(self.boiler_external.calc_boiler_eff(service_type = ServiceType.SPACE, 
                                                           temp_return_feed = 37,
                                                           energy_output_required = 3,
                                                           time_elapsed_hp = 0),
                              [0.8545088068138385,0.8555283757048464][t_idx])
                
    def test_calc_energy_output_provided(self):
        
        self.assertAlmostEqual(self.boiler._Boiler__calc_energy_output_provided(
                                            energy_output_required = 5.0,
                                            time_available = 1),
                                        5.0)
        
        self.assertAlmostEqual(self.boiler._Boiler__calc_energy_output_provided(
                                            energy_output_required = 25.0,
                                            time_available = 1),
                                        24.0)
        
    def test_time_available(self):
        
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                self.assertAlmostEqual(self.boiler._Boiler__time_available(0.0),
                                       [1.0, 1.0][t_idx])
                
        self.simtime.reset()
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                self.assertAlmostEqual(self.boiler._Boiler__time_available(0.2, time_elapsed_hp = 0.5),
                                       [0.4, 0.4][t_idx])
                
    def test_demand_energy(self):
        #Test with different values of  service types and hybrid_service_bool 
        self.boiler._Boiler__create_service_connection('boiler_demand_energy')

        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx): 
                self.assertAlmostEqual(self.boiler._Boiler__demand_energy(
                                                    service_name = 'boiler_demand_energy',
                                                    service_type = ServiceType.WATER_COMBI,
                                                    energy_output_required = 10,
                                                    temp_return_feed = 37,
                                                    hybrid_service_bool = False,
                                                    time_elapsed_hp = None),
                                        [10,0.0][t_idx])
                
        self.boiler._Boiler__create_service_connection('boiler_demand_energy_with_hybrid')
        
        self.simtime.reset()
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):  
                self.assertEqual(self.boiler._Boiler__demand_energy(
                                                    service_name = 'boiler_demand_energy_with_hybrid',
                                                    service_type = ServiceType.SPACE,
                                                    energy_output_required = 100,
                                                    temp_return_feed = 37,
                                                    hybrid_service_bool = True,
                                                    time_elapsed_hp = 0),
                                        [(24.0,1.0),(24.0,1.0)][t_idx])
         
        #Test with time_elapsed_hp        
        self.boiler._Boiler__create_service_connection('boiler_demand_energy_hybrid_time_elapsed')
        
        self.simtime.reset()
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):  
                self.assertEqual(self.boiler._Boiler__demand_energy(
                                                    service_name = 'boiler_demand_energy_hybrid_time_elapsed',
                                                    service_type = ServiceType.SPACE,
                                                    energy_output_required = 100,
                                                    temp_return_feed = 37,
                                                    hybrid_service_bool = True,
                                                    time_elapsed_hp = 0.5),
                                        [ (12.0, 0.5), (12.0, 0.5)][t_idx])
                
        required_services = {'boiler_demand_energy', 'boiler_demand_energy_with_hybrid',
                             'boiler_demand_energy_hybrid_time_elapsed'}
        service_names_in_list = {entry['service_name'] for entry in self.boiler._Boiler__service_results}   
        self.assertTrue(required_services.issubset(service_names_in_list))
        
        # Test with Mock to check demand_energy() of energy supply was called with 0.0
        
        self.boiler._Boiler__energy_supply_connections = {
            'mock': MagicMock()
        }
        self.boiler._Boiler__time_available = MagicMock()
        self.boiler._Boiler__time_available.return_value = 0.0
        self.boiler._Boiler__demand_energy(
                                            service_name = 'mock',
                                            service_type = ServiceType.SPACE,
                                            energy_output_required = 0,
                                            temp_return_feed = 37,
                                            hybrid_service_bool = False,
                                            time_elapsed_hp = 1
                                            )
        
        self.boiler._Boiler__energy_supply_connections['mock'].demand_energy.assert_called_with(0.0)
        
        # Test with Mock to check demand_energy() of energy supply was called with given value 

        self.boiler.calc_boiler_eff = MagicMock()
        self.boiler._Boiler__calc_energy_output_provided = MagicMock()
        self.boiler._Boiler__calc_current_boiler_power = MagicMock()
        
        self.boiler._Boiler__time_available.return_value = 1.0
        self.boiler.calc_boiler_eff.return_value = 0.9
        self.boiler._Boiler__calc_energy_output_provided.return_value = 100.0
        self.boiler._Boiler__calc_current_boiler_power.return_value = 50.0
        
        self.boiler._Boiler__demand_energy(
                                            service_name = 'mock',
                                            service_type = ServiceType.SPACE,
                                            energy_output_required = 100.0,
                                            temp_return_feed = 37,
                                            hybrid_service_bool = False,
                                            time_elapsed_hp = None
                                            )
        self.boiler._Boiler__energy_supply_connections['mock'].demand_energy.assert_called_with(100.0 / 0.9)
                     
        
    def test_calc_auxiliary_energy(self):
        '''Check boiler electrical consumption'''
        self.energysupply_aux = EnergySupply("electricity", self.simtime)
        self.energy_supply_conn_auxiliary = self.energysupply_aux.connection('boiler_auxillary')        
        
        self.boiler = Boiler(
            self.boiler_dict,
            self.energysupply,
            self.energy_supply_conn_auxiliary,
            self.simtime,
            self.extcond
            )
        #Check the function runs without throwing errors    
        self.assertEqual(self.boiler._Boiler__calc_auxiliary_energy(1,0),None)
        
        #Check the demand_energy() has been called once
        self.energy_supply_connection_aux = MagicMock()
        self.boiler = Boiler(
            self.boiler_dict,
            self.energysupply,
            self.energy_supply_connection_aux,
            self.simtime,
            self.extcond
            )
        self.boiler._Boiler__calc_auxiliary_energy(1, 0.5)
        self.boiler._Boiler__energy_supply_connection_aux.demand_energy.assert_called_once()
    
    
    def test_timestep_end(self):
        
        self.boiler._Boiler__create_service_connection('boiler_demand_energy')
        
        self.boiler._Boiler__demand_energy( service_name = 'boiler_demand_energy',
                                            service_type = ServiceType.WATER_COMBI,
                                            energy_output_required = 10,
                                            temp_return_feed = 60,
                                            hybrid_service_bool = False,
                                            time_elapsed_hp = None,
                                        )

        self.assertAlmostEqual(self.boiler._Boiler__total_time_running_current_timestep,
                                1.0)
        self.assertEqual(self.boiler._Boiler__service_results[0]['service_name'],'boiler_demand_energy') 
    
         # Call the method under test
        self.boiler.timestep_end()
        # Assertions to check if the internal state was updated correctly
        self.assertAlmostEqual(self.boiler._Boiler__total_time_running_current_timestep,
                                0.0)
        self.assertEqual(self.boiler._Boiler__service_results,[]) 
    
    def test_energy_output_max(self):
        
        self.assertAlmostEqual(self.boiler._Boiler__energy_output_max( temp_output = 30, time_elapsed_hp = 0),
                               24.0)
        
        self.assertAlmostEqual(self.boiler._Boiler__energy_output_max( temp_output = 30, time_elapsed_hp = 0.5),
                               12.0)
        
    def test_effvsreturntemp(self):
        '''Check boiler efficiency returned at different return temperatures '''
        # test_mains_gas_efficiency_below_dewpoint
        efficiency = self.boiler.effvsreturntemp(50,0.5)
        expected_efficiency = (-0.00007 * 50**2 + 0.0017 * 50 + 0.979) - 0.5
        self.assertAlmostEqual(efficiency, expected_efficiency)

        # test_mains_gas_efficiency_above_dewpoint
        efficiency = self.boiler.effvsreturntemp(60,0.5)
        expected_efficiency = (-0.0006 * 60 + 0.9129) -0.5
        self.assertAlmostEqual(efficiency, expected_efficiency)

        # test_lpg_efficiency_below_dewpoint
        self.energysupply = EnergySupply("LPG_bulk", self.simtime)
        self.energy_supply_connection_aux = MagicMock()
        self.boiler_lpg = Boiler(
            self.boiler_dict,
            self.energysupply,
            self.energy_supply_connection_aux,
            self.simtime,
            self.extcond
            )
     
        efficiency = self.boiler_lpg.effvsreturntemp(45,0.5)
        expected_efficiency = (-0.00006 * 45**2 + 0.0013 * 45 + 0.9859) - 0.5
        self.assertAlmostEqual(efficiency, expected_efficiency)

        # test_lpg_efficiency_above_dewpoint
        efficiency = self.boiler_lpg.effvsreturntemp(50,0.5)
        expected_efficiency = (-0.0006 * 50 + 0.933)-0.5
        self.assertAlmostEqual(efficiency, expected_efficiency)

        # Invalid fuel code
        with self.assertRaises(SystemExit):
            self.energysupply = EnergySupply("Invalid_code", self.simtime)
            self.boiler = Boiler(
            self.boiler_dict,
            self.energysupply,
            self.energy_supply_connection_aux,
            self.simtime,
            self.extcond
            )
            self.boiler.effvsreturntemp(50,0.5)

        # test_efficiency_without_offset
        self.energysupply = EnergySupply("mains_gas", self.simtime)
        self.boiler = Boiler(
            self.boiler_dict,
            self.energysupply,
            self.energy_supply_connection_aux,
            self.simtime,
            self.extcond
            )
        self.assertAlmostEqual(self.boiler.effvsreturntemp(50,0),0.889)
        
        
    def test_high_value_correction_part_load(self):
        """ Check  a Boiler efficiency corrected for high values """
        # Fuel Code Main_gas
        self.assertAlmostEqual(self.boiler.high_value_correction_part_load(5),1.08)
        self.assertAlmostEqual(self.boiler.high_value_correction_part_load(1),0.992758)
        
        # Fuel Code LPG_Bulk
        self.energysupply = EnergySupply("LPG_bulk", self.simtime)
        self.energy_supply_connection_aux = MagicMock()
        self.boiler_lpg = Boiler(
            self.boiler_dict,
            self.energysupply,
            self.energy_supply_connection_aux,
            self.simtime,
            self.extcond
            )
        self.assertAlmostEqual(self.boiler_lpg.high_value_correction_part_load(5),1.06)
        self.assertAlmostEqual(self.boiler_lpg.high_value_correction_part_load(1),0.992758)
        
        # Invalid fuel code
        with self.assertRaises(SystemExit):
            self.energysupply = EnergySupply("Invalid_code", self.simtime)
            self.boiler_invalid = Boiler(
            self.boiler_dict,
            self.energysupply,
            self.energy_supply_connection_aux,
            self.simtime,
            self.extcond
            )
            self.boiler_invalid.high_value_correction_part_load(0.5)    
    
    def test_high_value_correction_full_load(self):
        
        self.assertAlmostEqual(self.boiler.high_value_correction_full_load(net_efficiency_full_load = 1.0),
                               0.969715)

    def test_net_to_gross(self):
        '''Check the net to gross factor '''
        #Fuel code main_gas
        self.assertAlmostEqual(self.boiler.net_to_gross(),0.901)
                
        #Fuel Code LPG_Bulk        
        self.energysupply = EnergySupply("LPG_bulk", self.simtime)
        self.energy_supply_connection_aux = MagicMock()
        self.boiler_lpg = Boiler(
            self.boiler_dict,
            self.energysupply,
            self.energy_supply_connection_aux,
            self.simtime,
            self.extcond
            )
        self.assertAlmostEqual(self.boiler_lpg.net_to_gross(),0.921)
        
        # Invalid fuel code
        with self.assertRaises(SystemExit):
            self.energysupply = EnergySupply("Invalid_code", self.simtime)
            self.boiler_invalid = Boiler(
                self.boiler_dict,
                self.energysupply,
                self.energy_supply_connection_aux,
                self.simtime,
                self.extcond
                )
            self.boiler_invalid.net_to_gross()
