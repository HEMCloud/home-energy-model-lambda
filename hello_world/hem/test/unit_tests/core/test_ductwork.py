#!/usr/bin/env python3

"""
This module contains unit tests for the Ductwork module
"""

# Standard library imports
import unittest

# Set path to include modules to be tested (must be before local imports)
from unit_tests.common import test_setup
test_setup()

# Local imports
from core.simulation_time import SimulationTime
from core.ductwork import Ductwork,DuctType

class TestDuctType(unittest.TestCase):
    
    def test_from_string(self):
        """ Test that from_string function returns correct Enum values """
        for strval, result in [
            ['intake', DuctType.INTAKE],
            ['supply', DuctType.SUPPLY],
            ['extract', DuctType.EXTRACT],
            ['exhaust', DuctType.EXHAUST],
            ]:
            self.assertEqual(
                DuctType.from_string(strval),
                result,
                "incorrect DuctType returned",
                )


class TestDuctworkCircular(unittest.TestCase):
    """ Unit tests for Ductwork class """

    def setUp(self):
        """ Create Ductwork objects to be tested """
        self.ductwork = Ductwork("circular", None, 0.025, 0.027, 0.4, 0.02, 0.022, False, "exhaust", "inside", 0.4)
        self.ductwork2 = Ductwork("circular", None, 0.025, 0.027, 0.4, 0.02, 0.022, False, "intake", "inside", 0.4)
        self.ductwork3 = Ductwork("circular", None, 0.025, 0.027, 0.4, 0.02, 0.022, False, "supply", "inside", 0.4)
        self.ductwork4 = Ductwork("circular", None, 0.025, 0.027, 0.4, 0.02, 0.022, False, "extract", "inside", 0.4)
        self.ductwork5 = Ductwork("circular", None, 0.025, 0.027, 0.4, 0.02, 0.022, False, "exhaust", "outside", 0.4)
        self.ductwork6 = Ductwork("circular", None, 0.025, 0.027, 0.4, 0.02, 0.022, False, "intake", "outside", 0.4)
        self.ductwork7 = Ductwork("circular", None, 0.025, 0.027, 0.4, 0.02, 0.022, False, "supply", "outside", 0.4)
        self.ductwork8 = Ductwork("circular", None, 0.025, 0.027, 0.4, 0.02, 0.022, False, "extract", "outside", 0.4)
        self.simtime = SimulationTime(0, 8, 1)

    def test_D_ins(self):
        """ Test that correct D_ins value is returned when queried """
        self.assertAlmostEqual(
            self.ductwork._Ductwork__D_ins,
            0.071,
            3,
            "incorrect D_ins returned"
            )

    def test_internal_surface_resistance(self):
        """ Test that correct internal surface resistance value is returned when queried """
        self.assertAlmostEqual(
            self.ductwork._Ductwork__internal_surface_resistance ,
            0.82144,
            5,
            "incorrect internal surface resistance returned"
            )

    def test_insulation_resistance(self):
        """ Test that correct insulation resistance value is returned when queried """
        self.assertAlmostEqual(
            self.ductwork._Ductwork__insulation_resistance,
            8.30633,
            5,
            "incorrect insulation resistance returned"
            )

    def test_external_surface_resistance(self):
        """ Test that correct external surface resistance value is returned when queried """
        self.assertAlmostEqual(
            self.ductwork._Ductwork__external_surface_resistance,
            0.44832,
            5,
            "incorrect external surface resistance returned"
            )

    def test_duct_heat_loss(self):
        """ Test that correct heat loss is returned when queried """
        outside_temp = [20.0, 19.5, 19.0, 18.5, 19.0, 19.5, 20.0, 20.5]
        inside_temp = [5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0, 12.0]
        for t_idx, _, _ in self.simtime:
            with self.subTest(i = t_idx):
                self.assertAlmostEqual(
                    self.ductwork.duct_heat_loss(inside_temp[t_idx], outside_temp[t_idx]),
                    [-0.626560, -0.56390, -0.50125, -0.43859, -0.41771, -0.39682, -0.37594, -0.35505][t_idx],
                    5,
                    "incorrect heat loss returned",
                    )

    def test_total_duct_heat_loss(self):
        """ Test that correct total duct heat loss is returned when queried """
        outside_temp = [10.0] * 4 + [5.0] * 4
        inside_temp = [20.0, 19.5, 19.0, 18.5, 19.0, 19.5, 20.0, 20.5]
        for t_idx, _, _ in self.simtime:
            with self.subTest(i = t_idx):
                self.assertAlmostEqual(
                    self.ductwork.total_duct_heat_loss(inside_temp[t_idx], outside_temp[t_idx]),
                    [-0.1670826785692753, -0.15872854464081157, -0.15037441071234783, -0.14202027678388404,
                     -0.23391574999698542, -0.24226988392544924, -0.250624017853913, -0.25897815178237676,
                    ][t_idx],
                    msg="incorrect total heat loss returned (ductwork1)",
                    )
                self.assertAlmostEqual(
                    self.ductwork2.total_duct_heat_loss(inside_temp[t_idx], outside_temp[t_idx]),
                    [-0.16708267856927533, -0.15872854464081154, -0.1503744107123478, -0.14202027678388404,
                     -0.23391574999698542, -0.24226988392544924, -0.250624017853913, -0.25897815178237676,
                    ][t_idx],
                    msg="incorrect total heat loss returned (ductwork2)",
                    )
                self.assertAlmostEqual(
                    self.ductwork3.total_duct_heat_loss(inside_temp[t_idx], outside_temp[t_idx]),
                    0.0,
                    msg="incorrect total heat loss returned (ductwork3)",
                    )
                self.assertAlmostEqual(
                    self.ductwork4.total_duct_heat_loss(inside_temp[t_idx], outside_temp[t_idx]),
                    0.0,
                    msg="incorrect total heat loss returned (ductwork4)",
                    )
                self.assertAlmostEqual(
                    self.ductwork5.total_duct_heat_loss(inside_temp[t_idx], outside_temp[t_idx]),
                    0.0,
                    msg="incorrect total heat loss returned (ductwork5)",
                    )
                self.assertAlmostEqual(
                    self.ductwork6.total_duct_heat_loss(inside_temp[t_idx], outside_temp[t_idx]),
                    0.0,
                    msg="incorrect total heat loss returned (ductwork6)",
                    )
                self.assertAlmostEqual(
                    self.ductwork7.total_duct_heat_loss(inside_temp[t_idx], outside_temp[t_idx]),
                    [0.1670826785692753, 0.15872854464081157, 0.15037441071234778, 0.14202027678388404,
                     0.2339157499969855, 0.24226988392544924, 0.250624017853913, 0.2589781517823767,
                    ][t_idx],
                    msg="incorrect total heat loss returned (ductwork7)",
                    )
                self.assertAlmostEqual(
                    self.ductwork8.total_duct_heat_loss(inside_temp[t_idx], outside_temp[t_idx]),
                    [0.16708267856927533, 0.15872854464081154, 0.1503744107123478, 0.14202027678388404,
                     0.23391574999698542, 0.24226988392544924, 0.250624017853913, 0.25897815178237676,
                    ][t_idx],
                    msg="incorrect total heat loss returned (ductwork8)",
                    )

class TestDuctworkRectangular(unittest.TestCase):
    """ Unit tests for Ductwork class """

    def setUp(self):
        """ Create Ductwork objects to be tested """
        self.ductwork = Ductwork("rectangular", 0.1, None, None, 0.4, 0.02, 0.022, False, "exhaust", "inside", 0.4)
        self.simtime = SimulationTime(0, 8, 1)

    def test_internal_surface_resistance(self):
        """ Test that correct internal surface resistance value is returned when queried """
        self.assertAlmostEqual(
            self.ductwork._Ductwork__internal_surface_resistance ,
            0.64516,
            5,
            "incorrect internal surface resistance returned"
            )

    def test_insulation_resistance(self):
        """ Test that correct insulation resistance value is returned when queried """
        self.assertAlmostEqual(
            self.ductwork._Ductwork__insulation_resistance,
            5.85106,
            5,
            "incorrect insulation resistance returned"
            )

    def test_external_surface_resistance(self):
        """ Test that correct external surface resistance value is returned when queried """
        self.assertAlmostEqual(
            self.ductwork._Ductwork__external_surface_resistance,
            0.36232,
            5,
            "incorrect external surface resistance returned"
            )

    def test_duct_heat_loss(self):
        """ Test that correct heat loss is returned when queried """
        outside_temp = [20.0, 19.5, 19.0, 18.5, 19.0, 19.5, 20.0, 20.5]
        inside_temp = [5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0, 12.0]
        for t_idx, _, _ in self.simtime:
            with self.subTest(i = t_idx):
                self.assertAlmostEqual(
                    self.ductwork.duct_heat_loss(inside_temp[t_idx], outside_temp[t_idx]),
                    [-0.87482, -0.787339, -0.69986, -0.61237, -0.58321, -0.55405, -0.52489, -0.49573][t_idx],
                    5,
                    "incorrect heat loss returned",
                    )

    def test_total_duct_heat_loss(self):
        """ Test that correct total duct heat loss is returned when queried """
        inside_temp = [20.0, 19.5, 19.0, 18.5, 19.0, 19.5, 20.0, 20.5]
        outside_temp = [5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0, 12.0]
        for t_idx, _, _ in self.simtime:
            with self.subTest(i = t_idx):
                self.assertAlmostEqual(
                    self.ductwork.total_duct_heat_loss(inside_temp[t_idx], outside_temp[t_idx]),
                    [-0.349928, -0.314936, -0.279943, -0.244950, -0.233286, -0.221621, -0.209957, -0.198293][t_idx],
                    5,
                    "incorrect total heat loss returned",
                    )