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
from core.space_heat_demand.building_element import \
    BuildingElementOpaque, BuildingElementGround, BuildingElementTransparent, \
    BuildingElementAdjacentZTC, BuildingElementAdjacentZTU_Simple
from core.space_heat_demand.zone import *
from core.space_heat_demand.ventilation import Window, InfiltrationVentilation, Vent, Leaks
from core.space_heat_demand.thermal_bridge import ThermalBridgeLinear, ThermalBridgePoint

class TestZone(unittest.TestCase):
    """ Unit tests for Zone class """

    def setUp(self):
        """ Create Zone object to be tested """
        self.simtime = SimulationTime(0, 2, 1)
        air_temp_day_Jan = [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 7.5,
                            10.0, 12.5, 15.0, 19.5, 17.0, 15.0, 12.0, 10.0, 7.0, 5.0, 3.0, 1.0
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

        self.airtemp = []
        self.airtemp.extend(air_temp_day_Jan * 31)
        self.airtemp.extend(air_temp_day_Feb * 28)
        self.airtemp.extend(air_temp_day_Mar * 31)
        self.airtemp.extend(air_temp_day_Apr * 30)
        self.airtemp.extend(air_temp_day_May * 31)
        self.airtemp.extend(air_temp_day_Jun * 30)
        self.airtemp.extend(air_temp_day_Jul * 31)
        self.airtemp.extend(air_temp_day_Aug * 31)
        self.airtemp.extend(air_temp_day_Sep * 30)
        self.airtemp.extend(air_temp_day_Oct * 31)
        self.airtemp.extend(air_temp_day_Nov * 30)
        self.airtemp.extend(air_temp_day_Dec * 31)

        wind_speed_day_Jan = [4.7, 4.8, 4.9, 5.0, 5.1, 5.2, 5.3, 5.4, 5.7, 5.4, 5.6, 5.3,
                              5.1, 4.8, 4.7, 4.6, 4.5, 4.2, 4.9, 4.3, 4.4, 4.5, 4.3, 4.6
                           ]
        wind_speed_day_Feb = [x - 0.1 for x in wind_speed_day_Jan]
        wind_speed_day_Mar = [x - 0.2 for x in wind_speed_day_Jan]
        wind_speed_day_Apr = [x - 0.6 for x in wind_speed_day_Jan]
        wind_speed_day_May = [x - 0.8 for x in wind_speed_day_Jan]
        wind_speed_day_Jun = [x - 1.1 for x in wind_speed_day_Jan]
        wind_speed_day_Jul = [x - 1.2 for x in wind_speed_day_Jan]
        wind_speed_day_Aug = [x - 1.2 for x in wind_speed_day_Jan]
        wind_speed_day_Sep = [x - 1.1 for x in wind_speed_day_Jan]
        wind_speed_day_Oct = [x - 0.7 for x in wind_speed_day_Jan]
        wind_speed_day_Nov = [x - 0.5 for x in wind_speed_day_Jan]
        wind_speed_day_Dec = [x - 0.3 for x in wind_speed_day_Jan]

        self.windspeed = []
        self.windspeed.extend(wind_speed_day_Jan * 31)
        self.windspeed.extend(wind_speed_day_Feb * 28)
        self.windspeed.extend(wind_speed_day_Mar * 31)
        self.windspeed.extend(wind_speed_day_Apr * 30)
        self.windspeed.extend(wind_speed_day_May * 31)
        self.windspeed.extend(wind_speed_day_Jun * 30)
        self.windspeed.extend(wind_speed_day_Jul * 31)
        self.windspeed.extend(wind_speed_day_Aug * 31)
        self.windspeed.extend(wind_speed_day_Sep * 30)
        self.windspeed.extend(wind_speed_day_Oct * 31)
        self.windspeed.extend(wind_speed_day_Nov * 30)
        self.windspeed.extend(wind_speed_day_Dec * 31)

        wind_direction_day_Jan = [300, 250, 220, 180, 150, 120, 100, 80, 60, 40, 20, 10,
                              50, 100, 140, 190, 200, 320, 330, 340, 350, 355, 315, 5
                           ]
        wind_direction_day_Feb = [x - 1 for x in wind_direction_day_Jan]
        wind_direction_day_Mar = [x - 2 for x in wind_direction_day_Jan]
        wind_direction_day_Apr = [x - 3 for x in wind_direction_day_Jan]
        wind_direction_day_May = [x - 4 for x in wind_direction_day_Jan]
        wind_direction_day_Jun = [x + 1 for x in wind_direction_day_Jan]
        wind_direction_day_Jul = [x + 2 for x in wind_direction_day_Jan]
        wind_direction_day_Aug = [x + 3 for x in wind_direction_day_Jan]
        wind_direction_day_Sep = [x + 4 for x in wind_direction_day_Jan]
        wind_direction_day_Oct = [x - 5 for x in wind_direction_day_Jan]
        wind_direction_day_Nov = [x + 5 for x in wind_direction_day_Jan]
        wind_direction_day_Dec = [x - 0 for x in wind_direction_day_Jan]

        self.wind_direction = []
        self.wind_direction.extend(wind_direction_day_Jan * 31)
        self.wind_direction.extend(wind_direction_day_Feb * 28)
        self.wind_direction.extend(wind_direction_day_Mar * 31)
        self.wind_direction.extend(wind_direction_day_Apr * 30)
        self.wind_direction.extend(wind_direction_day_May * 31)
        self.wind_direction.extend(wind_direction_day_Jun * 30)
        self.wind_direction.extend(wind_direction_day_Jul * 31)
        self.wind_direction.extend(wind_direction_day_Aug * 31)
        self.wind_direction.extend(wind_direction_day_Sep * 30)
        self.wind_direction.extend(wind_direction_day_Oct * 31)
        self.wind_direction.extend(wind_direction_day_Nov * 30)
        self.wind_direction.extend(wind_direction_day_Dec * 31)

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
        extcond = ExternalConditions(
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

        window_part_list = [{'mid_height_air_flow_path': 1.5}]
        window_obj = Window(
            h_w_fa=1.6,
            h_w_path=1,
            A_w_max=3,
            window_part_list=window_part_list,
            orientation=0,
            pitch=0,
            altitude=30,
            on_off_ctrl_obj= False,
            ventilation_zone_base_height=2.5
        )
        self.window = {'window 0' : window_obj}
        
        vent_obj = Vent(
            h_path = 1.5,
            A_vent = 100.0,
            delta_p_vent_ref = 20.0,
            orientation = 180.0,
            pitch = 60.0,
            altitude = 30.0,
            ventilation_zone_base_height=2.5
            )
        self.vent = {'vent 1' : vent_obj}
        
        self.leaks =   { 
                        'ventilation_zone_height': 6, 
                        'test_pressure': 50, 
                        'test_result': 1.2, 
                        'env_area': 220,
                        'area_facades': 85.0, 
                        'area_roof': 25.0,
                        'altitude': 30
                        }

        self.infilvent = InfiltrationVentilation(
            self.simtime,
            f_cross= True,
            shield_class="Normal",
            terrain_class = 'OpenField',
            average_roof_pitch = 20.0,
            windows = self.window,
            vents = self.vent,
            leaks = self.leaks,
            combustion_appliances = {},
            ATDs = {},
            mech_vents = None,
            space_heating_ductworks=None,
            detailed_output_heating_cooling = False,
            altitude = 30.0,
            total_volume = 250.0,
            ventilation_zone_base_height=2.5
            )
        
        # Create objects for the different building elements in the zone
        be_opaque_I = BuildingElementOpaque(20,False, 180, 0.60, 0.25, 19000.0, "I", 0, 0, 2, 10, extcond)
        be_opaque_D = BuildingElementOpaque(26, True, 45, 0.55, 0.33, 16000.0, "D", 0, 0, 2, 10, extcond)
        be_ZTC = BuildingElementAdjacentZTC(22.5, 135, 0.50, 18000.0, "E", extcond)
        be_ground = BuildingElementGround(25.0,
                                          25.0,
                                          90,
                                          1.33,
                                          0.2,
                                          17000.0,
                                          "IE",
                                          'Suspended_floor',
                                          edge_insulation=None,
                                          h_upper=0.5,
                                          u_f_s=None,
                                          u_w=0.5,
                                          area_per_perimeter_vent=0.01,
                                          shield_fact_location='Sheltered',
                                          d_we=0.3,
                                          r_f_ins=7,
                                          z_b=None,
                                          r_w_b=None,
                                          h_w=None,
                                          perimeter=20.0,
                                          psi_wall_floor_junc=0.7,
                                          ext_cond=extcond,
                                          simulation_time=self.simtime,
                                          )
        be_transparent = BuildingElementTransparent(90, 0.4, 180, 0.75, 0.25, 1, 1.25, 4,False,None, extcond, self.simtime)
        be_ZTU = BuildingElementAdjacentZTU_Simple(30, 130, 0.50, 0.6, 18000.0, "E", extcond)

        # Put building element objects in a list that can be iterated over
        be_objs = [be_opaque_I, be_opaque_D, be_ZTC, be_ground, be_transparent, be_ZTU]

        # Create objects for thermal bridges
        tb_linear_1 = ThermalBridgeLinear(0.28, 5.0)
        tb_linear_2 = ThermalBridgeLinear(0.25, 6.0)
        tb_point = ThermalBridgePoint(1.4)

        # Put thermal bridge objects in a list that can be iterated over
        tb_objs = [tb_linear_1, tb_linear_2, tb_point]

        temp_ext_air_init = 2.2
        temp_setpnt_init = 21.0
        temp_setpnt_basis = "air"
    
        self.zone = Zone(80.0,
                         250.0,
                         be_objs,
                         tb_objs,
                         self.infilvent,
                         temp_ext_air_init,
                         temp_setpnt_init,
                         temp_setpnt_basis,
                         control_obj = None
                         )
    
    def test_volume(self):
        """ Test that the correct volume is returned when queried """
        self.assertEqual(
            self.zone.volume(),
            250.0,
            "incorrect volume returned"
            )

    def test_total_fabric_heat_loss(self):
        """ Test that the correct total for fabric heat loss is returned when queried """
        temp_int_air = 20.0
        temp_int_surface = 19.0

        self.assertAlmostEqual(self.zone.total_fabric_heat_loss(),
                               181.99557093947166,
                               2,
                               "incorrect total fabric heat loss returned")

    def test_total_heat_capacity(self):
        """ Test that the correct total for heat capacity is returned when queried """
        self.assertEqual(self.zone.total_heat_capacity(),
                               2166,
                               "incorrect total heat capacity returned")

    def test_total_thermal_bridges(self):
        """ Test that the correct total for thermal bridges is returned when queried """
        self.assertAlmostEqual(self.zone.total_thermal_bridges(),
                               4.3,
                               2,
                               "incorrect thermal bridge total returned")

    # def test_total_vent_heat_loss(self):
    #     """ Test that the correct total for ventilation heat loss is returned when queried """
    #     self.assertAlmostEqual(self.zone.total_vent_heat_loss(),
    #                            157.9,
    #                            1,
    #                            "incorrect total ventilation heat loss returned")

