#!/usr/bin/env python3

"""
This module contains unit tests for the Photovoltaic System module
"""

# Standard library imports
import unittest

# Set path to include modules to be tested (must be before local imports)
from unit_tests.common import test_setup

test_setup()

# Local imports
from core.simulation_time import SimulationTime
from core.external_conditions import ExternalConditions
from core.energy_supply.energy_supply import EnergySupply, EnergySupplyConnection
from core.energy_supply.pv import PhotovoltaicSystem

class TestPhotovoltaicSystem(unittest.TestCase):
    """ Unit tests for PhotovoltaicSystem class """

    def setUp(self):
        """ Create PhotovoltaicSystem object to be tested """
        #simulation time: start, end, step
        self.simtime = SimulationTime(0, 8, 1)
        proj_dict = {
            "ExternalConditions": {
                "air_temperatures": [0.0, 2.5, 5.0, 7.5, 10.0, 12.5, 15.0, 20.0],
                "wind_speeds": [3.9, 3.8, 3.9, 4.1, 3.8, 4.2, 4.3, 4.1],
                "wind_directions": [220, 230, 240, 250, 260, 270, 270, 280],
                "diffuse_horizontal_radiation": [11, 25, 42, 52, 60, 44, 28, 15],
                "direct_beam_radiation": [11, 25, 42, 52, 60, 44, 28, 15],
                "solar_reflectivity_of_ground": [0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2],
                "latitude": 51.42,
                "longitude": -0.75,
                "timezone": 0,
                "start_day": 0,
                "end_day": 0,
                "time_series_step": 1,
                "january_first": 1,
                "daylight_savings": "not applicable",
                "leap_day_included": False,
                "direct_beam_conversion_needed": False,
                "shading_segments":[{"number": 1, "start": 180, "end": 135},
                                    {"number": 2, "start": 135, "end": 90,
                                     "shading": [
                                         {"type": "overhang", "height": 2.2, "distance": 6}
                                         ]
                                     },
                                    {"number": 3, "start": 90, "end": 45},
                                    {"number": 4, "start": 45, "end": 0, 
                                     "shading": [
                                         {"type": "obstacle", "height": 40, "distance": 4},
                                         {"type": "overhang", "height": 3, "distance": 7}
                                         ]
                                     },
                                    {"number": 5, "start": 0, "end": -45,
                                     "shading": [
                                         {"type": "obstacle", "height": 3, "distance": 8},
                                         ]
                                     },
                                    {"number": 6, "start": -45, "end": -90},
                                    {"number": 7, "start": -90, "end": -135},
                                    {"number": 8, "start": -135, "end": -180}],
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
        self.energysupply = EnergySupply("electricity", self.simtime)
        energysupplyconn = self.energysupply.connection("pv generation without shading")
        self.pv_system = PhotovoltaicSystem(
                2.5,
                "moderately_ventilated",
                30,
                0,
                10,
                2,
                3,
                self.__external_conditions,
                energysupplyconn,
                self.simtime,
                [],
                2.5,
                0.05,
                False,
                "optimised_inverter",
                )
        
        energysupplyconn = self.energysupply.connection("pv generation with shading")
        self.pv_system_with_shading = PhotovoltaicSystem(
                2.5,
                "moderately_ventilated",
                30,
                0,
                10,
                2,
                3,
                self.__external_conditions,
                energysupplyconn,
                self.simtime,
                [{"type": "overhang", "depth": 0.5, "distance": 0.5},
                 {"type": "sidefinleft", "depth": 0.25, "distance": 0.1},
                 {"type": "sidefinright", "depth":0.25, "distance":0.1}],
                 2.5,
                 0.02,
                True,
                "string_inverter",
                )

    def test_is_inside(self):
        """ Test that the PhotovoltaicSystem object 'is inside' flag is being returned correctly """
        self.assertFalse(self.pv_system.inverter_is_inside())
        self.assertTrue(self.pv_system_with_shading.inverter_is_inside())

    def test_produce_energy(self):
        """ Test that PhotovoltaicSystem object returns correct electricity generated kWh
            Note: produced energy stored as a negative demand"""
        expected_results = [
            -0.002911179810082315, -0.01585915973389526, -0.03631681332778666, -0.0462218185635626,
            -0.05, -0.03841528069730012, -0.019985927280177524, -0.014819433057321862
        ]
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                self.pv_system.produce_energy()
                self.assertAlmostEqual(
                    self.energysupply.results_by_end_user()["pv generation without shading"][t_idx],
                    expected_results[t_idx],
                    places=6,
                    msg="incorrect electricity produced from pv returned"
                    )

    def test_produce_energy_with_shading(self):
        """ Test that PhotovoltaicSystem object with shading returns correct electricity 
            generated kWh
            Note: produced energy stored as a negative demand"""
        expected_results = [
            -0.0015507260447403823, -0.008732593505451556, -0.02, -0.02,
            -0.02, -0.013971934370722397, -0.006779589823217942, -0.007020372160065822
        ]
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                self.pv_system_with_shading.produce_energy()
                self.assertAlmostEqual(
                    self.energysupply.results_by_end_user()["pv generation with shading"][t_idx],
                    expected_results[t_idx],
                    places=6,
                    msg="incorrect electricity produced from pv returned"
                    )

    def test_produce_energy_produced_and_lost(self):
        """ Test that PhotovoltaicSystem object returns correct electricity produced and lost (in kWh) """
        expected_energy_produced = [
            0.002911179810082315,0.01585915973389526,0.03631681332778666,0.0462218185635626,
            0.05,0.03841528069730012,0.019985927280177524,0.014819433057321862
        ]
        expected_energy_lost = [
            0.012982394066666526,0.022261865114937766,0.024010573568482414,0.023376882776544372,
            0.02560556391283768,0.02392305675244094,0.023189444399645136,0.021949092776458276
        ]
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                energy_produced, energy_lost = self.pv_system.produce_energy()
                self.assertAlmostEqual(
                    energy_produced, expected_energy_produced[t_idx],
                    places=6,
                    msg=f"incorrect electricity produced from pv returned for timestep {t_idx}"
                )
                self.assertAlmostEqual(
                    energy_lost, expected_energy_lost[t_idx],
                    places=6,
                    msg=f"incorrect electricity lost from pv returned for timestep {t_idx}"
                )
                
