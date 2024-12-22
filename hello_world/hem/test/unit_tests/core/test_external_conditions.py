#!/usr/bin/env python3

"""
This module contains unit tests for the external_conditions module
"""

# Standard library imports
import unittest

# Set path to include modules to be tested (must be before local imports)
from unit_tests.common import test_setup
test_setup()

# Local imports
from core.simulation_time import SimulationTime
from core.external_conditions import ExternalConditions

class TestExternalConditions(unittest.TestCase):
    """ Unit tests for ExternalConditions class """

    def setUp(self):
        """ Create ExternalConditions object to be tested """
        self.simtime = SimulationTime(7, 15, 1)
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
        
        # Test data for 24 hour timestep
        self.diffuse_horizontal_radiation = [0,0,0,0,0,0,0,0,136,308,365,300,
                                             128,90,30,0,0,0,0,0,0,0,0,0]      
       
        # Test data for 24 hour timestep
        self.direct_beam_radiation = [0,0,0,0,0,0,0,0,54,113,148,149,
                                     98,50,10,0,0,0,0,0,0,0,0,0]
        

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
            {"number": 4, "start": 45, "end": 0,
            "shading": [
                    {"type": "obstacle", "height": 10.5, "distance": 12}
                ]
            },
            {"number": 5, "start": 0, "end": -45},
            {"number": 6, "start": -45, "end": -90},
            {"number": 7, "start": -90, "end": -135},
            {"number": 8, "start": -135, "end": -180}
        ]

        self.extcond = ExternalConditions(self.simtime,
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

    def test_air_temp(self):
        """ Test that ExternalConditions object returns correct air temperatures """
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                self.assertAlmostEqual(
                    self.extcond.air_temp(),
                    [3.5,4.0,4.5,5.0,7.5,10.0,12.5,15.0][t_idx],
                    "incorrect air temp returned",
                    )
    
    def test_air_temp_annual(self):
        """ Test that ExternalConditions object returns correct annual air temperature """
        self.assertAlmostEqual(
            self.extcond.air_temp_annual(),
            10.1801369863014,
            msg="incorrect annual air temp returned"
            )
    
    def test_air_temp_monthly(self):
        """ Test that ExternalConditions object returns correct monthly air temperature """
        results = []
        for t_idx, _, _ in self.simtime:
            month_idx = self.simtime.current_month()
            with self.subTest(i=t_idx):
                self.assertEqual(
                    self.extcond.air_temp_monthly(),
                    [6.75, 7.75, 8.75, 9.75, 10.75, 11.75,
                     12.75, 12.75, 11.75, 10.75, 9.75, 8.75][month_idx],
                    "incorrect monthly air temp returned",
                    )
    
    def test_wind_speed(self):
        """ Test that ExternalConditions object returns correct wind speeds"""
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                self.assertEqual(
                    self.extcond.wind_speed(),
                    [ 5.4, 5.7, 5.4, 5.6, 5.3, 5.1, 4.8, 4.7][t_idx],
                    "incorrect wind speed returned",
                    )
    
    def test_wind_speed_annual(self):
        """ Test that ExternalConditions object returns correct annual wind speed """
        self.assertAlmostEqual(
            self.extcond.wind_speed_annual(),
            4.23,
            2,
            msg="incorrect annual wind speed returned"
            )
    
    def test_wind_direction(self):
        """ Test that ExternalConditions object returns correct wind directions"""
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                self.assertEqual(
                    self.extcond.wind_direction(),
                    [80, 60, 40, 20, 10, 50, 100, 140][t_idx],
                    "incorrect wind speed returned",
                    )
    
    def test_diffuse_horizontal_radiation(self):
        """ Test that ExternalConditions object returns correct diffuse_horizontal_radiation """
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                self.assertEqual(
                    self.extcond.diffuse_horizontal_radiation(),
                    [0,136,308,365,300,128,90,30][t_idx],
                    "incorrect diffuse_horizontal_radiation returned",
                    )
    
    def test_direct_beam_radiation(self):
        """ Test that ExternalConditions object returns correct direct_beam_radiation """
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                self.assertEqual(
                    self.extcond.direct_beam_radiation(),
                    [0,54,113,148,149,98,50,10][t_idx],
                    "incorrect direct_beam_radiation returned",
                    )
    
    def test_solar_reflectivity_of_ground(self):
        """ Test that ExternalConditions object returns correct solar_reflectivity_of_ground """
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                self.assertEqual(
                    self.extcond.solar_reflectivity_of_ground(),
                    self.solar_reflectivity_of_ground[t_idx],
                    "incorrect solar_reflectivity_of_ground returned",
                    )
    
    def test_window_shading(self):
        """ Test that using a reveal produces the same results as an equivalent overhang and side fins """
        reveal_depth = 0.1
        reveal_distance = 0.2
        base_height = 0
        height = 2
        width = 2
        tilt = 90
        orientation = 180
        f_sky = 0.5

        # Create shading objects with reveal
        shading_with_reveal = [{"type": "reveal", "depth": reveal_depth, "distance": reveal_distance}]
    
        # Create shading objects with overhang and fins
        shading_with_overhang_fin = [
            {"type": "overhang", "depth": reveal_depth, "distance": reveal_distance},
            {"type": "sidefinright", "depth": reveal_depth, "distance": reveal_distance},
            {"type": "sidefinleft", "depth": reveal_depth, "distance": reveal_distance},
        ]
    
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                # Calculate shading factors with reveal
                shading_factor_reveal = self.extcond.shading_reduction_factor_direct_diffuse(
                    base_height,
                    height,
                    width,
                    tilt,
                    orientation,
                    shading_with_reveal,
                    )
    
                # Calculate shading factors with overhang and fins
                shading_factor_overhang_fin = self.extcond.shading_reduction_factor_direct_diffuse(
                    base_height,
                    height,
                    width,
                    tilt,
                    orientation,
                    shading_with_overhang_fin,
                    )
    
                # Assert that shading factors are equal
                self.assertAlmostEqual(shading_factor_reveal, shading_factor_overhang_fin, places=5)
    
    def test_init_direct_beam_radiation(self):
        # Check with direct_beam_conversion_needed =False
        self.assertAlmostEqual(
                    self.extcond._ExternalConditions__init_direct_beam_radiation(
                        raw_value = 100,
                        solar_altitude = 5.0),
                    100.0
                    )
    
        # Check with direct_beam_conversion_needed = True
        self.direct_beam_conversion_needed = True
    
        self.extcond_direct_beam = ExternalConditions(self.simtime,
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
    
        self.assertAlmostEqual(
                    self.extcond_direct_beam._ExternalConditions__init_direct_beam_radiation(
                        raw_value = 100,
                        solar_altitude = 5.0),
                    1147.3713245669855
                    )
    
        # Check with solar_altitude = 0 
        self.assertAlmostEqual(
                    self.extcond_direct_beam._ExternalConditions__init_direct_beam_radiation(
                        raw_value = 10,
                        solar_altitude = 0.0),
                    10
                    )
    def test_init_earth_orbit_deviation(self):
        #Check for non - leap year
        self.assertAlmostEqual(
                    self.extcond._ExternalConditions__init_earth_orbit_deviation(
                                current_day = 364),
                    360.0
                    )
    
        #Check for leap year
        self.assertAlmostEqual(
                    self.extcond._ExternalConditions__init_earth_orbit_deviation(
                                current_day = 365),
                    360.986301369863 
                    )
    
    def test_init_solar_declination(self):
    
        self.assertAlmostEqual(
                    self.extcond._ExternalConditions__init_solar_declination(
                                earth_orbit_deviation = 100),
                    8.239299094353976 
                    )
    
    def test_init_equation_of_time(self):
    
        self.assertAlmostEqual(
                    self.extcond._ExternalConditions__init_equation_of_time(
                                current_day = 1),
                    3.48 
                    )
        self.assertAlmostEqual(
                    self.extcond._ExternalConditions__init_equation_of_time(
                                current_day = 22),
                    12.001736328751521 
                    )
        self.assertAlmostEqual(
                    self.extcond._ExternalConditions__init_equation_of_time(
                                current_day = 137),
                    -3.5547083185334247  
                    )
        self.assertAlmostEqual(
                    self.extcond._ExternalConditions__init_equation_of_time(
                                current_day = 242),
                    0.12076422612546622 
                    )
        self.assertAlmostEqual(
                    self.extcond._ExternalConditions__init_equation_of_time(
                                current_day = 365),
                    3.15 
                    )
        with self.assertRaises(SystemExit):
            self.extcond._ExternalConditions__init_equation_of_time(current_day = 366)
    
    def test_init_time_shift(self):
    
        self.assertEqual(self.extcond._ExternalConditions__init_time_shift(),0.05)
    
        #Check for whether station in US
        self.longitude = -73
        self.timezone = -5
        self.extcond_us = ExternalConditions(self.simtime,
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
        self.assertAlmostEqual(self.extcond_us._ExternalConditions__init_time_shift(),
                          -0.13333333333333375)
    
    def test_init_solar_time(self):
    
        #Mid day without timeshift
        self.assertAlmostEqual(
                    self.extcond._ExternalConditions__init_solar_time(
                                hour_of_day = 12,
                                equation_of_time = 5,
                                time_shift = 0),
                    12.916666666666666 
                    )
            #Mid day with timeshift
        self.assertAlmostEqual(
                    self.extcond._ExternalConditions__init_solar_time(
                                hour_of_day = 12,
                                equation_of_time = 5,
                                time_shift = 1),
                    11.916666666666666  
                    )
    
        #End of day with -ve equation and +ve timeshift
        self.assertAlmostEqual(
                    self.extcond._ExternalConditions__init_solar_time(
                                hour_of_day = 23,
                                equation_of_time = -2.5,
                                time_shift = 1),
                    23.041666666666668 
                    )
    
    def test_init_solar_hour_angle(self):
    
        self.assertAlmostEqual(
                    self.extcond._ExternalConditions__init_solar_hour_angle(
                                solar_time = 23),
                    -157.5 
                    )
        self.assertAlmostEqual(
                    self.extcond._ExternalConditions__init_solar_hour_angle(
                                solar_time = 1),
                    172.5 
                    )
    
    def test_init_solar_altitude(self):
    
        self.assertAlmostEqual(
                    self.extcond._ExternalConditions__init_solar_altitude(
                                solar_declination = 10, 
                                solar_hour_angle = 50),
                    32.03953794285834
                    )
    
        self.assertAlmostEqual(
                    self.extcond._ExternalConditions__init_solar_altitude(
                                solar_declination = -23, 
                                solar_hour_angle = 60),
                    0.0
                    )
    
    def test_init_solar_azimuth_angle(self):
    
        self.assertAlmostEqual (
                    self.extcond._ExternalConditions__init_solar_azimuth_angle(
                                solar_declination = 23, 
                                solar_hour_angle = 0,
                                solar_altitude = 45),
                    9.134285141104091e-15 
                    )
    
        #Check for East
        self.assertAlmostEqual (
                    self.extcond._ExternalConditions__init_solar_azimuth_angle(
                                solar_declination = 23, 
                                solar_hour_angle = -15,
                                solar_altitude = 45),
                    -19.49201220785029
                    )
    
        #Check for West
        self.assertAlmostEqual (
                    self.extcond._ExternalConditions__init_solar_azimuth_angle(
                                solar_declination = 23, 
                                solar_hour_angle = 15,
                                solar_altitude = 45),
                    19.49201220785031 
                    )
    
        # Negative declination        
        self.assertAlmostEqual (
                    self.extcond._ExternalConditions__init_solar_azimuth_angle(
                                solar_declination = -23, 
                                solar_hour_angle = 15,
                                solar_altitude = 45),
                    19.49201220785031
                    )
    
    def test_init_air_mass(self):
    
        self.assertAlmostEqual(self.extcond._ExternalConditions__init_air_mass(
                                solar_altitude = 5),
                    10.323080326274896
                    )
        self.assertAlmostEqual(self.extcond._ExternalConditions__init_air_mass(
                                solar_altitude = 15),
                    3.8637033051562737 
                    )
    
    def test_solar_angle_of_incidence(self):
    
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                self.assertAlmostEqual(self.extcond.solar_angle_of_incidence(
                                tilt = 10,
                                orientation = 10),
                    [89.28367858027447,80.39193381264141,73.0084830472421,67.6707156423694,
                     64.91086719421193,65.0693571287282,68.1252145585689,73.70764473968616][t_idx]
                )
    
        self.simtime.reset()
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                self.assertAlmostEqual(self.extcond.solar_angle_of_incidence(
                                tilt = 0,
                                orientation = 10),
                    [95.78366411883604,88.23114711240953,81.97931494689718,77.41946173012103,
                     74.90762116550648,74.67327369297139,76.73922946774607,80.91274624480684][t_idx]
                )
    
        self.simtime.reset()
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                self.assertAlmostEqual(self.extcond.solar_angle_of_incidence(
                                tilt = 90,
                                orientation = -180),
                    [120.13031074122472,131.83510459862302,143.4374125410406,154.33449512110948,
                     162.6874363991092,163.66695597946457,156.3258508149546,145.71870170993543][t_idx]
                )
    
    def test_sun_surface_azimuth(self):        
    
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):    
                self.assertAlmostEqual(self.extcond.sun_surface_azimuth(
                                orientation = 180),
                        [-110.99000000000001,-125.99,-140.99,-155.99,
                         -170.98999999999998,174.01000000000002,159.01,144.01][t_idx]
                    )
        self.simtime.reset()
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx): 
                self.assertAlmostEqual(self.extcond.sun_surface_azimuth(
                                orientation = 0),
                    [69.00999999999999,54.010000000000005,39.010000000000005,24.010000000000005,
                     9.010000000000007,-5.989999999999993,-20.989999999999995,-35.989999999999995][t_idx]
                    )
        self.simtime.reset()
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx): 
                self.assertAlmostEqual(self.extcond.sun_surface_azimuth(
                                orientation = -180),
                    [-110.99000000000001,-125.99000000000001,-140.99,-155.99,
                     -170.98999999999998,174.01000000000002,159.01,144.01][t_idx]
                    )
    
    
    def test_sun_surface_tilt(self):        
    
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):    
                    self.assertAlmostEqual(self.extcond.sun_surface_tilt(
                                tilt = 0),
                        [-90,-88.23114711240953,-81.97931494689718,-77.41946173012103,
                         -74.90762116550647,-74.67327369297139,-76.73922946774607,
                         -80.91274624480684][t_idx]
                    )
        self.simtime.reset()
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx): 
                self.assertAlmostEqual(self.extcond.sun_surface_tilt(
                                tilt = 90),
                    [0,1.7688528875904694,8.020685053102824,12.580538269878971,
                     15.09237883449353,15.326726307028608,13.260770532253929,
                     9.08725375519316][t_idx]
                    )
        self.simtime.reset()
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx): 
                self.assertAlmostEqual(self.extcond.sun_surface_tilt(
                                tilt = 180),
                     [90,91.76885288759047,98.02068505310282,102.58053826987897,
                      105.09237883449353,105.32672630702861,103.26077053225393,99.08725375519316][t_idx]
                     )
    
    
    def test_direct_irradiance(self):
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx): 
                self.assertAlmostEqual(self.extcond.direct_irradiance(
                                tilt = 0,
                                orientation = 180),
                    [0.0,1.6668397643248698,15.766957881489741,32.23613721421553,
                     38.79603659734242,25.90364916630168,11.469168196073362,1.579383993776423][t_idx]
                    )
        self.simtime.reset()
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx): 
                self.assertAlmostEqual(self.extcond.direct_irradiance(
                                tilt = 65,
                                orientation = 180),
                    [0,0,0,0,0,0,0,0][t_idx]
                    )
        self.simtime.reset()
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):         
                self.assertAlmostEqual(self.extcond.direct_irradiance(
                                tilt = 65,
                                orientation = -180),
                    [0,0,0,0,0,0,0,0,0][t_idx]
                    )
        self.simtime.reset()
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx): 
                self.assertAlmostEqual(self.extcond.direct_irradiance(
                                tilt = 65,
                                orientation = 0),
                    [0,33.34729692480562,88.92202737221507,134.5232406821787,
                     145.31786982869673,96.18110717866088,46.34890065056773,8.15613633989895][t_idx]
                    )
    def test_init_extra_terrestrial_radiation(self):
    
    
        self.assertAlmostEqual(self.extcond._ExternalConditions__init_extra_terrestrial_radiation(
                                earth_orbit_deviation = 0),
                    1412.1109999999999
                    )
    
        self.assertAlmostEqual(self.extcond._ExternalConditions__init_extra_terrestrial_radiation(
                                earth_orbit_deviation = 90),
                    1367.0
                    )
    
        self.assertAlmostEqual(self.extcond._ExternalConditions__init_extra_terrestrial_radiation(
                                earth_orbit_deviation = 180),
                    1321.889
                    )
    
    def test_brightness_coefficient(self):
    
        self.assertAlmostEqual(self.extcond.brightness_coefficient(E = 1, Fij = 'f11'),-0.008)
        self.assertAlmostEqual(self.extcond.brightness_coefficient(E = 1.23, Fij = 'f12'),0.487)
        self.assertAlmostEqual(self.extcond.brightness_coefficient(E = 1.6, Fij = 'f13'), -0.295)
        self.assertAlmostEqual(self.extcond.brightness_coefficient(E = 2, Fij = 'f21'),0.226)
        self.assertAlmostEqual(self.extcond.brightness_coefficient(E = 2.9, Fij = 'f12'), -1.237)
        self.assertAlmostEqual(self.extcond.brightness_coefficient(E = 4.5, Fij = 'f22'), -1.127)
        self.assertAlmostEqual(self.extcond.brightness_coefficient(E = 7, Fij = 'f23'), 0.251)
    
    def test_init_F1(self):
    
        self.assertAlmostEqual(self.extcond._ExternalConditions__init_F1(E = 1.23,
                                                                   delta = 1,
                                                                   solar_zenith_angle = 30),
                        0.7012846705927759)
        self.assertAlmostEqual(self.extcond._ExternalConditions__init_F1(E = 3,
                                                                   delta = 1,
                                                                   solar_zenith_angle = 30),
                        0.0)
    
    def test_init_F2(self):
    
        self.assertAlmostEqual(self.extcond._ExternalConditions__init_F2(E = 1.23,
                                                                   delta = 1,
                                                                   solar_zenith_angle = 180),
                        -0.09068140899333463)
        self.assertAlmostEqual(self.extcond._ExternalConditions__init_F2(E = 3,
                                                                   delta = 0,
                                                                   solar_zenith_angle = 30),
                        0.3173215314335047)
    
    def test_init_dimensionless_clearness_parameter(self):
    
        self.assertAlmostEqual(self.extcond._ExternalConditions__init_dimensionless_clearness_parameter(Gsol_d = 0,
                                                                                       Gsol_b = 5,
                                                                                       asol = 15),
                        999) 
    
        self.assertAlmostEqual(self.extcond._ExternalConditions__init_dimensionless_clearness_parameter(Gsol_d = 1,
                                                                                       Gsol_b = 5,
                                                                                       asol = 15),
                        5.910652372233723) 
    
    def test_init_dimensionless_sky_brightness_parameter(self):
    
        self.assertAlmostEqual(self.extcond._ExternalConditions__init_dimensionless_sky_brightness_parameter(air_mass = 36.0,
                                                                                                  diffuse_horizontal_radiation = 50,
                                                                                                  extra_terrestrial_radiation = 1412),
                        1.274787535410765) 
    
    def test_a_over_b(self):
    
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                self.assertAlmostEqual(self.extcond.a_over_b(tilt = 0, orientation = 0),
                      [0.0,0.354163731154509,1.0,1.0,0.9999999999999986,1.0,1.0,1.0][t_idx]
                                  )
    
        self.simtime.reset()
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                self.assertAlmostEqual(self.extcond.a_over_b(
                                tilt = 90,
                                orientation = 180),
                    [0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0][t_idx]
                )
    
        self.simtime.reset()
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                self.assertAlmostEqual(self.extcond.a_over_b(
                                tilt = 180,
                                orientation = -180),
                   [1.156236348588363,0.0,0.0,0.0,0.0,0.0,0.0,0.0][t_idx]
                )
    
    def test_diffuse_irradiance(self):
    
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                actual_result = self.extcond.diffuse_irradiance(
                                    tilt = 0, 
                                    orientation = 0)                
                expected_result = [(0.0, 0.0, 0.0, 0.0),
                                   (51.050674242609674, 4.466157979564503, 46.584516263045174, -0.0),
                                   (308.0, 80.07131055825931, 227.9286894417407, -0.0),
                                   (365.0, 142.60279131112304, 222.39720868887696, -0.0),
                                   (299.9999999999998, 168.47209561804453, 131.52790438195527, -0.0),
                                   (128.0, 96.29997383163165, 31.700026168368353, 0.0),
                                   (90.0, 69.76354921067887, 20.236450789321122, 0.0),
                                   (30.0, 27.570058662939754, 2.4299413370602463, 0.0)][t_idx]
                
                for actual_value, expected_value in zip(actual_result, expected_result):
                    self.assertAlmostEqual(actual_value, expected_value)
                                  
    
        self.simtime.reset()
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                actual_result = self.extcond.diffuse_irradiance(
                                tilt = 90,
                                orientation = 180)
                expected_result = [(0.0, 0.0, 0.0, 0.0),
                                 (-13.202357427309334, 2.2330789897822516, 0.0, -15.435436417091585),
                                 (16.122288185513806, 40.03565527912966, 0.0, -23.91336709361585),
                                 (50.83171656478211, 71.30139565556152, 0.0, -20.469679090779405),
                                 (74.87257439807136, 84.23604780902227, 0.0, -9.363473410950908),
                                 (53.09439354327976, 48.14998691581582, 0.0, 4.944406627463934),
                                 (39.20317296034313, 34.88177460533944, 0.0, 4.321398355003694),
                                 (14.084774138824505, 13.785029331469877, 0.0, 0.29974480735462805)][t_idx]
                for actual_value, expected_value in zip(actual_result, expected_result):
                    self.assertAlmostEqual(actual_value, expected_value)                
    
        self.simtime.reset()
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                actual_result = self.extcond.diffuse_irradiance(
                                tilt = 180,
                                orientation = -180)
                expected_result =    [(0.0, 0.0, 0.0, 0.0),
                                      (-1.89029578016337e-15, 0.0, 0.0, -1.89029578016337e-15),
                                      (-2.9285428468032295e-15, 0.0, 0.0, -2.9285428468032295e-15),
                                      (-2.50681269780965e-15, 0.0, 0.0, -2.50681269780965e-15),
                                      (-1.1466947741622378e-15, 0.0, 0.0, -1.1466947741622378e-15),
                                      (6.055151750006666e-16, 0.0, 0.0, 6.055151750006666e-16),
                                      (5.292186663295911e-16, 0.0, 0.0, 5.292186663295911e-16),
                                      (3.670815188878853e-17, 0.0, 0.0, 3.670815188878853e-17)][t_idx]
                for actual_value, expected_value in zip(actual_result, expected_result):
                    self.assertAlmostEqual(actual_value, expected_value)  
                    
    
    def test_ground_reflection_irradiance(self):
    
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                self.assertAlmostEqual(self.extcond.ground_reflection_irradiance(tilt = 0),
                                       [0.0,0,0,0,0,0,0,0][t_idx]
                                  )
    
        self.simtime.reset()
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                self.assertAlmostEqual(self.extcond.ground_reflection_irradiance(
                                tilt = 90),
                    [0.0,13.766683976432486,32.37669578814897,39.72361372142155,
                     33.87960365973424,15.390364916630167,10.146916819607336,
                     3.157938399377642][t_idx]
                )
    
        self.simtime.reset()
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                self.assertAlmostEqual(self.extcond.ground_reflection_irradiance(
                                tilt = 180),
                    [0.0,27.533367952864975,64.75339157629796,79.44722744284311,
                     67.75920731946849,30.780729833260338,20.293833639214675,6.315876798755285][t_idx]
                )
    
    def test_circumsolar_irradiance(self):
    
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                self.assertAlmostEqual(self.extcond.circumsolar_irradiance(
                                tilt = 0, 
                                orientation = 0),
                                [0.0,46.584516263045174,227.9286894417407,222.39720868887696,
                                 131.52790438195527,31.700026168368353,20.236450789321122,
                                 2.4299413370602463][t_idx]
                                    )
    
        self.simtime.reset()
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                self.assertAlmostEqual(self.extcond.circumsolar_irradiance(
                                tilt = 90,
                                orientation = 180),
                                [0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0][t_idx]
                                )
    
        self.simtime.reset()
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                self.assertAlmostEqual(self.extcond.circumsolar_irradiance(
                                tilt = 180,
                                orientation = -180),
                                [0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0][t_idx]
                                )
    
    def test_calculated_direct_irradiance(self):
    
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                self.assertAlmostEqual(self.extcond.calculated_direct_irradiance(
                                tilt = 0, 
                                orientation = 0),
                    [0.0,48.25135602737004,243.69564732323042,254.6333459030925,
                     170.32394097929767,57.60367533467003,31.705618985394484,4.009325330836669][t_idx]
                    )
        
        self.simtime.reset()
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                self.assertAlmostEqual(self.extcond.calculated_direct_irradiance(
                                tilt = 90,
                                orientation = 180),
                    [0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0][t_idx]
                    )
                
        self.simtime.reset()
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                self.assertAlmostEqual(self.extcond.calculated_direct_irradiance(
                                tilt = 180,
                                orientation = -180),
                    [0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0][t_idx]
                    )
    
    def test_calculated_diffuse_irradiance(self):

        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                self.assertAlmostEqual(self.extcond.calculated_diffuse_irradiance(
                                tilt = 0, 
                                orientation = 0),
                    [0.0,4.4661579795645,80.07131055825931, 142.60279131112304,168.4720956180445,
                      96.29997383163165,69.76354921067887, 27.570058662939754][t_idx]
                    )
        self.simtime.reset()
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                self.assertAlmostEqual(self.extcond.calculated_diffuse_irradiance(
                                tilt = 90,
                                orientation = 180),
                    [0.0, 0.5643265491231517,48.498983973662774,90.55533028620366,
                     108.7521780578056,68.48475845990993,49.350089779950466,17.24271253820215][t_idx]
                    )
        
        self.simtime.reset()
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                self.assertAlmostEqual(self.extcond.calculated_diffuse_irradiance(
                                tilt = 180,
                                orientation = -180),
                     [0.0,27.53336795286497,64.75339157629796,79.44722744284311,
                      67.75920731946849,30.780729833260338,20.293833639214675,6.315876798755285][t_idx]
                    )
    def test_calculated_total_solar_irradiance(self):
        
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):    
                self.assertAlmostEqual(self.extcond.calculated_total_solar_irradiance(
                                tilt = 0, 
                                orientation = 0),
                    [0.0,52.71751400693454,323.7669578814897,397.23613721421555,
                     338.7960365973422,153.90364916630168,101.46916819607335,31.579383993776425][t_idx]
                    )
        self.simtime.reset()
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                self.assertAlmostEqual(self.extcond.calculated_total_solar_irradiance(
                                tilt = 90,
                                orientation = 180),
                    [0.0,0.5643265491231517,48.498983973662774,90.55533028620366,108.7521780578056,
                     68.48475845990993,49.350089779950466,17.24271253820215][t_idx]
                    )
        self.simtime.reset()
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                self.assertAlmostEqual(self.extcond.calculated_total_solar_irradiance(
                                tilt = 180,
                                orientation = -180),
                   [0.0,27.53336795286497,64.75339157629796,79.44722744284311,67.75920731946849,
                    30.780729833260338,20.293833639214675,6.315876798755285][t_idx]
                    )
    
    def test_calculated_direct_diffuse_total_irradiance(self):
    
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                actual_result = self.extcond.calculated_direct_diffuse_total_irradiance(
                                            tilt = 0, 
                                            orientation = 0,
                                            diffuse_breakdown= True)
        
                expected_result = [(0.0, 0.0, 0.0, {'sky': 0.0, 'circumsolar': 0.0, 'horiz': 0.0, 'ground_refl': 0.0}),
                     (48.25135602737004, 4.4661579795645, 52.71751400693454, 
                        {'sky': 4.466157979564503, 'circumsolar': 46.584516263045174, 'horiz': -0.0, 'ground_refl': 0.0}),
                     (243.69564732323042, 80.07131055825931, 323.7669578814897, 
                        {'sky': 80.07131055825931, 'circumsolar': 227.9286894417407, 'horiz': -0.0, 'ground_refl': 0.0}),
                     (254.6333459030925, 142.60279131112304, 397.23613721421555, 
                        {'sky': 142.60279131112304, 'circumsolar': 222.39720868887696, 'horiz': -0.0, 'ground_refl': 0.0}),
                     (170.32394097929767, 168.4720956180445, 338.7960365973422, 
                        {'sky': 168.47209561804453, 'circumsolar': 131.52790438195527, 'horiz': -0.0, 'ground_refl': 0.0}),
                     (57.60367533467003, 96.29997383163165, 153.90364916630168, 
                        {'sky': 96.29997383163165, 'circumsolar': 31.700026168368353, 'horiz': 0.0, 'ground_refl': 0.0}),
                     (31.705618985394484, 69.76354921067887, 101.46916819607335, 
                        {'sky': 69.76354921067887, 'circumsolar': 20.236450789321122, 'horiz': 0.0, 'ground_refl': 0.0}),
                     (4.009325330836669, 27.570058662939754, 31.579383993776425, 
                        {'sky': 27.570058662939754, 'circumsolar': 2.4299413370602463, 'horiz': 0.0, 'ground_refl': 0.0})][t_idx]
           
                for actual_value, expected_value in zip(actual_result, expected_result):
                    if isinstance(actual_value, dict) and isinstance(expected_value, dict):
                        for key in expected_value:
                            self.assertAlmostEqual(actual_value[key], expected_value[key])
                    else:
                        self.assertAlmostEqual(actual_value, expected_value)

        self.simtime.reset()
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                actual_result = self.extcond.calculated_direct_diffuse_total_irradiance(
                                tilt = 90,
                                orientation = 180,
                                diffuse_breakdown= True)
                expected_result = [(0.0, 0.0, 0.0, {'sky': 0.0, 'circumsolar': 0.0, 'horiz': 0.0, 'ground_refl': 0.0}),
                     (0.0, 0.5643265491231517, 0.5643265491231517, 
                      {'sky': 2.2330789897822516, 'circumsolar': 0.0, 'horiz': -15.435436417091585, 'ground_refl': 13.766683976432486}),
                     (0.0, 48.498983973662774, 48.498983973662774, 
                      {'sky': 40.03565527912966, 'circumsolar': 0.0, 'horiz': -23.91336709361585, 'ground_refl': 32.37669578814897}),
                     (0.0, 90.55533028620366, 90.55533028620366, 
                      {'sky': 71.30139565556152, 'circumsolar': 0.0, 'horiz': -20.469679090779405, 'ground_refl': 39.72361372142155}),
                     (0.0, 108.7521780578056, 108.7521780578056, 
                      {'sky': 84.23604780902227, 'circumsolar': 0.0, 'horiz': -9.363473410950908, 'ground_refl': 33.87960365973424}),
                     (0.0, 68.48475845990993, 68.48475845990993, 
                      {'sky': 48.14998691581582, 'circumsolar': 0.0, 'horiz': 4.944406627463934, 'ground_refl': 15.390364916630167}),
                     (0.0, 49.350089779950466, 49.350089779950466, 
                      {'sky': 34.88177460533944, 'circumsolar': 0.0, 'horiz': 4.321398355003694, 'ground_refl': 10.146916819607336}),
                     (0.0, 17.24271253820215, 17.24271253820215, 
                      {'sky': 13.785029331469877, 'circumsolar': 0.0, 'horiz': 0.29974480735462805, 'ground_refl': 3.157938399377642})][t_idx]

                for actual_value, expected_value in zip(actual_result, expected_result):
                    if isinstance(actual_value, dict) and isinstance(expected_value, dict):
                        for key in expected_value:
                            self.assertAlmostEqual(actual_value[key], expected_value[key])
                    else:
                        self.assertAlmostEqual(actual_value, expected_value)
                    
        self.simtime.reset()
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                actual_result = self.extcond.calculated_direct_diffuse_total_irradiance(
                                tilt = 180,
                                orientation = -180,
                                diffuse_breakdown= True)
                expected_result = [(0.0, 0.0, 0.0, {'sky': 0.0, 'circumsolar': 0.0, 'horiz': 0.0, 'ground_refl': 0.0}),
                       (0.0, 27.53336795286497, 27.53336795286497, 
                        {'sky': 0.0, 'circumsolar': 0.0, 'horiz': -1.89029578016337e-15, 'ground_refl': 27.533367952864975}),
                       (0.0, 64.75339157629796, 64.75339157629796, 
                        {'sky': 0.0, 'circumsolar': 0.0, 'horiz': -2.9285428468032295e-15, 'ground_refl': 64.75339157629796}),
                       (0.0, 79.44722744284311, 79.44722744284311, 
                        {'sky': 0.0, 'circumsolar': 0.0, 'horiz': -2.50681269780965e-15, 'ground_refl': 79.44722744284311}),
                       (0.0, 67.75920731946849, 67.75920731946849, 
                        {'sky': 0.0, 'circumsolar': 0.0, 'horiz': -1.1466947741622378e-15, 'ground_refl': 67.75920731946849}),
                       (0.0, 30.780729833260338, 30.780729833260338, 
                        {'sky': 0.0, 'circumsolar': 0.0, 'horiz': 6.055151750006666e-16, 'ground_refl': 30.780729833260338}),
                       (0.0, 20.293833639214675, 20.293833639214675, 
                        {'sky': 0.0, 'circumsolar': 0.0, 'horiz': 5.292186663295911e-16, 'ground_refl': 20.293833639214675}),
                       (0.0, 6.315876798755285, 6.315876798755285, 
                        {'sky': 0.0, 'circumsolar': 0.0, 'horiz': 3.670815188878853e-17, 'ground_refl': 6.315876798755285})][t_idx]
                
                for actual_value, expected_value in zip(actual_result, expected_result):
                    if isinstance(actual_value, dict) and isinstance(expected_value, dict):
                        for key in expected_value:
                            self.assertAlmostEqual(actual_value[key], expected_value[key])
                    else:
                        self.assertAlmostEqual(actual_value, expected_value)
                    
        self.simtime.reset()
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                actual_result = self.extcond.calculated_direct_diffuse_total_irradiance(
                                tilt = 0, 
                                orientation = 0,
                                diffuse_breakdown= False)
                expected_result = [(0.0, 0.0, 0.0) ,(48.25135602737004, 4.4661579795645, 52.71751400693454),
                                   (243.69564732323042, 80.07131055825931, 323.7669578814897),(254.6333459030925, 142.60279131112304, 397.23613721421555),
                                   (170.32394097929767, 168.4720956180445, 338.7960365973422), (57.60367533467003, 96.29997383163165, 153.90364916630168),
                                   (31.705618985394484, 69.76354921067887, 101.46916819607335), (4.009325330836669, 27.570058662939754, 31.579383993776425)][t_idx]
                    
                for actual_value, expected_value in zip(actual_result, expected_result):
                    self.assertAlmostEqual(actual_value, expected_value)
        
        self.simtime.reset()
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                actual_result = self.extcond.calculated_direct_diffuse_total_irradiance(
                                tilt = 90,
                                orientation = 180,
                                diffuse_breakdown= False)
                expected_result = [(0.0, 0.0, 0.0),
                     (0.0, 0.5643265491231517, 0.5643265491231517),
                     (0.0, 48.498983973662774, 48.498983973662774),
                     (0.0, 90.55533028620366, 90.55533028620366),
                     (0.0, 108.7521780578056, 108.7521780578056),
                     (0.0, 68.48475845990993, 68.48475845990993),
                     (0.0, 49.350089779950466, 49.350089779950466),
                     (0.0, 17.24271253820215, 17.24271253820215)][t_idx]
                    
                for actual_value, expected_value in zip(actual_result, expected_result):
                    self.assertAlmostEqual(actual_value, expected_value)
        self.simtime.reset()
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                actual_result = self.extcond.calculated_direct_diffuse_total_irradiance(
                                tilt = 180,
                                orientation = -180,
                                diffuse_breakdown= False)
                expected_result = [(0.0, 0.0, 0.0),
                     (0.0, 27.53336795286497, 27.53336795286497),
                     (0.0, 64.75339157629796, 64.75339157629796),
                     (0.0, 79.44722744284311, 79.44722744284311),
                     (0.0, 67.75920731946849, 67.75920731946849),
                     (0.0, 30.780729833260338, 30.780729833260338),
                     (0.0, 20.293833639214675, 20.293833639214675),
                     (0.0, 6.315876798755285, 6.315876798755285)][t_idx]
                
                for actual_value, expected_value in zip(actual_result, expected_result):
                    self.assertAlmostEqual(actual_value, expected_value)
                    
    
    def test_outside_solar_beam(self):
    
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                self.assertAlmostEqual(self.extcond.outside_solar_beam(
                                tilt = 0, 
                                orientation = 0),
                            [0,0,0,0,0,0,0,0][t_idx]
                            )
    
        self.simtime.reset()
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                self.assertAlmostEqual(self.extcond.outside_solar_beam(
                                tilt = 90,
                                orientation = 180),
                            [1,1,1,1,1,1,1,1][t_idx]
                            )
    
        self.simtime.reset()
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                self.assertAlmostEqual(self.extcond.outside_solar_beam(
                                tilt = 180,
                                orientation = -180),
                                [1,1,1,1,1,1,1,1][t_idx]
                                )
    
    def test_get_segment(self):
    
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                self.assertAlmostEqual(self.extcond.get_segment(),
                    [{'number': 3, 'start': 90, 'end': 45},
                     {'number': 3, 'start': 90, 'end': 45},
                     {'number': 4, 'start': 45, 'end': 0, 'shading': [{'type': 'obstacle', 'height': 10.5, 'distance': 12}]},
                     {'number': 4, 'start': 45, 'end': 0, 'shading': [{'type': 'obstacle', 'height': 10.5, 'distance': 12}]},
                     {'number': 4, 'start': 45, 'end': 0, 'shading': [{'type': 'obstacle', 'height': 10.5, 'distance': 12}]},
                     {'number': 5, 'start': 0, 'end': -45},
                     {'number': 5, 'start': 0, 'end': -45},
                     {'number': 5, 'start': 0, 'end': -45}][t_idx]
                      )
        # For the gap in second shading segment 
        self.shading_segments_gap= [
            {"number": 1, "start": 180, "end": 135},
            {"number": 2, "start": 50, "end": 90},
            {"number": 3, "start": 90, "end": 45},
        ]
    
        self.extcond_shading_gap = ExternalConditions(self.simtime,
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
                                          self.shading_segments_gap
                                        )
    
        with self.assertRaises(SystemExit):
            self.extcond_shading_gap.get_segment()
    
        # For the value of end > start  in second shading segment 
        self.shading_segments_value= [
            {"number": 1, "start": 180, "end": 135},
            {"number": 2, "start": 135, "end": 140},
            {"number": 3, "start": 90, "end": 45},
        ]
    
        self.extcond_shading_value = ExternalConditions(self.simtime,
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
                                          self.shading_segments_value
                                        )
    
        with self.assertRaises(SystemExit):
            self.extcond_shading_value.get_segment()
    
    
        # Empty shading segment 
        self.shading_segments_empty= []
    
        self.extcond_shading_empty = ExternalConditions(self.simtime,
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
                                          self.shading_segments_empty
                                        )
    
        with self.assertRaises(SystemExit):
            self.extcond_shading_empty.get_segment()

    def test_obstacle_shading_height(self):
        
        # Test for peak hours in Jan
        
        self.extcond_Jan = ExternalConditions(self.simtime,
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
              
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                self.assertAlmostEqual(self.extcond_Jan.obstacle_shading_height(Hkbase = 3,
                                                           Hobst = 5,
                                                           Lkobst = 1),
                [2.0,1.9691178812624324,1.8590909935052966,1.7768301326744398,
                1.7303219853707263,1.7259295208086824,1.7643328437619492,1.8400541145006308][t_idx]
                )

        # Test for peak hours in July
        self.simtime = SimulationTime(4474,4482,1)
        self.direct_beam_radiation_peak_Jul = ([0] * 4474) + [70,71,39,51,44,26,108,141]  
        self.diffuse_horizontal_radiation_Jul = ([0] * 4474) +  [232,310,342,393,421,426,466,424,397]
        self.solar_reflectivity_of_ground_Jul = ([0] * 4474) + [0.6] * 8
        
        self.extcond_Jul= ExternalConditions(self.simtime,
                                          self.airtemp,
                                          self.windspeed,
                                          self.wind_direction,
                                          self.diffuse_horizontal_radiation_Jul,
                                          self.direct_beam_radiation_peak_Jul,
                                          self.solar_reflectivity_of_ground_Jul,
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

        self.simtime.reset()
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                self.assertAlmostEqual(self.extcond_Jul.obstacle_shading_height(Hkbase = 3,
                                                           Hobst = 5,
                                                           Lkobst = 1),
                [0.5367256982895989,0.240221480766996,0.1963213106984325,0.4473885431039979,
                 0.79264418501541,1.1031372689550807,1.3579235500301707,1.5678670755252178][t_idx]
                )
                
    def test_overhang_shading_height(self):
    
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                self.assertAlmostEqual(self.extcond.overhang_shading_height(Hk = 5, Hkbase = 1, Hovh = 3, Lkovh =2),
                                 [3.0,3.0617642374751353,3.281818012989407,3.4463397346511204,
                                  3.5393560292585473,3.548140958382635,3.4713343124761016,3.3198917709987383][t_idx]
                                 )
    
    
    def test_direct_shading_reduction_factor(self):
    
        # obstacle shading defined in segment and empty window shading 
        base_height = 1
        height =   1.25
        width = 4
        orientation =  90
        window_shading =  []
    
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                self.assertAlmostEqual(self.extcond.direct_shading_reduction_factor(base_height, 
                                                           height, 
                                                           width, 
                                                           orientation, 
                                                           window_shading),
                        [1.0,1.0,0.0,0.0,0.0,1.0,1.0,1.0][t_idx]
                    )
    
        # With window shading
        window_shading_val =  [{'type': 'overhang', 'depth': 0.5, 'distance': 0.5}, 
                          {'type': 'sidefinleft', 'depth': 0.25, 'distance': 0.1}, 
                          {'type': 'sidefinright', 'depth': 0.25, 'distance': 0.1}
                          ]
    
        self.simtime.reset()
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                self.assertAlmostEqual(self.extcond.direct_shading_reduction_factor(base_height, 
                                                           height, 
                                                           width, 
                                                           orientation, 
                                                           window_shading_val),
                [1.0,1.0,0.0,0.0,0.0,0.4002331427001323,
                 0.8511094450438235,0.9292880457188379][t_idx]
                )
    
        #Test with zero orientation and with window shading
        self.simtime.reset()
        orientation =  0
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                self.assertAlmostEqual(self.extcond.direct_shading_reduction_factor(base_height, 
                                                           height, 
                                                           width, 
                                                           orientation, 
                                                           window_shading_val),
                [0.9201388647583034,0.9552620660549097,0.0,0.0,0.0,1.0,1.0,1.0][t_idx]
                )
    
        #Test with negative orientation and with window shading
        self.simtime.reset()
        orientation =  -180
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                self.assertAlmostEqual(self.extcond.direct_shading_reduction_factor(base_height, 
                                                           height, 
                                                           width, 
                                                           orientation, 
                                                           window_shading_val),
                [0.9201388647583035,0.9552620660549097,0.0,0.0,0.0,1.0,1.0,1.0][t_idx]
                )
    
    def test_diffuse_shading_reduction_factor(self):
    
        #With window shading
        diffuse_breakdown = {'sky': 12.0, 'circumsolar': 0.0, 'horiz': -2.0164780331874668, 'ground_refl': 2.4}
        tilt = 90
        height = 1.25
        base_height = 1.
        width = 4 
        orientation = 90.
        window_shading = [{'type': 'overhang', 'depth': 0.5, 'distance': 0.5},
                          {'type': 'sidefinleft', 'depth': 0.25, 'distance': 0.1}, 
                          {'type': 'sidefinright', 'depth': 0.25, 'distance': 0.1}]
        f_sky = 0.5
    
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                    self.assertAlmostEqual(self.extcond.diffuse_shading_reduction_factor(diffuse_breakdown,
                                                                                   tilt,
                                                                                   height,
                                                                                   base_height,
                                                                                   width,
                                                                                   orientation,
                                                                                   window_shading,
                                                                                   f_sky),
                        [0.5905238865770632,0.5905238865770632, 0.5905238865770632, 0.5905238865770632,
                         0.5905238865770632,0.5905238865770632,0.5905238865770632,0.5905238865770632][t_idx]
                    )
        #With no window shading
        self.simtime.reset()
        window_shading=[]
    
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                self.assertAlmostEqual(self.extcond.diffuse_shading_reduction_factor(diffuse_breakdown,
                                                                                   tilt,
                                                                                   height,
                                                                                   base_height,
                                                                                   width,
                                                                                   orientation,
                                                                                   window_shading,
                                                                                   f_sky),
                        [0.9699932956653645,0.9699932956653645,0.9699932956653645,0.9699932956653645,
                         0.9699932956653645,0.9699932956653645,0.9699932956653645,0.9699932956653645][t_idx]
                    )

    def test_solar_irradiance(self):
        base_height = 1
        height =   1.25
        width = 4
        tilt = 0
        orientation =  90
        window_shading = [
            {'type': 'overhang', 'depth': 0.5, 'distance': 0.5},
            {'type': 'sidefinleft', 'depth': 0.25, 'distance': 0.1},
            {'type': 'sidefinright', 'depth': 0.25, 'distance': 0.1},
            ]

        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                self.assertAlmostEqual(
                    self.extcond.surface_irradiance(
                        base_height,
                        height,
                        width,
                        tilt,
                        orientation,
                        window_shading,
                        ),
                    (0.0, 50.88872899552963, 47.28402151418233, 84.21035456178225,
                     99.48679668415026, 114.47111015899463, 72.90266120669479, 20.290103525633484)[t_idx],
                    )

    def test_shading_reduction_factor_direct_diffuse(self):
    
        # Test without window shading
        base_height = 1
        height =   1.25
        width = 4
        tilt = 0
        orientation = 0.
        window_shading =  []
        f_sky = 1.
    
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                    self.assertAlmostEqual(self.extcond.shading_reduction_factor_direct_diffuse(base_height, 
                                                           height,
                                                           width, 
                                                           tilt,
                                                           orientation, 
                                                           window_shading,
                                                           ),
                        [(0.0, 0.0),(1.0, 1.0),(0.0, 0.9948359023012616),(0.0, 0.988044845054899),
                         (0.0, 0.983862781044833),(1.0, 0.9816340106900042),(1.0, 0.9808582136351668),(1.0, 0.9791897009662986)][t_idx]
                    )
        # Test window shading
        window_shading_val =  [{'type': 'overhang', 'depth': 0.5, 'distance': 0.5}, 
                          {'type': 'sidefinleft', 'depth': 0.25, 'distance': 0.1}, 
                          {'type': 'sidefinright', 'depth': 0.25, 'distance': 0.1}
                          ]
    
        self.simtime.reset()
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                actual_result = self.extcond.shading_reduction_factor_direct_diffuse(base_height, 
                                                           height,
                                                           width, 
                                                           tilt,
                                                           orientation, 
                                                           window_shading_val,
                                                           )
                expected_result = [(0.0, 0.0),(0.9552620660549097, 0.5905238865770632),(0.0, 0.5905238865770632),
                    (0.0, 0.5905238865770632),(0.0, 0.5905238865770632),(1.0, 0.5905238865770632),
                    (1.0, 0.5905238865770632),(1.0, 0.5905238865770631)][t_idx]
                
                for actual_value, expected_value in zip(actual_result, expected_result):
                    self.assertAlmostEqual(actual_value, expected_value) 
    
        # Test with different combination of tilt , orientation with and without shading
    
        base_height = 1
        height =   1.25
        width = 4
        tilt = 90
        orientation = 180
        window_shading =  []
        f_sky = 0.5
        self.simtime.reset()
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                actual_result = self.extcond.shading_reduction_factor_direct_diffuse(base_height, 
                                                           height,
                                                           width, 
                                                           tilt,
                                                           orientation, 
                                                           window_shading,
                                                           )
                
                expected_result = [(0.0, 0.0),(1.0, 1.0),(1.0, 1.0),
                         (1.0, 1.0),(1.0, 1.0),(1.0, 1.0),
                         (1.0, 1.0),(1.0, 1.0)][t_idx]
                                                                    
                for actual_value, expected_value in zip(actual_result, expected_result):
                    self.assertAlmostEqual(actual_value, expected_value) 
    
        window_shading_val =  [{'type': 'overhang', 'depth': 0.5, 'distance': 0.5}, 
                          {'type': 'sidefinleft', 'depth': 0.25, 'distance': 0.1}, 
                          {'type': 'sidefinright', 'depth': 0.25, 'distance': 0.1}
                          ]
    
        self.simtime.reset()
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                actual_result = self.extcond.shading_reduction_factor_direct_diffuse(base_height, 
                                                           height, 
                                                           width, 
                                                           tilt,
                                                           orientation, 
                                                           window_shading_val,
                                                           )
                expected_result =  [(0.0, 0.0),(1.0, 0.5905238865770648),(1.0, 0.5905238865770633),
                                    (1.0, 0.5905238865770633),(1.0, 0.5905238865770633),
                                    (1.0, 0.5905238865770632),(1.0, 0.5905238865770633),
                                    (1.0, 0.5905238865770632)][t_idx]    
                                
                for actual_value, expected_value in zip(actual_result, expected_result):
                    self.assertAlmostEqual(actual_value, expected_value) 
    
        base_height = 1
        height =   1.25
        width = 4
        tilt = 180
        orientation = -180
        window_shading =  []
        f_sky = 0.
        self.simtime.reset()
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                actual_result = self.extcond.shading_reduction_factor_direct_diffuse(base_height, 
                                                           height,
                                                           width, 
                                                           tilt,
                                                           orientation, 
                                                           window_shading,
                                                           )
                expected_result = [(0.0, 0.0),(1.0, 1.0),(1.0, 1.0),(1.0, 1.0),
                                   (1.0, 1.0),(1.0, 1.0),(1.0, 1.0),(1.0, 1.0)][t_idx]
                                   
                for actual_value, expected_value in zip(actual_result, expected_result):
                    self.assertAlmostEqual(actual_value, expected_value) 
                    
        self.simtime.reset()
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                actual_result = self.extcond.shading_reduction_factor_direct_diffuse(base_height, 
                                                           height,
                                                           width, 
                                                           tilt,
                                                           orientation, 
                                                           window_shading_val,
                                                           )
                expected_result = [(0.0, 0.0),(1.0, 0.5905238865770632),(1.0, 0.5905238865770632),
                                   (1.0, 0.5905238865770632),(1.0, 0.5905238865770632),(1.0, 0.5905238865770632),
                                   (1.0, 0.5905238865770632),(1.0, 0.5905238865770632)][t_idx]            
                     
                for actual_value, expected_value in zip(actual_result, expected_result):
                    self.assertAlmostEqual(actual_value, expected_value)                