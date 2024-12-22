#!/usr/bin/env python3

"""
This module contains unit tests for the shower module
"""

# Standard library imports
import unittest

# Set path to include modules to be tested (must be before local imports)
from unit_tests.common import test_setup
test_setup()

# Local imports
from core.simulation_time import SimulationTime
from core.energy_supply.energy_supply import EnergySupplyConnection, EnergySupply
from core.water_heat_demand.cold_water_source import ColdWaterSource
from core.water_heat_demand.shower import MixerShower, InstantElecShower
from core.heating_systems.wwhrs import WWHRS_InstantaneousSystemB
from core.water_heat_demand.dhw_demand import DHWDemand

class TestDHWDemand(unittest.TestCase):
    """ Unit tests for DHWDemand class """

    def setUp(self):
        """ Create DHWDemand object to be tested """
        self.simtime                = SimulationTime(0, 24, 1)
        coldwatertemps              = [2.0, 3.0 ,4.0,2.0, 3.0 ,4.0,2.0, 3.0 ,4.0,2.0, 3.0 ,4.0,2.0, 3.0 ,4.0,2.0, 3.0 ,4.0,2.0, 3.0 ,4.0,2.0, 3.0 ,4.0]
        self.coldwatersource        = ColdWaterSource(coldwatertemps, self.simtime, 0, 1)
        self.shower_dict            = {
                                        'mixer':  {'type': 'MixerShower', 'flowrate': 8.0, 'ColdWaterSource': 'mains water',  'WWHRS': 'Example_Inst_WWHRS'}, 
                                        'IES': {'type': 'InstantElecShower', 'rated_power': 9.0, 'ColdWaterSource': 'mains water', 'EnergySupply': 'mains elec'}
                                        }
        self.baths_dict             = {
                                         'medium': {'size': 100, 'ColdWaterSource': 'mains water', 'flowrate': 8.0}
                                       }
        self.other_hw_users_dict    = {
                                        'other': {'flowrate': 8.0, 'ColdWaterSource': 'mains water'}
                                        }
        self.hw_pipework_list       = [
                                        {'location': 'internal', 'internal_diameter_mm': 30, 'length': 10.0}, 
                                        {'location': 'internal', 'internal_diameter_mm': 28, 'length': 9.0}, 
                                        {'location': 'external', 'internal_diameter_mm': 32, 'length': 5.0}, 
                                        {'location': 'external', 'internal_diameter_mm': 31, 'length': 8.0}
                                      ]
        
        self.cold_water_sources     = {'mains water': self.coldwatersource }
        
        self.flow_rates             = [5, 7, 9, 11, 13]
        self.efficiencies           = [44.8, 39.1, 34.8, 31.4, 28.6]
        self.utilisation_factor     = 0.7        
        self.wwhrsb                 = WWHRS_InstantaneousSystemB(self.flow_rates, 
                                                                 self.efficiencies,
                                                                 self.coldwatersource, 
                                                                 self.utilisation_factor)
        self.wwhrs                  = {'Example_Inst_WWHRS': self.wwhrsb}
        self.energy_supplies        = {
                                        '_unmet_demand': EnergySupply("unmet_demand", self.simtime), 
                                        'mains elec': EnergySupply("electricity", self.simtime)
                                      }
        self.event_schedules        = {0: None, 1: None, 2: None, 3: None, 
                                       4: [{'start': 4.1, 'duration': 6, 'temperature': 41.0, 'type': 'Shower', 'name': 'IES'}, 
                                           {'start': 4.5, 'duration': 6, 'temperature': 41.0, 'type': 'Shower', 'name': 'IES'}], 
                                       5: None, 
                                       6: [{'start': 6, 'duration': 6, 'temperature': 41.0, 'type': 'Shower', 'name': 'IES'}, 
                                           {'start': 6, 'volume': 100.0, 'temperature': 41.0, 'type': 'Bath', 'name': 'medium'}], 
                                       7: [{'start': 7, 'duration': 6, 'temperature': 41.0, 'type': 'Shower', 'name': 'mixer'}, 
                                           {'start': 7, 'duration': 1, 'temperature': 41.0, 'type': 'Other', 'name': 'other'}], 
                                       8: [{'start': 8, 'duration': 6, 'temperature': 41.0, 'type': 'Shower', 'name': 'mixer'}, 
                                           {'start': 8, 'duration': 3, 'temperature': 41.0, 'type': 'Bath', 'name': 'mixer'}], 
                                       9: None, 10: None, 11: None, 12: None, 13: None, 14: None, 15: None, 16: None, 
                                       17: None, 18: None, 19: None, 20: None, 21: None, 22: None, 23: None} 
        
        self.dhw_demand             =   DHWDemand(self.shower_dict,
                                                  self.baths_dict,
                                                  self.other_hw_users_dict,
                                                  self.hw_pipework_list,
                                                  self.cold_water_sources,
                                                  self.wwhrs,
                                                  self.energy_supplies,
                                                  self.event_schedules)   
        
        
    def test_hot_water_demand(self):            
            for t_idx, _, _ in self.simtime:
                with self.subTest(i=t_idx):
                    self.assertEqual(self.dhw_demand.hot_water_demand(t_idx,55.0),
                                    [(0.0, {}, 0.0, 0.0, 0.0, 0.0, None, 0.0),
                                     (0.0, {}, 0.0, 0.0, 0.0, 0.0, None, 0.0),
                                     (0.0, {}, 0.0, 0.0, 0.0, 0.0, None, 0.0),
                                     (0.0, {}, 0.0, 0.0, 0.0, 0.0, None, 0.0),
                                     (0.0, {}, 29.783791734078537, 0.0, 0.0, 0.0,
                                         [{'start': 4.1, 'duration': 6, 'temperature': 41.0, 'type': 'Shower', 
                                           'name': 'IES', 'pipework_volume': 7.556577529434648},
                                          {'start': 4.5, 'duration': 6, 'temperature': 41.0, 'type': 'Shower', 
                                           'name': 'IES', 'pipework_volume': 7.556577529434648}], 29.783791734078537),
                                     (0.0, {}, 0.0, 0.0, 0.0, 0.0, None, 0.0),
                                     (81.141483189812, {'41.0': {'warm_temp': 41.0, 'warm_vol': 100},
                                         'temp_hot_water': {'warm_temp': 55.0, 'warm_vol': 81.141483189812}}, 
                                          88.195822360114, 12.5, 1.0, 4.532666666666667,
                                          [{'start': 6, 'duration': 6, 'temperature': 41.0, 'type': 'Shower', 
                                            'name': 'IES', 'pipework_volume': 7.556577529434648},
                                           {'start': 6, 'volume': 100.0, 'temperature': 41.0, 'type': 'Bath',
                                            'name': 'medium', 'warm_volume': 100, 'duration': 12.5,
                                            'pipework_volume': 7.556577529434648}], 14.610916699736642),
                                     (53.58989404060333, {'41.0': {'warm_temp': 41.0, 'warm_vol': 56.0}, 
                                         'temp_hot_water': {'warm_temp': 55.0, 'warm_vol': 53.58989404060333}},
                                         38.47673898173404, 7.0, 2.0, 2.325363096327197, 
                                        [{'start': 7, 'duration': 6, 'temperature': 41.0, 'type': 'Shower', 
                                          'name': 'mixer', 'warm_volume': 48.0, 'pipework_volume': 7.556577529434648}, 
                                         {'start': 7, 'duration': 1, 'temperature': 41.0, 'type': 'Other', 
                                          'name': 'other', 'warm_volume': 8.0, 'pipework_volume': 7.556577529434648}], 0.0),
                                     (39.92207133670446, {'41.0': {'warm_temp': 41.0, 'warm_vol': 48.0}, 
                                        'temp_hot_water': {'warm_temp': 55.0, 'warm_vol': 39.92207133670446}}, 32.365493807269814,
                                         6.0, 1.0, 1.9184107029362394, 
                                         [{'start': 8, 'duration': 6, 'temperature': 41.0, 'type': 'Shower', 'name': 'mixer',
                                            'warm_volume': 48.0, 'pipework_volume': 7.556577529434648}, 
                                           {'start': 8, 'duration': 3, 'temperature': 41.0, 'type': 'Bath', 'name': 'mixer',
                                             'pipework_volume': 7.556577529434648}], 0.0),
                                     (0.0, {}, 0.0, 0.0, 0.0, 0.0, None, 0.0),
                                     (0.0, {}, 0.0, 0.0, 0.0, 0.0, None, 0.0),
                                     (0.0, {}, 0.0, 0.0, 0.0, 0.0, None, 0.0),
                                     (0.0, {}, 0.0, 0.0, 0.0, 0.0, None, 0.0),
                                     (0.0, {}, 0.0, 0.0, 0.0, 0.0, None, 0.0),
                                     (0.0, {}, 0.0, 0.0, 0.0, 0.0, None, 0.0),
                                     (0.0, {}, 0.0, 0.0, 0.0, 0.0, None, 0.0),
                                     (0.0, {}, 0.0, 0.0, 0.0, 0.0, None, 0.0),
                                     (0.0, {}, 0.0, 0.0, 0.0, 0.0, None, 0.0),
                                     (0.0, {}, 0.0, 0.0, 0.0, 0.0, None, 0.0),
                                     (0.0, {}, 0.0, 0.0, 0.0, 0.0, None, 0.0),
                                     (0.0, {}, 0.0, 0.0, 0.0, 0.0, None, 0.0),
                                     (0.0, {}, 0.0, 0.0, 0.0, 0.0, None, 0.0),
                                     (0.0, {}, 0.0, 0.0, 0.0, 0.0, None, 0.0),
                                     (0.0, {}, 0.0, 0.0, 0.0, 0.0, None, 0.0)][t_idx]
                                     )
                    
    def test_calc_pipework_losses(self):
        for t_idx, _, _ in self.simtime:
                with self.subTest(i=t_idx):
                    self.assertEqual(self.dhw_demand.calc_pipework_losses(
                                delta_t_h = 1,
                                hw_duration = 0,
                                no_of_hw_events = [0,0,0,2,0,2,2,2,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0][t_idx],
                                demand_water_temperature = [55.0,55.0,55.0,57.0,55.0,58.0,60.0,40.0,55.0,55.0,
                                                            55.0,55.0,55.0,55.0,55.0,55.0,55.0,55.0,55.0,55.0,
                                                            55.0,55.0,55.0,55.0][t_idx],
                                internal_air_temperature = 20.0,
                                external_air_temperature = 5.0),
                    [(0.0, 0.0),
                    (0.0, 0.0),
                    (0.0, 0.0),
                    (0.3615154654675836, 0.4052961328742277),
                    (0.0, 0.0),
                    (0.3712861537234643, 0.41309028927565516),
                    (0.3908275302352256, 0.42867860207851005),
                    (0.1954137651176128, 0.27279547404996096),
                    (0.0, 0.0),
                    (0.0, 0.0),
                    (0.0, 0.0),
                    (0.0, 0.0),
                    (0.0, 0.0),
                    (0.0, 0.0),
                    (0.0, 0.0),
                    (0.0, 0.0),
                    (0.0, 0.0),
                    (0.0, 0.0),
                    (0.0, 0.0),
                    (0.0, 0.0),
                    (0.0, 0.0),
                    (0.0, 0.0),
                    (0.0, 0.0),
                    (0.0, 0.0)][t_idx])
                    

        
    
    
            
