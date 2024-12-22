#!/usr/bin/env python3

"""
This module contains unit tests for the elec_battery module
"""

# Standard library imports
import unittest

# Set path to include modules to be tested (must be before local imports)
from unit_tests.common import test_setup
test_setup()

# Local imports
from core.simulation_time import SimulationTime
from core.energy_supply.elec_battery import ElectricBattery
from core.external_conditions import ExternalConditions

class TestElectricBattery(unittest.TestCase):
    """ Unit tests for ElectricBattery class """

    def setUp(self):
        self.simtime = SimulationTime(0, 8, 1)
        proj_dict = {
            "ExternalConditions": {
                "air_temperatures": [0.0, 2.5, 5.0, 7.5, 10.0, 12.5, 15.0, 20.0],
                "wind_speeds": [3.9, 3.8, 3.9, 4.1, 3.8, 4.2, 4.3, 4.1],
                "wind_directions": [0, 20, 40, 60, 0, 20, 40, 60],
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
                
        """ Create ElectricBattery object to be tested """
        self.elec_battery = ElectricBattery(2, 0.8, 3, 0.001, 1.5, 1.5, "outside", False, self.simtime, self.__external_conditions)
        
    def test_charge_discharge_battery(self):
        """ Test the charge_discharge_battery function including for
            overcharging and overdischarging.
        """
        #Supply to battery exceeds limit
        self.assertAlmostEqual(
            self.elec_battery.charge_discharge_battery(-1000),
            -1.6770509831248424,
            msg = "Test failed: Supply to battery exceeds limit",
            )

        #Demand on battery exceeds limit
        self.assertAlmostEqual(
            self.elec_battery.charge_discharge_battery(1000),
            1.121472,
            msg = "Test failed: Demand on battery exceeds limit",
            )

        #Normal charge
        self.assertAlmostEqual(
            self.elec_battery.charge_discharge_battery(-0.2),
            0.0,
            msg = "Test failed: Normal charge",
            )

        #Normal discharge
        self.assertAlmostEqual(
            self.elec_battery.charge_discharge_battery(0.1),
            0.0747648,
            msg = "Test failed: Normal discharge",
            )
