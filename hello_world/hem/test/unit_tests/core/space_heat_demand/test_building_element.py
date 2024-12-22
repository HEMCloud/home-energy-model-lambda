#!/usr/bin/env python3

"""
This module contains unit tests for the building_element module
"""

# Standard library imports
import unittest

# Set path to include modules to be tested (must be before local imports)
from unit_tests.common import test_setup

test_setup()

# Local imports
from core.external_conditions import ExternalConditions
from core.simulation_time import SimulationTime
from core.space_heat_demand.building_element import (
    BuildingElement,
    BuildingElementAdjacentZTC,
    BuildingElementAdjacentZTU_Simple,
    BuildingElementGround,
    BuildingElementOpaque,
    BuildingElementTransparent,
    HeatFlowDirection,
    HeatTransferInternal,
    HeatTransferOtherSide,
)


class TestBuildingElement(unittest.TestCase):
    """Unit tests for BuildingElement class"""

    def setUp(self):
        self.simtime = SimulationTime(0, 4, 1)

        external_conditions = None

        self.be_a = BuildingElement(external_conditions, area=3.0, pitch=0)  # a_sol=0.6, f_sky=0)
        self.be_b = BuildingElement(external_conditions, area=6.0, pitch=45)  # a_sol=0.7, f_sky=0.5)
        self.be_c = BuildingElement(external_conditions, area=6.0, pitch=90)  # a_sol=0.7, f_sky=0.5)
        self.be_d = BuildingElement(external_conditions, area=6.0, pitch=180)  # a_sol=0.7, f_sky=0.5)


class TestHeatTransferInternal(unittest.TestCase):
    """Unit tests for HeatTransferInternal class"""

    def setUp(self):
        self.be_a = HeatTransferInternal()
        self.be_a._pitch = 0
        self.be_b = HeatTransferInternal()
        self.be_b._pitch = 45
        self.be_c = HeatTransferInternal()
        self.be_c._pitch = 90
        self.be_d = HeatTransferInternal()
        self.be_d._pitch = 180

    def test_heat_flow_direction(self):

        self.assertEqual(self.be_b.heat_flow_direction(20, 25), HeatFlowDirection.DOWNWARDS)

        self.assertEqual(self.be_c.heat_flow_direction(20, 25), HeatFlowDirection.HORIZONTAL)

        self.assertEqual(self.be_d.heat_flow_direction(20, 25), HeatFlowDirection.UPWARDS)

    def test_convert_uvalue_to_resistance(self):

        self.assertEqual(self.be_a.convert_uvalue_to_resistance(1, 180), 0.7870483926665635)

    def test_r_si(self):
        self.assertEqual(self.be_a.r_si(), 0.0987166831194472)

    def test_r_si_pitch(self):

        # r_si_horizontal
        result = self.be_a._HeatTransferInternal__r_si(90.0)
        self.assertEqual(result, 0.1310615989515072)

        # r_si_upwards
        result = self.be_a._HeatTransferInternal__r_si(30.0)
        self.assertEqual(result, 0.0987166831194472)

        # r_si_downwards
        result = self.be_a._HeatTransferInternal__r_si(150.0)
        self.assertEqual(result, 0.17152658662092624)

    def test_pitch_class(self):
        self.assertEqual(self.be_a.pitch_class(90.0), HeatFlowDirection.HORIZONTAL)
        self.assertEqual(self.be_a.pitch_class(30.0), HeatFlowDirection.UPWARDS)
        self.assertEqual(self.be_a.pitch_class(150.0), HeatFlowDirection.DOWNWARDS)

    def test_h_ri(self):
        self.assertEqual(self.be_a.h_ri(), 5.13)


class TestHeatTransferOtherSide(unittest.TestCase):
    """Unit tests for HeatTransferOtherSide class"""

    def setUp(self):
        self.be_a = HeatTransferOtherSide(f_sky=0)
        self.be_b = HeatTransferOtherSide(f_sky=0.5)
        self.be_c = HeatTransferOtherSide(f_sky=0.5)
        self.be_d = HeatTransferOtherSide(f_sky=0.5)

    def test_r_se(self):
        self.assertEqual(self.be_a.r_se(), 0.041425020712510356)

    def test_h_ce(self):
        self.assertEqual(self.be_a.h_ce(), 20.0)

    def test_h_re(self):
        self.assertEqual(self.be_a.h_re(), 4.14)


class TestBuildingElementOpaque(unittest.TestCase):
    """Unit tests for BuildingElementOpaque class"""

    def setUp(self):
        """Create BuildingElementOpaque objects to be tested"""
        self.simtime = SimulationTime(0, 4, 1)
        ec = ExternalConditions(
            self.simtime,
            [0.0, 5.0, 10.0, 15.0],
            None,
            None,
            [0.0] * 4,  # Diffuse horizontal radiation
            [0.0] * 4,  # Direct beam radiation
            None,
            55.0,  # Latitude
            0.0,  # Longitude
            0.0,  # Timezone
            0,  # Start day
            None,
            1,  # Time-series step,
            None,
            None,
            None,
            None,
            None,
        )
        # TODO implement rest of external conditions in unit tests

        # Create an object for each mass distribution class
        be_I = BuildingElementOpaque(20, False, 180, 0.60, 0.25, 19000.0, "I", 0, 0, 2, 10, ec)
        be_E = BuildingElementOpaque(22.5, False, 135, 0.61, 0.50, 18000.0, "E", 180, 0, 2.25, 10, ec)
        be_IE = BuildingElementOpaque(25, False, 90, 0.62, 0.75, 17000.0, "IE", 90, 0, 2.5, 10, ec)
        be_D = BuildingElementOpaque(27.5, True, 45, 0.63, 0.80, 16000.0, "D", -90, 0, 2.75, 10, ec)
        be_M = BuildingElementOpaque(30, False, 0, 0.64, 0.40, 15000.0, "M", 0, 0, 3, 10, ec)

        # Put objects in a list that can be iterated over
        self.test_be_objs = [be_I, be_E, be_IE, be_D, be_M]

    def test_no_of_nodes(self):
        """Test that number of nodes (total and inside) have been calculated correctly"""
        for i, be in enumerate(self.test_be_objs):
            with self.subTest(i=i):
                self.assertEqual(be.no_of_nodes(), 5, "incorrect number of nodes")
                self.assertEqual(be.no_of_inside_nodes(), 3, "incorrect number of inside nodes")

    def test_area(self):
        """Test that correct area is returned when queried"""
        # Define increment between test cases
        area_inc = 2.5

        for i, be in enumerate(self.test_be_objs):
            with self.subTest(i=i):
                self.assertAlmostEqual(be.area, 20.0 + i * area_inc, msg="incorrect area returned")

    def test_heat_flow_direction(self):
        """Test that correct heat flow direction is returned when queried"""
        temp_int_air = 20.0
        temp_int_surface = [19.0, 21.0, 22.0, 21.0, 19.0]
        results = [
            HeatFlowDirection.DOWNWARDS,
            HeatFlowDirection.UPWARDS,
            HeatFlowDirection.HORIZONTAL,
            HeatFlowDirection.DOWNWARDS,
            HeatFlowDirection.UPWARDS,
        ]

        for i, be in enumerate(self.test_be_objs):
            with self.subTest(i=i):
                self.assertAlmostEqual(
                    be.heat_flow_direction(temp_int_air, temp_int_surface[i]),
                    results[i],
                    msg="incorrect heat flow direction returned",
                )

    def test_r_si(self):
        """Test that correct r_si is returned when queried"""
        results = [0.17, 0.17, 0.13, 0.10, 0.10]

        for i, be in enumerate(self.test_be_objs):
            with self.subTest(i=i):
                self.assertAlmostEqual(be.r_si(), results[i], 2, msg="incorrect r_si returned")

    def test_h_ci(self):
        """Test that correct h_ci is returned when queried"""
        temp_int_air = 20.0
        temp_int_surface = [19.0, 21.0, 22.0, 21.0, 19.0]
        results = [0.7, 5.0, 2.5, 0.7, 5.0]

        for i, be in enumerate(self.test_be_objs):
            with self.subTest(i=i):
                self.assertAlmostEqual(
                    be.h_ci(temp_int_air, temp_int_surface[i]), results[i], msg="incorrect h_ci returned"
                )

    def test_h_ri(self):
        """Test that correct h_ri is returned when queried"""
        for i, be in enumerate(self.test_be_objs):
            with self.subTest(i=i):
                self.assertAlmostEqual(be.h_ri(), 5.13, msg="incorrect h_ri returned")

    def test_h_ce(self):
        """Test that correct h_ce is returned when queried"""
        for i, be in enumerate(self.test_be_objs):
            with self.subTest(i=i):
                self.assertAlmostEqual(be.h_ce(), 20.0, msg="incorrect h_ce returned")

    def test_h_re(self):
        """Test that correct h_re is returned when queried"""
        for i, be in enumerate(self.test_be_objs):
            with self.subTest(i=i):
                self.assertAlmostEqual(be.h_re(), 4.14, msg="incorrect h_re returned")

    def test_a_sol(self):
        """Test that correct a_sol is returned when queried"""
        # Define increment between test cases
        a_sol_inc = 0.01

        for i, be in enumerate(self.test_be_objs):
            with self.subTest(i=i):
                self.assertAlmostEqual(be.a_sol, 0.6 + i * a_sol_inc, msg="incorrect a_sol returned")

    def test_therm_rad_to_sky(self):
        """Test that correct therm_rad_to_sky is returned when queried"""
        results = [0.0, 6.6691785923823135, 22.77, 38.87082140761768, 45.54]

        for i, be in enumerate(self.test_be_objs):
            with self.subTest(i=i):
                self.assertAlmostEqual(
                    be.therm_rad_to_sky,
                    results[i],
                    msg="incorrect therm_rad_to_sky returned",
                )

    def test_h_pli(self):
        """Test that correct h_pli list is returned when queried"""
        results = [
            [24.0, 12.0, 12.0, 24.0],
            [12.0, 6.0, 6.0, 12.0],
            [8.0, 4.0, 4.0, 8.0],
            [7.5, 3.75, 3.75, 7.5],
            [15.0, 7.5, 7.5, 15.0],
        ]
        for i, be in enumerate(self.test_be_objs):
            for j in range(0, be.no_of_nodes()-1):
                with self.subTest(i=i*(be.no_of_nodes()-1) + j):
                    self.assertEqual(be.h_pli(j), results[i][j], "incorrect h_pli returned")

    def test_k_pli(self):
        """Test that correct k_pli list is returned when queried"""
        results = [
            [0.0, 0.0, 0.0, 0.0, 19000.0],
            [18000.0, 0.0, 0.0, 0.0, 0.0],
            [8500.0, 0.0, 0.0, 0.0, 8500.0],
            [2000.0, 4000.0, 4000.0, 4000.0, 2000.0],
            [0.0, 0.0, 15000.0, 0.0, 0.0],
        ]
        for i, be in enumerate(self.test_be_objs):
            with self.subTest(i=i):
                self.assertEqual(be.k_pli, results[i], "incorrect k_pli list returned")

    def test_temp_ext(self):
        """Test that the correct external temperature is returned when queried"""
        for i, be in enumerate(self.test_be_objs):
            for t_idx, _, _ in self.simtime:
                with self.subTest(i=i * t_idx):
                    self.assertEqual(be.temp_ext(), t_idx * 5.0, "incorrect ext temp returned")

    def test_fabric_heat_loss(self):
        """Test that the correct fabric heat loss is returned when queried"""
        results = [43.20, 31.56, 27.10, 29.25, 55.54]

        for i, be in enumerate(self.test_be_objs):
            with self.subTest(i=i):
                self.assertAlmostEqual(be.fabric_heat_loss(), results[i], 2, "incorrect fabric heat loss returned")

    def test_heat_capacity(self):
        """Test that the correct heat capacity is returned when queried"""
        results = [380, 405, 425, 440, 450]

        for i, be in enumerate(self.test_be_objs):
            with self.subTest(i=i):
                self.assertEqual(be.heat_capacity(), results[i], "incorrect heat capacity returned")


class TestBuildingElementAdjacentZTC(unittest.TestCase):
    """Unit tests for BuildingElementAdjacentZTC class"""

    def setUp(self):
        """Create BuildingElementAdjacentZTC objects to be tested"""
        self.simtime = SimulationTime(0, 4, 1)
        ec = ExternalConditions(
            self.simtime,
            [0.0, 5.0, 10.0, 15.0],
            None,
            None,
            [0.0] * 4,  # Diffuse horizontal radiation
            [0.0] * 4,  # Direct beam radiation
            None,
            55.0,  # Latitude
            0.0,  # Longitude
            0.0,  # Timezone
            0,  # Start day
            None,
            1,  # Time-series step
            None,
            None,
            None,
            None,
            None,
        )
        # Create an object for each mass distribution class
        be_I = BuildingElementAdjacentZTC(20.0, 180, 0.25, 19000.0, "I", ec)
        be_E = BuildingElementAdjacentZTC(22.5, 135, 0.50, 18000.0, "E", ec)
        be_IE = BuildingElementAdjacentZTC(25.0, 90, 0.75, 17000.0, "IE", ec)
        be_D = BuildingElementAdjacentZTC(27.5, 45, 0.80, 16000.0, "D", ec)
        be_M = BuildingElementAdjacentZTC(30.0, 0, 0.40, 15000.0, "M", ec)

        # Put objects in a list that can be iterated over
        self.test_be_objs = [be_I, be_E, be_IE, be_D, be_M]

    def test_no_of_nodes(self):
        """Test that number of nodes (total and inside) have been calculated correctly"""
        for i, be in enumerate(self.test_be_objs):
            with self.subTest(i=i):
                self.assertEqual(be.no_of_nodes(), 5, "incorrect number of nodes")
                self.assertEqual(be.no_of_inside_nodes(), 3, "incorrect number of inside nodes")

    def test_area(self):
        """Test that correct area is returned when queried"""
        # Define increment between test cases
        area_inc = 2.5

        for i, be in enumerate(self.test_be_objs):
            with self.subTest(i=i):
                self.assertAlmostEqual(be.area, 20.0 + i * area_inc, msg="incorrect area returned")

    def test_heat_flow_direction(self):
        """Test that correct heat flow direction is returned when queried"""
        temp_int_air = 20.0
        temp_int_surface = [19.0, 21.0, 22.0, 21.0, 19.0]
        results = [
            HeatFlowDirection.DOWNWARDS,
            HeatFlowDirection.UPWARDS,
            HeatFlowDirection.HORIZONTAL,
            HeatFlowDirection.DOWNWARDS,
            HeatFlowDirection.UPWARDS,
        ]

        for i, be in enumerate(self.test_be_objs):
            with self.subTest(i=i):
                self.assertAlmostEqual(
                    be.heat_flow_direction(temp_int_air, temp_int_surface[i]),
                    results[i],
                    msg="incorrect heat flow direction returned",
                )

    def test_r_si(self):
        """Test that correct r_si is returned when queried"""
        results = [0.17, 0.17, 0.13, 0.10, 0.10]

        for i, be in enumerate(self.test_be_objs):
            with self.subTest(i=i):
                self.assertAlmostEqual(be.r_si(), results[i], 2, msg="incorrect r_si returned")

    def test_h_ci(self):
        """Test that correct h_ci is returned when queried"""
        temp_int_air = 20.0
        temp_int_surface = [19.0, 21.0, 22.0, 21.0, 19.0]
        results = [0.7, 5.0, 2.5, 0.7, 5.0]

        for i, be in enumerate(self.test_be_objs):
            with self.subTest(i=i):
                self.assertAlmostEqual(
                    be.h_ci(temp_int_air, temp_int_surface[i]), results[i], msg="incorrect h_ci returned"
                )

    def test_h_ri(self):
        """Test that correct h_ri is returned when queried"""
        for i, be in enumerate(self.test_be_objs):
            with self.subTest(i=i):
                self.assertAlmostEqual(be.h_ri(), 5.13, msg="incorrect h_ri returned")

    def test_h_ce(self):
        """Test that correct h_ce is returned when queried"""
        for i, be in enumerate(self.test_be_objs):
            with self.subTest(i=i):
                self.assertAlmostEqual(be.h_ce(), 0.0, msg="incorrect h_ce returned")

    def test_h_re(self):
        """Test that correct h_re is returned when queried"""
        for i, be in enumerate(self.test_be_objs):
            with self.subTest(i=i):
                self.assertAlmostEqual(be.h_re(), 0.0, msg="incorrect h_re returned")

    def test_a_sol(self):
        """Test that correct a_sol is returned when queried"""
        for i, be in enumerate(self.test_be_objs):
            with self.subTest(i=i):
                self.assertAlmostEqual(be.a_sol, 0.0, msg="incorrect a_sol returned")

    def test_therm_rad_to_sky(self):
        """Test that correct therm_rad_to_sky is returned when queried"""
        for i, be in enumerate(self.test_be_objs):
            with self.subTest(i=i):
                self.assertAlmostEqual(
                    be.therm_rad_to_sky,
                    0.0,
                    msg="incorrect therm_rad_to_sky returned",
                )

    def test_h_pli(self):
        """Test that correct h_pli list is returned when queried"""
        results = [
            [24.0, 12.0, 12.0, 24.0],
            [12.0, 6.0, 6.0, 12.0],
            [8.0, 4.0, 4.0, 8.0],
            [7.5, 3.75, 3.75, 7.5],
            [15.0, 7.5, 7.5, 15.0],
        ]
        for i, be in enumerate(self.test_be_objs):
            for j in range(be.no_of_nodes()-1):
                with self.subTest(i=i*(be.no_of_nodes()-1) + j):
                    self.assertEqual(be.h_pli(j), results[i][j], "incorrect h_pli returned")

    def test_k_pli(self):
        """Test that correct k_pli list is returned when queried"""
        results = [
            [0.0, 0.0, 0.0, 0.0, 19000.0],
            [18000.0, 0.0, 0.0, 0.0, 0.0],
            [8500.0, 0.0, 0.0, 0.0, 8500.0],
            [2000.0, 4000.0, 4000.0, 4000.0, 2000.0],
            [0.0, 0.0, 15000.0, 0.0, 0.0],
        ]
        for i, be in enumerate(self.test_be_objs):
            with self.subTest(i=i):
                self.assertEqual(be.k_pli, results[i], "incorrect k_pli list returned")

    # No test for temp_ext - not relevant as the external wall bounds ZTC not the external environment

    def test_fabric_heat_loss(self):
        """Test that the correct fabric heat loss is returned when queried"""
        results = [0.0, 0.0, 0.0, 0.0, 0.0]

        for i, be in enumerate(self.test_be_objs):
            with self.subTest(i=i):
                self.assertEqual(be.fabric_heat_loss(), results[i], "incorrect fabric heat loss returned")

    def test_heat_capacity(self):
        """Test that the correct heat capacity is returned when queried"""
        results = [380, 405, 425, 440, 450]

        for i, be in enumerate(self.test_be_objs):
            with self.subTest(i=i):
                self.assertEqual(be.heat_capacity(), results[i], "incorrect heat capacity returned")


class TestBuildingElementGround(unittest.TestCase):
    """Unit tests for BuildingElementGround class"""

    def setUp(self):
        """Create BuildingElementGround objects to be tested"""
        self.simtime = SimulationTime(742, 746, 1)

        air_temp_day_Jan = [
            0.0,
            0.5,
            1.0,
            1.5,
            2.0,
            2.5,
            3.0,
            3.5,
            4.0,
            4.5,
            5.0,
            7.5,
            10.0,
            12.5,
            15.0,
            19.5,
            17.0,
            15.0,
            12.0,
            10.0,
            7.0,
            5.0,
            3.0,
            1.0,
        ]
        air_temp_day_Feb = [x + 1.0 for x in air_temp_day_Jan]
        air_temp_day_Mar = [x + 2.0 for x in air_temp_day_Jan]
        air_temp_day_Apr = [x + 3.0 for x in air_temp_day_Jan]
        air_temp_day_May = [x + 4.0 for x in air_temp_day_Jan]
        air_temp_day_Jun = [x + 5.0 for x in air_temp_day_Jan]
        air_temp_day_Jul = [x + 6.0 for x in air_temp_day_Jan]
        air_temp_day_Aug = [x + 6.0 for x in air_temp_day_Jan]
        air_temp_day_Sep = [x + 5.0 for x in air_temp_day_Jan]
        air_temp_day_Oct = [x + 4.0 for x in air_temp_day_Jan]
        air_temp_day_Nov = [x + 3.0 for x in air_temp_day_Jan]
        air_temp_day_Dec = [x + 2.0 for x in air_temp_day_Jan]

        airtemp = []
        airtemp.extend(air_temp_day_Jan * 31)
        airtemp.extend(air_temp_day_Feb * 28)
        airtemp.extend(air_temp_day_Mar * 31)
        airtemp.extend(air_temp_day_Apr * 30)
        airtemp.extend(air_temp_day_May * 31)
        airtemp.extend(air_temp_day_Jun * 30)
        airtemp.extend(air_temp_day_Jul * 31)
        airtemp.extend(air_temp_day_Aug * 31)
        airtemp.extend(air_temp_day_Sep * 30)
        airtemp.extend(air_temp_day_Oct * 31)
        airtemp.extend(air_temp_day_Nov * 30)
        airtemp.extend(air_temp_day_Dec * 31)

        ec = ExternalConditions(
            self.simtime,
            airtemp,
            [2] * 8760,
            [180] * 8760,
            [0.0] * 8760,  # Diffuse horizontal radiation
            [0.0] * 8760,  # Direct beam radiation
            None,
            55.0,  # Latitude
            0.0,  # Longitude
            0.0,  # Timezone
            0,  # Start day
            None,
            1,  # Time-series step
            None,
            None,
            None,
            None,
            None,
        )
        # TODO implement rest of external conditions in unit tests

        # Create an object for each mass distribution class
        be_I = BuildingElementGround(
            total_area=20.0,
            area=20.0,
            pitch=180,
            u_value=1.5,
            r_f=0.1,
            k_m=19000.0,
            mass_distribution_class="I",
            floor_type="Suspended_floor",
            edge_insulation=None,
            h_upper=0.5,
            u_f_s=None,
            u_w=0.5,
            area_per_perimeter_vent=0.01,
            shield_fact_location="Sheltered",
            d_we=0.3,
            r_f_ins=7,
            z_b=None,
            r_w_b=None,
            h_w=None,
            perimeter=18.0,
            psi_wall_floor_junc=0.5,
            ext_cond=ec,
            simulation_time=self.simtime,
        )
        be_E = BuildingElementGround(
            total_area=22.5,
            area=22.5,
            pitch=135,
            u_value=1.4,
            r_f=0.2,
            k_m=18000.0,
            mass_distribution_class="E",
            floor_type="Slab_no_edge_insulation",
            edge_insulation=None,
            h_upper=None,
            u_f_s=None,
            u_w=None,
            area_per_perimeter_vent=None,
            shield_fact_location=None,
            d_we=0.3,
            r_f_ins=None,
            z_b=None,
            r_w_b=None,
            h_w=None,
            perimeter=19.0,
            psi_wall_floor_junc=0.6,
            ext_cond=ec,
            simulation_time=self.simtime,
        )
        be_IE = BuildingElementGround(
            total_area=25.0,
            area=25.0,
            pitch=90,
            u_value=1.33,
            r_f=0.2,
            k_m=17000.0,
            mass_distribution_class="IE",
            floor_type="Slab_edge_insulation",
            edge_insulation=[
                {"type": "horizontal", "width": 3.0, "edge_thermal_resistance": 2.0},
                {"type": "vertical", "depth": 1.0, "edge_thermal_resistance": 2.0},
            ],
            h_upper=None,
            u_f_s=None,
            u_w=None,
            area_per_perimeter_vent=None,
            shield_fact_location=None,
            d_we=0.3,
            r_f_ins=None,
            z_b=None,
            r_w_b=None,
            h_w=None,
            perimeter=20.0,
            psi_wall_floor_junc=0.7,
            ext_cond=ec,
            simulation_time=self.simtime,
        )
        be_D = BuildingElementGround(
            total_area=27.5,
            area=27.5,
            pitch=45,
            u_value=1.25,
            r_f=0.2,
            k_m=16000.0,
            mass_distribution_class="D",
            floor_type="Heated_basement",
            edge_insulation=None,
            h_upper=None,
            u_f_s=None,
            u_w=None,
            area_per_perimeter_vent=None,
            shield_fact_location=None,
            d_we=0.3,
            r_f_ins=None,
            z_b=2.3,
            r_w_b=6,
            h_w=None,
            perimeter=21.0,
            psi_wall_floor_junc=0.8,
            ext_cond=ec,
            simulation_time=self.simtime,
        )
        be_M = BuildingElementGround(
            total_area=30.0,
            area=30.0,
            pitch=0,
            u_value=1.0,
            r_f=0.3,
            k_m=15000.0,
            mass_distribution_class="M",
            floor_type="Unheated_basement",
            edge_insulation=None,
            h_upper=None,
            u_f_s=1.2,
            u_w=0.5,
            area_per_perimeter_vent=None,
            shield_fact_location=None,
            d_we=0.3,
            r_f_ins=None,
            z_b=2.3,
            r_w_b=0.15,
            h_w=2.3,
            perimeter=22.0,
            psi_wall_floor_junc=0.9,
            ext_cond=ec,
            simulation_time=self.simtime,
        )

        # Put objects in a list that can be iterated over
        self.test_be_objs = [be_I, be_E, be_IE, be_D, be_M]

    def test_no_of_nodes(self):
        """Test that number of nodes (total and inside) have been calculated correctly"""
        for i, be in enumerate(self.test_be_objs):
            with self.subTest(i=i):
                self.assertEqual(be.no_of_nodes(), 5, "incorrect number of nodes")
                self.assertEqual(be.no_of_inside_nodes(), 3, "incorrect number of inside nodes")

    def test_area(self):
        """Test that correct area is returned when queried"""
        # Define increment between test cases
        area_inc = 2.5

        for i, be in enumerate(self.test_be_objs):
            with self.subTest(i=i):
                self.assertAlmostEqual(be.area, 20.0 + i * area_inc, msg="incorrect area returned")

    def test_heat_flow_direction(self):
        """Test that correct heat flow direction is returned when queried"""
        temp_int_air = 20.0
        temp_int_surface = [19.0, 21.0, 22.0, 21.0, 19.0]
        results = [
            HeatFlowDirection.DOWNWARDS,
            HeatFlowDirection.UPWARDS,
            HeatFlowDirection.HORIZONTAL,
            HeatFlowDirection.DOWNWARDS,
            HeatFlowDirection.UPWARDS,
        ]

        for i, be in enumerate(self.test_be_objs):
            with self.subTest(i=i):
                self.assertEqual(
                    be.heat_flow_direction(temp_int_air, temp_int_surface[i]),
                    results[i],
                    msg="incorrect heat flow direction returned",
                )

    def test_r_si(self):
        """Test that correct r_si is returned when queried"""
        results = [0.17, 0.17, 0.13, 0.10, 0.10]

        for i, be in enumerate(self.test_be_objs):
            with self.subTest(i=i):
                self.assertAlmostEqual(be.r_si(), results[i], 2, msg="incorrect r_si returned")

    def test_h_ci(self):
        """Test that correct h_ci is returned when queried"""
        temp_int_air = 20.0
        temp_int_surface = [19.0, 21.0, 22.0, 21.0, 19.0]
        results = [0.7, 5.0, 2.5, 0.7, 5.0]

        for i, be in enumerate(self.test_be_objs):
            with self.subTest(i=i):
                self.assertAlmostEqual(
                    be.h_ci(temp_int_air, temp_int_surface[i]), results[i], msg="incorrect h_ci returned"
                )

    def test_h_ri(self):
        """Test that correct h_ri is returned when queried"""
        for i, be in enumerate(self.test_be_objs):
            with self.subTest(i=i):
                self.assertAlmostEqual(be.h_ri(), 5.13, msg="incorrect h_ri returned")

    def test_h_ce(self):
        """Test that correct h_ce is returned when queried"""
        results = [15.78947368, 91.30434783, 20.59886422, 10.34482759, 5.084745763]

        for i, be in enumerate(self.test_be_objs):
            with self.subTest(i=i):
                self.assertAlmostEqual(be.h_ce(), results[i], msg="incorrect h_ce returned")

    def test_h_re(self):
        """Test that correct h_re is returned when queried"""
        # Define increment between test cases
        h_re_inc = 0.01

        for i, be in enumerate(self.test_be_objs):
            with self.subTest(i=i):
                self.assertAlmostEqual(be.h_re(), 0.0, msg="incorrect h_re returned")

    def test_a_sol(self):
        """Test that correct a_sol is returned when queried"""
        for i, be in enumerate(self.test_be_objs):
            with self.subTest(i=i):
                self.assertAlmostEqual(be.a_sol, 0.0, msg="incorrect a_sol returned")

    def test_therm_rad_to_sky(self):
        """Test that correct therm_rad_to_sky is returned when queried"""
        for i, be in enumerate(self.test_be_objs):
            with self.subTest(i=i):
                self.assertAlmostEqual(
                    be.therm_rad_to_sky,
                    0.0,
                    msg="incorrect therm_rad_to_sky returned",
                )

    def test_h_pli(self):
        """Test that correct h_pli list is returned when queried"""
        results = [
            [6.0, 5.217391304347826, 20.0, 40.0],
            [6.0, 4.615384615384615, 10.0, 20.0],
            [6.0, 4.615384615384615, 10.0, 20.0],
            [6.0, 4.615384615384615, 10.0, 20.0],
            [6.0, 4.137931034482759, 6.666666666666667, 13.333333333333334],
        ]
        for i, be in enumerate(self.test_be_objs):
            for j in range(be.no_of_nodes()-1):
                with self.subTest(i=i*(be.no_of_nodes()-1) + j):
                    self.assertEqual(be.h_pli(j), results[i][j], "incorrect h_pli returned")

    def test_k_pli(self):
        """Test that correct k_pli list is returned when queried"""
        results = [
            [0.0, 1500000.0, 0.0, 0.0, 19000.0],
            [0.0, 1500000.0, 18000.0, 0.0, 0.0],
            [0.0, 1500000.0, 8500.0, 0.0, 8500.0],
            [0.0, 1500000.0, 4000.0, 8000.0, 4000.0],
            [0.0, 1500000.0, 0.0, 15000.0, 0.0],
        ]
        for i, be in enumerate(self.test_be_objs):
            with self.subTest(i=i):
                self.assertEqual(be.k_pli, results[i], "incorrect k_pli list returned")

    def test_temp_ext(self):
        """Test that the correct external temperature is returned when queried"""
        results = [
            [-0.6471789638993641, -0.6471789638993641, 2.505131315506123, 2.505131315506123],
            [7.428039862980361, 7.428039862980361, 8.234778286483786, 8.234778286483786],
            [7.732888552541917, 7.732888552541917, 8.448604706949336, 8.448604706949336],
            [8.366361777378224, 8.366361777378224, 8.86671506616569, 8.86671506616569],
            [6.293446005722892, 6.293446005722892, 7.413004622032444, 7.413004622032444],
        ]
        for t_idx, _, _ in self.simtime:
            for i, be in enumerate(self.test_be_objs):
                with self.subTest(i=i + len(self.test_be_objs) * t_idx):
                    self.assertEqual(be.temp_ext(), results[i][t_idx], "incorrect ext temp returned")

    def test_fabric_heat_loss(self):
        """Test that the correct fabric heat loss is returned when queried"""
        for i, be in enumerate(self.test_be_objs):
            with self.subTest(i=i):
                self.assertAlmostEqual(
                    be.fabric_heat_loss(),
                    [30.0, 31.5, 33.25, 34.375, 30.0][i],
                    2,
                    "incorrect fabric heat loss returned",
                )

    def test_heat_capacity(self):
        """Test that the correct heat capacity is returned when queried"""
        results = [380, 405, 425, 440, 450]

        for i, be in enumerate(self.test_be_objs):
            with self.subTest(i=i):
                self.assertEqual(be.heat_capacity(), results[i], "incorrect heat capacity returned")


class TestBuildingElementTransparent(unittest.TestCase):
    """Unit tests for BuildingElementTransparent class"""

    def setUp(self):
        """Create BuildingElementTransparent object to be tested"""
        self.simtime = SimulationTime(0, 4, 1)
        ec = ExternalConditions(
            self.simtime,
            [0.0, 5.0, 10.0, 15.0],
            None,
            None,
            [0.0] * 4,  # Diffuse horizontal radiation
            [0.0] * 4,  # Direct beam radiation
            None,
            55.0,  # Latitude
            0.0,  # Longitude
            0.0,  # Timezone
            0,  # Start day
            None,
            1,  # Time-series step
            None,
            None,
            None,
            None,
            None,
        )
        # TODO implement rest of external conditions in unit tests
        self.be = BuildingElementTransparent(90, 0.4, 180, 0.75, 0.25, 1, 1.25, 4, False, None, ec, self.simtime)

    def test_no_of_nodes(self):
        """Test that number of nodes (total and inside) have been calculated correctly"""
        self.assertEqual(self.be.no_of_nodes(), 2, "incorrect number of nodes")
        self.assertEqual(self.be.no_of_inside_nodes(), 0, "incorrect number of inside nodes")

    def test_area(self):
        """Test that correct area is returned when queried"""
        self.assertEqual(self.be.area, 5.0, "incorrect area returned")

    def test_heat_flow_direction(self):
        """Test that correct heat flow direction is returned when queried"""
        self.assertEqual(
            self.be.heat_flow_direction(None, None),
            HeatFlowDirection.HORIZONTAL,
            "incorrect heat flow direction returned",
        )

    def test_r_si(self):
        """Test that correct r_si is returned when queried"""
        self.assertAlmostEqual(self.be.r_si(), 0.13, 2, "incorrect r_si returned")

    def test_h_ci(self):
        """Test that correct h_ci is returned when queried"""
        self.assertEqual(self.be.h_ci(None, None), 2.5, "incorrect h_ci returned")

    def test_h_ri(self):
        """Test that correct h_ri is returned when queried"""
        self.assertEqual(self.be.h_ri(), 5.13, "incorrect h_ri returned")

    def test_h_ce(self):
        """Test that correct h_ce is returned when queried"""
        self.assertEqual(self.be.h_ce(), 20.0, "incorrect h_ce returned")

    def test_h_re(self):
        """Test that correct h_re is returned when queried"""
        self.assertEqual(self.be.h_re(), 4.14, "incorrect h_re returned")

    def test_a_sol(self):
        """Test that correct a_sol is returned when queried"""
        self.assertEqual(self.be.a_sol, 0.0, "non-zero a_sol returned")

    def test_therm_rad_to_sky(self):
        """Test that correct therm_rad_to_sky is returned when queried"""
        self.assertEqual(self.be.therm_rad_to_sky, 22.77, "incorrect therm_rad_to_sky returned")

    def test_h_pli(self):
        """Test that correct h_pli list is returned when queried"""
        for i in range(0, self.be.no_of_nodes()-1):
            with self.subTest(i=i):
                self.assertEqual(self.be.h_pli(i), [2.5,0.0][i], "incorrect h_pli returned")

    def test_k_pli(self):
        """Test that correct k_pli list is returned when queried"""
        self.assertEqual(self.be.k_pli, [0.0, 0.0], "non-zero k_pli list returned")

    def test_temp_ext(self):
        """Test that the correct external temperature is returned when queried"""
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                self.assertEqual(
                    self.be.temp_ext(),
                    t_idx * 5.0,
                    "incorrect ext temp returned",
                )

    def test_fabric_heat_loss(self):
        """Test that correct fabric heat loss is returned when queried"""
        self.assertAlmostEqual(self.be.fabric_heat_loss(), 8.16, 2, "incorrect fabric heat loss returned")

    def test_heat_capacity(self):
        """Test that the correct heat capacity is returned when queried"""
        self.assertEqual(self.be.heat_capacity(), 0, "incorrect heat capacity returned")


class TestBuildingElementAdjacentZTU_Simple(unittest.TestCase):

    def setUp(self):
        """Create BuildingElementAdjacentZTC_Simple objects to be tested"""
        self.simtime = SimulationTime(0, 4, 1)
        ec = ExternalConditions(
            self.simtime,
            [0.0, 5.0, 10.0, 15.0],
            None,
            None,
            [0.0] * 4,  # Diffuse horizontal radiation
            [0.0] * 4,  # Direct beam radiation
            None,
            55.0,  # Latitude
            0.0,  # Longitude
            0.0,  # Timezone
            0,  # Start day
            None,
            1,  # Time-series step
            None,
            None,
            None,
            None,
            None,
        )
        # Create an object for each mass distribution class
        be_I = BuildingElementAdjacentZTU_Simple(20.0, 180, 0.25, 0.5, 19000.0, "I", ec)
        be_E = BuildingElementAdjacentZTU_Simple(22.5, 135, 0.50, 1, 18000.0, "E", ec)
        be_IE = BuildingElementAdjacentZTU_Simple(25.0, 90, 0.75, 1.5, 17000.0, "IE", ec)
        be_D = BuildingElementAdjacentZTU_Simple(27.5, 45, 0.80, 2, 16000.0, "D", ec)
        be_M = BuildingElementAdjacentZTU_Simple(30.0, 0, 0.40, 2.5, 15000.0, "M", ec)

        # Put objects in a list that can be iterated over
        self.test_be_objs = [be_I, be_E, be_IE, be_D, be_M]

    def test_h_ce(self):
        """Test that correct h_ce is returned when queried"""

        for i, be in enumerate(self.test_be_objs):
            with self.subTest(i=i):
                self.assertAlmostEqual(
                    be.h_ce(),
                    [
                        1.8469778117827087,
                        0.960222752585521,
                        0.6487503359312012,
                        0.4898538961038961,
                        0.39348003259983705,
                    ][i],
                    msg="incorrect h_ce returned",
                )

    def test_h_re(self):
        """Test that correct h_re is returned when queried"""

        for i, be in enumerate(self.test_be_objs):
            with self.subTest(i=i):
                self.assertAlmostEqual(be.h_re(), [0.0, 0.0, 0.0, 0.0, 0.0][i], msg="incorrect h_re returned")

    def test_temp_ext(self):
        """Test that the correct external temperature is returned when queried"""
        results = [
            [0.0, 5.0, 10.0, 15.0],
            [0.0, 5.0, 10.0, 15.0],
            [0.0, 5.0, 10.0, 15.0],
            [0.0, 5.0, 10.0, 15.0],
            [0.0, 5.0, 10.0, 15.0],
        ]
        for t_idx, _, _ in self.simtime:
            for i, be in enumerate(self.test_be_objs):
                with self.subTest(i=i + len(self.test_be_objs) * t_idx):
                    self.assertAlmostEqual(be.temp_ext(), results[i][t_idx])

    def test_fabric_heat_loss(self):
        """Test that the correct fabric heat loss is returned when queried"""
        for i, be in enumerate(self.test_be_objs):
            with self.subTest(i=i):
                self.assertAlmostEqual(
                    be.fabric_heat_loss(),
                    [43.20, 31.56, 27.10, 29.25, 55.54][i],
                    2,
                    "incorrect fabric heat loss returned",
                )

    def test_heat_capacity(self):
        """Test that the correct heat capacity is returned when queried"""
        results = [380, 405, 425, 440, 450]

        for i, be in enumerate(self.test_be_objs):
            with self.subTest(i=i):
                self.assertEqual(be.heat_capacity(), results[i], "incorrect heat capacity returned")
