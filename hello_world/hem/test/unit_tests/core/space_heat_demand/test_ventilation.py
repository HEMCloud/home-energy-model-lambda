# Standard library imports
import unittest
from unittest.mock import patch, MagicMock

# Set path to include modules to be tested (must be before local imports)
from unit_tests.common import test_setup
test_setup()

# Local imports
from core.energy_supply.energy_supply import EnergySupply,EnergySupplyConnection
from core.schedule import expand_schedule
from core.controls.time_control import OnOffTimeControl
from core.space_heat_demand.ventilation import *
from core.units import seconds_per_hour, Celcius2Kelvin, litres_per_cubic_metre, \
    W_per_kW
from core.simulation_time import SimulationTime
from core.external_conditions import ExternalConditions
from core.material_properties import AIR

# Define constants
p_a_ref = AIR.density_kg_per_m3()
c_a = AIR.specific_heat_capacity_kWh()

# (Default values from BS EN 16798-7, Table 11)
# Coefficient to take into account stack effect in airing calculation in (m/s)/(m*K)
C_stack = 0.0035
# Coefficient to take into account wind speed in airing calculation in 1/(m/s)
C_wnd = 0.001
# Gravitational constant in m/s2
g = 9.81
#Room temperature in degrees K
T_e_ref = 293.15
#Absolute zero in degrees K
T_0_abs = 273.15

class TestFunctions(unittest.TestCase):

    def test_calculate_pressure_difference_at_an_airflow_path(self):
        h_path = 0.4
        C_p_path = 0.45
        u_site = 1
        T_e = 294.95
        T_z = 299.15
        p_z_ref = 2.5
        result = calculate_pressure_difference_at_an_airflow_path(h_path, C_p_path, u_site, T_e, T_z, p_z_ref)
        self.assertAlmostEqual(result, -2.2966793114) #Use spreadsheet to find answer.

    def test_wind_speed_at_zone_level(self):
        C_rgh_site = 0.8
        u_10 = 10
        result = wind_speed_at_zone_level(C_rgh_site, u_10)
        self.assertAlmostEqual(result, 8)

    def test_get_fuel_flow_factor(self):
        self.assertEqual(get_fuel_flow_factor('wood', 'open_fireplace'), 2.8)
        self.assertEqual(get_fuel_flow_factor('gas', 'closed_with_fan'), 0.38)
        self.assertEqual(get_fuel_flow_factor('gas', 'open_gas_flue_balancer'), 0.78)
        self.assertEqual(get_fuel_flow_factor('gas', 'open_gas_kitchen_stove'), 3.35)
        self.assertEqual(get_fuel_flow_factor('gas', 'open_gas_fire'), 3.35)
        self.assertEqual(get_fuel_flow_factor('oil', 'closed_fire'), 0.32)
        self.assertEqual(get_fuel_flow_factor('coal', 'closed_fire'), 0.52)
        
        with self.assertRaises(SystemExit):
            get_fuel_flow_factor('wood', 'invalid_appliance')
        
        with self.assertRaises(SystemExit):
            get_fuel_flow_factor('invalid_fuel', 'closed_fire')

    def test_get_appliance_system_factor(self):
        self.assertEqual(get_appliance_system_factor('outside', 'into_room'), 0)
        self.assertEqual(get_appliance_system_factor('room_air', 'into_room'), 0)
        self.assertEqual(get_appliance_system_factor('room_air', 'into_separate_duct'), 1)

        with self.assertRaises(SystemExit):
            get_appliance_system_factor('room_air', 'into_mech_vent')

        with self.assertRaises(SystemExit):
            get_appliance_system_factor('room_air', 'invalid_exhaust')

        with self.assertRaises(SystemExit):
            get_appliance_system_factor('invalid_supply', 'into_room')

    def test_adjust_air_density_for_altitude(self):
        h_alt = 10  # meters
        expected = 1.2028621569154314 # Pa
        result = adjust_air_density_for_altitude(h_alt)
        self.assertAlmostEqual(result, expected)

    def test_air_density_at_temp(self):
        temperature = 300  # K
        air_density_adjusted_for_alt = 1.2  # kg/m^3
        expected = 1.1725999999999999  # kg/m^3
        result = air_density_at_temp(temperature, air_density_adjusted_for_alt)
        self.assertAlmostEqual(result, expected)

    def test_convert_volume_flow_rate_to_mass_flow_rate(self):
        qv = 1000  # m^3/h
        temperature = 300  # K
        p_a_alt = p_a_ref
        expected = 1176.5086666666666  # kg/h
        result = convert_volume_flow_rate_to_mass_flow_rate(qv, temperature, p_a_alt)
        self.assertAlmostEqual(result, expected)

    def test_convert_mass_flow_rate_to_volume_flow_rate(self):
        qm = 1200  # kg/h
        temperature = 300  # K
        p_a_alt = p_a_ref
        expected = 1019.9669870685186  # m^3/h
        result = convert_mass_flow_rate_to_volume_flow_rate(qm, temperature, p_a_alt)
        self.assertAlmostEqual(result, expected)

    def test_convert_to_mass_air_flow_rate(self):
        qv_in = 30  # m^3/h
        qv_out = 40  # m^3/h
        T_e = 300  # K
        T_z = 295  # K
        p_a_alt = p_a_ref
        expected_qm_in = 35.29526  # kg/h
        expected_qm_out = 47.85797966101694  # kg/h
        qm_in, qm_out = convert_to_mass_air_flow_rate(qv_in, qv_out, T_e, T_z, p_a_alt)
        self.assertAlmostEqual(qm_in, expected_qm_in)
        self.assertAlmostEqual(qm_out, expected_qm_out)

    def test_ter_class_to_roughness_coeff(self):
        """Test converting terrain class to roughness coefficient."""
        z = 2.5

        self.assertAlmostEqual(ter_class_to_roughness_coeff('OpenWater', z), 0.9386483560365819)
        self.assertAlmostEqual(ter_class_to_roughness_coeff('OpenField', z), 0.8325850605880374)
        self.assertAlmostEqual(ter_class_to_roughness_coeff('Suburban', z), 0.7223511561212699)
        self.assertAlmostEqual(ter_class_to_roughness_coeff('Urban', z), 0.6654212933375474)


    def test_orientation_difference(self):
        # Test simple cases
        self.assertEqual(orientation_difference(0, 90), 90)
        self.assertEqual(orientation_difference(100, 90), 10)
        # Test handling of out of range input
        self.assertRaises(ValueError, orientation_difference, 0, 450)
        self.assertRaises(ValueError, orientation_difference, 540, 180)
        self.assertRaises(ValueError, orientation_difference, 90, -290)
        self.assertRaises(ValueError, orientation_difference, -90, 90)
        # Test cases where shortest angle crosses North
        self.assertEqual(orientation_difference(0, 310), 50)
        self.assertEqual(orientation_difference(300, 10), 70)

    def test_get_facade_direction(self):
        self.assertEqual(get_facade_direction(True, 0, 5, 0), "Roof10")
        self.assertEqual(get_facade_direction(True, 0, 20, 0), "Roof10_30")
        self.assertEqual(get_facade_direction(True, 0, 45, 0), "Roof30")
        self.assertEqual(get_facade_direction(True, 0, 70, 0), "Windward")
        self.assertEqual(get_facade_direction(True, 180, 70, 0), "Leeward")
        self.assertEqual(get_facade_direction(True, 90, 70, 0), "Neither")
        self.assertEqual(get_facade_direction(False, 0, 45, 0), "Roof")
        self.assertEqual(get_facade_direction(False, 0, 70, 0), "Windward")
        self.assertEqual(get_facade_direction(False, 180, 70, 0), "Leeward")
        self.assertEqual(get_facade_direction(False, 270, 70, 0), "Neither")

        with self.assertRaises(SystemExit):
            get_facade_direction("invalid", 0, 45, 0)

    def test_get_C_p_path(self):
        self.assertAlmostEqual(get_C_p_path(True, "Open", 10, 0, orientation=0, pitch=70), 0.50)
        self.assertAlmostEqual(get_C_p_path(True, "Normal", 10, 0, orientation=0, pitch=70), 0.25)
        self.assertAlmostEqual(get_C_p_path(True, "Shielded", 10, 0, orientation=0, pitch=70), 0.05)
        self.assertAlmostEqual(get_C_p_path(True, "Open", 30, 0, orientation=0, pitch=70), 0.65)
        self.assertAlmostEqual(get_C_p_path(True, "Normal", 30, 0, orientation=0, pitch=70), 0.45)
        self.assertAlmostEqual(get_C_p_path(True, "Shielded", 30, 0, orientation=0, pitch=70), 0.25)
        self.assertAlmostEqual(get_C_p_path(True, "Open", 60, 0, orientation=0, pitch=70), 0.80)
        self.assertAlmostEqual(get_C_p_path(True, "Normal", 30, 90, orientation=0, pitch=70), 0.00)
        self.assertAlmostEqual(get_C_p_path(False, "Normal", 10, 0, orientation=0, pitch=70), 0.05)
        self.assertAlmostEqual(get_C_p_path(False, "Normal", 10, 0, orientation=0, pitch=45), 0.00)
        self.assertAlmostEqual(get_C_p_path(False, "Normal", 15, 270, orientation=10, pitch=90), 0.00)

        with self.assertRaises(SystemExit):
            get_C_p_path(True, "Normal", 10, 0)

class TestWindow(unittest.TestCase):
    def setUp(self):

        self.simtime = SimulationTime(0, 2, 1)
        self.windspeed = [3.7, 3.8, 3.9, 4.0, 4.1, 4.2, 4.3, 4.4]
        self.wind_direction = [200, 220, 230, 240, 250, 260, 260, 270]
        self.airtemp = [0.0, 2.5, 5.0, 7.5, 10.0, 12.5, 15.0, 20.0]
        self.diffuse_horizontal_radiation = [333, 610, 572, 420, 0, 10, 90, 275]
        self.direct_beam_radiation = [420, 750, 425, 500, 0, 40, 0, 388]
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
            {"number": 3, "start": 90, "end": 45},
            {"number": 4, "start": 45, "end": 0},
            {"number": 5, "start": 0, "end": -45},
            {"number": 6, "start": -45, "end": -90},
            {"number": 7, "start": -90, "end": -135},
            {"number": 8, "start": -135, "end": -180}
        ]

        sched = expand_schedule(bool, {'main':[{'repeat': 8760, 'value': True}]}, "main", False)
        ctrl = OnOffTimeControl(
                    schedule=sched,
                    simulation_time=self.simtime,
                    start_day= 0,
                    time_series_step = 1
                )
        
        window_part_list = [{'mid_height_air_flow_path': 1.5}]
        self.__window = Window(
            h_w_fa=1.6,
            h_w_path=1.5,
            A_w_max=3,
            window_part_list=window_part_list,
            orientation=0,
            pitch=90,
            altitude=0,
            on_off_ctrl_obj = True,
            ventilation_zone_base_height=0 
        )

    def test_calculate_window_opening_free_area_ctrl_off(self):
        mock_ctrl = MagicMock()
        mock_ctrl.is_on.return_value = False
        self.__window._Window__on_off_ctrl_obj = mock_ctrl
        self.assertEqual(self.__window.calculate_window_opening_free_area(0.5), 0)

    def test_calculate_window_opening_free_area_ctrl_on(self):
        mock_ctrl = MagicMock()
        mock_ctrl.is_on.return_value = True
        self.__window._Window__on_off_ctrl_obj = mock_ctrl
        self.assertEqual(self.__window.calculate_window_opening_free_area(0.5), 1.5)

    def test_calculate_flow_coeff_for_window_ctrl_off(self):
        mock_ctrl = MagicMock()
        mock_ctrl.is_on.return_value = False
        self.__window._Window__on_off_ctrl_obj = mock_ctrl
        self.assertAlmostEqual(self.__window.calculate_flow_coeff_for_window(0.5), 0)

    def test_calculate_flow_coeff_for_window_ctrl_on(self):
        mock_ctrl = MagicMock()
        mock_ctrl.is_on.return_value = True
        self.__window._Window__on_off_ctrl_obj = mock_ctrl
        expected_A_w = 1.5
        expected_flow_coeff = 3600 * self.__window._Window__C_D_w * expected_A_w * (2/p_a_ref) ** self.__window._Window__n_w
        self.assertAlmostEqual(self.__window.calculate_flow_coeff_for_window(0.5), expected_flow_coeff)

    def test_calculate_flow_from_internal_p(self):
        u_site = 5.0
        p_a_alt = p_a_ref
        T_e = 290.15
        T_z = 293.15
        p_z_ref = 1
        f_cross = True
        shield_class = "Open"
        R_w_arg = 0.5
        mock_ctrl = MagicMock()
        mock_ctrl.is_on.return_value = True
        self.__window._Window__on_off_ctrl_obj = mock_ctrl

        qm_in, qm_out = self.__window.calculate_flow_from_internal_p(
            self.wind_direction[0],
            u_site,
            Celcius2Kelvin(self.airtemp[0]),
            T_z,
            p_z_ref,
            f_cross,
            shield_class,
            R_w_arg,
            )

        ''' qm_in returns 0.0 and qm_out returns -20707.309683335046'''
        self.assertAlmostEqual(qm_in, 0)
        self.assertAlmostEqual(qm_out, -20707.309683335)


class TestWindowPart(unittest.TestCase):
    def setUp(self):
        # Initialize your WindowPart object here or mock if needed
        self.window_part = WindowPart(
            h_w_path=1,
            h_w_fa=1.6,
            N_w_div = 0,
            window_part_number=1,
            ventilation_zone_base_height=0
        )

    def test_calculate_ventilation_through_windows_using_internal_p(self):
        ''' Function call returns -13235.33116157'''
        u_10 = 5
        C_rgh_site = 1
        u_site = 3.7
        T_e = 273.15
        T_z = 293.15
        C_w_path = 4663.05
        C_p_path = -0.7
        p_z_ref = 1
        expected_output = -13235.33116157
        self.assertAlmostEqual(
            self.window_part.calculate_ventilation_through_windows_using_internal_p(
                u_site,
                T_e,
                T_z,
                C_w_path,
                p_z_ref,
                C_p_path,
                ),
            expected_output
        )

    def test_calculate_height_for_delta_p_w_div_path(self):
        '''Function returns 1'''
        window_part_number = 1
        expected_output = 1
        self.assertAlmostEqual(
            self.window_part.calculate_height_for_delta_p_w_div_path(window_part_number), expected_output
        )
        

class TestVent(unittest.TestCase):
    def setUp(self):
        # Initialize your Vent object here or mock if needed
        self.simtime = SimulationTime(0, 2, 1)
        self.windspeed = [3.7, 3.8, 3.9, 4.0, 4.1, 4.2, 4.3, 4.4]
        self.wind_direction = [200, 220, 230, 240, 250, 260, 260, 270]
        self.airtemp = [0.0, 2.5, 5.0, 7.5, 10.0, 12.5, 15.0, 20.0]
        self.diffuse_horizontal_radiation = [333, 610, 572, 420, 0, 10, 90, 275]
        self.direct_beam_radiation = [420, 750, 425, 500, 0, 40, 0, 388]
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
            {"number": 3, "start": 90, "end": 45},
            {"number": 4, "start": 45, "end": 0},
            {"number": 5, "start": 0, "end": -45},
            {"number": 6, "start": -45, "end": -90},
            {"number": 7, "start": -90, "end": -135},
            {"number": 8, "start": -135, "end": -180}
        ]

        self.__vent = Vent(
            h_path = 1,
            A_vent = 100.0,
            delta_p_vent_ref = 20.0,
            orientation = 0,
            pitch = 90.0,
            altitude = 0,
            ventilation_zone_base_height=0
            )

    def test_calculate_vent_opening_free_area(self):
        ''' Returns output '''
        R_v_arg = 0.5
        expected_output = 50
        self.assertAlmostEqual(
            self.__vent.calculate_vent_opening_free_area(R_v_arg), expected_output
        )

    def test_calculate_flow_coeff_for_vent(self):
        ''' Returns output 27.8391201602292'''
        R_v_arg = 1
        expected_output = 27.8391201602292
        self.assertAlmostEqual(
            self.__vent.calculate_flow_coeff_for_vent(R_v_arg), expected_output
        )

    def test_calculate_ventilation_through_vents_using_internal_p(self):
        ''' Returns  -79.01694696980 '''
        
        u_10 = 5
        C_rgh_site = 1
        u_site = 3.7
        T_e = 273.15
        T_z = 293.15
        C_vent_path = 27.8391201602292
        C_p_path = -0.7
        p_z_ref = 1
        expected_output = -79.01694696980

        self.assertAlmostEqual(
            self.__vent.calculate_ventilation_through_vents_using_internal_p(u_site,
                                                                           T_e,
                                                                           T_z,
                                                                           C_vent_path,
                                                                           C_p_path,
                                                                           p_z_ref
                                                                           ),
            expected_output
        )

    def test_calculate_flow_from_internal_p(self):
        
        u_10 = 5
        C_rgh_site = 1
        u_site = 3.7
        T_z = 293.15
        p_z_ref = 1
        f_cross = True
        shield_class = "Open"
        R_v_arg = 1
        
        qm_in_through_vent, qm_out_through_vent = self.__vent.calculate_flow_from_internal_p(
                                                     self.wind_direction[0],
                                                     u_site,
                                                     Celcius2Kelvin(self.airtemp[0]),
                                                     T_z, 
                                                     p_z_ref, 
                                                     f_cross, 
                                                     shield_class,
                                                     R_v_arg,
                                                     )

        ''' qm_in_through_vent returns 0.0 and qm_out_through_vent returns  -95.136404151646'''
        self.assertAlmostEqual(qm_in_through_vent, 0.0)
        self.assertAlmostEqual(qm_out_through_vent, -95.136404151646)

class TestLeaks(unittest.TestCase):
    def setUp(self):
        self.simtime = SimulationTime(0, 2, 1)
        self.windspeed = [3.7, 3.8, 3.9, 4.0, 4.1, 4.2, 4.3, 4.4]
        self.wind_direction = [200, 220, 230, 240, 250, 260, 260, 270]
        self.airtemp = [0.0, 2.5, 5.0, 7.5, 10.0, 12.5, 15.0, 20.0]
        self.diffuse_horizontal_radiation = [333, 610, 572, 420, 0, 10, 90, 275]
        self.direct_beam_radiation = [420, 750, 425, 500, 0, 40, 0, 388]
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
            {"number": 3, "start": 90, "end": 45},
            {"number": 4, "start": 45, "end": 0},
            {"number": 5, "start": 0, "end": -45},
            {"number": 6, "start": -45, "end": -90},
            {"number": 7, "start": -90, "end": -135},
            {"number": 8, "start": -135, "end": -180}
        ]

        self.__leaks = Leaks(
            h_path = 1,
            delta_p_leak_ref = 50.0,
            qv_delta_p_leak_ref = 1.2,
            facade_direction = 'Leeward',
            A_roof = 100.0,
            A_facades = 120.0,
            A_leak = 220.0,
            altitude = 0,
            ventilation_zone_base_height=0
            )

    def test_calculate_flow_coeff_for_leak(self):
        ''' function returns value 2.6490460494125543'''
        expected_result = 2.6490460494125543
        self.assertAlmostEqual(
            self.__leaks.calculate_flow_coeff_for_leak(),
            expected_result
            )

    def test_calculate_ventilation_through_leaks_using_internal_p(self):
        ''' Returns  -10.6531458050959'''
        u_10 = 5
        C_rgh_site = 1
        u_site = 3.7
        T_e = 273.15
        T_z = 293.15
        C_p_path = -0.7
        p_z_ref = 1
        expected_output = -10.6531458050959

        self.assertAlmostEqual(
            self.__leaks.calculate_ventilation_through_leaks_using_internal_p(u_site,
                                                                           T_e,
                                                                           T_z,
                                                                           C_p_path,
                                                                           p_z_ref
                                                                           ),
            expected_output)

    def test_calculate_flow_from_internal_p(self):
        ''' Returns 0.0 for in and -12.826387549335472 for out'''

        u_10 = 5
        C_rgh_site = 1
        u_site = 3.7
        T_z = 293.15
        p_z_ref = 1
        f_cross = True
        shield_class = "Open"

        qm_in_through_leaks, qm_out_through_leaks = self.__leaks.calculate_flow_from_internal_p(
            self.wind_direction[0],
            u_site,
            Celcius2Kelvin(self.airtemp[0]),
            T_z,
            p_z_ref,
            f_cross,
            shield_class,
            )

        self.assertAlmostEqual(qm_in_through_leaks, 0)
        self.assertAlmostEqual(qm_out_through_leaks, -12.826387549335472)

class TestCombustionApplicances(unittest.TestCase):
    def setUp(self):
        self.__combustion_appliances = CombustionAppliances(
                                                supply_situation  = 'room_air',
                                                exhaust_situation = 'into_separate_duct',
                                                fuel_type = 'wood',
                                                appliance_type = 'open_fireplace'
                                            ) 
        
    def test_calculate_air_flow_req_for_comb_appliance(self):
        ''' Returns 0.0 for in and -10.08 for out'''
        f_op_comp = 1
        P_h_fi = 1
        q_in_comb, q_out_comb = self.__combustion_appliances.calculate_air_flow_req_for_comb_appliance(f_op_comp, P_h_fi)

        self.assertAlmostEqual(q_in_comb, 0)
        self.assertAlmostEqual(q_out_comb, -10.08)

class TestMechanicalVentilation(unittest.TestCase):
    def setUp(self):
        self.simtime = SimulationTime(0, 2, 1)
        self.windspeed = [3.7, 3.8, 3.9, 4.0, 4.1, 4.2, 4.3, 4.4]
        self.wind_direction = [200, 220, 230, 240, 250, 260, 260, 270]
        self.airtemp = [0.0, 2.5, 5.0, 7.5, 10.0, 12.5, 15.0, 20.0]
        self.diffuse_horizontal_radiation = [333, 610, 572, 420, 0, 10, 90, 275]
        self.direct_beam_radiation = [420, 750, 425, 500, 0, 40, 0, 388]
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
            {"number": 3, "start": 90, "end": 45},
            {"number": 4, "start": 45, "end": 0},
            {"number": 5, "start": 0, "end": -45},
            {"number": 6, "start": -45, "end": -90},
            {"number": 7, "start": -90, "end": -135},
            {"number": 8, "start": -135, "end": -180}
        ]

        self.__mechvent = MechanicalVentilation(
                                sup_air_flw_ctrl = 'ODA',
                                sup_air_temp_ctrl = 'CONST',
                                Q_H_des = 1.0,
                                Q_C_des = 3.4,
                                vent_type = 'MVHR',
                                specific_fan_power = 1.5,
                                design_outdoor_air_flow_rate = 0.5,
                                simulation_time = self.simtime,
                                energy_supply_conn = EnergySupplyConnection(
                                    EnergySupply('electricity',self.simtime),
                                    'mech_vent_fans'),
                                total_volume = 250.0,
                                altitude = 0,
                                ctrl_intermittent_MEV = None,
                                mvhr_eff = 0.0,
                                )

    def test_calculate_required_outdoor_air_flow_rate(self):
        ''' Returns 0.55'''
        expected_result =  0.55
        self.assertAlmostEqual(self.__mechvent.calculate_required_outdoor_air_flow_rate(),
                               expected_result)

    def test_calc_req_ODA_flow_rates_at_ATDs(self):
        
        ''' Retruns 0.55 -0.55 for SUP and ETA''' 
        qv_SUP_req, qv_ETA_req = self.__mechvent.calc_req_ODA_flow_rates_at_ATDs()
        self.assertAlmostEqual(qv_SUP_req,0.55)
        self.assertAlmostEqual(qv_ETA_req,-0.55)
    
    def test_calc_mech_vent_air_flw_rates_req_to_supply_vent_zone(self):
        '''0.7106861797547136 -0.6622 0.0'''
        qm_SUP_dis_req, qm_ETA_dis_req, qm_in_effective_heat_recovery_saving = \
            self.__mechvent.calc_mech_vent_air_flw_rates_req_to_supply_vent_zone(
                T_z = 293.15,
                T_e = Celcius2Kelvin(self.airtemp[0])
                )
        self.assertAlmostEqual(qm_SUP_dis_req, 0.7106861797547136)
        self.assertAlmostEqual(qm_ETA_dis_req, -0.6622)
        self.assertAlmostEqual(qm_in_effective_heat_recovery_saving, 0)
    
    #def test_fans(self):  
     
        #fan_energy = self.__mechvent.fans(zone_volume = 10.0, throughput_factor = 1.0)
        # print(fan_energy)
        # #self.assertAlmostEqual()

class TestInfiltrationVentilation(unittest.TestCase):
    def setUp(self):
        self.simtime = SimulationTime(0, 2, 1)
        self.windspeed = [3.7, 3.8, 3.9, 4.0, 4.1, 4.2, 4.3, 4.4]
        self.wind_direction = [200, 220, 230, 240, 250, 260, 260, 270]
        self.airtemp = [0.0, 2.5, 5.0, 7.5, 10.0, 12.5, 15.0, 20.0]
        self.diffuse_horizontal_radiation = [333, 610, 572, 420, 0, 10, 90, 275]
        self.direct_beam_radiation = [420, 750, 425, 500, 0, 40, 0, 388]
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
            {"number": 3, "start": 90, "end": 45},
            {"number": 4, "start": 45, "end": 0},
            {"number": 5, "start": 0, "end": -45},
            {"number": 6, "start": -45, "end": -90},
            {"number": 7, "start": -90, "end": -135},
            {"number": 8, "start": -135, "end": -180}
        ]

        sched = expand_schedule(bool, {'main':[{'repeat': 8760, 'value': True}]}, "main", False)
        ctrl = OnOffTimeControl(
                    schedule=sched,
                    simulation_time=self.simtime,
                    start_day= 0,
                    time_series_step = 1
                )
        window_part_list = [{'mid_height_air_flow_path': 1.5}]
        self.window = Window(
            h_w_fa=1.6,
            h_w_path=1,
            A_w_max=3,
            window_part_list=window_part_list,
            orientation=0,
            pitch=90,
            altitude=30,
            on_off_ctrl_obj = ctrl,
            ventilation_zone_base_height=2.5
        )
        
        self.window_dict = {'window 0' : self.window}
        
        self.vent = Vent(
            h_path = 1.5,
            A_vent = 100.0,
            delta_p_vent_ref = 20.0,
            orientation = 0.0,
            pitch = 90.0,
            altitude = 30.0,
            ventilation_zone_base_height=2.5
            )
        self.vent_dict = {'vent 1' : self.vent}
        self.leaks_dict =   { 
                        'ventilation_zone_height': 6, 
                        'test_pressure': 50, 
                        'test_result': 1.2, 
                        'env_area': 220,
                        'area_facades': 85.0, 
                        'area_roof': 25.0,
                        'altitude': 30.0
                        }
        
        self.mechvent = MechanicalVentilation(
                                sup_air_flw_ctrl = 'ODA',
                                sup_air_temp_ctrl = 'CONST',
                                Q_H_des = 1.0,
                                Q_C_des = 3.4,
                                vent_type = 'MVHR',
                                specific_fan_power = 1.5,
                                design_outdoor_air_flow_rate = 0.5,
                                simulation_time = self.simtime,
                                energy_supply_conn = EnergySupplyConnection(
                                    EnergySupply('electricity',self.simtime),
                                    'mech_vent_fans'),
                                total_volume = 250.0,
                                altitude = 0,
                                ctrl_intermittent_MEV = None,
                                mvhr_eff = 0.0,
                                )
        self.mechvent_dict = {'mechvent1' : self.mechvent}
        
        self.combustion_appliances = CombustionAppliances(
                                                supply_situation  = 'room_air',
                                                exhaust_situation = 'into_separate_duct',
                                                fuel_type = 'wood',
                                                appliance_type = 'open_fireplace'
                                            ) 
        self.combustion_appliances_dict = {'Fireplace' : self.combustion_appliances}
        
        
        self.infil_vent = InfiltrationVentilation(self.simtime,
                                                  f_cross = True,
                                                  shield_class = 'Open',
                                                  terrain_class = 'OpenField',
                                                  average_roof_pitch = 20.0,
                                                  windows = self.window_dict,
                                                  vents = self.vent_dict,
                                                  leaks = self.leaks_dict,
                                                  combustion_appliances = self.combustion_appliances_dict,
                                                  ATDs = {},
                                                  mech_vents = self.mechvent_dict.values(),
                                                  space_heating_ductworks=None,
                                                  detailed_output_heating_cooling = False,
                                                  altitude = 0,
                                                  total_volume =250.0,
                                                  ventilation_zone_base_height=2.5
                                                  )

    # def test_temp_supply(self):
    #     ''' Returns 0.0'''
    #     air_temp = self.infil_vent.temp_supply()
    #     self.assertAlmostEqual(air_temp, 0.0)

    def test_calculate_total_volume_air_flow_rate_in(self):
        
        qm_in = 0.5
        external_air_density = 1
        self.assertAlmostEqual(self.infil_vent.calculate_total_volume_air_flow_rate_in(qm_in, external_air_density),
                               0.5)

    def test_calculate_total_volume_air_flow_rate_out(self):
        qm_out = 0.5
        zone_air_density = 1
        self.assertAlmostEqual(self.infil_vent.calculate_total_volume_air_flow_rate_out(qm_out, zone_air_density),
                               0.5)

    def test_make_leak_objects(self):
        ''' returns leak object'''
        leaklist = self.infil_vent.make_leak_objects(self.leaks_dict,average_roof_pitch = 40.0, ventilation_zone_base_height=2.5)
        for leak in leaklist:
            self.assertEqual(isinstance(leak, Leaks), True)

    #Currently not implemented
    # def test_calculate_qv_pdu(self):
    #     ''' Returns 1.0'''
    #     T_z = 299.15
    #     p_z_ref = 0.5
    #     qv_pdu = 1
    #     h_z = 100
    #     self.assertAlmostEqual(self.infil_vent.calculate_qv_pdu(qv_pdu, p_z_ref, T_z, h_z),
    #                            1)

    def test_implicit_formula_for_qv_pdu(self):
        ''' Returns  -112.556370'''
        T_z = 299.15
        p_z_ref = 0.5
        qv_pdu = 1
        h_z = 100
        #Currently not being used
        # self.assertEqual(self.infil_vent.implicit_formula_for_qv_pdu(qv_pdu, p_z_ref, T_z, h_z),
        #                  1)

    def test_calculate_internal_reference_pressure(self):
        '''Returns -6.312225965701547'''
        initial_p_z_ref_guess = 0
        temp_int_air  = 20
        R_v_arg = 1
        R_w_arg = 0.5
        self.assertAlmostEqual(self.infil_vent.calculate_internal_reference_pressure(
                initial_p_z_ref_guess,
                self.windspeed[0],
                self.wind_direction[0],
                temp_int_air,
                self.airtemp[0],
                R_v_arg,
                R_w_arg,
                ),
            -6.235527862635629,
            )

    def test_implicit_mass_balance_for_internal_reference_pressure(self):
        ''' returns -30430.689049309116'''
        p_z_ref = 1
        temp_int_air  = 20
        R_v_arg = 1
        R_w_arg_min_max = 1
        self.assertAlmostEqual(
                self.infil_vent.implicit_mass_balance_for_internal_reference_pressure(
                    p_z_ref,
                    self.windspeed[0],
                    self.wind_direction[0],
                    temp_int_air,
                    self.airtemp[0],
                    R_v_arg,
                    R_w_arg_min_max),
                -30270.984047975235,
                )

    def test_incoming_air_flow(self):
        ''' Returns 4.973297477194108'''
        p_z_ref = 1
        temp_int_air  = 20
        R_v_arg = 1
        R_w_arg_min_max = 1

        self.assertAlmostEqual(self.infil_vent.incoming_air_flow(
                                p_z_ref,
                                self.windspeed[0],
                                self.wind_direction[0],
                                temp_int_air,
                                self.airtemp[0],
                                R_v_arg,
                                R_w_arg_min_max,
                                reporting_flag = False,
                                report_effective_flow_rate = False,
                                ),
            4.846594835429536)

    def test_find_R_v_arg_within_bounds(self):
        # Checking for ach_target = ach_max
        ach_min = 0.3
        ach_max = 1
        temp_int_air = 20
        initial_R_v_arg = 1
        expected_output = 0.5359731535118643
        self.assertAlmostEqual(self.infil_vent.find_R_v_arg_within_bounds(
            ach_min,
            ach_max,
            initial_R_v_arg,
            20,
            self.wind_direction[0],
            temp_int_air,
            self.airtemp[0],
            R_w_arg = 0,
            initial_p_z_ref_guess = 0,
            reporting_flag = None,
            ),
        expected_output,
        )

        # Checking for ach_target = ach_min
        ach_min = 1.0
        ach_max = 1.4
        temp_int_air = 20
        initial_R_v_arg = 0.4
        expected_output = 0.5359731535118643
        self.assertAlmostEqual(self.infil_vent.find_R_v_arg_within_bounds(
            ach_min,
            ach_max,
            initial_R_v_arg,
            20,
            self.wind_direction[0],
            temp_int_air,
            self.airtemp[0],
            R_w_arg = 0,
            initial_p_z_ref_guess = 0,
            reporting_flag = None,
            ),
        expected_output,
        )

    @patch.object(InfiltrationVentilation, 'calc_air_changes_per_hour')
    def test_ach_within_bounds(self, mock_calc_ach):
        # Set up the mock to return a value within bounds
        mock_calc_ach.return_value = 2.0

        result = self.infil_vent.find_R_v_arg_within_bounds(
            ach_min=1.5,
            ach_max=2.5,
            initial_R_v_arg=0.5,
            wind_speed=5.0,
            wind_direction=90.0,
            temp_int_air=20.0,
            temp_ext_air=10.0,
            R_w_arg=1.0,
            initial_p_z_ref_guess=0.5,
            reporting_flag=None,
        )
        self.assertEqual(result, 0.5)

    @patch.object(InfiltrationVentilation, 'calc_air_changes_per_hour')
    def test_no_ach_target(self, mock_calc_ach):
        # Set up the mock to return an initial value
        mock_calc_ach.return_value = 2.0
        
        result = self.infil_vent.find_R_v_arg_within_bounds(
            ach_min=None,
            ach_max=None,
            initial_R_v_arg=0.5,
            wind_speed=5.0,
            wind_direction=90.0,
            temp_int_air=20.0,
            temp_ext_air=10.0,
            R_w_arg=1.0,
            initial_p_z_ref_guess=0.5,
            reporting_flag=None,
        )
        self.assertEqual(result, 0.5)

if __name__ == '__main__':
    unittest.main()
