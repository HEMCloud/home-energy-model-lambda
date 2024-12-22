#!/usr/bin/env python3

"""
This module contains unit tests for the heat_battery module
"""

# Standard library imports
import unittest

# Set path to include modules to be tested (must be before local imports)
from unit_tests.common import test_setup
test_setup()

# Local imports
from core.heating_systems.wwhrs import *
from core.simulation_time import SimulationTime
from core.water_heat_demand.cold_water_source import ColdWaterSource

class TestWWHRS_InstantaneousSystemB(unittest.TestCase):

    def setUp(self):
        self.simtime = SimulationTime(0, 2, 1)
        self.cold_water_source = ColdWaterSource(cold_water_temps = [17.0,17.0,17.0],
                                                 simulation_time = self.simtime, 
                                                 start_day = 0,
                                                 time_series_step = 1            
                                                  )
        self.flow_rates = [5, 7, 9, 11, 13]
        self.efficiencies = [44.8, 39.1, 34.8, 31.4, 28.6]
        self.utilisation_factor = 0.7
        
        self.wwhrsb = WWHRS_InstantaneousSystemB(self.flow_rates, 
                                                 self.efficiencies,
                                                 self.cold_water_source, 
                                                 self.utilisation_factor)
        
    def test_return_temperature(self):
        '''Check the return temperature of cold water'''
        
        self.assertAlmostEqual(self.wwhrsb.return_temperature(temp_target = 35.0,
                                                              flowrate_waste_water = 8.0, 
                                                              flowrate_cold_water = 8.0),
                                21.6557)
        
    def test_get_efficiency_from_flowrate(self):
        ''' Check the interpolated efficiency from the flowrate of waste water'''
        
        self.assertAlmostEqual(self.wwhrsb.get_efficiency_from_flowrate(flowrate = 5.0),
                               44.8)

class TestWWHRS_InstantaneousSystemC(unittest.TestCase):

    def setUp(self):
        self.simtime = SimulationTime(0, 2, 1)
        self.cold_water_source = ColdWaterSource(cold_water_temps = [17.1,17.2,17.3],
                                                 simulation_time = self.simtime, 
                                                 start_day = 0,
                                                 time_series_step = 1            
                                                  )
        self.flow_rates = [5, 7, 9, 11, 13]
        self.efficiencies = [44.8, 39.1, 34.8, 31.4, 28.6]
        self.utilisation_factor = 0.7
        
        self.wwhrsc = WWHRS_InstantaneousSystemC(self.flow_rates, 
                                                 self.efficiencies,
                                                 self.cold_water_source, 
                                                 self.utilisation_factor)
        
    def test_return_temperature(self):
        '''Check the return temperature of cold water'''
        
        self.assertAlmostEqual(self.wwhrsc.return_temperature(temp_target = 35.0,
                                                              flowrate_waste_water = 8.0, 
                                                              flowrate_cold_water = 8.0),
                                21.729835)
        
    def test_get_efficiency_from_flowrate(self):
        ''' Check the interpolated efficiency from the flowrate of waste water'''
        
        self.assertAlmostEqual(self.wwhrsc.get_efficiency_from_flowrate(flowrate = 7.0),
                               39.1)
        

class TestWWHRS_InstantaneousSystemA(unittest.TestCase):

    def setUp(self):
        self.simtime = SimulationTime(0, 2, 1)
        self.cold_water_source = ColdWaterSource(cold_water_temps = [17.1,17.2,17.3],
                                                 simulation_time = self.simtime, 
                                                 start_day = 0,
                                                 time_series_step = 1            
                                                  )
        self.flow_rates = [5, 7, 9, 11, 13]
        self.efficiencies = [44.8, 39.1, 34.8, 31.4, 28.6]
        self.utilisation_factor = 0.7
        
        self.wwhrsa = WWHRS_InstantaneousSystemA(self.flow_rates, 
                                                 self.efficiencies,
                                                 self.cold_water_source, 
                                                 self.utilisation_factor)
        
    def test_return_temperature(self):
        '''Check the return temperature of cold water'''
        
        self.assertAlmostEqual(self.wwhrsa.return_temperature(temp_target = 35.0,
                                                              flowrate_waste_water = 8.0, 
                                                              flowrate_cold_water = 8.0),
                               21.729835)
        
    def test_get_efficiency_from_flowrate(self):
        ''' Check the interpolated efficiency from the flowrate of waste water'''
        
        self.assertAlmostEqual(self.wwhrsa.get_efficiency_from_flowrate(flowrate = 8.0),
                               36.95)