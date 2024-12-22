#!/usr/bin/env python3

"""
This module contains unit tests for the energy_supply module
"""

# Standard library imports
import unittest
from unittest.mock import MagicMock

# Set path to include modules to be tested (must be before local imports)
from unit_tests.common import test_setup
test_setup()

# Local imports
from core.simulation_time import SimulationTime
from core.external_conditions import ExternalConditions
from core.energy_supply.elec_battery import ElectricBattery
from core.heating_systems.storage_tank import PVDiverter
from core.energy_supply.energy_supply import EnergySupply, EnergySupplyConnection

class TestEnergySupply(unittest.TestCase):
    """ Unit tests for EnergySupply class """

    def setUp(self):
        """ Create EnergySupply object to be tested """
        self.simtime            = SimulationTime(0, 8, 1)
        self.energysupply       = EnergySupply("mains_gas", self.simtime)
        """ Set up two different energy supply connections """
        self.energysupplyconn_1 = self.energysupply.connection("shower")
        self.energysupplyconn_2 = self.energysupply.connection("bath")

    def test_connection(self):
        """ Test the correct end user name is assigned when creating the
        two different connections.
        """
        self.assertEqual(
            self.energysupplyconn_1._EnergySupplyConnection__end_user_name,
            "shower",
            "end user name for connection 1 not returned"
            )
        self.assertEqual(
            self.energysupplyconn_2._EnergySupplyConnection__end_user_name,
            "bath",
            "end user name for connection 2 not returned"
            )
    
        """ Test the energy supply is created as expected for the two
        different connections.
        """
        self.assertIs(
            self.energysupply,
            self.energysupplyconn_1._EnergySupplyConnection__energy_supply,
            "energy supply for connection 1 not returned"
            )
        self.assertIs(
            self.energysupply,
            self.energysupplyconn_2._EnergySupplyConnection__energy_supply,
            "energy supply for connection 2 not returned"
            )
    
    def test_init_demand_list(self):
        '''Check the initialised list of zero is returned'''
        self.assertEqual(self.energysupply._EnergySupply__init_demand_list(),
                         [0, 0, 0, 0, 0, 0, 0, 0])
    
    def test_energy_out(self):        
        # Check with existing end user name
        amount_demand = [10.0,20.0,30.0,40.0,50.0,60.0,70.0,80.0]
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                self.energysupply._EnergySupply__energy_out('shower',amount_demand[t_idx])
                self.assertEqual(
                    self.energysupply._EnergySupply__energy_out_by_end_user["shower"][t_idx],
                    [10.0,20.0,30.0,40.0,50.0,60.0,70.0,80.0][t_idx]
                    ) 
        # Check a system error is raised with new end user name
        with self.assertRaises(SystemExit):
            self.energysupply._EnergySupply__energy_out('electricshower',10.0)
    
    def test_connect_diverter(self):
    
        self.diverter = MagicMock()
        self.energysupply.connect_diverter(self.diverter)
        self.assertEqual(self.energysupply._EnergySupply__diverter,self.diverter)
        #Check system exits if diverter is already connected
        with self.assertRaises(SystemExit):
            self.energysupply.connect_diverter(self.diverter)
    
    def test_demand_energy(self):
    
        amount_demanded = [10.0,20.0,30.0,40.0,50.0,60.0,70.0,80.0]        
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                self.energysupply._EnergySupply__demand_energy('shower',amount_demanded[t_idx])
                self.assertEqual(
                    self.energysupply._EnergySupply__demand_total[t_idx],
                    [10.0,20.0,30.0,40.0,50.0,60.0,70.0,80.0][t_idx]
                    ) 
                self.assertEqual(
                    self.energysupply._EnergySupply__demand_by_end_user["shower"][t_idx],
                    [10.0,20.0,30.0,40.0,50.0,60.0,70.0,80.0][t_idx]
                    )
    
    def test_supply_energy(self):
    
        amount_produced = [10.0,20.0,30.0,40.0,50.0,60.0,70.0,80.0]        
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                self.energysupply._EnergySupply__supply_energy('shower',amount_produced[t_idx])
                self.assertEqual(
                    self.energysupply._EnergySupply__demand_total[t_idx],
                    [-10.0,-20.0,-30.0,-40.0,-50.0,-60.0,-70.0,-80.0][t_idx]
                    ) 
                self.assertEqual(
                    self.energysupply._EnergySupply__demand_by_end_user["shower"][t_idx],
                     [-10.0,-20.0,-30.0,-40.0,-50.0,-60.0,-70.0,-80.0][t_idx]
                    )
    
    def test_results_total(self):
        """ Check the correct list of the total demand on this energy
        source for each timestep is returned.
        """
        demandtotal = [50.0, 120.0, 190.0, 260.0, 330.0, 400.0, 470.0, 540.0]
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                self.energysupplyconn_1.demand_energy((t_idx+1.0)*50.0)
                self.energysupplyconn_2.demand_energy((t_idx)*20.0)
                self.assertEqual(
                    self.energysupply.results_total()[t_idx],
                    demandtotal[t_idx],
                    "incorrect total demand energy returned",
                    )
    
    def test_results_by_end_user(self):
        """ Check the correct list of the total demand on this energy
        source for each timestep is returned for each connection.
        """
        demandtotal_1 = [50.0, 100.0, 150.0, 200.0, 250.0, 300.0, 350.0, 400.0]
        demandtotal_2 = [0.0, 20.0, 40.0, 60.0, 80.0, 100.0, 120.0, 140.0]
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                self.energysupplyconn_1.demand_energy((t_idx+1.0)*50.0)
                self.energysupplyconn_2.demand_energy((t_idx)*20.0)
                self.assertEqual(
                    self.energysupply.results_by_end_user()["shower"][t_idx],
                    demandtotal_1[t_idx],
                    "incorrect demand by end user returned",
                    )
                self.assertEqual(
                    self.energysupply.results_by_end_user()["bath"][t_idx],
                    demandtotal_2[t_idx],
                    "incorrect demand by end user returned",
                    )
    
    def test_beta_factor(self):
        """check beta factor and surplus supply/demand are calculated correctly"""
        energysupplyconn_3 = self.energysupply.connection("PV")
        betafactor = [1.0, 
                      0.8973610789278808, 
                      0.4677549807236648, 
                      0.3297589507351858, 
                      0.2578125, 
                      0.2, 
                      0.16319444444444445, 
                      0.1377551020408163]
    
        surplus = [0.0, -8.21111368576954, -170.3184061684273, -482.57355547066624, -950.0, -1600.0, -2410.0, -3380.0]
        demandnotmet = [50.0, 48.21111368576953, 40.31840616842726, 22.573555470666236, 0.0, 0.0, 0.0, 0.0]
    
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                self.energysupplyconn_1.demand_energy((t_idx+1.0)*50.0)
                self.energysupplyconn_2.demand_energy((t_idx)*20.0)
                energysupplyconn_3.supply_energy((t_idx)*(t_idx)*80.0)
    
                self.energysupply.calc_energy_import_export_betafactor()
    
                self.assertEqual(
                    self.energysupply.get_beta_factor()[t_idx],
                    betafactor[t_idx],
                    "incorrect beta factor returned",
                    )
                self.assertEqual(
                    self.energysupply.get_energy_export()[t_idx],
                    surplus[t_idx],
                    "incorrect energy export returned",
                    )
                self.assertEqual(
                    self.energysupply.get_energy_import()[t_idx],
                    demandnotmet[t_idx],
                    "incorrect energy import returned",
                    )

    def test_calc_energy_import_export_betafactor(self):
        
        amount_demanded         = [50.0,100.0,150.0,200.0,250.0,300.0,350.0,400.0] 
        amount_produced         = [50.0,90.0,130.0,210.0,2300.0,290.0,300.0,350.0]     
        proj_dict = {
            "ExternalConditions": {
                "air_temperatures": [0.0, 2.5, 5.0, 7.5, 10.0, 12.5, 15.0, 20.0],
                "wind_speeds": [3.9, 3.8, 3.9, 4.1, 3.8, 4.2, 4.3, 4.1],
                "wind_directions": [0, 20, 40, 60, 0, 20, 40, 60],
                "diffuse_horizontal_radiation": [11, 25, 42, 52, 60, 44, 28, 15],
                "direct_beam_radiation": [11, 25, 42, 52, 60, 44, 28, 15],
                "solar_reflectivity_of_ground": [0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2],
                "latitude": 51.42,
                "longitude": -0.75,
                "timezone": 0,
                "start_day": 0,
                "end_day": 0,
                "time_series_step": 1,
                "january_first": 1,
                "daylight_savings": "not applicable",
                "leap_day_included": False,
                "direct_beam_conversion_needed": False,
                "shading_segments":[{"number": 1, "start": 180, "end": 135},
                                    {"number": 2, "start": 135, "end": 90,
                                     "shading": [
                                         {"type": "overhang", "height": 2.2, "distance": 6}
                                         ]
                                     },
                                    {"number": 3, "start": 90, "end": 45},
                                    {"number": 4, "start": 45, "end": 0, 
                                     "shading": [
                                         {"type": "obstacle", "height": 40, "distance": 4},
                                         {"type": "overhang", "height": 3, "distance": 7}
                                         ]
                                     },
                                    {"number": 5, "start": 0, "end": -45,
                                     "shading": [
                                         {"type": "obstacle", "height": 3, "distance": 8},
                                         ]
                                     },
                                    {"number": 6, "start": -45, "end": -90},
                                    {"number": 7, "start": -90, "end": -135},
                                    {"number": 8, "start": -135, "end": -180}],
            }
        }
        self.__external_conditions = ExternalConditions(
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
        self.elec_battery = ElectricBattery(2, 0.8, 3, 0.001, 1.5, 1.5,
                                            "outside", False, self.simtime, self.__external_conditions)
        self.energysupply = EnergySupply("electricity", self.simtime,elec_battery = self.elec_battery)  
        
        # Test with elec_battery
        shower_conn = self.energysupply.connection("shower")
        bath_conn = self.energysupply.connection("bath")
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):          
                self.energysupply._EnergySupply__demand_energy('shower',amount_demanded[t_idx])
                self.energysupply._EnergySupply__supply_energy('bath',amount_produced[t_idx])
                self.energysupply.calc_energy_import_export_betafactor()
                
        self.assertEqual(self.energysupply._EnergySupply__demand_total,[0.0, 10.0, 20.0, -10.0, -2050.0, 10.0, 50.0, 50.0])
        self.assertEqual(self.energysupply._EnergySupply__demand_not_met,[15.138528000000004, 34.37872423953049,
                                                                           52.991809292243516, 63.07009986960006,
                                                                           -2.842170943040401e-14, 99.5880926222444,
                                                                           124.3891811736907, 140.57522007095577])
        self.assertEqual(self.energysupply._EnergySupply__supply_surplus,[-14.582949016875158, -24.59889302603037, 
                                                                          -32.991809292243516, -73.07009986960004, 
                                                                          -2050.0, -89.5880926222444, 
                                                                          -74.38918117369072, -90.5752200709558])
        self.assertEqual(self.energysupply._EnergySupply__energy_generated_consumed,[33.739999999999995, 65.40110697396963,
                                                                                     97.00819070775648, 136.92990013039994, 
                                                                                     250.00000000000003, 200.4119073777556, 
                                                                                     225.6108188263093, 259.42477992904423])
        self.assertEqual(self.energysupply._EnergySupply__energy_into_battery_from_generation,[1.6770509831248424, -0.0, -0.0,
                                                                               -0.0, -0.0,
                                                                               -0.0, -0.0, -0.0])
        self.assertEqual(self.energysupply._EnergySupply__energy_out_of_battery,[-1.121472, -0.2201687864998738,
                                                                                 -0.0, -0.0, 0.0, 
                                                                                 -0.0, -0.0, 
                                                                                 -0.0])
        self.assertEqual(self.energysupply._EnergySupply__energy_diverted,[0, 0, 0, 0, 0, 0, 0, 0])
        self.assertEqual(self.energysupply._EnergySupply__beta_factor,[0.6748, 0.7266789663774403,
                                                                       0.7462168515981268, 0.652047143478095,
                                                                       0.10869565217391305, 0.6910755426819158,
                                                                       0.7520360627543643, 0.7412136569401263])
        
        # Test with PV diverter
        self.diverter = MagicMock()
        self.energysupply.connect_diverter(self.diverter)
        self.diverter.divert_surplus.return_value = 10
        self.simtime.reset()
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):          
                self.energysupply._EnergySupply__demand_energy('shower',amount_demanded[t_idx])
                self.energysupply._EnergySupply__supply_energy('bath',amount_produced[t_idx])
                self.energysupply.calc_energy_import_export_betafactor()
                
        self.assertEqual(self.energysupply._EnergySupply__demand_total,[0.0, 20.0, 40.0, -20.0, -4100.0, 20.0, 100.0, 100.0])
        self.assertEqual(self.energysupply._EnergySupply__demand_not_met,[47.65852800000002, 103.57651029159123, 
                                                                          158.97542787673055, 189.21029960880017,
                                                                          -8.526512829121202e-14, 298.7642778667332, 
                                                                          373.1675435210721, 421.7256602128673])

        self.assertEqual(self.energysupply._EnergySupply__supply_surplus,[-37.10294901687516, -63.79667907809112,
                                                                          -88.97542787673055, -209.21029960880014,
                                                                          -6140.0, -258.7642778667332, 
                                                                          -213.16754352107216, -261.7256602128674])
        
        self.assertEqual(self.energysupply._EnergySupply__energy_generated_consumed,[101.21999999999998, 196.2033209219089,
                                                                                     291.0245721232694, 410.78970039119986, 
                                                                                     750.0000000000001, 601.2357221332668, 
                                                                                     676.832456478928, 778.2743397871327])
        
        self.assertEqual(self.energysupply._EnergySupply__energy_into_battery_from_generation,[-0.0, -0.0, -0.0,
                                                                               -0.0, -0.0,
                                                                               -0.0, -0.0, -0.0])
        self.assertEqual(self.energysupply._EnergySupply__energy_out_of_battery,[-0.0, -0.0, -0.0, -0.0, 0, -0.0, -0.0, -0.0])
        self.assertEqual(self.energysupply._EnergySupply__energy_diverted,[10, 10, 10, 10, 10, 10, 10, 10])
        self.assertEqual(self.energysupply._EnergySupply__beta_factor,[0.6748, 0.7266789663774403,
                                                                       0.7462168515981268, 0.652047143478095,
                                                                       0.10869565217391305, 0.6910755426819158,
                                                                       0.7520360627543643, 0.7412136569401263])

        #Set priority
        self.energysupply = EnergySupply("electricity", 
                                         self.simtime,elec_battery = self.elec_battery,
                                         priority = ['diverter','ElectricBattery']) 
        shower_conn = self.energysupply.connection("shower")
        bath_conn = self.energysupply.connection("bath")
        self.diverter = MagicMock()
        self.energysupply.connect_diverter(self.diverter)
        self.diverter.divert_surplus.return_value = 10
        self.simtime.reset()
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):          
                self.energysupply._EnergySupply__demand_energy('shower',amount_demanded[t_idx])
                self.energysupply._EnergySupply__supply_energy('bath',amount_produced[t_idx])
                self.energysupply.calc_energy_import_export_betafactor()
                        
        self.assertEqual(self.energysupply._EnergySupply__demand_total,[0.0, 10.0, 20.0, -10.0, -2050.0, 10.0, 50.0, 50.0])
        self.assertEqual(self.energysupply._EnergySupply__demand_not_met,[16.260000000000005, 34.59889302603037,
                                                                           52.991809292243516, 63.07009986960006,
                                                                           -2.842170943040401e-14, 99.5880926222444,
                                                                           124.3891811736907, 140.57522007095577])
        self.assertEqual(self.energysupply._EnergySupply__supply_surplus,[-6.260000000000002, -14.598893026030371, 
                                                                          -22.991809292243516, -63.07009986960004, 
                                                                          -2040.0, -79.5880926222444, 
                                                                          -64.38918117369072, -80.5752200709558])
        self.assertEqual(self.energysupply._EnergySupply__energy_generated_consumed,[33.739999999999995, 65.40110697396963,
                                                                                     97.00819070775648, 136.92990013039994, 
                                                                                     250.00000000000003, 200.4119073777556, 
                                                                                     225.6108188263093, 259.42477992904423])
        self.assertEqual(self.energysupply._EnergySupply__energy_into_battery_from_generation,[-0.0, -0.0, -0.0, -0.0, -0.0, -0.0, -0.0, -0.0])
        self.assertEqual(self.energysupply._EnergySupply__energy_out_of_battery,[-0.0, -0.0, -0.0, -0.0, -0.0, -0.0, -0.0, -0.0])
        self.assertEqual(self.energysupply._EnergySupply__energy_diverted,[10, 10, 10, 10, 10, 10, 10, 10])
        self.assertEqual(self.energysupply._EnergySupply__beta_factor,[0.6748, 0.7266789663774403,
                                                                       0.7462168515981268, 0.652047143478095,
                                                                       0.10869565217391305, 0.6910755426819158,
                                                                       0.7520360627543643, 0.7412136569401263])
        

class TestEnergySupplyWithExport(unittest.TestCase):
    """ Unit tests for EnergySupply class """

    def setUp(self):
        """ Create EnergySupply object to be tested """
        self.simtime = SimulationTime(0, 8, 1)
        self.energysupply = EnergySupply("mains_gas", self.simtime, is_export_capable=False)
        """ Set up two different energy supply connections """
        self.energysupplyconn_1 = self.energysupply.connection("shower")
        self.energysupplyconn_2 = self.energysupply.connection("bath")

    def test_without_export(self):
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                self.energysupplyconn_1.demand_energy((t_idx+1.0)*50.0)
                self.energysupplyconn_2.demand_energy((t_idx)*20.0)
                self.assertEqual(
                    self.energysupply.get_energy_export()[t_idx],
                    0,
                    "incorrect energy export returned",
                    )
    
