#!/usr/bin/env python3

"""
This module contains unit tests for the heat_pump module
"""

# Standard library imports
import copy
import unittest
from unittest.mock import patch,MagicMock

# Set path to include modules to be tested (must be before local imports)
from unit_tests.common import test_setup
test_setup()

# Local imports
from core.heating_systems.heat_pump import \
    HeatPumpTestData, SourceType, SinkType, ServiceType,\
    interpolate_exhaust_air_heat_pump_test_data, \
    HeatPump, HeatPumpServiceWater, HeatPumpServiceSpace, \
    HeatPumpServiceSpaceWarmAir, BackupCtrlType, HeatPump_HWOnly
from core.units import Celcius2Kelvin
from core.water_heat_demand.cold_water_source import ColdWaterSource
from core.simulation_time import SimulationTime
from core.external_conditions import ExternalConditions
from core.energy_supply.energy_supply import EnergySupply, EnergySupplyConnection
from core.heating_systems.boiler import Boiler, \
    BoilerServiceWaterCombi,BoilerServiceSpace
from core.controls.time_control import SetpointTimeControl


class TestHeatPumpFreeFunctions(unittest.TestCase):
    """ Unit tests for free functions in heat_pump module """

    def test_interpolate_exhaust_air_heat_pump_test_data(self):
        """ Test interpolation of exhaust air heat pump test data """
        data_eahp = [
            {
                "air_flow_rate": 100.0,
                "test_letter": "A",
                "capacity": 5.0,
                "cop": 2.0,
                "degradation_coeff": 0.9,
                "design_flow_temp": 55,
                "temp_outlet": 55,
                "temp_source": 20,
                "temp_test": -7,
                "eahp_mixed_ext_air_ratio": 0.25
            },
            {
                "air_flow_rate": 200.0,
                "test_letter": "A",
                "capacity": 6.0,
                "cop": 2.5,
                "degradation_coeff": 0.95,
                "design_flow_temp": 55,
                "temp_outlet": 55,
                "temp_source": 20,
                "temp_test": -7,
                "eahp_mixed_ext_air_ratio": 0.75
            },
            {
                "air_flow_rate":100.0,
                "test_letter": "B",
                "capacity": 5.5,
                "cop": 2.4,
                "degradation_coeff": 0.92,
                "design_flow_temp": 35,
                "temp_outlet": 34,
                "temp_source": 20,
                "temp_test": 2,
                "eahp_mixed_ext_air_ratio": 0.25
            },
            {
                "air_flow_rate": 200.0,
                "test_letter": "B",
                "capacity": 6.0,
                "cop": 3.0,
                "degradation_coeff": 0.98,
                "design_flow_temp": 35,
                "temp_outlet": 34,
                "temp_source": 20,
                "temp_test": 2,
                "eahp_mixed_ext_air_ratio": 0.75
            },
        ]
        data_eahp_interpolated = [
            {
                "test_letter": "A",
                "capacity": 5.4,
                "cop": 2.2,
                "degradation_coeff": 0.92,
                "design_flow_temp": 55,
                "temp_outlet": 55,
                "temp_source": 20,
                "temp_test": -7,
                "ext_air_ratio": 0.45
            },
            {
                "test_letter": "B",
                "capacity": 5.7,
                "cop": 2.64,
                "degradation_coeff": 0.9440000000000001,
                "design_flow_temp": 35,
                "temp_outlet": 34,
                "temp_source": 20,
                "temp_test": 2,
                "ext_air_ratio": 0.45
            },
        ]
        source_type = SourceType.from_string('ExhaustAirMixed')
        lowest_air_flow_rate_in_test_data, data_eahp_func_result \
            = interpolate_exhaust_air_heat_pump_test_data(140.0, data_eahp, source_type)

        self.assertEqual(
            lowest_air_flow_rate_in_test_data,
            100.0,
            "incorrect lowest air flow rate identified",
            )

        self.maxDiff = None
        self.assertEqual(
            data_eahp_func_result,
            data_eahp_interpolated,
            "incorrect interpolation of exhaust air heat pump test data",
            )


# Before defining the code to run the tests, we define the data to be parsed
# and the sorted/processed data structure it should be transformed into. Note
# that the data for design flow temp of 55 has an extra record (test letter F2)
# to test that the code can handle more than 2 records with the same temp_test
# value properly. This probably won't occur in practice.
data_unsorted = [
    {
        "test_letter": "A",
        "capacity": 8.4,
        "cop": 4.6,
        "degradation_coeff": 0.90,
        "design_flow_temp": 35,
        "temp_outlet": 34,
        "temp_source": 0,
        "temp_test": -7
    },
    {
        "test_letter": "B",
        "capacity": 8.3,
        "cop": 4.9,
        "degradation_coeff": 0.90,
        "design_flow_temp": 35,
        "temp_outlet": 30,
        "temp_source": 0,
        "temp_test": 2
    },
    {
        "test_letter": "C",
        "capacity": 8.3,
        "cop": 5.1,
        "degradation_coeff": 0.90,
        "design_flow_temp": 35,
        "temp_outlet": 27,
        "temp_source": 0,
        "temp_test": 7
    },
    {
        "test_letter": "D",
        "capacity": 8.2,
        "cop": 5.4,
        "degradation_coeff": 0.95,
        "design_flow_temp": 35,
        "temp_outlet": 24,
        "temp_source": 0,
        "temp_test": 12
    },
    {
        "test_letter": "F",
        "capacity": 8.4,
        "cop": 4.6,
        "degradation_coeff": 0.90,
        "design_flow_temp": 35,
        "temp_outlet": 34,
        "temp_source": 0,
        "temp_test": -7
    },
    {
        "test_letter": "A",
        "capacity": 8.8,
        "cop": 3.2,
        "degradation_coeff": 0.90,
        "design_flow_temp": 55,
        "temp_outlet": 52,
        "temp_source": 0,
        "temp_test": -7
    },
    {
        "test_letter": "B",
        "capacity": 8.6,
        "cop": 3.6,
        "degradation_coeff": 0.90,
        "design_flow_temp": 55,
        "temp_outlet": 42,
        "temp_source": 0,
        "temp_test": 2
    },
    {
        "test_letter": "C",
        "capacity": 8.5,
        "cop": 3.9,
        "degradation_coeff": 0.98,
        "design_flow_temp": 55,
        "temp_outlet": 36,
        "temp_source": 0,
        "temp_test": 7
    },
    {
        "test_letter": "D",
        "capacity": 8.5,
        "cop": 4.3,
        "degradation_coeff": 0.98,
        "design_flow_temp": 55,
        "temp_outlet": 30,
        "temp_source": 0,
        "temp_test": 12
    },
    {
        "test_letter": "F",
        "capacity": 8.8,
        "cop": 3.2,
        "degradation_coeff": 0.90,
        "design_flow_temp": 55,
        "temp_outlet": 52,
        "temp_source": 0,
        "temp_test": -7
    },
    {
        "test_letter": "F2",
        "capacity": 8.8,
        "cop": 3.2,
        "degradation_coeff": 0.90,
        "design_flow_temp": 55,
        "temp_outlet": 52,
        "temp_source": 0,
        "temp_test": -7
    }
]
data_sorted = {
    35: [
        {
            "test_letter": "A",
            "capacity": 8.4,
            "carnot_cop": 9.033823529411764,
            "cop": 4.6,
            "degradation_coeff": 0.90,
            "design_flow_temp": 35,
            "exergetic_eff": 0.5091974605241738,
            "temp_outlet": 34,
            "temp_source": 0,
            "temp_test": -7,
            "theoretical_load_ratio": 1.0,
        },
        {
            "test_letter": "F",
            "capacity": 8.4,
            "carnot_cop": 9.033823529438331,
            "cop": 4.6,
            "degradation_coeff": 0.90,
            "design_flow_temp": 35,
            "exergetic_eff": 0.5091974605226763,
            "temp_outlet": 34,
            "temp_source": 0.0000000001,
            "temp_test": -6.9999999999,
            "theoretical_load_ratio": 1.0000000000040385,
        },
        {
            "test_letter": "B",
            "capacity": 8.3,
            "carnot_cop": 10.104999999999999,
            "cop": 4.9,
            "degradation_coeff": 0.90,
            "design_flow_temp": 35,
            "exergetic_eff": 0.48490846115784275,
            "temp_outlet": 30,
            "temp_source": 0,
            "temp_test": 2,
            "theoretical_load_ratio": 1.1634388356892613,
        },
        {
            "test_letter": "C",
            "capacity": 8.3,
            "carnot_cop": 11.116666666666665,
            "cop": 5.1,
            "degradation_coeff": 0.90,
            "design_flow_temp": 35,
            "exergetic_eff": 0.4587706146926537,
            "temp_outlet": 27,
            "temp_source": 0,
            "temp_test": 7,
            "theoretical_load_ratio": 1.3186802349509577,
        },
        {
            "test_letter": "D",
            "capacity": 8.2,
            "carnot_cop": 12.38125,
            "cop": 5.4,
            "degradation_coeff": 0.95,
            "design_flow_temp": 35,
            "exergetic_eff": 0.43614336193841496,
            "temp_outlet": 24,
            "temp_source": 0,
            "temp_test": 12,
            "theoretical_load_ratio": 1.513621351820552,
        }
    ],
    55: [
        {
            "test_letter": "A",
            "capacity": 8.8,
            "carnot_cop": 6.252884615384615,
            "cop": 3.2,
            "degradation_coeff": 0.90,
            "design_flow_temp": 55,
            "exergetic_eff": 0.5117638013224666,
            "temp_outlet": 52,
            "temp_source": 0,
            "temp_test": -7,
            "theoretical_load_ratio": 1.0,
        },
        {
            "test_letter": "F",
            "capacity": 8.8,
            "carnot_cop": 6.252884615396638,
            "cop": 3.2,
            "degradation_coeff": 0.90,
            "design_flow_temp": 55,
            "exergetic_eff": 0.5117638013214826,
            "temp_outlet": 52,
            "temp_source": 0.0000000001,
            "temp_test": -6.9999999999,
            "theoretical_load_ratio": 1.0000000000030207,
        },
        {
            "test_letter": "F2",
            "capacity": 8.8,
            "carnot_cop": 6.252884615408662,
            "cop": 3.2,
            "degradation_coeff": 0.90,
            "design_flow_temp": 55,
            "exergetic_eff": 0.5117638013204985,
            "temp_outlet": 52,
            "temp_source": 0.0000000002,
            "temp_test": -6.9999999998,
            "theoretical_load_ratio": 1.0000000000060418,
        },
        {
            "test_letter": "B",
            "capacity": 8.6,
            "carnot_cop": 7.503571428571428,
            "cop": 3.6,
            "degradation_coeff": 0.90,
            "design_flow_temp": 55,
            "exergetic_eff": 0.4797715373631604,
            "temp_outlet": 42,
            "temp_source": 0,
            "temp_test": 2,
            "theoretical_load_ratio": 1.3179136223360988,
        },
        {
            "test_letter": "C",
            "capacity": 8.5,
            "carnot_cop": 8.587499999999999,
            "cop": 3.9,
            "degradation_coeff": 0.98,
            "design_flow_temp": 55,
            "exergetic_eff": 0.4541484716157206,
            "temp_outlet": 36,
            "temp_source": 0,
            "temp_test": 7,
            "theoretical_load_ratio": 1.5978273764295179,
        },
        {
            "test_letter": "D",
            "capacity": 8.5,
            "carnot_cop": 10.104999999999999,
            "cop": 4.3,
            "degradation_coeff": 0.98,
            "design_flow_temp": 55,
            "exergetic_eff": 0.4255319148936171,
            "temp_outlet": 30,
            "temp_source": 0,
            "temp_test": 12,
            "theoretical_load_ratio": 1.9940427298329144,
        }
    ]
}

class TestHeatPumpTestData(unittest.TestCase):
    """ Unit tests for HeatPumpTestData class """
    # TODO Test handling of case where test data for only 1 design flow temp has been provided

    def setUp(self):
        """ Create HeatPumpTestData object to be tested """
        self.hp_testdata = HeatPumpTestData(data_unsorted)

    def test_init(self):
        """ Test that internal data structures have been populated correctly.

        This includes parsing and sorting the test data records, and producing
        sorted list of the design flow temperatures for which the data records
        apply.
        """
        self.maxDiff = None
        self.assertEqual(
            self.hp_testdata._HeatPumpTestData__dsgn_flow_temps,
            [35, 55],
            "list of design flow temps populated incorrectly"
            )
        self.assertEqual(
            self.hp_testdata._HeatPumpTestData__testdata,
            data_sorted,
            "list of test data records populated incorrectly"
            )
        # TODO Should also test that invalid data is handled correctly. This
        #      will require the init function to throw exceptions rather than
        #      exit the process as it does now.

    def test_init_regression_coeffs(self):
        """ Test that regression coefficients have been populated correctly """
        results_expected = {
            35: [4.810017281274474, 0.03677543129969712, 0.0009914765238219557],
            55: [3.4857982546529747, 0.050636568790103545, 0.0014104955583514216]
            }
        for flow_temp, reg_coeffs in self.hp_testdata._HeatPumpTestData__regression_coeffs.items():
            for i, coeff in enumerate(reg_coeffs):
                with self.subTest(msg="flow temp = " + str(flow_temp) + ", i = " + str(i)):
                    self.assertAlmostEqual(
                        coeff,
                        results_expected[flow_temp][i],
                        msg="list of regression coefficients populated incorrectly"
                        )

    def test_average_degradation_coeff(self):
        """ Test that correct average degradation coeff is returned for the flow temp """
        results = [0.9125, 0.919375, 0.92625, 0.933125, 0.94]

        for i, flow_temp in enumerate([35, 40, 45, 50, 55]):
            with self.subTest(i=i):
                self.assertAlmostEqual(
                    self.hp_testdata.average_degradation_coeff(Celcius2Kelvin(flow_temp)),
                    results[i],
                    msg="incorrect average degradation coefficient returned"
                    )

    def test_average_capacity(self):
        """ Test that correct average capacity is returned for the flow temp """
        results = [8.3, 8.375, 8.45, 8.525, 8.6]

        for i, flow_temp in enumerate([35, 40, 45, 50, 55]):
            with self.subTest(i=i):
                self.assertAlmostEqual(
                    self.hp_testdata.average_capacity(Celcius2Kelvin(flow_temp)),
                    results[i],
                    msg="incorrect average capacity returned"
                    )

    def test_temp_spread_test_conditions(self):
        """ Test that correct temp spread at test conditions is returned for the flow temp """ 
        results = [5.0, 5.75, 6.5, 7.25, 8.0]
        
        for i, flow_temp in enumerate([35, 40, 45, 50, 55]):
            with self.subTest(i=i):
                self.assertEqual(
                    self.hp_testdata.temp_spread_test_conditions(Celcius2Kelvin(flow_temp)),
                    results[i],
                    msg="incorrect temp spread at test conditions returned"
                    )

    def test_carnot_cop_at_test_condition(self):
        """ Test that correct Carnot CoP is returned for the flow temp and test condition """
        # TODO Test conditions other than just coldest
        i = -1
        for flow_temp, test_condition, result in [
            [35, 'cld', 9.033823529411764],
            [40, 'cld', 8.338588800904978],
            [45, 'cld', 7.643354072398189],
            [50, 'cld', 6.948119343891403],
            [55, 'cld', 6.252884615384615],
            [45, 'A', 7.643354072398189],
            [45, 'B', 8.804285714285713],
            [45, 'C', 9.852083333333333],
            [45, 'D', 11.243125],
            [45, 'F', 7.643354072417485],
            ]:
            # TODO Note that the result above for condition F is different to
            #      that for condition A, despite the source and outlet temps in
            #      the inputs being the same for both, because of the adjustment
            #      to the source temp applied in the HeatPumpTestData __init__
            #      function when duplicate records are found. This may not be
            #      the desired behaviour (see the TODO comment in that function)
            #      but in that case the problem is not with the function that
            #      is being tested here, so for now we set the result so that
            #      the test passes.
            i += 1
            flow_temp = Celcius2Kelvin(flow_temp)
            with self.subTest(i=i):
                self.assertEqual(
                    self.hp_testdata.carnot_cop_at_test_condition(test_condition, flow_temp),
                    result,
                    "incorrect Carnot CoP at condition "+test_condition+" returned"
                    )

    def test_outlet_temp_at_test_condition(self):
        """ Test that correct outlet temp is returned for the flow temp and test condition """
        # TODO Test conditions other than just coldest
        i = -1
        for flow_temp, test_condition, result in [
            [35, 'cld', 307.15],
            [40, 'cld', 311.65],
            [45, 'cld', 316.15],
            [50, 'cld', 320.65],
            [55, 'cld', 325.15],
            [45, 'A', 316.15],
            [45, 'B', 309.15],
            [45, 'C', 304.65],
            [45, 'D', 300.15],
            [45, 'F', 316.15],
            ]:
            i += 1
            flow_temp = Celcius2Kelvin(flow_temp)
            with self.subTest(i=i):
                self.assertEqual(
                    self.hp_testdata.outlet_temp_at_test_condition(test_condition, flow_temp),
                    result,
                    "incorrect outlet temp at condition "+test_condition+" returned"
                    )

    def test_source_temp_at_test_condition(self):
        """ Test that correct source temp is returned for the flow temp and test condition """
        # TODO Test conditions other than just coldest
        i = -1
        for flow_temp, test_condition, result in [
            [35, 'cld', 273.15],
            [40, 'cld', 273.15],
            [45, 'cld', 273.15],
            [50, 'cld', 273.15],
            [55, 'cld', 273.15],
            [45, 'A', 273.15],
            [45, 'B', 273.15],
            [45, 'C', 273.15],
            [45, 'D', 273.15],
            [45, 'F', 273.15000000009996],
            ]:
            # TODO Note that the result above for condition F is different to
            #      that for condition A, despite the source and outlet temps in
            #      the inputs being the same for both, because of the adjustment
            #      to the source temp applied in the HeatPumpTestData __init__
            #      function when duplicate records are found. This may not be
            #      the desired behaviour (see the TODO comment in that function)
            #      but in that case the problem is not with the function that
            #      is being tested here, so for now we set the result so that
            #      the test passes.
            i += 1
            flow_temp = Celcius2Kelvin(flow_temp)
            with self.subTest(i=i):
                self.assertEqual(
                    self.hp_testdata.source_temp_at_test_condition(test_condition, flow_temp),
                    result,
                    "incorrect source temp at condition "+test_condition+" returned"
                    )

    def test_capacity_at_test_condition(self):
        """ Test that correct capacity is returned for the flow temp and test condition """
        i = -1
        for flow_temp, test_condition, result in [
            [35, 'cld', 8.4],
            [40, 'cld', 8.5],
            [45, 'cld', 8.6],
            [50, 'cld', 8.7],
            [55, 'cld', 8.8],
            [45, 'A', 8.6],
            [45, 'B', 8.45],
            [45, 'C', 8.4],
            [45, 'D', 8.35],
            [45, 'F', 8.6],
            ]:
            i += 1
            flow_temp = Celcius2Kelvin(flow_temp)
            with self.subTest(i=i):
                self.assertAlmostEqual(
                    self.hp_testdata.capacity_at_test_condition(test_condition, flow_temp),
                    result,
                    msg="incorrect capacity at condition "+test_condition+" returned"
                    )

    def test_lr_op_cond(self):
        """ Test that correct load ratio at operating conditions is returned """
        i = -1
        for flow_temp, temp_source, carnot_cop_op_cond, result in [
            [35.0, 283.15, 12.326, 1.50508728516368],
            [40.0, 293.15, 15.6575, 2.38250354792371],
            [45.0, 278.15, 7.95375, 1.21688682087694],
            [50.0, 288.15, 9.23285714285714, 1.58193632324929],
            [55.0, 273.15, 5.96636363636364, 1.0],
            ]:
            i += 1
            flow_temp = Celcius2Kelvin(flow_temp)
            with self.subTest(i=i):
                self.assertAlmostEqual(
                    self.hp_testdata.lr_op_cond(flow_temp, temp_source, carnot_cop_op_cond),
                    result, 
                    msg="incorrect load ratio at operating conditions returned"
                    )

    def test_lr_eff_degcoeff_either_side_of_op_cond(self):
        """ Test that correct test results either side of operating conditions are returned """
        results_lr_below = [
            1.1634388356892613, 1.1225791267684564, 1.0817194178476517, 1.0408597089268468,
            1.0000000000060418,
            1.3186802349509577, 1.318488581797243, 1.3182969286435282, 1.3181052754898135,
            1.3179136223360988,
            ]
        results_lr_above = [
            1.3186802349509577, 1.318488581797243, 1.3182969286435282, 1.3181052754898135,
            1.3179136223360988,
            1.513621351820552, 1.5346728579727933, 1.555724364125035, 1.5767758702772765,
            1.5978273764295179,
            ]
        results_eff_below = [
            0.48490846115784275, 0.49162229619850667, 0.49833613123917064, 0.5050499662798346,
            0.5117638013204985,
            0.4587706146926537, 0.4640208453602804, 0.4692710760279071, 0.4745213066955337,
            0.4797715373631604,
            ]
        results_eff_above = [
            0.4587706146926537, 0.4640208453602804, 0.4692710760279071, 0.4745213066955337,
            0.4797715373631604,
            0.43614336193841496, 0.44064463935774134, 0.4451459167770678, 0.4496471941963942,
            0.4541484716157206,
            ]
        results_deg_below = [0.9] * 10
        results_deg_above = \
            [0.9, 0.9, 0.9, 0.9, 0.9, 0.95, 0.9575, 0.965, 0.9724999999999999, 0.98]

        i = -1
        for exergy_lr_op_cond in [1.2, 1.4]:
            for flow_temp in [35, 40, 45, 50, 55]:
                i += 1
                flow_temp = Celcius2Kelvin(flow_temp)
                with self.subTest(i=i):
                    lr_below, lr_above, eff_below, eff_above, deg_below, deg_above = \
                        self.hp_testdata.lr_eff_degcoeff_either_side_of_op_cond(
                            flow_temp,
                            exergy_lr_op_cond,
                            )
                    self.assertEqual(
                        lr_below,
                        results_lr_below[i],
                        "incorrect load ratio below operating conditions returned",
                        )
                    self.assertEqual(
                        lr_above,
                        results_lr_above[i],
                        "incorrect load ratio above operating conditions returned",
                        )
                    self.assertEqual(
                        eff_below,
                        results_eff_below[i],
                        "incorrect efficiency below operating conditions returned",
                        )
                    self.assertEqual(
                        eff_above,
                        results_eff_above[i],
                        "incorrect efficiency above operating conditions returned",
                        )
                    self.assertEqual(
                        deg_below,
                        results_deg_below[i],
                        "incorrect degradation coeff below operating conditions returned",
                        )
                    self.assertEqual(
                        deg_above,
                        results_deg_above[i],
                        "incorrect degradation coeff above operating conditions returned",
                        )

    def test_cop_op_cond_if_not_air_source(self):
        """ Test that correct CoP at operating conditions (not air source) is returned """
        results = [
            6.5629213163133,
            8.09149749487405,
            4.60977003063163,
            5.92554693808559,
            3.76414827675397,
            ]

        i = -1
        for temp_diff_limit_low, temp_ext, temp_source, temp_output in [
            [8.0, 0.00, 283.15, 308.15],
            [7.0, -5.0, 293.15, 313.15],
            [6.0, 5.00, 278.15, 318.15],
            [5.0, 10.0, 288.15, 323.15],
            [4.0, 7.50, 273.15, 328.15],
            ]:
            i += 1
            with self.subTest(i=i):
                self.assertAlmostEqual(
                    self.hp_testdata.cop_op_cond_if_not_air_source(
                        temp_diff_limit_low,
                        temp_ext,
                        temp_source,
                        temp_output,
                        ),
                    results[i],
                    msg="incorrect CoP at operating conditions (not air source) returned",
                    )

    def test_capacity_op_cond_var_flow_or_source_temp(self):
        """ Test that correct capacity at operating conditions is returned """
        results = [
            9.26595980986965,
            8.18090909090909,
            8.95014809894768,
            10.0098208201822,
            8.84090909090909,
            ]

        i = -1
        for mod_ctrl, temp_source, temp_output in [
            [True, 283.15, 308.15],
            [False, 293.15, 313.15],
            [True, 278.15, 318.15],
            [True, 288.15, 323.15],
            [False, 273.15, 328.15],
            ]:
            i += 1
            with self.subTest(i=i):
                self.assertAlmostEqual(
                    self.hp_testdata.capacity_op_cond_var_flow_or_source_temp(
                        temp_output,
                        temp_source,
                        mod_ctrl,
                        ),
                    results[i],
                    msg="incorrect capacity at operating conditions returned",
                    )

    def test_temp_spread_correction(self):
        """ Test that correct temperature spread correction factor is returned """
        results = [
            1.1219512195122,
            1.08394607843137,
            1.05822498586772,
            1.03966445733223,
            1.02564102564103,
            ]
        temp_source = 275.15
        temp_diff_evaporator = - 15.0
        temp_diff_condenser = 5.0
        temp_spread_emitter = 10.0

        for i, temp_output in enumerate([308.15, 313.15, 318.15, 323.15, 328.15]):
            with self.subTest(i=i):
                self.assertAlmostEqual(
                    self.hp_testdata.temp_spread_correction(
                        temp_source,
                        temp_output,
                        temp_diff_evaporator,
                        temp_diff_condenser,
                        temp_spread_emitter,
                        ),
                    results[i],
                    msg="incorrect temperature spread correction factor returned",
                    )


class TestSourceType(unittest.TestCase):
    """ Unit tests for SourceType """

    def test_from_string(self):
        """ Test that from_string function returns correct Enum values """
        for strval, result in [
            ['Ground', SourceType.GROUND],
            ['OutsideAir', SourceType.OUTSIDE_AIR],
            ['ExhaustAirMEV', SourceType.EXHAUST_AIR_MEV],
            ['ExhaustAirMVHR', SourceType.EXHAUST_AIR_MVHR],
            ['ExhaustAirMixed', SourceType.EXHAUST_AIR_MIXED],
            ['WaterGround', SourceType.WATER_GROUND],
            ['WaterSurface', SourceType.WATER_SURFACE],
            ['HeatNetwork', SourceType.HEAT_NETWORK],
            ]:
            self.assertEqual(
                SourceType.from_string(strval),
                result,
                "incorrect SourceType returned",
                )

    def test_is_exhaust_air(self):
        """ Test that is_exhaust_air function returns correct results """
        for source_type, result in [
            [SourceType.GROUND, False],
            [SourceType.OUTSIDE_AIR, False],
            [SourceType.EXHAUST_AIR_MEV, True],
            [SourceType.EXHAUST_AIR_MVHR, True],
            [SourceType.EXHAUST_AIR_MIXED, True],
            [SourceType.WATER_GROUND, False],
            [SourceType.WATER_SURFACE, False],
            [SourceType.HEAT_NETWORK, False],
            ]:
            self.assertEqual(
                SourceType.is_exhaust_air(source_type),
                result,
                "incorrectly identified whether or not source type is exhaust air",
                )

    def test_source_fluid_is_air(self):
        """ Test that source_fluid_is_air function returns correct results """
        for source_type, result in [
            [SourceType.GROUND, False],
            [SourceType.OUTSIDE_AIR, True],
            [SourceType.EXHAUST_AIR_MEV, True],
            [SourceType.EXHAUST_AIR_MVHR, True],
            [SourceType.EXHAUST_AIR_MIXED, True],
            [SourceType.WATER_GROUND, False],
            [SourceType.WATER_SURFACE, False],
            [SourceType.HEAT_NETWORK, False],
            ]:
            self.assertEqual(
                SourceType.source_fluid_is_air(source_type),
                result,
                "incorrectly identified whether or not source fluid is air",
                )

    def test_source_fluid_is_water(self):
        """ Test that source_fluid_is_water function returns correct results """
        for source_type, result in [
            [SourceType.GROUND, True],
            [SourceType.OUTSIDE_AIR, False],
            [SourceType.EXHAUST_AIR_MEV, False],
            [SourceType.EXHAUST_AIR_MVHR, False],
            [SourceType.EXHAUST_AIR_MIXED, False],
            [SourceType.WATER_GROUND, True],
            [SourceType.WATER_SURFACE, True],
            [SourceType.HEAT_NETWORK, True]
            ]:
            self.assertEqual(
                SourceType.source_fluid_is_water(source_type),
                result,
                "incorrectly identified whether or not source fluid is air",
                )


class TestSinkType(unittest.TestCase):
    """ Unit tests for SinkType """

    def test_from_string(self):
        """ Test that from_string function returns correct Enum values """
        for strval, result in [
            ['Air', SinkType.AIR],
            ['Water', SinkType.WATER],
            ['Glycol25', SinkType.GLYCOL25]
            ]:
            self.assertEqual(
                SinkType.from_string(strval),
                result,
                "incorrect SourceType returned",
                )
            
class TestHeatPump(unittest.TestCase):
    def setUp(self):
        self.heat_dict      =  {
                                    'type': 'HeatPump',
                                   'EnergySupply': 'mains_gas',
                                   'source_type': 'OutsideAir',
                                   'sink_type': 'Water',
                                   'backup_ctrl_type': 'TopUp',
                                   'time_delay_backup': 1.0,
                                   'modulating_control': True,
                                   'min_modulation_rate_35': 0.35,
                                   'min_modulation_rate_55': 0.4,
                                   'time_constant_onoff_operation': 140,
                                   'temp_return_feed_max': 70,
                                   'temp_lower_operating_limit': -5.0,
                                   'min_temp_diff_flow_return_for_hp_to_operate': 0.0,
                                   'var_flow_temp_ctrl_during_test': False,
                                   'power_heating_circ_pump': 0.015,
                                   'power_source_circ_pump': 0.01,
                                   'power_standby': 0.015,
                                   'power_crankcase_heater': 0.01,
                                   'power_off': 0.015,
                                   'power_max_backup': 3.0,
                                   'test_data': [{'test_letter': 'A', 
                                                  'capacity': 8.4, 
                                                  'cop': 4.6,
                                                  'degradation_coeff': 0.9, 
                                                  'design_flow_temp': 35,
                                                  'temp_outlet': 34,
                                                  'temp_source': 0, 
                                                  'temp_test': -7}, 
                                                  {'test_letter': 'B',
                                                    'capacity': 8.3, 
                                                    'cop': 4.9, 
                                                    'degradation_coeff': 0.9, 
                                                    'design_flow_temp': 35, 
                                                    'temp_outlet': 30, 
                                                    'temp_source': 0, 
                                                    'temp_test': 2},
                                                  {'test_letter': 'C',
                                                   'capacity': 8.3,
                                                   'cop': 5.1,
                                                   'degradation_coeff': 0.9, 
                                                   'design_flow_temp': 35, 
                                                   'temp_outlet': 27, 
                                                   'temp_source': 0, 
                                                   'temp_test': 7},
                                                  {'test_letter': 'D', 
                                                   'capacity': 8.2, 
                                                   'cop': 5.4, 
                                                   'degradation_coeff': 0.95, 
                                                   'design_flow_temp': 35, 
                                                   'temp_outlet': 24, 
                                                   'temp_source': 0, 
                                                   'temp_test': 12},
                                                   {'test_letter': 'F', 
                                                    'capacity': 8.4, 
                                                    'cop': 4.6, 
                                                    'degradation_coeff': 0.9, 
                                                    'design_flow_temp': 35, 
                                                    'temp_outlet': 34, 
                                                    'temp_source': 0, 
                                                    'temp_test': -7},
                                                   {"test_letter": "A",
                                                    "capacity": 8.8,
                                                    "cop": 3.2,
                                                    "degradation_coeff": 0.90,
                                                    "design_flow_temp": 55,
                                                    "temp_outlet": 52,
                                                    "temp_source": 0,
                                                    "temp_test": -7
                                                   },
                                                   {
                                                    "test_letter": "B",
                                                    "capacity": 8.6,
                                                    "cop": 3.6,
                                                    "degradation_coeff": 0.90,
                                                    "design_flow_temp": 55,
                                                    "temp_outlet": 42,
                                                    "temp_source": 0,
                                                    "temp_test": 2
                                                   },
                                                   {
                                                    "test_letter": "C",
                                                    "capacity": 8.5,
                                                    "cop": 3.9,
                                                    "degradation_coeff": 0.98,
                                                    "design_flow_temp": 55,
                                                    "temp_outlet": 36,
                                                    "temp_source": 0,
                                                    "temp_test": 7
                                                   },
                                                   {
                                                    "test_letter": "D",
                                                    "capacity": 8.5,
                                                    "cop": 4.3,
                                                    "degradation_coeff": 0.98,
                                                    "design_flow_temp": 55,
                                                    "temp_outlet": 30,
                                                    "temp_source": 0,
                                                    "temp_test": 12
                                                   },
                                                   {
                                                    "test_letter": "F",
                                                    "capacity": 8.8,
                                                    "cop": 3.2,
                                                    "degradation_coeff": 0.90,
                                                    "design_flow_temp": 55,
                                                    "temp_outlet": 52,
                                                    "temp_source": 0,
                                                    "temp_test": -7
                                                   }
                                                  ]
                                   }
        self.simtime        = SimulationTime(0, 2, 1)
        self.energysupply   = EnergySupply("mains_gas", self.simtime)
        self.energy_supply_conn_name_auxiliary = 'HeatPump_auxiliary: hp'
        self.windspeed      = [3.7, 3.8]
        self.wind_direction = [200, 220]
        self.airtemp        = [0.0, 2.5]
        self.diffuse_horizontal_radiation = [333, 610]
        self.direct_beam_radiation = [420, 750]
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
        self.number_of_zones = 2

        self.heat_pump = HeatPump(self.heat_dict,
                                 self.energysupply,
                                 self.energy_supply_conn_name_auxiliary,
                                 self.simtime,
                                 self.extcond,
                                 self.number_of_zones)
        
        # Test data for heat_neatwork
        self.heat_dict_heat_nw =  {
                                    'type': 'HeatPump',
                                   'EnergySupply': 'mains_gas',
                                   'source_type': 'HeatNetwork',
                                   'sink_type': 'Water',
                                   'backup_ctrl_type': 'TopUp',
                                   "temp_distribution_heat_network": 20.0,
                                   'time_delay_backup': 2.0,
                                   'modulating_control': True,
                                   'min_modulation_rate_35': 0.35,
                                   'min_modulation_rate_55': 0.4,
                                   'time_constant_onoff_operation': 140,
                                   'temp_return_feed_max': 70.0,
                                   'temp_lower_operating_limit': -5.0,
                                   'min_temp_diff_flow_return_for_hp_to_operate': 0.0,
                                   'var_flow_temp_ctrl_during_test': False,
                                   'power_heating_circ_pump': 0.015,
                                   'power_source_circ_pump': 0.01,
                                   'power_standby': 0.015,
                                   'power_crankcase_heater': 0.01,
                                   'power_off': 0.015,
                                   'power_max_backup': 3.0,
                                   'test_data': [{'test_letter': 'A', 
                                                  'capacity': 8.4, 
                                                  'cop': 4.6,
                                                  'degradation_coeff': 0.9, 
                                                  'design_flow_temp': 35,
                                                  'temp_outlet': 34,
                                                  'temp_source': 0, 
                                                  'temp_test': -7}, 
                                                  {'test_letter': 'B',
                                                    'capacity': 8.3, 
                                                    'cop': 4.9, 
                                                    'degradation_coeff': 0.9, 
                                                    'design_flow_temp': 35, 
                                                    'temp_outlet': 30, 
                                                    'temp_source': 0, 
                                                    'temp_test': 2},
                                                  {'test_letter': 'C',
                                                   'capacity': 8.3,
                                                   'cop': 5.1,
                                                   'degradation_coeff': 0.9, 
                                                   'design_flow_temp': 35, 
                                                   'temp_outlet': 27, 
                                                   'temp_source': 0, 
                                                   'temp_test': 7},
                                                  {'test_letter': 'D', 
                                                   'capacity': 8.2, 
                                                   'cop': 5.4, 
                                                   'degradation_coeff': 0.95, 
                                                   'design_flow_temp': 35, 
                                                   'temp_outlet': 24, 
                                                   'temp_source': 0, 
                                                   'temp_test': 12},
                                                   {'test_letter': 'F', 
                                                    'capacity': 8.4, 
                                                    'cop': 4.6, 
                                                    'degradation_coeff': 0.9, 
                                                    'design_flow_temp': 35, 
                                                    'temp_outlet': 34, 
                                                    'temp_source': 0, 
                                                    'temp_test': -7}]
                                   }
        # Test data for exhaust heat pump
        self.heat_dict_exhaust  =  {
                                    'type': 'HeatPump',
                                   'EnergySupply': 'mains_gas',
                                   'source_type': 'ExhaustAirMixed',
                                   'sink_type': 'Water',
                                   'backup_ctrl_type': 'Substitute',
                                   'time_delay_backup': 2.0,
                                   'modulating_control': True,
                                   'min_modulation_rate_35': 0.35,
                                   'min_modulation_rate_55': 0.4,
                                   'time_constant_onoff_operation': 140,
                                   'temp_return_feed_max': 70,
                                   'temp_lower_operating_limit': -5.0,
                                   'min_temp_diff_flow_return_for_hp_to_operate': 0.0,
                                   'var_flow_temp_ctrl_during_test': True,
                                   'power_heating_circ_pump': 0.015,
                                   'power_source_circ_pump': 0.01,
                                   'power_standby': 0.015,
                                   'power_crankcase_heater': 0.01,
                                   'power_off': 0.015,
                                   'power_max_backup': 3.0,
                                   "eahp_mixed_max_temp": 10,
                                   "eahp_mixed_min_temp": 0,
                                   'test_data': [{"air_flow_rate": 100.0,
                                                  'test_letter': 'A', 
                                                  'capacity': 8.4, 
                                                  'cop': 4.6,
                                                  'degradation_coeff': 0.9, 
                                                  'design_flow_temp': 35,
                                                  'temp_outlet': 34,
                                                  'temp_source': 0, 
                                                  'temp_test': -7,
                                                  "eahp_mixed_ext_air_ratio": 0.62}, 
                                                  {"air_flow_rate": 100.0,
                                                   'test_letter': 'B',
                                                    'capacity': 8.3, 
                                                    'cop': 4.9, 
                                                    'degradation_coeff': 0.9, 
                                                    'design_flow_temp': 35, 
                                                    'temp_outlet': 30, 
                                                    'temp_source': 0, 
                                                    'temp_test': 2,
                                                    "eahp_mixed_ext_air_ratio": 0.62},
                                                  {"air_flow_rate": 100.0,
                                                   'test_letter': 'C',
                                                   'capacity': 8.3,
                                                   'cop': 5.1,
                                                   'degradation_coeff': 0.9, 
                                                   'design_flow_temp': 35, 
                                                   'temp_outlet': 27, 
                                                   'temp_source': 0, 
                                                   'temp_test': 7,
                                                   "eahp_mixed_ext_air_ratio": 0.62},
                                                  {"air_flow_rate": 100.0,
                                                   'test_letter': 'D', 
                                                   'capacity': 8.2, 
                                                   'cop': 5.4, 
                                                   'degradation_coeff': 0.95, 
                                                   'design_flow_temp': 35, 
                                                   'temp_outlet': 24, 
                                                   'temp_source': 0, 
                                                   'temp_test': 12,
                                                   "eahp_mixed_ext_air_ratio": 0.62},
                                                   {"air_flow_rate": 100.0,
                                                    'test_letter': 'F', 
                                                    'capacity': 8.4, 
                                                    'cop': 4.6, 
                                                    'degradation_coeff': 0.9, 
                                                    'design_flow_temp': 35, 
                                                    'temp_outlet': 34, 
                                                    'temp_source': 0, 
                                                    'temp_test': -7,
                                                    "eahp_mixed_ext_air_ratio": 0.62}                                                ]
                                   }
        self.heat_dict_sinktype_air = {
                                   'type': 'HeatPump',
                                   'EnergySupply': 'mains_gas',
                                   'source_type': 'OutsideAir',
                                   'sink_type': 'Air',
                                   'backup_ctrl_type': 'TopUp',
                                   'time_delay_backup': 2.0,
                                   'modulating_control': True,
                                   'min_modulation_rate_35': 0.35,
                                   'min_modulation_rate_55': 0.4,
                                   'time_constant_onoff_operation': 140,
                                   'temp_return_feed_max': 70.0,
                                   'temp_lower_operating_limit': -5.0,
                                   'min_temp_diff_flow_return_for_hp_to_operate': 0.0,
                                   'var_flow_temp_ctrl_during_test': True,
                                   'power_heating_circ_pump': 0.015,
                                   'power_source_circ_pump': 0.01,
                                   'power_standby': 0.015,
                                   'power_crankcase_heater': 0.01,
                                   'power_off': 0.015,
                                   'power_max_backup': 3.0,
                                   'min_modulation_rate_20' : 20.0,
                                   'test_data': [{'test_letter': 'A', 
                                                  'capacity': 8.4, 
                                                  'cop': 4.6,
                                                  'degradation_coeff': 0.9, 
                                                  'design_flow_temp': 35,
                                                  'temp_outlet': 34,
                                                  'temp_source': 0, 
                                                  'temp_test': -7}, 
                                                  {'test_letter': 'B',
                                                    'capacity': 8.3, 
                                                    'cop': 4.9, 
                                                    'degradation_coeff': 0.9, 
                                                    'design_flow_temp': 35, 
                                                    'temp_outlet': 30, 
                                                    'temp_source': 0, 
                                                    'temp_test': 2},
                                                  {'test_letter': 'C',
                                                   'capacity': 8.3,
                                                   'cop': 5.1,
                                                   'degradation_coeff': 0.9, 
                                                   'design_flow_temp': 35, 
                                                   'temp_outlet': 27, 
                                                   'temp_source': 0, 
                                                   'temp_test': 7},
                                                  {'test_letter': 'D', 
                                                   'capacity': 8.2, 
                                                   'cop': 5.4, 
                                                   'degradation_coeff': 0.95, 
                                                   'design_flow_temp': 35, 
                                                   'temp_outlet': 24, 
                                                   'temp_source': 0, 
                                                   'temp_test': 12},
                                                   {'test_letter': 'F', 
                                                    'capacity': 8.4, 
                                                    'cop': 4.6, 
                                                    'degradation_coeff': 0.9, 
                                                    'design_flow_temp': 35, 
                                                    'temp_outlet': 34, 
                                                    'temp_source': 0, 
                                                    'temp_test': -7}
                                                  ]
                                   }
        
        self.boiler_dict =  {'EnergySupply': 'mains gas',
                             'EnergySupply_aux': 'mains elec', 
                             'rated_power': 24.0, 
                             'efficiency_full_load': 0.891, 
                             'efficiency_part_load': 0.991, 
                             'boiler_location': 'internal', 
                             'modulation_load': 0.3, 
                             'electricity_circ_pump': 0.06, 
                             'electricity_part_load': 0.0131, 
                             'electricity_full_load': 0.0388, 
                             'electricity_standby': 0.0244}

        
    
    def test_create_service_connection(self):
        ''' Test creation of EnergySupplyConnection for the service name given''' 
        self.service_name = 'new_service'
        # Ensure the service name does not exist in __energy_supply_connections
        self.assertNotIn(self.service_name, 
                         self.heat_pump._HeatPump__energy_supply_connections)
        # Call the method under test
        self.heat_pump._HeatPump__create_service_connection(self.service_name)
        # Check that the service name was added to __energy_supply_connections
        self.assertIn(self.service_name,
                      self.heat_pump._HeatPump__energy_supply_connections)
        # Check system exit when connection is created with exiting service name
        with self.assertRaises(SystemExit):
            self.heat_pump._HeatPump__create_service_connection(self.service_name)
        
        # Check with heat_network
        self.energy_supply_conn_name_auxiliary = 'HeatPump_auxiliary: hp1'
        self.heat_network = EnergySupply(simulation_time = self.simtime ,
                                         fuel_type = 'custom')
        self.heat_pump_nw = HeatPump(self.heat_dict_heat_nw,
                                 self.energysupply,
                                 self.energy_supply_conn_name_auxiliary,
                                 self.simtime,
                                 self.extcond,
                                 self.number_of_zones,
                                 heat_network = self.heat_network)
        # Call the method under test
        self.heat_pump_nw._HeatPump__create_service_connection('new_service_nw')
        self.assertIn('new_service_nw',
                      self.heat_pump_nw._HeatPump__energy_supply_HN_connections) 
        

    def test_create_service_hot_water_combi(self):
        ''' Check BoilerServiceWaterCombi object is created correctly'''

        self.energy_supply_conn_name_auxiliary = 'HeatPump_auxiliary: boiler'
        self.boiler = Boiler(self.boiler_dict,
                             self.energysupply,
                             self.energy_supply_conn_name_auxiliary,
                             self.simtime,
                             self.extcond, 
                             )
        self.heat_pump_with_boiler = HeatPump(self.heat_dict,
                                 self.energysupply,
                                 self.energy_supply_conn_name_auxiliary,
                                 self.simtime,
                                 self.extcond,
                                 self.number_of_zones,
                                 boiler = self.boiler)

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
        boiler_service_WaterCombi_obj = self.heat_pump_with_boiler.create_service_hot_water_combi( 
                                                       self.boiler_data,
                                                       self.service_name,
                                                       self.temp_hot_water,
                                                       self.coldfeed)
        
        self.assertTrue(isinstance(boiler_service_WaterCombi_obj,BoilerServiceWaterCombi))
        
        # Check function does system exit if boiler object is not defined
        self.energy_supply_conn_name_auxiliary = 'HeatPump_auxiliary: boiler1'
        self.heat_pump = HeatPump(self.heat_dict,
                                 self.energysupply,
                                 self.energy_supply_conn_name_auxiliary,
                                 self.simtime,
                                 self.extcond,
                                 self.number_of_zones)
        with self.assertRaises(SystemExit):          
            self.heat_pump.create_service_hot_water_combi( self.boiler_data,
                                                           self.service_name,
                                                           self.temp_hot_water,
                                                           self.coldfeed)            
        
        
    def test_create_service_hot_water(self):
        ''' Check the function returns HeatPumpServiceWater object'''
        
        self.energy_supply_conn_name_auxiliary = 'HeatPump_auxiliary: HotWater'
        self.heat_pump = HeatPump(self.heat_dict,
                                 self.energysupply,
                                 self.energy_supply_conn_name_auxiliary,
                                 self.simtime,
                                 self.extcond,
                                 self.number_of_zones)
        self.service_name = 'service_hot_water'
        self.temp_limit_upper = 60.0
        self.coldfeed = ColdWaterSource([1.0, 1.2], self.simtime, 0, 1)
        self.temp_hot_water = 50
        
        heatpump_servicewater_obj = self.heat_pump.create_service_hot_water(self.service_name,
                                                self.temp_hot_water,
                                                self.temp_limit_upper,
                                                self.coldfeed,
                                                )
        
        self.assertTrue(isinstance(heatpump_servicewater_obj, HeatPumpServiceWater))
        
        self.assertIn(self.service_name,
                      self.heat_pump._HeatPump__energy_supply_connections)
        
        # Check the with boiler data in heat pump
        self.energy_supply_conn_name_auxiliary = 'HeatPump_auxiliary: HotWater_boiler'
        
        self.heat_pump_with_boiler = HeatPump(self.heat_dict,
                                 self.energysupply,
                                 self.energy_supply_conn_name_auxiliary,
                                 self.simtime,
                                 self.extcond,
                                 self.number_of_zones,
                                 boiler = MagicMock()
                                 )
        self.service_name = 'service_hot_water_boiler'
        self.heat_pump_with_boiler.create_service_hot_water(self.service_name,
                                                self.temp_limit_upper,
                                                self.coldfeed,
                                                None,
                                                None
                                                )
        self.heat_pump_with_boiler._HeatPump__boiler. \
            create_service_hot_water_regular.assert_called_once_with(
                                self.service_name,
                                self.coldfeed,
                                None,
                                None
                                )       
        
    
    def test_create_service_space_heating(self):
        ''' Check the function returns HeatPumpServiceSpace object'''        
        
        self.service_name = 'service_space'
        self.temp_limit_upper = 50.0
        self.temp_diff_emit_dsgn = 50.0
        self.control  = None
        self.volume_heated = 250.0
        
        heatpump_servicespace_obj = self.heat_pump.create_service_space_heating(
                                                    self.service_name,
                                                    self.temp_limit_upper,
                                                    self.temp_diff_emit_dsgn,
                                                    self.control,
                                                    self.volume_heated
                                                    )
        
        self.assertTrue(isinstance(heatpump_servicespace_obj, HeatPumpServiceSpace))
        
        self.assertIn(self.service_name,
                      self.heat_pump._HeatPump__energy_supply_connections)
        
        # Check the with boiler data in heat pump
        self.energy_supply_conn_name_auxiliary = 'HeatPump_auxiliary: SpaceHeating_boiler'
        
        self.heat_pump_with_boiler = HeatPump(self.heat_dict,
                                 self.energysupply,
                                 self.energy_supply_conn_name_auxiliary,
                                 self.simtime,
                                 self.extcond,
                                 self.number_of_zones,
                                 boiler = MagicMock()
                                 )
        self.service_name = 'service_space_boiler'
        self.heat_pump_with_boiler.create_service_space_heating(
                                                    self.service_name,
                                                    self.temp_limit_upper,
                                                    self.temp_diff_emit_dsgn,
                                                    self.control,
                                                    self.volume_heated
                                                    )
        self.heat_pump_with_boiler._HeatPump__boiler. \
            create_service_space_heating.assert_called_once_with(
                                self.service_name,
                                self.control) 
        self.assertIn(self.service_name,
                      self.heat_pump_with_boiler._HeatPump__energy_supply_connections)
        
        # Check with exhaust air heat pump
        self.energy_supply_conn_name_auxiliary = 'HeatPump_auxiliary: exhaust_service_space' 
        self.heat_pump_exhaust = HeatPump(self.heat_dict_exhaust,
                                 self.energysupply,
                                 self.energy_supply_conn_name_auxiliary,
                                 self.simtime,
                                 self.extcond,
                                 self.number_of_zones,
                                 throughput_exhaust_air = 101)
        
        self.service_name = 'service_space_exhaust'        
        self.heat_pump_exhaust.create_service_space_heating(
                                                    self.service_name,
                                                    self.temp_limit_upper,
                                                    self.temp_diff_emit_dsgn,
                                                    self.control,
                                                    self.volume_heated
                                                    )        
        self.assertAlmostEqual(self.heat_pump_exhaust._HeatPump__volume_heated_all_services,
                               250.0)        
        
        
    def test_create_service_space_heating_warm_air(self):
        ''' Check HeatPumpServiceSpaceWarmAir object is returned'''
        self.service_name = 'service_space_warmair'
        self.control  = None
        self.volume_heated = 250.0
        self.frac_convective = 0.9
        # Check the system exit is raised when Sink type is not air
        with self.assertRaises(SystemExit): 
            self.heat_pump.create_service_space_heating_warm_air(
                                                        self.service_name,
                                                        self.control,
                                                        self.frac_convective,
                                                        self.volume_heated
                                                        )
            
        # Check without boiler object and sink type 'AIR'    
        self.energy_supply_conn_name_auxiliary = 'HeatPump_auxiliary: sink_air'
        self.heat_pump_sink_air = HeatPump(self.heat_dict_sinktype_air,
                                 self.energysupply,
                                 self.energy_supply_conn_name_auxiliary,
                                 self.simtime,
                                 self.extcond,
                                 self.number_of_zones,
                                )
        heatpump_servicespace_warmair_obj = self.heat_pump_sink_air.create_service_space_heating_warm_air(
                                                        self.service_name,
                                                        self.control,
                                                        self.frac_convective,
                                                        self.volume_heated
                                                        )
        
        
        self.assertTrue(isinstance(heatpump_servicespace_warmair_obj, HeatPumpServiceSpaceWarmAir))
        
        self.assertIn(self.service_name,
                      self.heat_pump_sink_air._HeatPump__energy_supply_connections)        

        # Check that warm air hybrid heat pump service cannot be created
        boiler = Boiler(
            self.boiler_dict,
            self.energysupply,
            self.energy_supply_conn_name_auxiliary,
            self.simtime,
            self.extcond, 
            )
        hybrid_warm_air_hp = HeatPump(
            self.heat_dict_sinktype_air,
            self.energysupply,
            "Aux EnergySupply connection name",
            self.simtime,
            self.extcond,
            self.number_of_zones,
            boiler=boiler,
            )
        self.assertRaises(
            ValueError,
            hybrid_warm_air_hp.create_service_space_heating_warm_air,
            "Hybrid HP warm air service",
            self.control,
            self.frac_convective,
            self.volume_heated,
            )

    def test_get_temp_source(self):
        # Check with source_type OutsideAir
        self.assertAlmostEqual(self.heat_pump._HeatPump__get_temp_source(), 273.15)
        # Check with ExhaustAirMixed
        self.energy_supply_conn_name_auxiliary = 'HeatPump_auxiliary: exhaust_source'
        throughput_exhaust_air = 101
        project = MagicMock()
        project.temp_internal_air_prev_timestep.return_value = 20
        self.heat_pump_exhaust = HeatPump(self.heat_dict_exhaust,
                                 self.energysupply,
                                 self.energy_supply_conn_name_auxiliary,
                                 self.simtime,
                                 self.extcond,
                                 self.number_of_zones,
                                 throughput_exhaust_air = throughput_exhaust_air,
                                 project = project)
        self.assertAlmostEqual(self.heat_pump_exhaust._HeatPump__get_temp_source(),  280.75)
        # Check with heat_network
        self.energy_supply_conn_name_auxiliary = 'HeatPump_auxiliary: heat_nw'
        self.heat_network = EnergySupply(simulation_time = self.simtime ,
                                         fuel_type = 'custom')
        self.heat_pump_nw = HeatPump(self.heat_dict_heat_nw,
                                 self.energysupply,
                                 self.energy_supply_conn_name_auxiliary,
                                 self.simtime,
                                 self.extcond,
                                 self.number_of_zones,
                                 heat_network = self.heat_network)
        self.assertAlmostEqual(self.heat_pump_nw._HeatPump__get_temp_source(), 293.15)

        
    def test_thermal_capacity_op_cond(self):
        # Check with source_type OutsideAir
        self.assertAlmostEqual(self.heat_pump._HeatPump__thermal_capacity_op_cond(290.0,260.0),
                                8.607029286155587)
        
        # Check with ExhaustAirMixed
        self.energy_supply_conn_name_auxiliary = 'HeatPump_auxiliary: exhaust_source_capacity'
        throughput_exhaust_air = 101
        project = MagicMock()
        self.heat_pump_exhaust = HeatPump(self.heat_dict_exhaust,
                                 self.energysupply,
                                 self.energy_supply_conn_name_auxiliary,
                                 self.simtime,
                                 self.extcond,
                                 self.number_of_zones,
                                 throughput_exhaust_air = throughput_exhaust_air,
                                 project = project)
        self.assertAlmostEqual(self.heat_pump_exhaust._HeatPump__thermal_capacity_op_cond(300.0,270.0),
                                8.70672362099314)
        
        
    def test_backup_energy_output_max(self):
        # With TopUp backup control
        temp_output =  300.0
        temp_return_feed = 290.0 
        time_available = 1.0
        time_start = 0.0

        self.assertAlmostEqual(
            self.heat_pump._HeatPump__backup_energy_output_max(
                temp_output,
                temp_return_feed,
                time_available,
                time_start
                ),
            3.0,
            )
        
        # With substitute backup control
        self.energy_supply_conn_name_auxiliary = 'HeatPump_auxiliary: exhaust_backup_energy' 
        self.heat_pump_exhaust = HeatPump(self.heat_dict_exhaust,
                                 self.energysupply,
                                 self.energy_supply_conn_name_auxiliary,
                                 self.simtime,
                                 self.extcond,
                                 self.number_of_zones,
                                 throughput_exhaust_air = 101)
        self.assertAlmostEqual(
            self.heat_pump._HeatPump__backup_energy_output_max(
                temp_output,
                temp_return_feed,
                time_available,
                time_start,
                ),
            3.0,
            )
        
        #With a hybrid boiler
        self.energy_supply_conn_name_auxiliary = 'HeatPump_auxiliary: hybrid_boiler'
        self.boiler = Boiler(self.boiler_dict,
                             self.energysupply,
                             self.energy_supply_conn_name_auxiliary,
                             self.simtime,
                             self.extcond, 
                             )
        self.ctrl = SetpointTimeControl([21.0,22.0],
                                        self.simtime,
                                        0, #start_day
                                        1.0, #time_series_step
                                        )   
        self.boilerservicespace = self.boiler.create_service_space_heating('service_boilerspace',
                                                     self.ctrl)
        self.heat_pump_with_boiler = HeatPump(self.heat_dict,
                                 self.energysupply,
                                 self.energy_supply_conn_name_auxiliary,
                                 self.simtime,
                                 self.extcond,
                                 self.number_of_zones,
                                 boiler = self.boiler)
        self.assertAlmostEqual(
            self.heat_pump_with_boiler._HeatPump__backup_energy_output_max(
                temp_output,
                temp_return_feed,
                time_available,
                time_start,
                self.boilerservicespace,
                ),
            24.0,
            )

    def test_energy_output_max(self):
        ''' Check the maximum energy output'''
        temp_output = 300.0
        temp_return_feed = 295.0         
        hybrid_boiler_service = BoilerServiceSpace(self,                                       
                                        service_name = 'boiler_service_space',
                                        control = MagicMock()
                                    )
                
        #self.simtime_copy = copy.deepcopy(self.simtime)
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                self.assertAlmostEqual(self.heat_pump._HeatPump__energy_output_max(temp_output,
                                                                           temp_return_feed,
                                                                           hybrid_boiler_service),
                [9.015028019161107,9.26483004027644][t_idx])
        
        
            
        # Check with backup SUBSTITUTE
        self.energy_supply_conn_name_auxiliary = 'HeatPump_auxiliary: backup_substitute' 
        project = MagicMock()
        project.temp_internal_air_prev_timestep.return_value = 30
        self.heat_pump_exhaust = HeatPump(self.heat_dict_exhaust,
                                  self.energysupply,
                                  self.energy_supply_conn_name_auxiliary,
                                  self.simtime,
                                  self.extcond,
                                  self.number_of_zones,
                                  throughput_exhaust_air = 101,
                                  project = project) 
        self.simtime.reset()       
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                self.assertAlmostEqual(self.heat_pump_exhaust._HeatPump__energy_output_max(temp_output,
                                                                            temp_return_feed,
                                                                            hybrid_boiler_service),
                    [10.191526455038767, 10.358981076999134][t_idx])

        # Test that backup heater takes over when HP source temp lower than operating limit
        project.temp_internal_air_prev_timestep.return_value = -7
        self.simtime.reset()
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                self.assertAlmostEqual(
                    self.heat_pump_exhaust._HeatPump__energy_output_max(
                        temp_output,
                        temp_return_feed,
                        None,
                        ),
                    [3.0, 3.0][t_idx],
                    )

    def test_cop_deg_coeff_op_cond(self):
        '''Check CoP and degradation coefficient at operating conditions'''
        # Check with type service type SPACE
        temp_spread_correction = MagicMock(return_value= 1.0)
        service_type = 'ServiceType.SPACE',
        temp_output = 320
        temp_source = 275
        
        cop_op_cond, deg_coeff_op_cond = self.heat_pump._HeatPump__cop_deg_coeff_op_cond(service_type,
                                                              temp_output, # Kelvin
                                                              temp_source, # Kelvin
                                                              temp_spread_correction)
        self.assertAlmostEqual(cop_op_cond, 3.5280895101045804)
        self.assertAlmostEqual(deg_coeff_op_cond, 0.9)
        
        # Check with sink type 'AIR'
        self.energy_supply_conn_name_auxiliary = 'auxillary_cop_deg_eff'
        self.heat_pump_sink_air = HeatPump(self.heat_dict_sinktype_air,
                                 self.energysupply,
                                 self.energy_supply_conn_name_auxiliary,
                                 self.simtime,
                                 self.extcond,
                                 self.number_of_zones
                                )
        service_type = 'ServiceType.SPACE'
        cop_op_cond, deg_coeff_op_cond = self.heat_pump_sink_air._HeatPump__cop_deg_coeff_op_cond(service_type,
                                                              temp_output, # Kelvin
                                                              temp_source, # Kelvin
                                                              temp_spread_correction)
        self.assertAlmostEqual(cop_op_cond, 3.6209597192830136)
        self.assertAlmostEqual(deg_coeff_op_cond, 0.25)
        
    
    def test_energy_output_limited(self):
        ''' Check energy output limited by upper temperature'''
        energy_output_required  = 1.5
        temp_output = 320.0
        temp_used_for_scaling = 310.0
        temp_limit_upper = 340.0
        
        self.assertAlmostEqual(self.heat_pump._HeatPump__energy_output_limited(energy_output_required,
                                                                           temp_output,
                                                                           temp_used_for_scaling,
                                                                           temp_limit_upper),                                                                           
                                 1.5)
        
        energy_output_required  = 1.5
        temp_output = 320.0
        temp_used_for_scaling = 50.0
        temp_limit_upper = 310.0
        
        self.assertAlmostEqual(self.heat_pump._HeatPump__energy_output_limited(energy_output_required,
                                                                           temp_output,
                                                                           temp_used_for_scaling,
                                                                           temp_limit_upper),                                                                           
                                 1.4444444444444444)
        
    def test_backup_heater_delay_time_elapsed(self):
        '''Check if backup heater is available or still in delay period'''
        
        self.heat_pump._HeatPump__create_service_connection('service_backupheater')
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                self.heat_pump._HeatPump__demand_energy(
                                                service_name = 'service_backupheater',
                                                service_type = ServiceType.WATER,
                                                energy_output_required = 500.0,
                                                temp_output = 330.0, # Kelvin
                                                temp_return_feed =330.0, # Kelvin
                                                temp_limit_upper= 340.0, # Kelvin
                                                time_constant_for_service = 1560,
                                                service_on = True,
                                                temp_spread_correction=1.0,
                                                temp_used_for_scaling = None,
                                                hybrid_boiler_service = None,
                                                emitters_data_for_buffer_tank=None
                                                )
                
                self.assertEqual(self.heat_pump._HeatPump__backup_heater_delay_time_elapsed(),
                                 [False,True][t_idx])
                
                self.heat_pump.timestep_end()
                
            
        
    def test_outside_operating_limits(self):
        
        self.assertFalse(self.heat_pump._HeatPump__outside_operating_limits(temp_return_feed = 300.0))
        #Check with less temp_return_feed_max
        self.heat_dict_exhaust  =  {
                                    'type': 'HeatPump',
                                   'EnergySupply': 'mains_gas',
                                   'source_type': 'ExhaustAirMixed',
                                   'sink_type': 'Water',
                                   'backup_ctrl_type': 'Substitute',
                                   'time_delay_backup': -1,
                                   'modulating_control': True,
                                   'min_modulation_rate_35': 0.35,
                                   'min_modulation_rate_55': 0.4,
                                   'time_constant_onoff_operation': 140,
                                   'temp_return_feed_max': 10,
                                   'temp_lower_operating_limit': -5.0,
                                   'min_temp_diff_flow_return_for_hp_to_operate': 0.0,
                                   'var_flow_temp_ctrl_during_test': True,
                                   'power_heating_circ_pump': 0.015,
                                   'power_source_circ_pump': 0.01,
                                   'power_standby': 0.015,
                                   'power_crankcase_heater': 0.01,
                                   'power_off': 0.015,
                                   'power_max_backup': 3.0,
                                   "eahp_mixed_max_temp": 10,
                                   "eahp_mixed_min_temp": 0,
                                   'test_data': [{"air_flow_rate": 100.0,
                                                  'test_letter': 'A', 
                                                  'capacity': 8.4, 
                                                  'cop': 4.6,
                                                  'degradation_coeff': 0.9, 
                                                  'design_flow_temp': 35,
                                                  'temp_outlet': 34,
                                                  'temp_source': 0, 
                                                  'temp_test': -7,
                                                  "eahp_mixed_ext_air_ratio": 0.62}, 
                                                  {"air_flow_rate": 100.0,
                                                   'test_letter': 'B',
                                                    'capacity': 8.3, 
                                                    'cop': 4.9, 
                                                    'degradation_coeff': 0.9, 
                                                    'design_flow_temp': 35, 
                                                    'temp_outlet': 30, 
                                                    'temp_source': 0, 
                                                    'temp_test': 2,
                                                    "eahp_mixed_ext_air_ratio": 0.62},
                                                  {"air_flow_rate": 100.0,
                                                   'test_letter': 'C',
                                                   'capacity': 8.3,
                                                   'cop': 5.1,
                                                   'degradation_coeff': 0.9, 
                                                   'design_flow_temp': 35, 
                                                   'temp_outlet': 27, 
                                                   'temp_source': 0, 
                                                   'temp_test': 7,
                                                   "eahp_mixed_ext_air_ratio": 0.62},
                                                  {"air_flow_rate": 100.0,
                                                   'test_letter': 'D', 
                                                   'capacity': 8.2, 
                                                   'cop': 5.4, 
                                                   'degradation_coeff': 0.95, 
                                                   'design_flow_temp': 35, 
                                                   'temp_outlet': 24, 
                                                   'temp_source': 0, 
                                                   'temp_test': 12,
                                                   "eahp_mixed_ext_air_ratio": 0.62},
                                                   {"air_flow_rate": 100.0,
                                                    'test_letter': 'F', 
                                                    'capacity': 8.4, 
                                                    'cop': 4.6, 
                                                    'degradation_coeff': 0.9, 
                                                    'design_flow_temp': 35, 
                                                    'temp_outlet': 34, 
                                                    'temp_source': 0, 
                                                    'temp_test': -7,
                                                    "eahp_mixed_ext_air_ratio": 0.62}                                                ]
                                   }
        project = MagicMock()
        project.temp_internal_air_prev_timestep.return_value = 20
        self.energy_supply_conn_name_auxiliary = 'aux_outside_operating_limit'
        self.heat_pump_exhaust = HeatPump(self.heat_dict_exhaust,
                                self.energysupply,
                                self.energy_supply_conn_name_auxiliary,
                                self.simtime,
                                self.extcond,
                                self.number_of_zones,
                                throughput_exhaust_air = 101,
                                project = project)
        
        self.assertTrue(self.heat_pump_exhaust._HeatPump__outside_operating_limits(temp_return_feed = 300.0))

    def test_inadequate_capacity(self):  
    
        energy_output_required = 5.0
        thermal_capacity_op_cond = 5.0
        temp_output = 310.0
        time_available = 1.0
        temp_return_feed = 315.0
        hybrid_boiler_service =  None
        time_start = 0.0

        self.assertFalse(
            self.heat_pump._HeatPump__inadequate_capacity(
                energy_output_required,
                thermal_capacity_op_cond,
                temp_output,
                time_available,
                temp_return_feed,
                time_start,
                hybrid_boiler_service,
                )
            )

    @patch.object(HeatPump, '_HeatPump__backup_heater_delay_time_elapsed', return_value=True)
    @patch.object(HeatPump, '_HeatPump__backup_energy_output_max', return_value=5.0)
    def test_inadequate_capacity_topup(self, mock_backup_energy_output_max, 
                                       mock_backup_heater_delay_time_elapsed):
        ''' Function __inadequate_capacity can be tested with Mock as its function call  
        __backup_energy_output_max references BoilerServiceWaterRegular/BoilerServiceSpace
        which inherits Boiler object.Inherited parameters cannot be accessed from TestHeatPump class'''
        
        self.heat_pump.__backup_ctrl = BackupCtrlType.TOPUP
        result = self.heat_pump._HeatPump__inadequate_capacity(
            energy_output_required= 5.0,
            thermal_capacity_op_cond= 1.0,
            temp_output=343,
            time_available=2,
            time_start=0.0,
            temp_return_feed=313,
            hybrid_boiler_service=None
        )
        self.assertTrue(result)
        mock_backup_heater_delay_time_elapsed.assert_called_once()
        mock_backup_energy_output_max.assert_called_once_with(343, 313, 2, 0.0, None)

    @patch.object(HeatPump, '_HeatPump__backup_heater_delay_time_elapsed', return_value=True)
    @patch.object(HeatPump, '_HeatPump__backup_energy_output_max', return_value=5.0)
    def test_inadequate_capacity_substitute(self, mock_backup_energy_output_max,
                                             mock_backup_heater_delay_time_elapsed):
        self.heat_pump.__backup_ctrl = BackupCtrlType.SUBSTITUTE
        result = self.heat_pump._HeatPump__inadequate_capacity(
            energy_output_required=5.0,
            thermal_capacity_op_cond=1,
            temp_output=343,
            temp_return_feed=313,
            time_available=2,
            time_start=0.0,
            hybrid_boiler_service=None
        )
        self.assertTrue(result)
        mock_backup_heater_delay_time_elapsed.assert_called_once()
        mock_backup_energy_output_max.assert_called_once_with(343, 313, 2, 0.0, None)

    @patch.object(HeatPump, '_HeatPump__backup_heater_delay_time_elapsed', return_value=False)
    @patch.object(HeatPump, '_HeatPump__backup_energy_output_max', return_value=5.0)
    def test_inadequate_capacity_no_delay_elapsed(self, mock_backup_energy_output_max,
                                                   mock_backup_heater_delay_time_elapsed):
        self.heat_pump.__backup_ctrl = BackupCtrlType.TOPUP
        result = self.heat_pump._HeatPump__inadequate_capacity(
            energy_output_required=5.0,
            thermal_capacity_op_cond=5.0,
            temp_output=343,
            temp_return_feed=313,
            time_available=2,
            time_start=0.0,
            hybrid_boiler_service=None
        )
        self.assertFalse(result)
        mock_backup_heater_delay_time_elapsed.assert_called_once()
        mock_backup_energy_output_max.assert_called_once()

    @patch.object(HeatPump, '_HeatPump__backup_heater_delay_time_elapsed', return_value=True)
    @patch.object(HeatPump, '_HeatPump__backup_energy_output_max', return_value=5.0)
    def test_inadequate_capacity_insufficient_backup(self, mock_backup_energy_output_max,
                                                      mock_backup_heater_delay_time_elapsed):
        self.heat_pump.__backup_ctrl = BackupCtrlType.SUBSTITUTE
        result = self.heat_pump._HeatPump__inadequate_capacity(
            energy_output_required=5.0,
            thermal_capacity_op_cond=5.0,
            temp_output=343,
            temp_return_feed=313,
            time_available=2,
            time_start=0.0,
            hybrid_boiler_service=None
        )
        self.assertFalse(result)
        mock_backup_heater_delay_time_elapsed.assert_called_once()
        mock_backup_energy_output_max.assert_called_once_with(343, 313, 2, 0.0, None)
        
    def test_is_heat_pump_cost_effective_equal_cost(self):

        cop_op_cond = 3.0
        boiler_eff = 0.9
        self.cost_schedule_hybrid_hp = {'cost_schedule_start_day': 0, 
                                   'cost_schedule_time_series_step': 1,
                                   'cost_schedule_hp':
                                        {'main': [16, 20, 24, {'value': 16, 'repeat': 5}]}, 
                                   'cost_schedule_boiler': {'main': [{'value': 4, 'repeat': 8}]}
                                    }
        
        self.energy_supply_conn_name_auxiliary = 'HeatPump_auxiliary: CostSchedule'
        
        self.heat_pump_with_cost_schedule = HeatPump(self.heat_dict,
                                                     self.energysupply,
                                                     self.energy_supply_conn_name_auxiliary,
                                                     self.simtime,
                                                     self.extcond,
                                                     self.number_of_zones,
                                                     cost_schedule_hybrid_hp = self.cost_schedule_hybrid_hp)

        self.heat_pump_with_cost_schedule.__backup_ctrl = BackupCtrlType.SUBSTITUTE
        self.assertFalse(self.heat_pump_with_cost_schedule.\
                         _HeatPump__is_heat_pump_cost_effective(cop_op_cond, boiler_eff))
        
        cop_op_cond = 16
        boiler_eff = 2.0
        
        self.assertTrue(self.heat_pump_with_cost_schedule.\
                        _HeatPump__is_heat_pump_cost_effective(cop_op_cond, boiler_eff))
        
    def test_use_backup_heater_only(self):
        
        cop_op_cond = 3.0
        energy_output_required = 4.0
        thermal_capacity_op_cond = 4.0
        temp_output = 320.0
        time_available = 1.0
        temp_return_feed = 320.0
        time_start = 0.0

        self.assertFalse(
            self.heat_pump._HeatPump__use_backup_heater_only(
                cop_op_cond,
                energy_output_required,
                thermal_capacity_op_cond,
                temp_output,
                time_available,
                time_start,
                temp_return_feed,
                )
            )
        
        self.cost_schedule_hybrid_hp = {'cost_schedule_start_day': 0, 
                                   'cost_schedule_time_series_step': 1,
                                   'cost_schedule_hp':
                                        {'main': [16, 20, 24, {'value': 16, 'repeat': 5}]}, 
                                   'cost_schedule_boiler': {'main': [{'value': 4, 'repeat': 8}]}
                                    }
        
        self.energy_supply_conn_name_auxiliary = 'HeatPump_auxiliary: CostSchedule_1'
        
        self.heat_pump_with_cost_schedule = HeatPump(self.heat_dict,
                                                     self.energysupply,
                                                     self.energy_supply_conn_name_auxiliary,
                                                     self.simtime,
                                                     self.extcond,
                                                     self.number_of_zones,
                                                     cost_schedule_hybrid_hp = self.cost_schedule_hybrid_hp)

        self.assertTrue(
            self.heat_pump_with_cost_schedule._HeatPump__use_backup_heater_only(
                cop_op_cond,
                energy_output_required,
                thermal_capacity_op_cond,
                temp_output,
                time_available,
                time_start,
                temp_return_feed,
                boiler_eff = 3.0,
                )
            )

    def test_run_demand_energy_calc(self):
    
        # Test with hybrid_boiler_service and boiler_eff
        self.energy_supply_conn_name_auxiliary = 'HeatPump_auxiliary: boiler'
        self.boiler = Boiler(self.boiler_dict,
                              self.energysupply,
                              self.energy_supply_conn_name_auxiliary,
                              self.simtime,
                              self.extcond, 
                              )
    
        self.ctrl = SetpointTimeControl([21.0,22.0],
                                         self.simtime,
                                         0, #start_day
                                         1.0, #time_series_step
                                         )
        self.boilerservicespace = self.boiler.create_service_space_heating('service_boilerspace',
                                                      self.ctrl)
    
        self.heat_pump_with_boiler = HeatPump(self.heat_dict,
                                  self.energysupply,
                                  self.energy_supply_conn_name_auxiliary,
                                  self.simtime,
                                  self.extcond,
                                  self.number_of_zones,
                                  boiler = self.boiler)
        self.simtime.reset() 
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                self.assertEqual(self.heat_pump_with_boiler._HeatPump__run_demand_energy_calc(
                                                          service_name = 'service_boilerspace',
                                                          service_type = ServiceType.WATER,
                                                          energy_output_required = 1.0,
                                                          temp_output = 320.0, # Kelvin
                                                          temp_return_feed =310.0, # Kelvin
                                                          temp_limit_upper= 340.0, # Kelvin
                                                          time_constant_for_service = 1560,
                                                          service_on = True, # bool - is service allowed to run?
                                                          temp_spread_correction=1.0,
                                                          temp_used_for_scaling = None,
                                                          hybrid_boiler_service = self.boilerservicespace,
                                                          boiler_eff = 1.0,
                                                          additional_time_unavailable=0.0,
                                                          ),
                 [{'service_name': 'service_boilerspace', 'service_type': ServiceType.WATER,
                  'service_on': True,'energy_output_required': 1.0, 'temp_output': 320.0,
                  'temp_source': 273.15,'cop_op_cond': 3.421525960735136,
                  'thermal_capacity_op_cond': 8.496784419801095,'time_running': 0.11769158196712368,
                  'deg_coeff_op_cond': 0.9, 'time_constant_for_service': 1560,
                  'use_backup_heater_only': False,
                  'energy_delivered_HP': 1.0, 'energy_input_backup': 0.0, 'energy_delivered_backup': 0.0,
                  'energy_delivered_total': 1.0,
                  'energy_heating_circ_pump': 0.001765373729506855, 'energy_source_circ_pump': 0.0011769158196712369,
                  'energy_output_required_boiler': 0.0, 'energy_heating_warm_air_fan': 0},
                 {'service_name': 'service_boilerspace', 'service_type': ServiceType.WATER,
                  'service_on': True, 'energy_output_required': 1.0, 'temp_output': 320.0,
                  'temp_source': 275.65, 'cop_op_cond': 3.566917590730002,
                  'thermal_capacity_op_cond': 8.732226164023768, 'time_running': 0.11451833486859722,
                  'deg_coeff_op_cond': 0.9, 'time_constant_for_service': 1560,
                  'use_backup_heater_only': False,
                  'energy_delivered_HP': 1.0, 'energy_input_backup': 0.0, 'energy_delivered_backup': 0.0,
                  'energy_delivered_total': 1.0,
                  'energy_heating_circ_pump': 0.0017177750230289582, 'energy_source_circ_pump': 0.0011451833486859722,
                  'energy_output_required_boiler': 0.0, 'energy_heating_warm_air_fan': 0}][t_idx]
                 )                                                                               
    
    
        # Check without boiler and service_on True
        self.simtime.reset() 
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                self.assertEqual(self.heat_pump._HeatPump__run_demand_energy_calc(service_name = 'service_no_boiler',
                                                          service_type = ServiceType.WATER,
                                                          energy_output_required = 1.0,
                                                          temp_output = 330.0, # Kelvin
                                                          temp_return_feed =330.0, # Kelvin
                                                          temp_limit_upper= 340.0, # Kelvin
                                                          time_constant_for_service = 1560,
                                                          service_on = True, # bool - is service allowed to run?
                                                          temp_spread_correction=1.0,
                                                          temp_used_for_scaling = None,
                                                          hybrid_boiler_service = None,
                                                          boiler_eff = None,
                                                          additional_time_unavailable=0.0,
                                                          ),
                    [{'service_name': 'service_no_boiler', 'service_type': ServiceType.WATER,'service_on': True,
                      'energy_output_required': 1.0, 'temp_output': 330.0, 'temp_source': 273.15,
                      'cop_op_cond': 2.9706605881515196, 'thermal_capacity_op_cond': 8.417674488123662,
                      'time_running': 0.11879765621857688, 'deg_coeff_op_cond': 0.9,
                      'time_constant_for_service': 1560, 'use_backup_heater_only': False,
                      'energy_delivered_HP': 0.9999999999999999,
                      'energy_input_backup': 0.0, 'energy_delivered_backup': 0.0, 
                      'energy_delivered_total': 0.9999999999999999,
                      'energy_heating_circ_pump': 0.001781964843278653, 'energy_source_circ_pump': 0.0011879765621857687,
                      'energy_output_required_boiler': 0.0, 'energy_heating_warm_air_fan': 0},
                      {'service_name': 'service_no_boiler', 'service_type': ServiceType.WATER, 'service_on': True, 
                       'energy_output_required': 1.0, 'temp_output': 330.0, 'temp_source': 275.65, 
                       'cop_op_cond': 3.107305509409639, 'thermal_capacity_op_cond': 8.650924134797519,
                       'time_running': 0.11559458670751663, 'deg_coeff_op_cond': 0.9,
                       'time_constant_for_service': 1560, 'use_backup_heater_only': False,
                       'energy_delivered_HP': 1.0,
                       'energy_input_backup': 0.0, 'energy_delivered_backup': 0.0, 
                       'energy_delivered_total': 1.0,
                       'energy_heating_circ_pump': 0.0017339188006127494, 'energy_source_circ_pump': 0.0011559458670751662,
                       'energy_output_required_boiler': 0.0, 'energy_heating_warm_air_fan': 0}][t_idx]
                 )
    
    
        # Check without modulating control
        self.heat_dict_modcontrol = {
                                    'type': 'HeatPump',
                                    'EnergySupply': 'mains_gas',
                                    'source_type': 'OutsideAir',
                                    'sink_type': 'Water',
                                    'backup_ctrl_type': 'Substitute',
                                    'time_delay_backup': 2.0,
                                    'modulating_control': False,
                                    'min_modulation_rate_35': 0.35,
                                    'min_modulation_rate_55': 0.4,
                                    'time_constant_onoff_operation': 140,
                                    'temp_return_feed_max': 70.0,
                                    'temp_lower_operating_limit': -5.0,
                                    'min_temp_diff_flow_return_for_hp_to_operate': 0.0,
                                    'var_flow_temp_ctrl_during_test': True,
                                    'power_heating_circ_pump': 0.015,
                                    'power_source_circ_pump': 0.01,
                                    'power_standby': 0.015,
                                    'power_crankcase_heater': 0.01,
                                    'power_off': 0.015,
                                    'power_max_backup': 3.0,
                                    'test_data': [{'test_letter': 'A', 
                                                   'capacity': 8.4, 
                                                   'cop': 4.6,
                                                   'degradation_coeff': 0.9, 
                                                   'design_flow_temp': 35,
                                                   'temp_outlet': 34,
                                                   'temp_source': 0, 
                                                   'temp_test': -7}, 
                                                   {'test_letter': 'B',
                                                     'capacity': 8.3, 
                                                     'cop': 4.9, 
                                                     'degradation_coeff': 0.9, 
                                                     'design_flow_temp': 35, 
                                                     'temp_outlet': 30, 
                                                     'temp_source': 0, 
                                                     'temp_test': 2},
    
                                                   {'test_letter': 'C',
                                                    'capacity': 8.3,
                                                    'cop': 5.1,
                                                    'degradation_coeff': 0.9, 
                                                    'design_flow_temp': 35, 
                                                    'temp_outlet': 27, 
                                                    'temp_source': 0, 
                                                    'temp_test': 7},
                                                   {'test_letter': 'D', 
                                                    'capacity': 8.2, 
                                                    'cop': 5.4, 
                                                    'degradation_coeff': 0.95, 
                                                    'design_flow_temp': 35, 
                                                    'temp_outlet': 24, 
                                                    'temp_source': 0, 
                                                    'temp_test': 12},
                                                    {'test_letter': 'F', 
                                                     'capacity': 8.4, 
                                                     'cop': 4.6, 
                                                     'degradation_coeff': 0.9, 
                                                     'design_flow_temp': 35, 
                                                     'temp_outlet': 34, 
                                                     'temp_source': 0, 
                                                     'temp_test': -7}
                                                   ]
                                    }
    
        self.energy_supply_conn_name_auxiliary = 'HeatPump_auxiliary: modulating_control'
    
        self.heat_pump_mod_ctrl = HeatPump(self.heat_dict_modcontrol,
                                  self.energysupply,
                                  self.energy_supply_conn_name_auxiliary,
                                  self.simtime,
                                  self.extcond,
                                  self.number_of_zones)
        self.simtime.reset() 
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                self.assertEqual(self.heat_pump_mod_ctrl._HeatPump__run_demand_energy_calc(
                                                        service_name = 'service_backup_modctrl',
                                                        service_type = ServiceType.WATER,
                                                        energy_output_required = 1.0,
                                                        temp_output = 330.0, # Kelvin
                                                        temp_return_feed =330.0, # Kelvin
                                                        temp_limit_upper= 340.0, # Kelvin
                                                        time_constant_for_service = 1560,
                                                        service_on = True, 
                                                        temp_spread_correction=1.0,
                                                        temp_used_for_scaling = None,
                                                        hybrid_boiler_service = None,
                                                        boiler_eff = None,
                                                        additional_time_unavailable=0.0,
                                                        ),
                         [{'service_name': 'service_backup_modctrl', 'service_type': ServiceType.WATER, 'service_on': True, 
                           'energy_output_required': 1.0, 'temp_output': 330.0, 'temp_source': 273.15, 
                           'cop_op_cond': 2.955763623095467, 'thermal_capacity_op_cond': 8.857000000000003, 
                           'time_running': 0.11290504685559441, 'deg_coeff_op_cond': 0.9, 'time_constant_for_service': 1560,
                           'use_backup_heater_only': False,
                           'energy_delivered_HP': 1.0, 'energy_input_backup': 0.0, 'energy_delivered_backup': 0.0, 
                           'energy_delivered_total': 1.0, 
                           'energy_heating_circ_pump': 0.0016935757028339162, 'energy_source_circ_pump': 0.0011290504685559442, 
                           'energy_output_required_boiler': 0.0, 'energy_heating_warm_air_fan': 0},
                           {'service_name': 'service_backup_modctrl', 'service_type': ServiceType.WATER, 'service_on': True, 
                            'energy_output_required': 1.0, 'temp_output': 330.0, 'temp_source': 275.65, 'cop_op_cond': 3.091723311370327, 
                            'thermal_capacity_op_cond': 8.807000000000002, 'time_running': 0.1135460429204042, 'deg_coeff_op_cond': 0.9, 
                            'time_constant_for_service': 1560, 'use_backup_heater_only': False, 'energy_delivered_HP': 1.0, 
                            'energy_input_backup': 0.0, 'energy_delivered_backup': 0.0,
                            'energy_delivered_total': 1.0, 'energy_heating_circ_pump': 0.001703190643806063, 
                            'energy_source_circ_pump': 0.001135460429204042, 'energy_output_required_boiler': 0.0,
                             'energy_heating_warm_air_fan': 0}][t_idx]
                         )
    
    
        self.simtime.reset() 
        # Check the results with service off and more energy_output_required
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                self.assertEqual(self.heat_pump._HeatPump__run_demand_energy_calc(service_name = 'service_erengy_output_required',
                                                          service_type = ServiceType.WATER,
                                                          energy_output_required = 50,
                                                          temp_output = 330.0, # Kelvin
                                                          temp_return_feed =330.0, # Kelvin
                                                          temp_limit_upper= 340.0, # Kelvin
                                                          time_constant_for_service = 1560,
                                                          service_on = False, # bool - is service allowed to run?
                                                          temp_spread_correction=1.0,
                                                          temp_used_for_scaling = None,
                                                          hybrid_boiler_service = None,
                                                          boiler_eff = None,
                                                          additional_time_unavailable=0.0,
                                                          ),
                             [{'service_name': 'service_erengy_output_required', 'service_type': ServiceType.WATER, 'service_on': False, 
                               'energy_output_required': 50.0, 'temp_output': 330.0, 'temp_source': 273.15, 'cop_op_cond': 2.9706605881515196,
                               'thermal_capacity_op_cond': 8.417674488123662, 'time_running': 0.0, 'deg_coeff_op_cond': 0.9,
                               'time_constant_for_service': 1560, 'use_backup_heater_only': False,
                               'energy_delivered_HP': 0.0, 'energy_input_backup': 0.0, 'energy_delivered_backup': 0.0, 
                               'energy_delivered_total': 0.0, 'energy_heating_circ_pump': 0.0, 
                               'energy_source_circ_pump': 0.0, 'energy_output_required_boiler': 0.0, 'energy_heating_warm_air_fan': 0},
                              {'service_name': 'service_erengy_output_required', 'service_type': ServiceType.WATER, 'service_on': False, 
                               'energy_output_required': 50.0, 'temp_output': 330.0, 'temp_source': 275.65, 'cop_op_cond': 3.107305509409639,
                               'thermal_capacity_op_cond': 8.650924134797519, 'time_running': 0.0, 'deg_coeff_op_cond': 0.9,
                               'time_constant_for_service': 1560, 'use_backup_heater_only': False, 'energy_delivered_HP': 0.0, 'energy_input_backup': 0.0, 'energy_delivered_backup': 0.0, 
                               'energy_delivered_total': 0.0, 'energy_heating_circ_pump': 0.0, 
                               'energy_source_circ_pump': 0.0, 'energy_output_required_boiler': 0.0, 'energy_heating_warm_air_fan': 0}][t_idx]
                             )
    
    
        # Check service off with boiler
        self.energy_supply_conn_name_auxiliary = 'HeatPump_auxiliary: boiler_and_sevice_off'
        self.boiler = Boiler(self.boiler_dict,
                              self.energysupply,
                              self.energy_supply_conn_name_auxiliary,
                              self.simtime,
                              self.extcond, 
                              )
    
        self.ctrl = SetpointTimeControl([21.0,22.0],
                                         self.simtime,
                                         0, #start_day
                                         1.0, #time_series_step
                                         )
        self.boilerservicespace = self.boiler.create_service_space_heating('service_boilerspace_service_off',
                                                      self.ctrl)
    
        self.heat_pump_with_boiler = HeatPump(self.heat_dict,
                                  self.energysupply,
                                  self.energy_supply_conn_name_auxiliary,
                                  self.simtime,
                                  self.extcond,
                                  self.number_of_zones,
                                  boiler = self.boiler)
        self.simtime.reset() 
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                self.assertEqual(self.heat_pump_with_boiler._HeatPump__run_demand_energy_calc(
                                                        service_name = 'service_boilerspace_service_off',
                                                        service_type = ServiceType.WATER,
                                                        energy_output_required = 1.0,
                                                        temp_output = 330.0, # Kelvin
                                                        temp_return_feed =330.0, # Kelvin
                                                        temp_limit_upper= 340.0, # Kelvin
                                                        time_constant_for_service = 1560,
                                                        service_on = False, # bool - is service allowed to run?
                                                        temp_spread_correction=1.0,
                                                        temp_used_for_scaling = None,
                                                        hybrid_boiler_service = self.boilerservicespace,
                                                        boiler_eff = 1.0,
                                                        additional_time_unavailable=0.0,
                                                        ),
                            [{'service_name': 'service_boilerspace_service_off', 'service_type': ServiceType.WATER, 'service_on': False,
                               'energy_output_required': 1.0, 'temp_output': 330.0, 'temp_source': 273.15, 'cop_op_cond': 2.9706605881515196,
                               'thermal_capacity_op_cond': 8.417674488123662, 'time_running': 0.0, 'deg_coeff_op_cond': 0.9,
                               'time_constant_for_service': 1560, 'use_backup_heater_only': False,
                               'energy_delivered_HP': 0.0, 'energy_input_backup': 0.0, 'energy_delivered_backup': 0.0, 
                               'energy_delivered_total': 0.0, 'energy_heating_circ_pump': 0.0, 
                               'energy_source_circ_pump': 0.0, 'energy_output_required_boiler': 0.0, 'energy_heating_warm_air_fan': 0},
                             {'service_name': 'service_boilerspace_service_off', 'service_type': ServiceType.WATER, 'service_on': False,
                               'energy_output_required': 1.0, 'temp_output': 330.0, 'temp_source': 275.65, 'cop_op_cond': 3.107305509409639,
                               'thermal_capacity_op_cond': 8.650924134797519, 'time_running': 0.0, 'deg_coeff_op_cond': 0.9,
                               'time_constant_for_service': 1560, 'use_backup_heater_only': False,
                               'energy_delivered_HP': 0.0, 'energy_input_backup': 0.0, 'energy_delivered_backup': 0.0, 
                               'energy_delivered_total': 0.0, 'energy_heating_circ_pump': 0.0, 
                               'energy_source_circ_pump': 0.0, 'energy_output_required_boiler': 0.0, 'energy_heating_warm_air_fan': 0}][t_idx]
                     )
    
        # Check wtih backup_ctrl_type Substitute
        self.heat_dict_with_sub =  {'type': 'HeatPump',
                                    'EnergySupply': 'mains_gas',
                                    'source_type': 'OutsideAir',
                                    'sink_type': 'Water',
                                    'backup_ctrl_type': 'Substitute',
                                    'time_delay_backup': 2.0,
                                    'modulating_control': True,
                                    'min_modulation_rate_35': 0.35,
                                    'min_modulation_rate_55': 0.4,
                                    'time_constant_onoff_operation': 140,
                                    'temp_return_feed_max': 70.0,
                                    'temp_lower_operating_limit': -5.0,
                                    'min_temp_diff_flow_return_for_hp_to_operate': 0.0,
                                    'var_flow_temp_ctrl_during_test': True,
                                    'power_heating_circ_pump': 0.015,
                                    'power_source_circ_pump': 0.01,
                                    'power_standby': 0.015,
                                    'power_crankcase_heater': 0.01,
                                    'power_off': 0.015,
                                    'power_max_backup': 3.0,
                                    'test_data': [{'test_letter': 'A', 
                                                   'capacity': 8.4, 
                                                   'cop': 4.6,
                                                   'degradation_coeff': 0.9, 
                                                   'design_flow_temp': 35,
                                                   'temp_outlet': 34,
                                                   'temp_source': 0, 
                                                   'temp_test': -7}, 
                                                   {'test_letter': 'B',
                                                     'capacity': 8.3, 
                                                     'cop': 4.9, 
                                                     'degradation_coeff': 0.9, 
                                                     'design_flow_temp': 35, 
                                                     'temp_outlet': 30, 
                                                     'temp_source': 0, 
                                                     'temp_test': 2},
                                                   {'test_letter': 'C',
                                                    'capacity': 8.3,
                                                    'cop': 5.1,
                                                    'degradation_coeff': 0.9, 
                                                    'design_flow_temp': 35, 
                                                    'temp_outlet': 27, 
                                                    'temp_source': 0, 
                                                    'temp_test': 7},
                                                   {'test_letter': 'D', 
                                                    'capacity': 8.2, 
                                                    'cop': 5.4, 
                                                    'degradation_coeff': 0.95, 
                                                    'design_flow_temp': 35, 
                                                    'temp_outlet': 24, 
                                                    'temp_source': 0, 
                                                    'temp_test': 12},
                                                    {'test_letter': 'F', 
                                                     'capacity': 8.4, 
                                                     'cop': 4.6, 
                                                     'degradation_coeff': 0.9, 
                                                     'design_flow_temp': 35, 
                                                     'temp_outlet': 34, 
                                                     'temp_source': 0, 
                                                     'temp_test': -7}
                                                   ]
                                    }
        self.energy_supply_conn_name_auxiliary = 'HeatPump_auxiliary: backup'
    
        self.heat_pump_backup = HeatPump(self.heat_dict_with_sub,
                                  self.energysupply,
                                  self.energy_supply_conn_name_auxiliary,
                                  self.simtime,
                                  self.extcond,
                                  self.number_of_zones)
        self.simtime.reset() 
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                self.assertEqual(self.heat_pump_backup._HeatPump__run_demand_energy_calc(
                                                          service_name = 'service_backup_substitute',
                                                          service_type = ServiceType.SPACE,
                                                          energy_output_required = 1.0,
                                                          temp_output = 330.0, # Kelvin
                                                          temp_return_feed =330.0, # Kelvin
                                                          temp_limit_upper= 340.0, # Kelvin
                                                          time_constant_for_service = 1560,
                                                          service_on = True, 
                                                          temp_spread_correction=1.0,
                                                          temp_used_for_scaling = None,
                                                          hybrid_boiler_service = None,
                                                          boiler_eff = None,
                                                          additional_time_unavailable=0.0,
                                                          ),
                                         [{'service_name': 'service_backup_substitute', 'service_type': ServiceType.SPACE, 'service_on': True,
                                           'energy_output_required': 1.0, 'temp_output': 330.0, 'temp_source': 273.15, 
                                           'cop_op_cond': 2.955763623095467, 'thermal_capacity_op_cond': 6.773123981338176, 
                                           'time_running': 0.1476423586450323, 'deg_coeff_op_cond': 0.9, 
                                           'time_constant_for_service': 1560, 'use_backup_heater_only': False, 
                                           'energy_delivered_HP': 1.0, 'energy_input_backup': 0.0, 
                                           'energy_delivered_backup': 0.0,
                                           'energy_delivered_total': 1.0, 'energy_heating_circ_pump': 0.0022146353796754846, 
                                           'energy_source_circ_pump': 0.0014764235864503231, 'energy_output_required_boiler': 0.0, 
                                           'energy_heating_warm_air_fan': 0},
                                           {'service_name': 'service_backup_substitute', 'service_type': ServiceType.SPACE, 'service_on': True, 
                                            'energy_output_required': 1.0, 'temp_output': 330.0, 'temp_source': 275.65, 
                                            'cop_op_cond': 3.091723311370327, 'thermal_capacity_op_cond': 6.9608039370972525, 
                                            'time_running': 0.1436615668300253, 'deg_coeff_op_cond': 0.9, 
                                            'time_constant_for_service': 1560, 'use_backup_heater_only': False, 
                                            'energy_delivered_HP': 1.0, 
                                            'energy_input_backup': 0.0, 'energy_delivered_backup': 0.0, 
                                            'energy_delivered_total': 1.0, 
                                            'energy_heating_circ_pump': 0.002154923502450379, 'energy_source_circ_pump': 0.0014366156683002528,
                                             'energy_output_required_boiler': 0.0, 'energy_heating_warm_air_fan': 0}][t_idx])

    
    def test_demand_energy(self):
        
        self.energy_supply_conn_name_auxiliary = 'HeatPump_auxiliary: boiler'
        self.boiler = Boiler(self.boiler_dict,
                              self.energysupply,
                              self.energy_supply_conn_name_auxiliary,
                              self.simtime,
                              self.extcond, 
                              )
    
        self.ctrl = SetpointTimeControl([21.0,22.0],
                                         self.simtime,
                                         0, #start_day
                                         1.0, #time_series_step
                                         )
        self.boilerservicespace = self.boiler.create_service_space_heating('service_boilerspace',
                                                      self.ctrl)
    
        self.heat_pump_with_boiler = HeatPump(self.heat_dict,
                                  self.energysupply,
                                  self.energy_supply_conn_name_auxiliary,
                                  self.simtime,
                                  self.extcond,
                                  self.number_of_zones,
                                  boiler = self.boiler)
        self.heat_pump_with_boiler._HeatPump__create_service_connection('service_boiler_demand_energy')

    
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                self.assertAlmostEqual(self.heat_pump_with_boiler._HeatPump__demand_energy(
                                                         service_name = 'service_boiler_demand_energy',
                                                         service_type = ServiceType.WATER,
                                                         energy_output_required = 1.0,
                                                         temp_output = 330.0, # Kelvin
                                                         temp_return_feed =330.0, # Kelvin
                                                         temp_limit_upper= 340.0, # Kelvin
                                                         time_constant_for_service = 1560,
                                                         service_on = True,
                                                         temp_spread_correction=1.0,
                                                         temp_used_for_scaling = None,
                                                         hybrid_boiler_service = self.boilerservicespace,
                                                         ),
                                    [1.0,1.0][t_idx] )
        self.assertEqual(self.heat_pump_with_boiler._HeatPump__service_results,
                                 [{'service_name': 'service_boiler_demand_energy', 'service_type': ServiceType.WATER, 
                                   'service_on': True, 'energy_output_required': 1.0, 'temp_output': 330.0, 
                                   'temp_source': 273.15, 'cop_op_cond': 2.9706605881515196,
                                   'thermal_capacity_op_cond': 8.417674488123662, 'time_running': 0.11879765621857688,
                                   'deg_coeff_op_cond': 0.9, 'time_constant_for_service': 1560,
                                   'use_backup_heater_only': False,
                                   'energy_delivered_HP': 0.9999999999999999, 'energy_input_backup': 0.0,
                                   'energy_delivered_backup': 0.0,
                                   'energy_delivered_total': 0.9999999999999999, 'energy_heating_circ_pump': 0.001781964843278653,
                                   'energy_source_circ_pump': 0.0011879765621857687, 'energy_output_required_boiler': 0.0,
                                   'energy_heating_warm_air_fan': 0, 'energy_output_delivered_boiler': 0.0},
                                 {'service_name': 'service_boiler_demand_energy', 'service_type': ServiceType.WATER, 
                                  'service_on': True, 'energy_output_required': 1.0, 'temp_output': 330.0, 
                                  'temp_source': 275.65, 'cop_op_cond': 3.107305509409639,
                                  'thermal_capacity_op_cond': 8.650924134797519, 'time_running': 0.11559458670751663,
                                  'deg_coeff_op_cond': 0.9, 'time_constant_for_service': 1560,
                                  'use_backup_heater_only': False,
                                  'energy_delivered_HP': 1.0, 'energy_input_backup': 0.0, 'energy_delivered_backup': 0.0, 
                                  'energy_delivered_total': 1.0,
                                  'energy_heating_circ_pump': 0.0017339188006127494, 'energy_source_circ_pump': 0.0011559458670751662,
                                  'energy_output_required_boiler': 0.0, 'energy_heating_warm_air_fan': 0,
                                   'energy_output_delivered_boiler': 0.0}])
        
        
        
        
    def test_running_time_throughput_factor(self):
        """ Check the cumulative running time and throughput factor (exhaust air HPs only) """
        
        self.energy_supply_conn_name_auxiliary = 'HeatPump_auxiliary: exhaust_runtime_throughput'
        project = MagicMock()
        project.temp_internal_air_prev_timestep.return_value = 30

        self.heat_pump_exhaust = HeatPump(self.heat_dict_exhaust,
                                 self.energysupply,
                                 self.energy_supply_conn_name_auxiliary,
                                 self.simtime,
                                 self.extcond,
                                 self.number_of_zones,
                                 throughput_exhaust_air = 101,
                                 project = project)
        
        time_running, throughput_factor_zone = self.heat_pump_exhaust._HeatPump__running_time_throughput_factor(
                                                        space_heat_running_time_cumulative = 0,
                                                        service_name = 'service_runtime_throughput',
                                                        service_type = ServiceType.WATER,
                                                        energy_output_required = 1.0,
                                                        temp_output = 330.0, # Kelvin
                                                        temp_return_feed =330.0, # Kelvin
                                                        temp_limit_upper= 340.0, # Kelvin
                                                        time_constant_for_service = 1350,
                                                        service_on = True, 
                                                        volume_heated_by_service = 100.0,
                                                        temp_spread_correction=1.0)
        self.assertAlmostEqual(time_running,  0.1305986895949177)
        self.assertAlmostEqual(throughput_factor_zone, 1.0)
            
    def test_calc_throughput_factor(self):
        
        self.assertAlmostEqual(self.heat_pump._HeatPump__calc_throughput_factor(time_running = 10),
                               1.0)

    def test_calc_energy_input(self):
        self.heat_pump._HeatPump__energy_supply_connections = {
            'service_water': MagicMock(),
            'service1': MagicMock(),
            'service2': MagicMock(),
            }
        self.heat_pump._HeatPump__service_results = [
            {
                'service_name': 'service_water',
                'service_type': ServiceType.WATER,
                'service_on': True,
                'energy_output_required': 1.0,
                'temp_output': 330.0,
                'temp_source': 273.15,
                'cop_op_cond': 2.9706605881515196,
                'thermal_capacity_op_cond': 8.417674488123662,
                'time_running': 0.11879765621857688,
                'deg_coeff_op_cond': 0.9,
                'time_constant_for_service': 1560,
                'use_backup_heater_only': False,
                'energy_delivered_HP': 0.9999999999999999,
                'energy_input_backup': 0.0,
                'energy_delivered_backup': 0.0,
                'energy_delivered_total': 0.9999999999999999,
                'energy_heating_circ_pump': 0.001781964843278653,
                'energy_source_circ_pump': 0.0011879765621857687,
                'energy_output_required_boiler': 0.0,
                'energy_heating_warm_air_fan': 0,
                'energy_output_delivered_boiler': 0.0,
            },
            {
                'service_name': 'service1',
                'service_type': ServiceType.SPACE,
                'service_on': True,
                'energy_output_required': 1.0,
                'temp_output': 330.0,
                'temp_source': 275.65,
                'cop_op_cond': 3.091723311370327,
                'thermal_capacity_op_cond': 6.9608039370972525,
                'time_running': 0.1476423586450323,
                'deg_coeff_op_cond': 0.9,
                'time_constant_for_service': 1560,
                'use_backup_heater_only': False,
                'energy_delivered_HP': 1.0,
                'energy_input_backup': 0.0,
                'energy_delivered_backup': 0.0,
                'energy_delivered_total': 1.0,
                'energy_heating_circ_pump': 0.0022146353796754846,
                'energy_source_circ_pump': 0.0014764235864503231,
                'energy_output_required_boiler': 0.0,
                'energy_heating_warm_air_fan': 0,
            },
            {
                'service_name': 'service2',
                'service_type': ServiceType.SPACE,
                'service_on': True,
                'energy_output_required': 0.97,
                'temp_output': 330.0,
                'temp_source': 275.65,
                'cop_op_cond': 3.091723311370327,
                'thermal_capacity_op_cond': 6.9608039370972525,
                'time_running': 0.1436615668300253,
                'deg_coeff_op_cond': 0.9,
                'time_constant_for_service': 1560,
                'use_backup_heater_only': False,
                'energy_delivered_HP': 1.0,
                'energy_input_backup': 0.0,
                'energy_delivered_backup': 0.0,
                'energy_delivered_total': 1.0,
                'energy_heating_circ_pump': 0.002154923502450379,
                'energy_source_circ_pump': 0.0014366156683002528,
                'energy_output_required_boiler': 0.0,
                'energy_heating_warm_air_fan': 0,
            },
        ]
        self.heat_pump._HeatPump__calc_energy_input()
        self.assertEqual(
            self.heat_pump._HeatPump__service_results,
            [
                {
                    'service_name': 'service_water',
                    'service_type': ServiceType.WATER,
                    'service_on': True,
                    'energy_output_required': 1.0,
                    'temp_output': 330.0,
                    'temp_source': 273.15,
                    'cop_op_cond': 2.9706605881515196,
                    'thermal_capacity_op_cond': 8.417674488123662,
                    'time_running': 0.11879765621857688,
                    'deg_coeff_op_cond': 0.9,
                    'cop_op_cond': 2.9706605881515196,
                    'compressor_power_min_load': 1.133441433423604,
                    'time_constant_for_service': 1560,
                    'use_backup_heater_only': False,
                    'hp_operating_in_onoff_mode': True,
                    'load_ratio': 0.11879765621857688,
                    'load_ratio_continuous_min': 0.4,
                    'energy_input_HP': 0.33789047423833063,
                    'energy_input_HP_divisor': 1.0,
                    'energy_delivered_HP': 0.9999999999999999,
                    'energy_input_backup': 0.0,
                    'energy_delivered_backup': 0.0,
                    'energy_input_total': 0.34086041564379504,
                    'energy_delivered_total': 0.9999999999999999,
                    'energy_heating_circ_pump': 0.001781964843278653,
                    'energy_source_circ_pump': 0.0011879765621857687,
                    'energy_output_required_boiler': 0.0,
                    'energy_heating_warm_air_fan': 0,
                    'energy_output_delivered_boiler': 0.0,
                },
                {
                    'service_name': 'service1',
                    'service_type': ServiceType.SPACE,
                    'service_on': True,
                    'energy_output_required': 1.0,
                    'temp_output': 330.0,
                    'temp_source': 275.65,
                    'time_constant_for_service': 1560,
                    'cop_op_cond': 3.091723311370327,
                    'thermal_capacity_op_cond': 6.9608039370972525,
                    'time_running': 0.1476423586450323,
                    'deg_coeff_op_cond': 0.9,
                    'compressor_power_min_load': 0.9005726885711587,
                    'load_ratio_continuous_min': 0.4,
                    'load_ratio': 0.29130392547505757,
                    'use_backup_heater_only': False,
                    'hp_operating_in_onoff_mode': True,
                    'energy_input_HP_divisor': 1.0,
                    'energy_input_HP': 0.3348701158353444,
                    'energy_delivered_HP': 1.0,
                    'energy_input_backup': 0.0,
                    'energy_delivered_backup': 0.0,
                    'energy_input_total': 0.3385611748014702,
                    'energy_delivered_total': 1.0,
                    'energy_heating_circ_pump': 0.0022146353796754846,
                    'energy_source_circ_pump': 0.0014764235864503231,
                    'energy_output_required_boiler': 0.0,
                    'energy_heating_warm_air_fan': 0,
                },
                {
                    'service_name': 'service2',
                    'service_type': ServiceType.SPACE,
                    'service_on': True,
                    'energy_output_required': 0.97,
                    'temp_output': 330.0,
                    'temp_source': 275.65,
                    'time_constant_for_service': 1560,
                    'cop_op_cond': 3.091723311370327,
                    'thermal_capacity_op_cond': 6.9608039370972525,
                    'time_running': 0.1436615668300253,
                    'deg_coeff_op_cond': 0.9,
                    'compressor_power_min_load': 0.9005726885711587,
                    'load_ratio_continuous_min': 0.4,
                    'load_ratio': 0.29130392547505757,
                    'use_backup_heater_only': False,
                    'hp_operating_in_onoff_mode': True,
                    'energy_input_HP_divisor': 1.0,
                    'energy_input_HP': 0.3258412149938673,
                    'energy_delivered_HP': 1.0,
                    'energy_input_backup': 0.0,
                    'energy_delivered_backup': 0.0,
                    'energy_input_total': 0.329432754164618,
                    'energy_delivered_total': 1.0,
                    'energy_heating_circ_pump': 0.002154923502450379,
                    'energy_source_circ_pump': 0.0014366156683002528,
                    'energy_output_required_boiler': 0.0,
                    'energy_heating_warm_air_fan': 0,
                }
            ]
        )
        self.heat_pump._HeatPump__energy_supply_connections['service_water'].\
            demand_energy.assert_called_once_with(0.34086041564379504)
        self.heat_pump._HeatPump__energy_supply_connections['service1'].\
            demand_energy.assert_called_once_with(0.3385611748014702)
        self.heat_pump._HeatPump__energy_supply_connections['service2'].\
            demand_energy.assert_called_once_with(0.329432754164618)

    def test_calc_ancillary_energy(self):
        
        self.heat_pump._HeatPump__create_service_connection('service_anc_energy')
        self.heat_pump._HeatPump__demand_energy(
                                                service_name = 'service_anc_energy',
                                                service_type = ServiceType.WATER,
                                                          energy_output_required = 1.0,
                                                          temp_output = 330.0, # Kelvin
                                                          temp_return_feed =330.0, # Kelvin
                                                          temp_limit_upper= 340.0, # Kelvin
                                                          time_constant_for_service = 1560,
                                                          service_on = True, # bool - is service allowed to run?
                                                          temp_spread_correction=1.0,
                                                          temp_used_for_scaling = None,
                                                          hybrid_boiler_service = None,
                                                          )
        self.heat_pump._HeatPump__calc_energy_input()
        self.assertEqual(self.heat_pump._HeatPump__service_results[0]['energy_input_HP'], 0.33789047423833063)
        self.assertEqual(self.heat_pump._HeatPump__service_results[0]['energy_input_total'], 0.34086041564379504)

        self.heat_pump._HeatPump__calc_ancillary_energy(timestep= 1,
                                                        time_remaining_current_timestep = 0.5)
        

        # Check if the energy_input_HP and energy_input_total were updated correctly
        self.assertEqual(self.heat_pump._HeatPump__service_results[0]['energy_input_HP'], 0.39541428732143846)
        self.assertEqual(self.heat_pump._HeatPump__service_results[0]['energy_input_total'], 0.3983842287269028)
        
    def test_calc_auxiliary_energy(self):
        
        energy_standby, energy_crankcase_heater_mode, \
        energy_off_mode = self.heat_pump._HeatPump__calc_auxiliary_energy(timestep= 1,
                                                        time_remaining_current_timestep = 0.5)
                                                        
        self.assertAlmostEqual(energy_standby, 0.0)
        self.assertAlmostEqual(energy_crankcase_heater_mode, 0.0)
        self.assertAlmostEqual(energy_off_mode, 0.015)
        
    def test_extract_energy_from_source(self):

        self.energy_supply_conn_name_auxiliary = 'HeatPump_auxiliary: hp1'
        
        self.heat_network = EnergySupply(simulation_time = self.simtime ,fuel_type = 'custom')
        self.heat_pump_with_nw = HeatPump(self.heat_dict_heat_nw,
                                 self.energysupply,
                                 self.energy_supply_conn_name_auxiliary,
                                 self.simtime,
                                 self.extcond,
                                 self.number_of_zones,
                                 heat_network = self.heat_network)
        
        self.heat_pump_with_nw._HeatPump__create_service_connection('service_extract_energy')
        self.heat_pump_with_nw._HeatPump__demand_energy(
                                                          service_name = 'service_extract_energy',
                                                          service_type = ServiceType.WATER,
                                                          energy_output_required = 1.0,
                                                          temp_output = 330.0, # Kelvin
                                                          temp_return_feed =330.0, # Kelvin
                                                          temp_limit_upper= 340.0, # Kelvin
                                                          time_constant_for_service = 1560,
                                                          service_on = True, 
                                                          temp_spread_correction=1.0,
                                                          temp_used_for_scaling = None,
                                                          hybrid_boiler_service = None,
                                                          )
        self.heat_pump_with_nw._HeatPump__calc_energy_input()
        test_service_results = self.heat_pump_with_nw._HeatPump__service_results
        # Call the method under test
        self.heat_pump_with_nw._HeatPump__extract_energy_from_source()
        actual_service_results = self.heat_pump_with_nw._HeatPump__service_results
        
        self.assertEqual(test_service_results, actual_service_results)
        
        # Check demand_energy function is called
        self.heat_pump._HeatPump__service_results = [
            {'service_name': 'service1', 'energy_delivered_HP': 100, 'energy_input_HP': 30},
            ]
        self.heat_pump._HeatPump__energy_supply_HN_connections = {
            'service1': MagicMock(),
            }
        self.heat_pump._HeatPump__extract_energy_from_source()
        self.heat_pump._HeatPump__energy_supply_HN_connections['service1'].\
            demand_energy.assert_called_once_with(100-30)
        
    def test_timestep_end(self):
        
        # Call demand_energy function to record the state of variables
        self.heat_pump._HeatPump__create_service_connection('servicetimestep_demand_energy')
        self.heat_pump._HeatPump__demand_energy(
                                                service_name = 'servicetimestep_demand_energy',
                                                service_type = ServiceType.WATER,
                                                energy_output_required = 5.0,
                                                temp_output = 330.0, # Kelvin
                                                temp_return_feed =330.0, # Kelvin
                                                temp_limit_upper= 340.0, # Kelvin
                                                time_constant_for_service = 1560,
                                                service_on = True,
                                                temp_spread_correction=1.0,
                                                temp_used_for_scaling = None,
                                                hybrid_boiler_service = None,
                                                )

        self.assertAlmostEqual(self.heat_pump._HeatPump__total_time_running_current_timestep, 0.5939882810928845)
        self.assertEqual(self.heat_pump._HeatPump__service_results,
                         [{'service_name': 'servicetimestep_demand_energy','service_type': ServiceType.WATER, 'service_on': True, 
                          'energy_output_required': 5.0, 'temp_output': 330.0, 'temp_source': 273.15, 'cop_op_cond': 2.9706605881515196,
                          'thermal_capacity_op_cond': 8.417674488123662, 'time_running': 0.5939882810928845, 'deg_coeff_op_cond': 0.9,
                          'time_constant_for_service': 1560, 'use_backup_heater_only': False,
                          'energy_delivered_HP': 5.0, 'energy_input_backup': 0.0, 'energy_delivered_backup': 0.0,
                          'energy_delivered_total': 5.0, 'energy_heating_circ_pump': 0.008909824216393266,
                          'energy_source_circ_pump': 0.005939882810928845, 'energy_output_required_boiler': 0.0, 'energy_heating_warm_air_fan': 0,
                          'energy_output_delivered_boiler': 0.0}])
        
        # Call the method under test
        self.heat_pump.timestep_end()

        self.assertAlmostEqual(self.heat_pump._HeatPump__total_time_running_current_timestep,
                                0.0)
        self.assertEqual(self.heat_pump._HeatPump__service_results,[])      

class TestHeatPump_HWOnly(unittest.TestCase):
    def setUp(self):
        self.heat_dict = {
            'M': {
                'cop_dhw': 2.7,
                'hw_tapping_prof_daily_total': 5.845,
                'energy_input_measured': 2.15,
                'power_standby': 0.02,
                'hw_vessel_loss_daily': 1.18
            },
            'L': {
                'cop_dhw': 2.5,
                'hw_tapping_prof_daily_total': 11.655,
                'energy_input_measured': 4.6,
                'power_standby': 0.03,
                'hw_vessel_loss_daily': 1.6
            }
        }
        self.simtime        = SimulationTime(0, 2, 1)
        self.energysupply   = EnergySupply("mains_gas", self.simtime)
        self.energy_supply_conn_name = 'HeatPump: hp'

        self.power_max = 3.0
        self.vol_daily_average = 150.0
        self.tank_volume = 200.0
        self.daily_losses = 1.5
        self.heat_exchanger_surface_area = 1.2
        self.in_use_factor_mismatch = 0.6
        self.tank_volume_declared = 180.0
        self.heat_exchanger_surface_area_declared = 1.0
        self.daily_losses_declared = 1.2

    def test_calc_efficiency(self):
        heat_pump = HeatPump_HWOnly(self.power_max, self.heat_dict, self.vol_daily_average,
                                    self.tank_volume, self.daily_losses, self.heat_exchanger_surface_area,
                                    self.in_use_factor_mismatch, self.tank_volume_declared,
                                    self.heat_exchanger_surface_area_declared, self.daily_losses_declared,
                                    self.energy_supply_conn_name, self.simtime)

        self.assertAlmostEqual(heat_pump.calc_efficiency(), 1.738556406)

