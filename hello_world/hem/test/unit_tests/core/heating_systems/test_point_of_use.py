#!/usr/bin/env python3

"""
This module contains unit tests for the Instant Electric Heater module
"""

# Standard library imports
import unittest

# Set path to include modules to be tested (must be before local imports)
from unit_tests.common import test_setup
test_setup()

# Local imports
from core.simulation_time import SimulationTime
from core.energy_supply.energy_supply import EnergySupplyConnection, EnergySupply
from core.heating_systems.point_of_use import PointOfUse
from core.water_heat_demand.cold_water_source import ColdWaterSource


class TestPointOfUse(unittest.TestCase):
    """ Unit tests for PointOfUse class """

    def setUp(self):
        """ Create PointOfUse object to be tested """
        self.efficiency         = 1
        self.simtime            = SimulationTime(0, 2, 1)
        self.energysupply       = EnergySupply("electricity", self.simtime)
        self.energysupplyconn   = self.energysupply.connection("shower")
        self.coldwatertemps     = [15, 20, 25]
        self.coldfeed           = ColdWaterSource(self.coldwatertemps, self.simtime, 0, 1)
        self.temp_hot_water     = 55
        
        self.point_of_use = PointOfUse(self.efficiency,
                                       self.energysupplyconn,
                                       self.simtime,
                                       self.coldfeed,
                                       self.temp_hot_water)
    
    def test_demand_hot_water(self):
        ''' Test energy used to meet the temperature demand'''        
        # Test when temp_hot_water is set
        volume_demanded_target = {
                    'temp_hot_water': {
                            'warm_vol': 60
                            }
                    }
        self.assertAlmostEqual(self.point_of_use.demand_hot_water(volume_demanded_target),
                               2.7893333333333334)
    
        # Test when temp_hot_water is not set
        volume_demanded_target = {}
        self.assertAlmostEqual(self.point_of_use.demand_hot_water(volume_demanded_target),
                               0.0)
        
    def test_demand_energy(self):
        ''' Test demand energy for the heater'''
        energy_demand = 2.0
        self.assertAlmostEqual(self.point_of_use.demand_energy(energy_demand),
                               2.0)
        
    
        
        
       