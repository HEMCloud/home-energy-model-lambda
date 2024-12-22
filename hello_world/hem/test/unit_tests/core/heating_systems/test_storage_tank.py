#!/usr/bin/env python3

"""
This module contains unit tests for the Storage Tank module
"""

# Standard library imports
import unittest

# Set path to include modules to be tested (must be before local imports)
from unit_tests.common import test_setup
from unittest.mock import MagicMock
test_setup()

# Local imports
from core.simulation_time import SimulationTime
from core.material_properties import WATER, MaterialProperties
from core.heating_systems.storage_tank import StorageTank, \
            ImmersionHeater,PVDiverter,SolarThermalSystem            
from core.water_heat_demand.cold_water_source import ColdWaterSource
from core.energy_supply.energy_supply import EnergySupply, EnergySupplyConnection
from core.controls.time_control import SetpointTimeControl
from core.external_conditions import ExternalConditions
from core.pipework import Pipework,Location
from core import project

class DummyProject:
  def __init__(self, temp_internal_air):
    self.__temp_internal_air = temp_internal_air
  def temp_internal_air_prev_timestep(self):
      return self.__temp_internal_air

class Test_StorageTank(unittest.TestCase):
    """ Unit tests for StorageTank class """

    def setUp(self):
        """ Create StorageTank object to be tested """
        self.coldwatertemps = [10.0, 10.1, 10.2, 10.5, 10.6, 11.0, 11.5, 12.1]
        self.simtime     = SimulationTime(0, 8, 1)
        self.coldfeed     = ColdWaterSource(self.coldwatertemps, self.simtime, 0, 1)
        self.controlmin = SetpointTimeControl(
                               [52.0, None, None, None, 52.0, 52.0, 52.0, 52.0],
                               self.simtime,
                               0,
                               1
                               )
        self.controlmax = SetpointTimeControl(
                               [55.0, 55.0, 55.0, 55.0, 55.0, 55.0, 55.0, 55.0],
                               self.simtime,
                               0,
                               1
                               )
        self.controlmax2 = SetpointTimeControl(
                               [60.0, 60.0, 60.0, 60.0, 60.0, 60.0, 60.0, 60.0],
                               self.simtime,
                               0,
                               1
                               )
        self.energysupply = EnergySupply("electricity", self.simtime)
        self.energysupplyconn = self.energysupply.connection("immersion")
        self.imheater         = ImmersionHeater(50.0, self.energysupplyconn, self.simtime, self.controlmin, self.controlmax)
        self.heat_source_dict = {self.imheater: (0.1, 0.33)}
        self.windspeed = [3.7, 3.8, 3.9, 4.0, 4.1, 4.2, 4.3, 4.4]
        self.wind_direction = [0.0] * 8
        self.energy_supply_conn_name_auxiliary = 'Boiler_auxiliary'
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
        self.storagetank = StorageTank(150.0, 1.68, 55.0, self.coldfeed, self.simtime, self.heat_source_dict, DummyProject(20), self.extcond)

        # Also test case where heater does not heat all layers, to ensure this is handled correctly
        self.energysupplyconn2 = self.energysupply.connection("immersion2")
        self.imheater2         = ImmersionHeater(5.0, self.energysupplyconn2, self.simtime, self.controlmin, self.controlmax2)
        self.heat_source_dict2 = {self.imheater2: (0.6, 0.6)}
        self.storagetank2 = StorageTank(210.0, 1.61, 60.0, self.coldfeed, self.simtime, self.heat_source_dict2, DummyProject(20), self.extcond)

        # Also test case where the cold feed is a pre-heated source
        energysupplyconn3 = self.energysupply.connection("immersion3")
        imheater3         = ImmersionHeater(5.0, energysupplyconn3, self.simtime, self.controlmin, self.controlmax)
        heat_source_dict3 = {imheater3: (0.6, 0.6)}
        preheatfeed       = StorageTank(80, 1.61, 30, self.coldfeed, self.simtime, None, DummyProject(20), self.extcond)
        self.storagetank3 = StorageTank(210.0, 1.61, 52.0, preheatfeed, self.simtime, heat_source_dict3, DummyProject(20), self.extcond)

    def test_demand_hot_water(self):

        test_data_pairs = [
            ({41.0: [41.0, 48.0], 43.0: [43.0, 100], 40.0: [40.0, 8.0], 'temp_hot_water': [55.0, 110.59194954841298]},
             [{'start': 6, 'duration': 6, 'temperature': 41.0, 'type': 'Shower', 'name': 'IES'},
              {'start': 6, 'duration': 6, 'temperature': 41.0, 'type': 'Shower', 'name': 'mixer', 'warm_volume': 48.0},
              {'start': 6.0, 'duration': 20, 'temperature': 43.0, 'type': 'Bath', 'name': 'medium', 'warm_volume': 100},
              {'start': 6, 'duration': 1, 'temperature': 40.0, 'type': 'Other', 'name': 'other', 'warm_volume': 8.0}]),

            ({41.0: [41.0, 48.0], 'temp_hot_water': [55.0, 32.60190808710678]},
             [{'start': 7, 'duration': 6, 'temperature': 41.0, 'type': 'Shower', 'name': 'mixer', 'warm_volume': 48.0}]),

            ({}, None),

            ({45.0: [45.0, 48.0], 'temp_hot_water': [55.0, 37.953086226276454]},
             [{'start': 9, 'duration': 6, 'temperature': 45.0, 'type': 'Shower', 'name': 'mixer', 'warm_volume': 48.0}]),

            ({}, None),

            ({41.0: [41.0, 52.0], 'temp_hot_water': [55.0, 35.30764905040529]},
             [{'start': 11, 'duration': 6.5, 'temperature': 41.0, 'type': 'Shower', 'name': 'mixer', 'warm_volume': 52.0}]),

            ({}, None),

            ({}, None)
        ]

        # Expected results for the unit test
        expected_temperatures_1 = [
            [55.0, 55.0, 55.0, 55.0],
            [15.45, 54.595555555555556, 54.595555555555556, 54.595555555555556],
            [15.45, 54.19530534979424, 54.19530534979424, 54.19530534979424],
            [10.5, 15.4, 53.38820740740741, 53.80385185185185],
            [55.0, 55.0, 55.0, 55.0],
            [13.4, 54.595555555555556, 54.595555555555556, 54.595555555555556],
            [13.4, 54.19530534979424, 54.19530534979424, 54.19530534979424],
            [13.4, 53.79920588690749, 53.79920588690749, 53.79920588690749],
        ]

        expected_temperatures_2 = [
            [10.0, 24.55880864197531, 60.0, 60.0],
            [10.06, 16.317728395061728, 39.76012654320988, 59.687654320987654],
            [10.06, 16.315472915714068, 39.59145897824265, 59.37752591068435],
            [10.34, 12.28, 24.509163580246913, 46.392706790123455],
            [10.34, 12.28, 60.0, 60.0],
            [10.74, 11.1, 60.0, 60.0],
            [10.74, 11.1, 59.687654320987654, 59.687654320987654],
            [10.74, 11.1, 59.37752591068435, 59.37752591068435],
        ]

        expected_temperatures_3 = [
            [22.354567901234567, 38.02254938271605, 53.89904012345679, 59.290493827160496],
            [15.62, 28.927574074074073, 44.5756975308642, 55.90470061728395],
            [15.62, 28.83580425811614, 44.37284535703399, 55.621426507963726],
            [11.72, 19.574444444444445, 33.38570061728395, 47.53454320987654],
            [11.72, 19.549070301783267, 60.0, 60.0],
            [10.83, 14.8, 60.0, 60.0],
            [10.83, 14.8, 59.687654320987654, 59.687654320987654],
            [10.83, 14.8, 59.37752591068435, 59.37752591068435]
        ]
        
        # Loop through the timesteps and the associated data pairs using `subTest`
        for t_idx, _, _ in self.simtime:  # Assuming simtime generates correct time indices
            volume_demanded_target, usage_events = test_data_pairs[t_idx]
            with self.subTest(timestep=t_idx):
                self.storagetank.demand_hot_water(usage_events)
        
                # Verify the temperatures against expected results
                self.assertListEqual(
                    self.storagetank._StorageTank__temp_n,  
                    expected_temperatures_1[t_idx],
                    "incorrect temperatures returned"
                )
                #print(self.energysupply.results_by_end_user()["immersion"][t_idx])
                self.assertAlmostEqual(
                    self.energysupply.results_by_end_user()["immersion"][t_idx],
                    [5.913725648148166,
                     0.0,
                     0.0,
                     0.0,
                     3.858245898765432,
                     0.0,
                     0.0,
                     0.0][t_idx],
                    msg="incorrect energy supplied returned",
                    )

                self.storagetank2.demand_hot_water(usage_events)
        
                # Verify the temperatures against expected results
                self.assertListEqual(
                    self.storagetank2._StorageTank__temp_n,  
                    expected_temperatures_2[t_idx],
                    "incorrect temperatures returned in case where heater does not heat all layers"
                    )
                self.assertAlmostEqual(
                    self.energysupply.results_by_end_user()["immersion2"][t_idx],
                    [0.6720797510288063,
                     0.0,
                     0.0,
                     0.0,
                     3.033920793930041,
                     1.8039389176954712,
                     0.0,
                     0.0,
                    ][t_idx],
                    msg="incorrect energy supplied returned in case where heater does not heat all layers",
                    )
    def test_temp_surrounding_primary_pipework(self):
        # External Pipe
        self.pipework = Pipework(Location.EXTERNAL, 0.025, 0.027, 1.0, 0.035, 0.038, False, 'water')        
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                self.assertEqual(self.storagetank.temp_surrounding_primary_pipework(self.pipework),
                                 [0.0, 2.5, 5.0, 7.5, 10.0, 12.5, 15.0, 20.0][t_idx])
    
        # Internal Pipe
        self.pipework = Pipework(Location.INTERNAL, 0.025, 0.027, 1.0, 0.035, 0.038, False, 'water')        
        self.simtime.reset()
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                self.assertEqual(self.storagetank.temp_surrounding_primary_pipework(self.pipework),
                                 [ 20.0, 20.0, 20.0, 20.0, 20.0, 20.0, 20.0, 20.0][t_idx])
    
        #Invalid pipe location
        with self.assertRaises(AttributeError):
            self.pipework = Pipework(Location.INVALID, 0.025, 0.027, 1.0, 0.035, 0.038, False, 'water')
    
    def test_get_cold_water_source(self):
        self.assertTrue(isinstance(self.storagetank.get_cold_water_source(),ColdWaterSource))
    
    def test_get_temp_hot_water(self):
        self.assertEqual(self.storagetank.get_temp_hot_water(),55.0)
        
    def test_stand_by_losses_coefficient(self):
        self.assertAlmostEqual(self.storagetank.stand_by_losses_coefficient(),1.5555555555555556)
    
    def test_potential_energy_input(self):
        
        # Immersionheater as heat_source 
        temp_s3_n = [55.0, 55.0, 55.0, 55.0, 55.0, 55.0, 55.0, 55.0]
        self.assertEqual(self.storagetank.potential_energy_input(temp_s3_n, self.imheater, 0, 7),[0.0, 0, 0, 0])
        
        #SolarThermal as Heat source
        
        coldwatertemps = [17.0, 17.1, 17.2, 17.3, 17.4, 17.5, 17.6, 17.7, 17.0, 17.1, 17.2, 17.3,
                             17.4, 17.5, 17.6, 17.7, 17.0, 17.1, 17.2, 17.3, 17.4, 17.5, 17.6, 17.7]
        self.simtime     = SimulationTime(5088, 5112, 1)
        coldfeed         = ColdWaterSource(coldwatertemps, self.simtime, 212, 1)
        self.controlmax = SetpointTimeControl(
                                [55.0, 55.0, 55.0, 55.0, 55.0, 55.0, 55.0, 55.0,
                                 55.0, 55.0, 55.0, 55.0, 55.0, 55.0, 55.0, 55.0,
                                 55.0, 55.0, 55.0, 55.0, 55.0, 55.0, 55.0, 55.0
                                ],
                                self.simtime,
                                212,
                                1
                                )
        self.energysupply = EnergySupply("electricity", self.simtime)
        self.energysupplyconnst = self.energysupply.connection("solarthermal")

        #Adding solarthermal to the test
        proj_dict = {
            "ExternalConditions": {
                "air_temperatures": [19.0, 19.0, 19.0, 19.0, 19.0, 19.0, 19.0, 19.0, 19.0, 19.0, 19.0, 19.0, 
                                        19.0, 19.0, 19.0, 19.0, 19.0, 19.0, 19.0, 19.0, 19.0, 19.0, 19.0, 19.0],
                "wind_speeds": [3.9, 3.8, 3.9, 4.1, 3.8, 4.2, 4.3, 4.1, 3.9, 3.8, 3.9, 4.1, 
                                    3.8, 4.2, 4.3, 4.1, 3.9, 3.8, 3.9, 4.1, 3.8, 4.2, 4.3, 4.1],
                "wind_directions": [300, 250, 220, 180, 150, 120, 100, 80, 60, 40, 20, 10,
                                    50, 100, 140, 190, 200, 320, 330, 340, 350, 355, 315, 5],
                "diffuse_horizontal_radiation": [0, 0, 0, 0, 35, 73, 139, 244, 320, 361, 369, 348, 
                                                    318, 249, 225, 198, 121, 68, 19, 0, 0, 0, 0, 0],
                "direct_beam_radiation": [0, 0, 0, 0, 0, 0, 7, 53, 63, 164, 339, 242, 
                                            315, 577, 385, 285, 332, 126, 7, 0, 0, 0, 0, 0],
                "solar_reflectivity_of_ground": [0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 
                                                    0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2],
                "latitude": 51.383,
                "longitude": -0.783,
                "timezone": 0,
                "start_day": 212,
                "end_day": 212,
                "time_series_step": 1,
                "january_first": 1,
                "daylight_savings": "not applicable",
                "leap_day_included": False,
                "direct_beam_conversion_needed": False,
                "shading_segments":[
            {"number": 1, "start": 180, "end": 135},
            {"number": 2, "start": 135, "end": 90},
            {"number": 3, "start": 90, "end": 45},
            {"number": 4, "start": 45, "end": 0, 
                "shading": [
                    {"type": "obstacle", "height": 10.5, "distance": 12}
                ]
            },
            {"number": 5, "start": 0, "end": -45},
            {"number": 6, "start": -45, "end": -90},
            {"number": 7, "start": -90, "end": -135},
            {"number": 8, "start": -135, "end": -180}
        ],
            }
        }
        self.__external_conditions = ExternalConditions(
            self.simtime,
            proj_dict['ExternalConditions']['air_temperatures'],
            proj_dict['ExternalConditions']['wind_speeds'],
            proj_dict['ExternalConditions']['wind_directions'],
            proj_dict['ExternalConditions']['diffuse_horizontal_radiation'],
            proj_dict['ExternalConditions']['direct_beam_radiation'],
            proj_dict['ExternalConditions']['solar_reflectivity_of_ground'],
            proj_dict['ExternalConditions']['latitude'],
            proj_dict['ExternalConditions']['longitude'],
            proj_dict['ExternalConditions']['timezone'],
            proj_dict['ExternalConditions']['start_day'],
            proj_dict['ExternalConditions']['end_day'],
            proj_dict['ExternalConditions']["time_series_step"],
            proj_dict['ExternalConditions']['january_first'],
            proj_dict['ExternalConditions']['daylight_savings'],
            proj_dict['ExternalConditions']['leap_day_included'],
            proj_dict['ExternalConditions']['direct_beam_conversion_needed'],
            proj_dict['ExternalConditions']['shading_segments']
            )
        self.solthermal  = SolarThermalSystem("OUT", 3, 1, 0.8, 0.9, 3.5, 0, 1, 100, 10, 
                                              self.energysupplyconnst, 30, 0, 0.5, 
                                              self.__external_conditions, self.simtime, 
                                              DummyProject(20), self.controlmax,
                                              )
        heat_source_dict = {self.solthermal: (0.1, 0.33)}

        self.storagetank = StorageTank(150.0, 1.68, 55.0, coldfeed, self.simtime, 
                                       heat_source_dict, DummyProject(20), self.__external_conditions)
        
        temp_s3_n = [25.0, 15.0, 35.0, 45.0, 55.0, 50.0, 30.0, 20.0,25.0, 15.0, 35.0, 45.0, 
                     55.0, 50.0, 30.0, 20.0,25.0, 15.0, 35.0, 45.0, 55.0, 50.0, 30.0, 20.0,
                     25.0, 15.0, 35.0, 45.0, 55.0, 50.0, 30.0, 20.0]

        for t_idx, _, _ in self.simtime:
            with self.subTest(timestep=t_idx):
                actual_result = self.storagetank.potential_energy_input(temp_s3_n, self.solthermal, 0, 7)
            
                expected_result = [
                    [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0],
                    [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0],
                    [0.47214338269526945, 0, 0, 0], [0.794165996101526, 0, 0, 0],
                    [1.2488375719961642, 0, 0, 0], [1.0218936489635675, 0, 0, 0],
                    [1.1483985152150102, 0, 0, 0], [1.5175839864027383, 0, 0, 0],
                    [0.9602170463493307, 0, 0, 0], [0.5981490998786696, 0, 0, 0],
                    [0.3454397002046902, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0],
                    [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]
                    ][t_idx]
    
                # Compare each element using assertAlmostEqual
                for expected_value, actual_value in zip(expected_result, actual_result):
                    self.assertAlmostEqual(expected_value, actual_value, places=13)        
        
    
    def test_storage_tank_potential_effect(self):
        energy_proposed = 0
        temp_s3_n = [25.0, 15.0, 35.0, 45.0, 55.0, 50.0, 30.0, 20.0]
        self.assertEqual(self.storagetank.storage_tank_potential_effect(energy_proposed,temp_s3_n),
                         (20.0,45.0))
        
    def test_energy_input(self):
        temp_s3_n = [25.0, 15.0, 35.0, 45.0, 55.0, 50.0, 30.0, 20.0]
        Q_x_in_n =  [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7]
        self.assertEqual(self.storagetank.energy_input(temp_s3_n,Q_x_in_n),
              (5.83, [25.0, 17.294455066921607, 39.588910133843214, 51.883365200764814]))
    
    def test_rearrange_temperatures(self):
        
        temp_s6_n  = [2.5, 3.7, 10.36, 17.43, 32.95, 35.91, 35.91, 42.2]
        self.assertEqual(self.storagetank.rearrange_temperatures(temp_s6_n),
                         ([0.10895833333333334, 0.16125833333333334, 0.45152333333333333, 0.7596575],
                          [2.5, 3.7, 10.36, 17.43, 32.95, 35.91, 35.91, 42.2]))
        
    def test_thermal_losses(self):
        
        temp_s7_n =  [12.0,18.0,25.0,32.0,37.0,45.0,49.0,58.0] 
        Q_x_in_n  =  [0, 1, 2.0, 3, 4, 5, 6, 7, 8] 
        Q_h_sto_s7 = [0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8] 
        heater_layer =  2 
        Q_ls_n_prev_heat_source = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,0.0] 
        setpntmax =  55.0
        self.assertEqual(self.storagetank.thermal_losses(temp_s7_n,Q_x_in_n,Q_h_sto_s7,heater_layer,
                                        Q_ls_n_prev_heat_source,setpntmax),
                        (36.0, 0.012203333333333333, 
                        [12.0, 17.97925925925926, 24.906666666666666, 31.834074074074074], 
                        [0.0, 0.0009039506172839507, 0.004067777777777778, 0.007231604938271605]))
    
    def test_run_heat_sources(self):
        
        temp_s3_n = [5.0, 10.0, 15.0, 20.0, 25.0, 30.0, 35.0, 40.0]
        heat_source = self.imheater
        heater_layer = 2 
        thermostat_layer = 7
        Q_ls_prev_heat_source = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        self.assertEqual(self.storagetank.run_heat_sources(temp_s3_n, 
                                                           heat_source,
                                                           heater_layer, 
                                                           thermostat_layer, 
                                                           Q_ls_prev_heat_source),
                        ([5.0, 10.0, 55.0, 55.0], 
                         [0, 0, 50.0, 0], 
                         52.17916666666666, 
                         [5.0, 10.0, 1162.227533460803, 20.0], 
                         [5.0, 10.0, 591.1137667304015, 591.1137667304015], 
                         3.3040040740740793, 0.03525407407407408, 
                            [0.0, 0.0, 0.01762703703703704, 0.01762703703703704]))
        
    def test_calculate_temperatures(self):
        
        temp_s3_n = [10, 15, 20, 25, 25, 30, 35, 50]
        heat_source = self.imheater
        Q_x_in_n  =  [0, 1, 2.0, 3, 4, 5, 6, 7, 8]
        heater_layer =  2 
        Q_ls_n_prev_heat_source = [0.0, 0.0, 0.0, 0.0,
                                   0.0, 0.0, 0.0, 0.0]
        
        self.assertEqual(self.storagetank._StorageTank__calculate_temperatures(temp_s3_n,
                                                                               heat_source, 
                                                                               Q_x_in_n, 
                                                                               heater_layer, 
                                                                               Q_ls_n_prev_heat_source),
                ([10.0, 37.71697755116492, 55.0, 55.0], 
                 [0, 1, 2.0, 3, 4, 5, 6, 7, 8], 
                 9.050833333333333, 
                 [10.0, 37.944550669216056, 65.88910133843211, 93.83365200764818], 
                 [10.0, 37.944550669216056, 65.88910133843211, 93.83365200764818], 
                 33.86817074074074, 
                 0.04517246913580247, 
                 [0.0, 0.009918395061728393, 0.01762703703703704, 0.01762703703703704])
              )
    
    def test_allocate_hot_water(self):
        

        self.storagetank._StorageTank__temp_average_drawoff_volweighted = 0.0
        self.storagetank._StorageTank__total_volume_drawoff = 0.0
        
        event = {'start': 0, 'duration': 1, 'temperature': 41.0, 'type': 'Other', 
                 'name': 'other', 'warm_volume': 8.0, 'pipework_volume': 5}
        
        self.assertEqual(self.storagetank.allocate_hot_water(event),
                         (10.51111111111112, 
                          [42.39, 55.0, 55.0, 55.0], 
                          0.5497311111111112, 
                          0.0, False))
        # With no pipework vol
        event = {'start': 0, 'duration': 1, 'temperature': 41.0, 'type': 'Other', 
                 'name': 'other', 'warm_volume': 8.0,'pipework_volume': 0}
        
        self.assertEqual(self.storagetank.allocate_hot_water(event),
              (5.51111111111112, 
               [48.39, 55.0, 55.0, 55.0], 
               0.2882311111111111, 
               0.0, False))
    
    def test_calculate_new_temperatures(self):
        
        remaining_vol = [0.5,1,1.5,2,2.5,3,3.5,4]
        self.assertEqual(self.storagetank.calculate_new_temperatures(remaining_vol),
                         ([10.0, 10.0, 10.0, 16.0], False))
        
    def test_additional_energy_input(self):
        
        heat_source = self.imheater
        energy_input = 5.0
        
        self.storagetank._StorageTank__Q_ls_n_prev_heat_source = [0.0,0.1,0.2,0.3]
        self.assertEqual(self.storagetank.additional_energy_input(heat_source, energy_input),
                         0.01762703703703572)
        
        # Test with no energy input
        heat_source = self.imheater2
        energy_input = 0.0
        self.storagetank._StorageTank__Q_ls_n_prev_heat_source = [0.0,0.1,0.2,0.3]
        self.assertEqual(self.storagetank.additional_energy_input(heat_source, energy_input),
                         0.0)
        
    def test_internal_gains(self):
        self.storagetank._StorageTank__Q_sto_h_ls_rbl = 0.05
        self.assertEqual(self.storagetank.internal_gains(),
                                 50.0)
        
        
        
    def test_primary_pipework_losses(self):
        
        input_energy_adj = 0.0
        setpnt_max = 55.0
        nb_vol=4
        primary_pipework_lst =[{'location': 'internal', 'internal_diameter_mm': 24, 
                                'external_diameter_mm': 27, 'length': 2.0, 
                                 'insulation_thermal_conductivity': 0.035, 
                                 'insulation_thickness_mm': 40, 
                                 'surface_reflectivity': False, 
                                 'pipe_contents': 'water', 'internal_diameter': 0.024,
                                  'external_diameter': 0.027, 'insulation_thickness': 0.04}, 
                                {'location': 'external', 'internal_diameter_mm': 25, 
                                  'external_diameter_mm': 27, 'length': 0.0, 
                                  'insulation_thermal_conductivity': 0.035, 
                                  'insulation_thickness_mm': 38, 'surface_reflectivity': False,
                                  'pipe_contents': 'water', 'internal_diameter': 0.025, 
                                  'external_diameter': 0.027, 'insulation_thickness': 0.038
                                }]
        
        self.storagetank_with_pipework = StorageTank(150.0, 1.68, 55.0, self.coldfeed, self.simtime, 
                                                     self.heat_source_dict, DummyProject(20), self.extcond, False,
                                                     nb_vol, primary_pipework_lst)
        for t_idx, _, _ in self.simtime:  
            with self.subTest(timestep=t_idx):          
                self.assertEqual(self.storagetank_with_pipework._StorageTank__primary_pipework_losses(
                                                        input_energy_adj, setpnt_max),
                                [(0.0, 0.0),(0.0, 0.0),(0.0, 0.0),(0.0, 0.0),
                                 (0.0, 0.0),(0.0, 0.0),(0.0, 0.0),(0.0, 0.0)][t_idx])
               
        # With value for input_energy_adj
        input_energy_adj = 3.0
        
        self.simtime.reset()
        for t_idx, _, _ in self.simtime:  
            with self.subTest(timestep=t_idx):          
                self.assertEqual(self.storagetank_with_pipework._StorageTank__primary_pipework_losses(
                                                        input_energy_adj, setpnt_max),
                                [(0.04665869119015863, 9.854304934823482),
                                 (0.04665869119015863, 9.854304934823482),
                                 (0.04665869119015863, 9.854304934823482),
                                 (0.04665869119015863, 9.854304934823482),
                                 (0.04665869119015863, 9.854304934823482),
                                 (0.04665869119015863, 9.854304934823482),
                                 (0.04665869119015863, 9.854304934823482),
                                 (0.04665869119015863, 9.854304934823482)][t_idx])
    
    # def test_heat_source_output(self):
    #
    #     # Heat source is immersion heater
    #     heat_source = self.imheater
    #     input_energy_adj = 0.5
    #     self.assertEqual(self.storagetank.heat_source_output(heat_source, input_energy_adj),
    #                      0.5)
    #
    #     # Test with solarthermal heat_source        
    #     coldwatertemps = [17.0, 17.1, 17.2, 17.3, 17.4, 17.5, 17.6, 17.7, 17.0, 17.1, 17.2, 17.3,
    #                          17.4, 17.5, 17.6, 17.7, 17.0, 17.1, 17.2, 17.3, 17.4, 17.5, 17.6, 17.7]
    #     self.simtime     = SimulationTime(5088, 5112, 1)
    #     coldfeed         = ColdWaterSource(coldwatertemps, self.simtime, 212, 1)
    #     self.controlmax = SetpointTimeControl(
    #                             [55.0, 55.0, 55.0, 55.0, 55.0, 55.0, 55.0, 55.0,
    #                              55.0, 55.0, 55.0, 55.0, 55.0, 55.0, 55.0, 55.0,
    #                              55.0, 55.0, 55.0, 55.0, 55.0, 55.0, 55.0, 55.0
    #                             ],
    #                             self.simtime,
    #                             212,
    #                             1
    #                             )
    #     self.energysupply = EnergySupply("electricity", self.simtime)
    #     self.energysupplyconnst = self.energysupply.connection("solarthermal")
    #
    #     #Adding solarthermal to the test
    #     proj_dict = {
    #         "ExternalConditions": {
    #             "air_temperatures": [19.0, 19.0, 19.0, 19.0, 19.0, 19.0, 19.0, 19.0, 19.0, 19.0, 19.0, 19.0, 
    #                                     19.0, 19.0, 19.0, 19.0, 19.0, 19.0, 19.0, 19.0, 19.0, 19.0, 19.0, 19.0],
    #             "wind_speeds": [3.9, 3.8, 3.9, 4.1, 3.8, 4.2, 4.3, 4.1, 3.9, 3.8, 3.9, 4.1, 
    #                                 3.8, 4.2, 4.3, 4.1, 3.9, 3.8, 3.9, 4.1, 3.8, 4.2, 4.3, 4.1],
    #             "wind_directions": [300, 250, 220, 180, 150, 120, 100, 80, 60, 40, 20, 10,
    #                                 50, 100, 140, 190, 200, 320, 330, 340, 350, 355, 315, 5],
    #             "diffuse_horizontal_radiation": [0, 0, 0, 0, 35, 73, 139, 244, 320, 361, 369, 348, 
    #                                                 318, 249, 225, 198, 121, 68, 19, 0, 0, 0, 0, 0],
    #             "direct_beam_radiation": [0, 0, 0, 0, 0, 0, 7, 53, 63, 164, 339, 242, 
    #                                         315, 577, 385, 285, 332, 126, 7, 0, 0, 0, 0, 0],
    #             "solar_reflectivity_of_ground": [0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 
    #                                                 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2],
    #             "latitude": 51.383,
    #             "longitude": -0.783,
    #             "timezone": 0,
    #             "start_day": 212,
    #             "end_day": 212,
    #             "time_series_step": 1,
    #             "january_first": 1,
    #             "daylight_savings": "not applicable",
    #             "leap_day_included": False,
    #             "direct_beam_conversion_needed": False,
    #             "shading_segments":[
    #         {"number": 1, "start": 180, "end": 135},
    #         {"number": 2, "start": 135, "end": 90},
    #         {"number": 3, "start": 90, "end": 45},
    #         {"number": 4, "start": 45, "end": 0, 
    #             "shading": [
    #                 {"type": "obstacle", "height": 10.5, "distance": 12}
    #             ]
    #         },
    #         {"number": 5, "start": 0, "end": -45},
    #         {"number": 6, "start": -45, "end": -90},
    #         {"number": 7, "start": -90, "end": -135},
    #         {"number": 8, "start": -135, "end": -180}
    #     ],
    #         }
    #     }
    #     self.__external_conditions = ExternalConditions(
    #         self.simtime,
    #         proj_dict['ExternalConditions']['air_temperatures'],
    #         proj_dict['ExternalConditions']['wind_speeds'],
    #         proj_dict['ExternalConditions']['wind_directions'],
    #         proj_dict['ExternalConditions']['diffuse_horizontal_radiation'],
    #         proj_dict['ExternalConditions']['direct_beam_radiation'],
    #         proj_dict['ExternalConditions']['solar_reflectivity_of_ground'],
    #         proj_dict['ExternalConditions']['latitude'],
    #         proj_dict['ExternalConditions']['longitude'],
    #         proj_dict['ExternalConditions']['timezone'],
    #         proj_dict['ExternalConditions']['start_day'],
    #         proj_dict['ExternalConditions']['end_day'],
    #         proj_dict['ExternalConditions']["time_series_step"],
    #         proj_dict['ExternalConditions']['january_first'],
    #         proj_dict['ExternalConditions']['daylight_savings'],
    #         proj_dict['ExternalConditions']['leap_day_included'],
    #         proj_dict['ExternalConditions']['direct_beam_conversion_needed'],
    #         proj_dict['ExternalConditions']['shading_segments']
    #         )
    #     self.solthermal  = SolarThermalSystem("OUT", 3, 1, 0.8, 0.9, 3.5, 0, 1, 100, 10, 
    #                                           self.energysupplyconnst, 30, 0, 0.5, 
    #                                           self.__external_conditions, self.simtime, 
    #                                           DummyProject(20), self.controlmax,
    #                                           )
    #     heat_source_dict = {self.solthermal: (0.1, 0.33)}
    #
    #     self.storagetank = StorageTank(150.0, 1.68, 55.0, coldfeed, self.simtime, 
    #                                    heat_source_dict, DummyProject(20), self.__external_conditions)
    #     input_energy_adj = 1
    #     self.assertEqual(self.storagetank.heat_source_output(self.solthermal, input_energy_adj),
    #                      0.0)
    #
    #     self.storagetank3.demand_hot_water(usage_events)
    #
    #     # Verify the temperatures against expected results
    #     self.assertListEqual(
    #         self.storagetank3._StorageTank__temp_n,  
    #         expected_temperatures_3[t_idx],
    #         "incorrect temperatures returned in case where storage tank has pre-heated feed"
    #         )
    #     self.assertAlmostEqual(
    #         self.energysupply.results_by_end_user()["immersion3"][t_idx],
    #         [0.0,
    #          0.0,
    #          0.0,
    #          0.0,
    #          2.4226330401748983,
    #          1.5348554176954723,
    #          0.0,
    #          0.0,
    #         ][t_idx],
    #         msg="incorrect energy supplied returned in case where storage tank has pre-heated feed",
    #         )

class Test_ImmersionHeater(unittest.TestCase):
    """ Unit tests for ImmersionHeater class """

    def setUp(self):
        """ Create ImmersionHeater object to be tested """
        self.simtime          = SimulationTime(0, 4, 1)
        self.energysupply     = EnergySupply("mains_gas", self.simtime)
        energysupplyconn      = self.energysupply.connection("shower")
        controlmin            = SetpointTimeControl([52, 52, None, 52], self.simtime, 0, 1)
        controlmax            = SetpointTimeControl([60, 60, 60, 60], self.simtime, 0, 1)
        self.immersionheater  = ImmersionHeater(50, energysupplyconn, self.simtime, controlmin, controlmax)

    def test_demand_energy(self):
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                self.assertEqual(
                    self.immersionheater.demand_energy([40.0, 100.0, 30.0, 20.0][t_idx]),
                    [40.0, 50.0, 0.0, 20.0][t_idx],
                    "incorrect energy supplied returned",
                    )

        with self.assertRaises(ValueError):
            self.immersionheater.demand_energy(-1)

    def test_energy_output_max(self):
                
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                self.assertEqual(self.immersionheater.energy_output_max(return_temp = 55.0, 
                                                                        ignore_standard_ctrl=True),
                                [50.0, 50.0, 50.0, 50.0][t_idx])
                
        self.simtime.reset()
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                self.assertEqual(self.immersionheater.energy_output_max(return_temp = 40.0, 
                                                                        ignore_standard_ctrl=False),
                                [50.0, 50.0, 0.0, 50.0][t_idx])
                
    
class TestPVDiverter(unittest.TestCase):
    '''Unit tests for TestPVDiverter class'''    

    def setUp(self):
        """ Create PVDiverter object to be tested """

        self.simtime          = SimulationTime(0, 4, 1)
        self.coldwatertemps   = [10.6, 11.0, 11.5, 12.1]
        self.coldfeed         = ColdWaterSource(self.coldwatertemps, self.simtime, 0, 1)
        self.energysupply     = EnergySupply("mains_gas", self.simtime)
        energysupplyconn      = self.energysupply.connection("shower")
        controlmin            = SetpointTimeControl([52, 52, None, 52], self.simtime, 0, 1)
        controlmax            = SetpointTimeControl([60, 60, 60, 60], self.simtime, 0, 1)
        self.immersionheater  = ImmersionHeater(50, energysupplyconn, self.simtime, controlmin, controlmax)
        self.heat_source_dict = {self.immersionheater : (0.1, 0.33)}
        self.windspeed = [3.7, 3.8, 3.9, 4.0, 4.1, 4.2, 4.3, 4.4]
        self.wind_direction = [0.0] * 8
        self.energy_supply_conn_name_auxiliary = 'Boiler_auxiliary'
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
        self.storagetank = StorageTank(150.0, 1.68, 55.0, self.coldfeed, self.simtime, self.heat_source_dict, DummyProject(20), self.extcond)
        self.pvdiverter = PVDiverter(self.storagetank,self.immersionheater)
        
    def test_divert_surplus(self):
        
        # _StorageTank__Q_ls_n_prev_heat_source is needed for the functions to 
        # run the test but have no bearing in the results     
        self.storagetank._StorageTank__Q_ls_n_prev_heat_source = [0.0,0.1,0.2,0.3]

        self.assertAlmostEqual(self.pvdiverter.divert_surplus(supply_surplus = -1.0),
                               0.891553580246915)
        self.assertAlmostEqual(self.pvdiverter.divert_surplus(supply_surplus = 0.0),
                               0.0)
        self.assertAlmostEqual(self.pvdiverter.divert_surplus(supply_surplus = 1.0),
                               0.0)

class TestSolarThermalSystem(unittest.TestCase):    
    '''Unit tests for SolarThermalSystem class'''    

    def setUp(self):
        """ Create SolarThermalSystem object to be tested """        
        coldwatertemps = [17.0, 17.1, 17.2, 17.3, 17.4, 17.5, 17.6, 17.7, 17.0, 17.1, 17.2, 17.3,
                             17.4, 17.5, 17.6, 17.7, 17.0, 17.1, 17.2, 17.3, 17.4, 17.5, 17.6, 17.7]
        self.simtime     = SimulationTime(5088, 5112, 1)
        coldfeed         = ColdWaterSource(coldwatertemps, self.simtime, 212, 1)
        self.controlmax = SetpointTimeControl(
                                [55.0, 55.0, 55.0, 55.0, 55.0, 55.0, 55.0, 55.0,
                                 55.0, 55.0, 55.0, 55.0, 55.0, 55.0, 55.0, 55.0,
                                 55.0, 55.0, 55.0, 55.0, 55.0, 55.0, 55.0, 55.0
                                ],
                                self.simtime,
                                212,
                                1
                                )
        self.energysupply = EnergySupply("electricity", self.simtime)
        self.energysupplyconnst = self.energysupply.connection("solarthermal")

        #Adding solarthermal to the test
        proj_dict = {
            "ExternalConditions": {
                "air_temperatures": [19.0, 19.0, 19.0, 19.0, 19.0, 19.0, 19.0, 19.0, 19.0, 19.0, 19.0, 19.0, 
                                        19.0, 19.0, 19.0, 19.0, 19.0, 19.0, 19.0, 19.0, 19.0, 19.0, 19.0, 19.0],
                "wind_speeds": [3.9, 3.8, 3.9, 4.1, 3.8, 4.2, 4.3, 4.1, 3.9, 3.8, 3.9, 4.1, 
                                    3.8, 4.2, 4.3, 4.1, 3.9, 3.8, 3.9, 4.1, 3.8, 4.2, 4.3, 4.1],
                "wind_directions": [300, 250, 220, 180, 150, 120, 100, 80, 60, 40, 20, 10,
                                    50, 100, 140, 190, 200, 320, 330, 340, 350, 355, 315, 5],
                "diffuse_horizontal_radiation": [0, 0, 0, 0, 35, 73, 139, 244, 320, 361, 369, 348, 
                                                    318, 249, 225, 198, 121, 68, 19, 0, 0, 0, 0, 0],
                "direct_beam_radiation": [0, 0, 0, 0, 0, 0, 7, 53, 63, 164, 339, 242, 
                                            315, 577, 385, 285, 332, 126, 7, 0, 0, 0, 0, 0],
                "solar_reflectivity_of_ground": [0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 
                                                    0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2],
                "latitude": 51.383,
                "longitude": -0.783,
                "timezone": 0,
                "start_day": 212,
                "end_day": 212,
                "time_series_step": 1,
                "january_first": 1,
                "daylight_savings": "not applicable",
                "leap_day_included": False,
                "direct_beam_conversion_needed": False,
                "shading_segments":[
            {"number": 1, "start": 180, "end": 135},
            {"number": 2, "start": 135, "end": 90},
            {"number": 3, "start": 90, "end": 45},
            {"number": 4, "start": 45, "end": 0, 
                "shading": [
                    {"type": "obstacle", "height": 10.5, "distance": 12}
                ]
            },
            {"number": 5, "start": 0, "end": -45},
            {"number": 6, "start": -45, "end": -90},
            {"number": 7, "start": -90, "end": -135},
            {"number": 8, "start": -135, "end": -180}
        ],
            }
        }
        self.__external_conditions = ExternalConditions(
            self.simtime,
            proj_dict['ExternalConditions']['air_temperatures'],
            proj_dict['ExternalConditions']['wind_speeds'],
            proj_dict['ExternalConditions']['wind_directions'],
            proj_dict['ExternalConditions']['diffuse_horizontal_radiation'],
            proj_dict['ExternalConditions']['direct_beam_radiation'],
            proj_dict['ExternalConditions']['solar_reflectivity_of_ground'],
            proj_dict['ExternalConditions']['latitude'],
            proj_dict['ExternalConditions']['longitude'],
            proj_dict['ExternalConditions']['timezone'],
            proj_dict['ExternalConditions']['start_day'],
            proj_dict['ExternalConditions']['end_day'],
            proj_dict['ExternalConditions']["time_series_step"],
            proj_dict['ExternalConditions']['january_first'],
            proj_dict['ExternalConditions']['daylight_savings'],
            proj_dict['ExternalConditions']['leap_day_included'],
            proj_dict['ExternalConditions']['direct_beam_conversion_needed'],
            proj_dict['ExternalConditions']['shading_segments']
            )
        self.solthermal  = SolarThermalSystem("OUT", 3, 1, 0.8, 0.9, 3.5, 0, 1, 100, 10, 
                                              self.energysupplyconnst, 30, 0, 0.5, 
                                              self.__external_conditions, self.simtime, 
                                              DummyProject(20), self.controlmax,
                                              )
        heat_source_dict = {self.solthermal: (0.1, 0.33)}

        self.storagetank = StorageTank(150.0, 1.68, 55.0, coldfeed, self.simtime, heat_source_dict, DummyProject(20), self.__external_conditions)
                 
    def test_energy_output_max(self):
        
        self.temp_storage_tank_s3_n = [17.2, 17.2, 17.2, 17.2, 17.43, 32.95, 35.91, 35.91, 35.91, 42.25,
                                       43.46, 43.46, 43.46, 43.46, 43.46, 43.46, 43.46, 43.46, 43.46, 43.46, 
                                       43.46, 43.46, 43.46, 43.46]
        
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                self.assertAlmostEqual(self.solthermal.energy_output_max(self.storagetank,
                                                            self.temp_storage_tank_s3_n),
                [0,0,0,0,0,0,0,0.5441009409757523,0.7375096332994749,1.043768276267769,1.4751675743361337,
                1.2419712751344847,1.3717388178387737,1.7256641787433769,1.1745201463530213,0.8403815010507395,
                0.6056200608960752,0,0,0,0,0,0,0][t_idx])
                        
        
        self.sol_loc  = 'NHS'        
        self.solar_thermal_system_NHS = SolarThermalSystem(self.sol_loc,
                                                       3, 1, 0.8, 0.9, 3.5, 0, 1, 100, 10, 
                                                       self.energysupplyconnst, 30, 0, 0.5, 
                                                       self.__external_conditions, self.simtime, 
                                                       DummyProject(20), self.controlmax
                                                       )
                                                       
        self.simtime.reset()
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                self.assertAlmostEqual(self.solar_thermal_system_NHS.energy_output_max(self.storagetank,
                                                          self.temp_storage_tank_s3_n),
                                [0,0,0,0,0,0,0,0.5443432944582923,0.7377445749305638,
                                 1.044003444574131,1.4754027357101285,1.2422064367204904,
                                 1.371973979418296,1.7258993403230973,1.1747553079327355,
                                 0.8406166626304539,0.6058552224757895,0,0,0,0,0,0,0][t_idx])
        
        self.sol_loc  = 'HS'        
        self.solar_thermal_system_HS = SolarThermalSystem(self.sol_loc,
                                                       3, 1, 0.8, 0.9, 3.5, 0, 1, 100, 10, 
                                                       self.energysupplyconnst, 30, 0, 0.5, 
                                                       self.__external_conditions, self.simtime, 
                                                       DummyProject(20), self.controlmax
                                                       )
        self.simtime.reset()
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                self.assertAlmostEqual(self.solar_thermal_system_HS.energy_output_max(self.storagetank,
                                                          self.temp_storage_tank_s3_n),
                     [0,0,0,0,0,0,0,0.5445856479408322,0.7379795165616525,1.044238612880493,
                      1.475637897084123,1.2424415983064963,1.372209140997818,1.7261345019028178,
                      1.1749904695124498,0.8408518242101682,0.6060903840555039,0,0,0,0,0,0,0][t_idx])
                        
        
    def test_demand_energy(self):
        
        self.temp_storage_tank_s3_n = [17.2, 17.2, 17.2, 17.2, 17.43, 32.95, 35.91, 35.91, 35.91, 42.25,
                                       43.46, 43.46, 43.46, 43.46, 43.46, 43.46, 43.46, 43.46, 43.46, 43.46, 
                                       43.46, 43.46, 43.46, 43.46]
        
        self.solthermal.energy_output_max(self.storagetank,
                                          self.temp_storage_tank_s3_n)
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                self.assertAlmostEqual(self.solthermal.demand_energy(energy_demand = 100),
                                 [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0][t_idx])
                         
        
        
        
        
    
    
        
        
                
                
                
                
