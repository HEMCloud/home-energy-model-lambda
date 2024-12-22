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
from core.heating_systems.instant_elec_heater import InstantElecHeater
from core.controls.time_control import SetpointTimeControl

class TestInstantElecHeater(unittest.TestCase):
    """ Unit tests for InstantElecHeater class """

    def setUp(self):
        """ Create InstantElecHeater object to be tested """
        self.simtime            = SimulationTime(0, 4, 1)
        energysupply            = EnergySupply("electricity", self.simtime)
        energysupplyconn        = energysupply.connection("shower")
        control                 = SetpointTimeControl([21.0, 21.0, None, 21.0],self.simtime,0, 1.0)
        self.inselecheater      = InstantElecHeater(50, 0.4, energysupplyconn, self.simtime, control)

    def test_demand_energy(self):
        """ Test that InstantElecHeater object returns correct energy supplied """
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                self.assertEqual(
                    self.inselecheater.demand_energy([40.0, 100.0, 30.0, 20.0][t_idx]),
                    [40.0, 50.0, 0.0, 20.0][t_idx],
                    "incorrect energy supplied returned",
                    )

    def test_temp_setpnt(self):
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                self.assertEqual(self.inselecheater.temp_setpnt(),
                                 [21.0,21.0,None,21.0][t_idx])

    def test_in_required_period(self):
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                self.assertEqual(self.inselecheater.in_required_period(),
                                 [True,True,False,True][t_idx])

    def test_frac_convective(self):
        self.assertEqual(self.inselecheater.frac_convective(),0.4)

    def test_energy_output_min(self):
        self.assertEqual(self.inselecheater.energy_output_min(), 0.0)

