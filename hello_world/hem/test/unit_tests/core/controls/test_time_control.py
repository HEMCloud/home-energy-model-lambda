#!/usr/bin/env python3

"""
This module contains unit tests for the Time Control module
"""

# Standard library imports
import unittest

# Set path to include modules to be tested (must be before local imports)
from unit_tests.common import test_setup
test_setup()

# Local imports
from core.simulation_time import SimulationTime
from core.external_conditions import ExternalConditions
from core.controls.time_control import \
    OnOffTimeControl, SetpointTimeControl, CombinationTimeControl, \
    OnOffCostMinimisingTimeControl, ChargeControl

class Test_OnOffTimeControl(unittest.TestCase):
    """ Unit tests for OnOffTimeControl class """

    def setUp(self):
        """ Create TimeControl object to be tested """
        self.simtime     = SimulationTime(0, 8, 1)
        self.schedule    = [True, False, True, True, False, True, False, False]
        self.timecontrol = OnOffTimeControl(self.schedule, self.simtime, 0, 1)

    def test_is_on(self):
        """ Test that OnOffTimeControl object returns correct schedule"""
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                self.assertEqual(
                    self.timecontrol.is_on(),
                    self.schedule[t_idx],
                    "incorrect schedule returned",
                    )


class Test_OnOffCostMinimisingTimeControl(unittest.TestCase):

    def setUp(self):
        self.simtime = SimulationTime(0, 48, 1)
        cost_schedule = 2 * ([5.0] * 7 + [10.0] * 2 + [7.5] * 8 + [15.0] * 6 + [5.0])
        self.cost_minimising_ctrl = OnOffCostMinimisingTimeControl(
            cost_schedule,
            self.simtime,
            0.0, # Start day
            1.0, # Schedule data is hourly
            12.0, # Need 12 "on" hours
            )

    def test_is_on(self):
        resulting_schedule \
            = 2 * ([True] * 7 + [False] * 2 + [True] * 4 + [False] * 4 + [False] * 6 + [True])
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                self.assertEqual(
                    self.cost_minimising_ctrl.is_on(),
                    resulting_schedule[t_idx],
                    "incorrect schedule returned",
                    )


class Test_SetpointTimeControl(unittest.TestCase):
    """ Unit tests for SetpointTimeControl class """

    def setUp(self):
        """ Create TimeControl object to be tested """
        self.simtime     = SimulationTime(0, 8, 1)
        self.schedule    = [21.0, None, None, 21.0, None, 21.0, 25.0, 15.0]
        self.timecontrol = SetpointTimeControl(self.schedule, self.simtime, 0, 1)
        self.timecontrol_min \
            = SetpointTimeControl(self.schedule, self.simtime, 0, 1, 16.0, None)
        self.timecontrol_max \
            = SetpointTimeControl(self.schedule, self.simtime, 0, 1, None, 24.0)
        self.timecontrol_minmax \
            = SetpointTimeControl(self.schedule, self.simtime, 0, 1, 16.0, 24.0, False)
        self.timecontrol_advstart \
            = SetpointTimeControl(self.schedule, self.simtime, 0, 1, None, None, False, 1.0)
        self.timecontrol_advstart_minmax \
            = SetpointTimeControl(self.schedule, self.simtime, 0, 1, 16.0, 24.0, False, 1.0)

    def test_in_required_period(self):
        """ Test that SetpointTimeControl objects return correct status for required period """
        results = [True, False, False, True, False, True, True, True]
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                self.assertEqual(
                    self.timecontrol.in_required_period(),
                    results[t_idx],
                    "incorrect in_required_period value returned for control with no min or max set",
                    )
                self.assertEqual(
                    self.timecontrol_min.in_required_period(),
                    results[t_idx],
                    "incorrect in_required_period value returned for control with min set",
                    )
                self.assertEqual(
                    self.timecontrol_max.in_required_period(),
                    results[t_idx],
                    "incorrect in_required_period value returned for control with max set",
                    )
                self.assertEqual(
                    self.timecontrol_minmax.in_required_period(),
                    results[t_idx],
                    "incorrect in_required_period value returned for control with min and max set",
                    )
                self.assertEqual(
                    self.timecontrol_advstart.in_required_period(),
                    results[t_idx],
                    "incorrect in_required_period value returned for control with advanced start"
                    )
                self.assertEqual(
                    self.timecontrol_advstart_minmax.in_required_period(),
                    results[t_idx],
                    "incorrect in_required_period value returned for control with advanced start"
                    )

    def test_is_on(self):
        """ Test that SetpointTimeControl object is always on """
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                self.assertEqual(
                    self.timecontrol.is_on(),
                    [True, False, False, True, False, True, True, True][t_idx],
                    "incorrect is_on value returned for control with no min or max set",
                    )
                self.assertEqual(
                    self.timecontrol_min.is_on(),
                    True, # Should always be True for this type of control
                    "incorrect is_on value returned for control with min set",
                    )
                self.assertEqual(
                    self.timecontrol_max.is_on(),
                    True, # Should always be True for this type of control
                    "incorrect is_on value returned for control with max set",
                    )
                self.assertEqual(
                    self.timecontrol_minmax.is_on(),
                    True, # Should always be True for this type of control
                    "incorrect is_on value returned for control with min and max set",
                    )
                self.assertEqual(
                    self.timecontrol_advstart.is_on(),
                    [True, False, True, True, True, True, True, True][t_idx],
                    "incorrect is_on value returned for control with advanced start"
                    )
                self.assertEqual(
                    self.timecontrol_advstart_minmax.is_on(),
                    True,
                    "incorrect is_on value returned for control with advanced start"
                    )

    def test_setpnt(self):
        """ Test that SetpointTimeControl object returns correct schedule"""
        results_min             = [21.0, 16.0, 16.0, 21.0, 16.0, 21.0, 25.0, 16.0]
        results_max             = [21.0, 24.0, 24.0, 21.0, 24.0, 21.0, 24.0, 15.0]
        results_minmax          = [21.0, 16.0, 16.0, 21.0, 16.0, 21.0, 24.0, 16.0]
        results_advstart        = [21.0, None, 21.0, 21.0, 21.0, 21.0, 25.0, 15.0]
        results_advstart_minmax = [21.0, 16.0, 21.0, 21.0, 21.0, 21.0, 24.0, 16.0]

        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                self.assertEqual(
                    self.timecontrol.setpnt(),
                    self.schedule[t_idx],
                    "incorrect schedule returned for control with no min or max set",
                    )
                self.assertEqual(
                    self.timecontrol_min.setpnt(),
                    results_min[t_idx],
                    "incorrect schedule returned for control with min set",
                    )
                self.assertEqual(
                    self.timecontrol_max.setpnt(),
                    results_max[t_idx],
                    "incorrect schedule returned for control with max set",
                    )
                self.assertEqual(
                    self.timecontrol_minmax.setpnt(),
                    results_minmax[t_idx],
                    "incorrect schedule returned for control with min and max set",
                    )
                self.assertEqual(
                    self.timecontrol_advstart.setpnt(),
                    results_advstart[t_idx],
                    "incorrect schedule returned for control with advanced start",
                    )
                self.assertEqual(
                    self.timecontrol_advstart_minmax.setpnt(),
                    results_advstart_minmax[t_idx],
                    "incorrect schedule returned for control with advanced start and min and max set",
                    )

class Test_ChargeControl(unittest.TestCase):
    """ Unit tests for ChargeControl class """

    def setUp(self):
        """ Create ChargeControl object to be tested """
        self.simtime1     = SimulationTime(0, 24, 1)
        self.simtime2     = SimulationTime(0, 24, 1)
        self.schedule    = [True, True, True, True, 
                            True, True, True, True, 
                            False, False, False, False,
                            False, False, False, False, 
                            True, True, True, True, 
                            False, False, False, False]
        proj_dict = {
            "ExternalConditions": {
                "air_temperatures": [19.0, 0.0, 1.0, 2.0, 5.0, 7.0, 6.0, 12.0, 19.0, 19.0, 19.0, 19.0, 
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
                "start_day": 0,
                "end_day": 0,
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
        self.external_conditions1 = ExternalConditions(
            self.simtime1,
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
        self.external_conditions2 = ExternalConditions(
            self.simtime2,
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
        self.external_sensor = {
                "correlation": [
                    {"temperature": 0.0, "max_charge": 1.0},
                    {"temperature": 10.0, "max_charge": 0.9},
                    {"temperature": 18.0, "max_charge": 0.0}
                ]
            }
        self.charge_control1   = ChargeControl("Automatic",
                                                 self.schedule, 
                                                 self.simtime1, 
                                                 0, 
                                                 1, 
                                                 [ 1.0, 0.8 ],
                                                 15.5, None, 
                                                 None, None,
                                                 self.external_conditions1,
                                                 self.external_sensor)
        self.charge_control2  = ChargeControl("Automatic",
                                                 self.schedule, 
                                                 self.simtime2, 
                                                 0, 
                                                 1, 
                                                 [ 1.0, 0.8 ],
                                                 15.5, None, 
                                                 None, None,
                                                 self.external_conditions2,
                                                 self.external_sensor)
        
    def test_is_on(self):
        """ Test that ChargeControl object returns correct schedule"""
        for t_idx, _, _ in self.simtime1:
            with self.subTest(i=t_idx):
                self.assertEqual(
                    self.charge_control1.is_on(),
                    self.schedule[t_idx],
                    "incorrect schedule returned",
                    )
        
    def test_target_charge(self):
        """ Test that ChargeControl object returns correct schedule"""
        # Expected results for the unit test
        expected_target_charges_1 = [
            0.0, 1.0, 0.99, 0.98, 
            0.95, 0.93, 0.9400000000000001, 0.675, 
            0.0, 0.0, 0.0, 0.0, 
            0.0, 0.0, 0.0, 0.0, 
            0.0, 0.0, 0.0, 0.0, 
            0.0, 0.0, 0.0, 0.0
        ]
        expected_target_charges_2 = [
            0.0, 0.0, 0.0, 0.0, 
            0.0, 0.0, 0.0, 0.0, 
            0.0, 0.0, 0.0, 0.0, 
            0.0, 0.0, 0.0, 0.0, 
            0.0, 0.0, 0.0, 0.0, 
            0.0, 0.0, 0.0, 0.0
        ]
        for t_idx, _, _ in self.simtime1:
            with self.subTest(i=t_idx):
                self.assertEqual(
                    self.charge_control1.target_charge(12.5),
                    expected_target_charges_1[t_idx],
                    "incorrect target charge returned",
                    )

        for t_idx, _, _ in self.simtime2:
            with self.subTest(i=t_idx):
                self.assertEqual(
                    self.charge_control2.target_charge(19.5),
                    expected_target_charges_2[t_idx],
                    "incorrect target charge returned",
                    )

    def test_temp_charge_cut_corr(self):
        ''' Check correction of nominal/json temp_charge_cut with monthly table.
            This function will most likely be superseded when the Electric Storage methodology 
            is upgraded to consider more realistic manufacturers' controls and corresponding
            unit_test will be deprecated.  '''
    
        self.assertAlmostEqual(self.charge_control1.temp_charge_cut_corr(),15.5)

class TestCombinationTimeControl(unittest.TestCase):
    
    def setUp(self):
        # Define mock controls based on JSON configuration
        self.simtime     = SimulationTime(0, 8, 1)
        self.start_day   = 0
        self.time_series_step = 1

        self.simtime_cost     = SimulationTime(0,24,1)
        self.cost_schedule = [5.0] * 12 + [10.0] * 6 + [5.0] * 6
        self.cost_minimising_ctrl = OnOffCostMinimisingTimeControl(
            self.cost_schedule,
            self.simtime,
            0.0, # Start day
            1.0, # Schedule data is hourly
            5.0 #Need 12 "on" hours
            )
        self.controls = {
            "ctrl1": OnOffTimeControl([True, True, False, True, True, True, True, True],self.simtime, 0, 1),
            "ctrl2": OnOffTimeControl([False, True, True, False, False, False, True, False],self.simtime, 0, 1),
            "ctrl3": OnOffTimeControl([True, False, True, False, False, False, True, False],self.simtime, 0, 1),
            "ctrl4": SetpointTimeControl([45.0, 47.0, 50.0, 48.0, 48.0, 48.0, 48.0, 48.0],self.simtime, 0, 1),
            "ctrl5": SetpointTimeControl([52.0, 52.0, 52.0, 52.0, 52.0, 52.0, 52.0, 52.0],self.simtime, 0, 1),
            "ctrl6": OnOffTimeControl([True, True, False, True, True, True, True, True],self.simtime, 0, 1),
            "ctrl7": OnOffTimeControl([False, True, False, False, False, False, True, False],self.simtime, 0, 1),
            "ctrl8": OnOffTimeControl([True, False, False, True, True, True, True, True],self.simtime, 0, 1),
            "ctrl9": SetpointTimeControl([45.0, None, 50.0, 48.0, 48.0, None, 48.0, 48.0],self.simtime, 0, 1),
            "ctrl10": self.cost_minimising_ctrl
        }

        self.combination_on_off = {
            'main': {'operation': 'AND', 'controls': ['ctrl1', 'ctrl2', 'comb1', 'comb2']},
            'comb1': {'operation': 'OR', 'controls': ['ctrl3', 'comb3']},
            'comb2': {'operation': 'MAX', 'controls': ['ctrl4', 'ctrl5']},
            'comb3': {'operation': 'XOR', 'controls': ['ctrl6', 'ctrl7', 'ctrl8']}
        }
        
        # Create an instance of CombinationTimeControl
        self.combination_control_on_off = CombinationTimeControl(
            combination     = self.combination_on_off,
            controls        = self.controls,
            simulation_time = self.simtime,
            start_day       = self.start_day,
            time_series_step= self.time_series_step
        )

        self.combination_setpnt= {
                "main": {"operation": "AND", "controls": ["ctrl1", "ctrl2", "comb1"]},
                "comb1": {"operation": "MAX", "controls": ["ctrl4", "ctrl5"]}
        }
        # Create an instance of CombinationTimeControl
        self.combination_control_setpnt = CombinationTimeControl(
            combination     = self.combination_setpnt,
            controls        = self.controls,
            simulation_time = self.simtime,
            start_day       = self.start_day,
            time_series_step= self.time_series_step
        )
        
        self.combination_req = {
                "main": {"operation": "AND", "controls": ["ctrl9", "comb1"]},
                "comb1": {"operation": "AND", "controls": ["ctrl4", "ctrl1"]}
        }
        # Create an instance of CombinationTimeControl
        self.combination_control_req = CombinationTimeControl(
            combination     = self.combination_req,
            controls        = self.controls,
            simulation_time = self.simtime,
            start_day       = self.start_day,
            time_series_step= self.time_series_step
        )
        
        self.combination_on_off_cost = {
            'main': {'operation': 'AND', 'controls': ['ctrl1', 'ctrl2', 'comb1']},
            'comb1': {'operation': 'OR', 'controls': ['ctrl3', 'ctrl10']}            
        }
        
        # Create an instance of CombinationTimeControl
        self.combination_control_on_off_cost = CombinationTimeControl(
            combination     = self.combination_on_off_cost,
            controls        = self.controls,
            simulation_time = self.simtime,
            start_day       = self.start_day,
            time_series_step= self.time_series_step
        )
        
        #Setup for ChargeControl test
        
        self.simtime1     = SimulationTime(0, 24, 1)
        self.schedule    = [True, True, True, True, 
                            True, True, False, True, 
                            False, False, False, False,
                            False, False, False, False, 
                            True, True, True, True, 
                            False, False, False, False]
        proj_dict = {
            "ExternalConditions": {
                "air_temperatures": [19.0, 0.0, 1.0, 2.0, 5.0, 7.0, 6.0, 12.0, 19.0, 19.0, 19.0, 19.0, 
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
                "start_day": 0,
                "end_day": 0,
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
        self.external_conditions = ExternalConditions(
            self.simtime1,
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

        self.external_sensor = {
                "correlation": [
                    {"temperature": 0.0, "max_charge": 1.0},
                    {"temperature": 10.0, "max_charge": 0.9},
                    {"temperature": 18.0, "max_charge": 0.0}
                ]
            }
        self.charge_control   = ChargeControl("Automatic",
                                                 self.schedule, 
                                                 self.simtime1, 
                                                 0, 
                                                 1, 
                                                 [ 1.0, 0.8 ],
                                                 15.5, None, 
                                                 None, None,
                                                 self.external_conditions,
                                                 self.external_sensor)
        
        self.controls1 = {
            "ctrl11": OnOffTimeControl([True, False, False, True, True, True, True, True],self.simtime, 0, 1),
            "ctrl12": self.charge_control,
            "ctrl13": OnOffTimeControl([True, True, False, False, True, False, True, True],self.simtime, 0, 1)
        }
        
        self.combination_target_charge = {
            'main': {'operation': 'AND', 'controls': ['ctrl11', 'ctrl12']}
           }
        self.combination_target_charge1 = {
            'main': {'operation': 'AND', 'controls': ['ctrl11', 'ctrl13']}
           }
        # Create an instance of CombinationTimeControl
        self.combination_control_target_charge = CombinationTimeControl(
            combination     = self.combination_target_charge,
            controls        = self.controls1,
            simulation_time = self.simtime,
            start_day       = self.start_day,
            time_series_step= self.time_series_step
        )
        
        self.combination_control_target_charge1 = CombinationTimeControl(
            combination     = self.combination_target_charge1,
            controls        = self.controls1,
            simulation_time = self.simtime,
            start_day       = self.start_day,
            time_series_step= self.time_series_step
        )
       
        
        
    def test_is_on(self):
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                self.assertEqual(self.combination_control_on_off.is_on(),
                                 [False, False, False, False, False, False, True, False][t_idx])
    
    def test_setpnt(self):                
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                self.assertEqual(self.combination_control_setpnt.setpnt(),
                                 [None, 52.0, None, None, None, None, 52.0, None][t_idx])
        
    def test_in_required_period(self):
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                self.assertEqual(self.combination_control_req.in_required_period(),
                                 [True,False,False,True,True,False,True,True][t_idx])
                
    def test_is_on_cost(self):
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                self.assertEqual(self.combination_control_on_off_cost.is_on(),
                                  [False,True,False,False,False,False,True,False][t_idx])
    
    def test_target_charge(self):
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                self.assertEqual(self.combination_control_target_charge.target_charge(temp_air=None),
                                  [0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0][t_idx])
                
        
        with self.assertRaises(ValueError):
            self.combination_control_target_charge1.target_charge(temp_air=None)
        
