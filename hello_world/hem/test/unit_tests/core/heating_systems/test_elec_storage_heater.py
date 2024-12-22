#!/usr/bin/env python3

"""
This module contains unit tests for the ElecStorageHeater module
"""

# Standard library imports
import unittest

# Set path to include modules to be tested (must be before local imports)
from unittest.mock import Mock
from core.simulation_time import SimulationTime
from core.energy_supply.energy_supply import EnergySupplyConnection, EnergySupply
from core.heating_systems.elec_storage_heater import ElecStorageHeater, AirFlowType, OutputMode
from core.controls.time_control import SetpointTimeControl, ChargeControl
from core.external_conditions import ExternalConditions

class TestElecStorageHeater(unittest.TestCase):
    """ Unit tests for ElecStorageHeater class """

    def setUp(self):
        """ Create ElecStorageHeater object to be tested """
        self.simtime = SimulationTime(0, 24, 1)
        
        # Define schedule for ChargeControl
        self.schedule = [True, True, True, True, 
                         True, True, True, True, 
                         False, False, False, False,
                         False, False, False, False, 
                         True, True, True, True, 
                         False, False, False, False]
        
        # External conditions for ChargeControl
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

        self.external_sensor = {
            "correlation": [
                {"temperature": 0.0, "max_charge": 1.0},
                {"temperature": 10.0, "max_charge": 0.9},
                {"temperature": 18.0, "max_charge": 0.5}
            ]
        }

        # Create the ChargeControl object
        self.charge_control = ChargeControl("Automatic", self.schedule, self.simtime, 0, 1, [1.0, 0.8], 
                                            22, None, None, None, self.external_conditions, self.external_sensor)
        
        self.mock_zone = Mock()
        self.mock_zone.temp_internal_air.return_value = 20.0
        self.mock_zone.setpnt_init.return_value = 21.0

        energysupply = EnergySupply("electricity", self.simtime)
        energysupplyconn = energysupply.connection("storage_heater")

        control = SetpointTimeControl([21.0, 21.0, None, 21.0], self.simtime, 0, 1.0)

        self.ESH_min_output = [[0.0, 0.0], [0.5, 0.02], [1.0, 0.05]]
        self.ESH_max_output = [[0.0, 0.0], [0.5, 1.5], [1.0, 3.0]]

        # Initialize ElecStorageHeater with ChargeControl
        self.heater = ElecStorageHeater(
            pwr_in=3.5,  # kW
            rated_power_instant=2.5,  # kW
            storage_capacity=10.0,  # kWh
            air_flow_type="fan-assisted",
            frac_convective=0.7,
            fan_pwr=11,  # W
            n_units=1,
            zone=self.mock_zone,
            energy_supply_conn=energysupplyconn,
            simulation_time=self.simtime,
            control=control,
            charge_control=self.charge_control,  # Use real ChargeControl object here
            ESH_min_output=self.ESH_min_output,
            ESH_max_output=self.ESH_max_output,
            ext_cond=None
        )

        self.heater._ElecStorageHeater__state_of_charge = 0.5


    def test_initialisation(self):
        """Test that the ElecStorageHeater is initialised correctly."""
        self.assertEqual(self.heater._ElecStorageHeater__pwr_in, 3.5)
        self.assertEqual(self.heater._ElecStorageHeater__storage_capacity, 10.0)
        self.assertIsInstance(self.heater._ElecStorageHeater__air_flow_type, AirFlowType)
        self.assertEqual(self.heater._ElecStorageHeater__air_flow_type, AirFlowType.FAN_ASSISTED)

    def test_energy_output_min(self):
        """Test minimum energy output calculation across all timesteps."""
        expected_min_energy_output = [
            0.019999999999999997, 0.030419151282454364, 0.0406826518009459, 0.046014105108884346,
            0.04674323706081289, 0.045800000000000014, 0.046400000000000004, 0.038,
            0.046886897763894056, 0.03215061095009046, 0.021233700713726503, 0.01542628227371725,
            0.011428072222071864, 0.008466125322130943, 0.006271860545638567, 0.004646308882570838,
            0.010432746398675731, 0.01897277720547578, 0.019999999999999997, 0.019999999999999997,
            0.020056174317410178, 0.014844117518306485, 0.010996794239857175, 0.008146626650951819
        ]  # Actual minimum energy output for each timestep

        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                min_energy_output = self.heater.energy_output_min()
                energy_delivered = self.heater.demand_energy(5.0)
                self.assertAlmostEqual(
                    min_energy_output, 
                    expected_min_energy_output[t_idx], 
                    msg=f"energy output min failed at timestep {t_idx}"
                )

    def test_energy_output_max(self):
        """Test maximum energy output calculation across all timesteps."""
        expected_max_energy_output = [
            1.5, 1.772121660521405, 2.2199562136927717, 2.5517202117781994,
            2.7913851590672585, 2.7899999999999996, 2.8200000000000003, 2.4000000000000004,
            2.463423313846487, 1.8249489529640162, 1.3519554011630448, 1.0015529506734968,
            0.7419686857505708, 0.5496640579327374, 0.40720123344887615, 0.30166213975932143,
            0.6996897293886958, 1.3814284569589004, 1.5, 1.5,
            1.3009346098448467, 0.9637557636923015, 0.713967931076402, 0.5289205810615784
        ]  # Expected max energy output for each timestep

        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                max_energy_output = self.heater._ElecStorageHeater__energy_output_max()
                energy_delivered = self.heater.demand_energy(5.0)
                energy, time_used, __, __ = max_energy_output
                self.assertAlmostEqual(
                    energy, 
                    expected_max_energy_output[t_idx], 
                    msg=f"energy output max failed at timestep {t_idx}"
                )

    def test_electric_charge(self):
        """Test electric charge calculation across all timesteps."""
        expected_target_elec_charge = [
            0.5, 1.0, 0.99, 0.98,
            0.95, 0.93, 0.9400000000000001, 0.8,
            0.0, 0.0, 0.0, 0.0,
            0.0, 0.0, 0.0, 0.0,
            0.5, 0.5, 0.5, 0.5,
            0.0, 0.0, 0.0, 0.0
            ]  # Expected target charge for each timestep

        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                target_elec_charge = self.heater._ElecStorageHeater__target_electric_charge(time=self.simtime.current_hour())
                self.assertAlmostEqual(
                    target_elec_charge, 
                    expected_target_elec_charge[t_idx],
                    msg=f"target electric charge failed at timestep {t_idx}")

    def test_demand_energy(self):
        """Test demand energy functionality across all timesteps."""
        expected_energy = [
            4.0, 4.272121660521405, 4.719956213692772, 5.0,
            5.0, 5.0, 5.0, 4.9,
            4.963423313846487, 4.324948952964016, 3.851955401163045, 3.5015529506734966,
            3.241968685750571, 3.0496640579327376, 2.907201233448876, 2.8016621397593213,
            3.199689729388696, 3.8814284569589006, 4.0, 4.0,
            3.8009346098448464, 3.4637557636923013, 3.213967931076402, 3.0289205810615782
            ]  # Expected energy for each timestep

        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                energy_out = self.heater.demand_energy(5.0)
                self.assertAlmostEqual(
                    energy_out, 
                    expected_energy[t_idx], 
                    msg=f"demand energy failed at timestep {t_idx}"
                )

    def test_energy_for_fan(self):
        """Test energy for fan calculation across all timesteps."""
        expected_energy_for_fan = [
            0.003666666666666666, 0.002707621094790285, 0.0019580976410457644, 0.0018707482993197276,
            0.0019298245614035089, 0.0019713261648745518, 0.001950354609929078, 0.0022916666666666662,
            0.0021220628632204496, 0.002233750362976654, 0.0023578475867206904, 0.0024965444862427343,
            0.0026525785014320812, 0.0028294170564121318, 0.003031518268419362, 0.0032647119841350417,
            0.003666666666666666, 0.003666666666666666, 0.003666666666666666, 0.003666666666666666,
            0.0021220628632204505, 0.0022337503629766544, 0.0023578475867206913, 0.002496544486242736
        ]  # Expected energy for fan for each timestep

        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                energy_delivered = self.heater.demand_energy(0.5)
                energy_for_fan = self.heater._ElecStorageHeater__energy_for_fan
                self.assertAlmostEqual(
                    energy_for_fan, 
                    expected_energy_for_fan[t_idx], 
                    msg=f"Energy for fan failed at timestep {t_idx}"
                )

    def test_energy_instant(self):
        """Test instant energy output calculation across all timesteps."""
        expected_energy_instant = [
            2.5, 2.5, 2.5, 2.4482797882218006,
            2.208614840932741, 2.2100000000000004, 2.18, 2.5,
            2.5, 2.5, 2.5, 2.5,
            2.5, 2.5, 2.5, 2.5,
            2.5, 2.5, 2.5, 2.5,
            2.5, 2.5, 2.5, 2.5
        ]  # Expected backup energy instant for each timestep

        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                energy_delivered = self.heater.demand_energy(5)
                energy_instant = self.heater._ElecStorageHeater__energy_instant
                self.assertAlmostEqual(
                    energy_instant, 
                    expected_energy_instant[t_idx], 
                    msg=f"Energy instant failed at timestep {t_idx}"
                )

    def test_energy_charged(self):
        """Test energy charged calculation across all timesteps."""
        expected_energy_charged = [
            1.5, 3.500000000000001, 3.5, 3.5,
            3.3397997646920756, 2.7899999999999996, 2.82, 2.4000000000000004,
            0.0, 0.0, 0.0, 0.0,
            0.0, 0.0, 0.0, 0.0,
            3.500000000000001, 2.738269398472182, 1.5, 1.5,
            0.0, 0.0, 0.0, 0.0
        ]  # Expected energy charged for each timestep

        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                energy_delivered = self.heater.demand_energy(5)
                energy_charged = self.heater._ElecStorageHeater__energy_charged
                self.assertAlmostEqual(
                    energy_charged, 
                    expected_energy_charged[t_idx], 
                    msg=f"Energy charged failed at timestep {t_idx}"
                )

    def test_energy_stored_delivered(self):
        """Test stored energy delivered calculation across all timesteps."""
        expected_energy_delivered = [
            1.5, 1.772121660521405, 2.219956213692772, 2.5517202117781994,
            2.791385159067259, 2.7899999999999996, 2.82, 2.4000000000000004,
            2.4634233138464876, 1.8249489529640166, 1.3519554011630448, 1.0015529506734968,
            0.7419686857505706, 0.5496640579327375, 0.4072012334488761, 0.30166213975932155,
            0.6996897293886956, 1.3814284569589008, 1.5, 1.5,
            1.300934609844847, 0.9637557636923016, 0.713967931076402, 0.5289205810615786
        ]  # Expected energy stored delivered for each timestep

        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                energy_demand = self.heater.demand_energy(5)
                energy_delivered = self.heater._ElecStorageHeater__energy_delivered
                self.assertAlmostEqual(
                    energy_delivered, 
                    expected_energy_delivered[t_idx], 
                    msg=f"Energy stored delivered failed at timestep {t_idx}"
                )
                
    def test_invalid_air_flow_type(self):
        """Test invalid air flow type."""
        with self.assertRaises(SystemExit):
            ElecStorageHeater(
                pwr_in=3.5,
                rated_power_instant=2.5,
                storage_capacity=10.0,
                air_flow_type='invalid-type',
                frac_convective=0.7,
                fan_pwr=0.1,
                n_units=1,
                zone=self.mock_zone,
                energy_supply_conn=self.heater._ElecStorageHeater__energy_supply_conn,
                simulation_time=self.simtime,
                control=self.heater._ElecStorageHeater__control,
                charge_control=self.heater._ElecStorageHeater__charge_control,
                ESH_min_output=self.ESH_min_output,
                ESH_max_output=self.ESH_max_output,
                ext_cond=None
            )
