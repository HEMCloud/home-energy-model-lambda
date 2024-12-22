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
from core.space_heat_demand.internal_gains import InternalGains,\
         ApplianceGains,EventApplianceGains
from core.controls.time_control import SmartApplianceControl


class TestInternalGains(unittest.TestCase):
    """ Unit tests for InternalGains class """

    def setUp(self):
        """ Create InternalGains object to be tested """
        self.simtime                = SimulationTime(0, 4, 1)
        self.total_internal_gains   = [3.2, 4.6, 7.3, 5.2]
        self.internalgains          = InternalGains(self.total_internal_gains, self.simtime, 0, 1)

    def test_total_internal_gain(self):
        """ Test that InternalGains object returns correct internal gains and electricity demand"""
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                self.assertEqual(
                    self.internalgains.total_internal_gain(10.0),
                    [32, 46, 73, 52][t_idx],
                    "incorrect internal gains returned",
                    )


class TestApplianceGains(unittest.TestCase):
    """ Unit tests for ApplianceGains class """

    def setUp(self):
        """ Create ApplianceGains object to be tested """
        self.simtime                = SimulationTime(0, 4, 1)
        self.energysupply           = EnergySupply("electricity", self.simtime)
        energysupplyconn            = self.energysupply.connection("lighting")
        self.total_energy_supply    = [32.0, 46.0, 30.0, 20.0]
        self.appliancegains         = ApplianceGains(self.total_energy_supply, energysupplyconn, 0.5, self.simtime, 0, 1)

    def test_total_internal_gain(self):
        """ Test that ApplianceGains object returns correct internal gains and electricity demand"""
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                self.assertEqual(
                    self.appliancegains.total_internal_gain(10.0),
                    [160.0, 230.0, 150.0, 100.0][t_idx],
                    "incorrect internal gains for appliances returned",
                    )
                self.assertEqual(
                    self.energysupply.results_by_end_user()["lighting"][t_idx],
                    [0.32, 0.46, 0.30, 0.20][t_idx],
                    "incorrect electricity demand  returned"
                    )

class TestEventApplianceGains(unittest.TestCase):
    def setUp(self):
        """ Create EventApplianceGains object to be tested """
        
        self.simtime                = SimulationTime(0, 24, 0.5)
        self.energy_supply          = EnergySupply("electricity", self.simtime)
        self.energy_supply_conn     = self.energy_supply.connection('new_connection')
        self.appliance_data         = {
                                       'type': 'Clothes_drying', 
                                       'EnergySupply': 'mains elec', 
                                       'start_day': 0, 
                                       'time_series_step': 1, 
                                       'gains_fraction': 0.7, 
                                       'Events': [{'start': 0.1, 'duration': 1.75, 'demand_W': 900.0},
                                                  {'start': 5.3, 'duration': 1.50, 'demand_W': 900.0}
                                                  ],
                                        'Standby': 0.5, 
                                        'loadshifting':
                                                 {'demand_limit_weighted': 0, 
                                                  'power_timeseries': [ 
                                                    77.70823134533667,
                                                    70.07710122045972,
                                                    66.26153469022015,
                                                    62.445968159980595,
                                                    58.6304045653432,
                                                    66.26153469022015,
                                                    81.52379787557622,
                                                    872.7293737820189,
                                                    448.95976141145366,
                                                    146.38841421163792,
                                                    150.20398074187744,
                                                    246.13290374339178,
                                                    157.8351108667544,
                                                    146.38841421163792,
                                                    150.20398074187744,
                                                    236.48451946096566,
                                                    1235.1378596577206,
                                                    257.03982010376774,
                                                    801.2313187689566,
                                                    207.4374669530622,
                                                    192.17520376770614,
                                                    290.41445627425867,
                                                    138.757284086761,
                                                    100.60162759117186,
                                                    77.70823134533667,
                                                    ], 
                                                  'max_shift_hrs': 8, 
                                                  'weight': 'Tariff',
                                                  'weight_timeseries': [
                                                    1.0,
                                                    1.0,
                                                    1.0,
                                                    1.0,
                                                    1.0,
                                                    1.0,
                                                    1.0,
                                                    1.0,
                                                    1.0,
                                                    1.0,
                                                    1.0,
                                                    1.0,
                                                    1.0,
                                                    1.0,
                                                    1.0,
                                                    1.0,
                                                    1.0,
                                                    1.0,
                                                    1.0,
                                                    1.0,
                                                    1.0,
                                                    1.0,
                                                    1.0,
                                                    1.0,
                                                    1.0,
                                                  ]
                                                }
                                        }
        self.non_appliance_demand_24hr = {
            'mains elec': [
                0.06830825101566576, 0.060105811973985415,
                0.05305939286989522, 0.0501236916686892,
                0.011659722362322093, 0.009841650327447332,
                0.008628179127672608, 0.00780480411138585,
                0.007342238555297734, 0.0068683142767418555,
                0.007092339066083696, 0.0073738789491060025,
                0.00890318157456338, 0.013196350717229778,
                3.8185258665440713, 3.686604856404327,
                3.321741503132428, 2.1009771847288543,
                1.9577604381160962, 0.982853996628817,
                -0.4690062980892011, -0.47106808673125095,
                -0.440083286258449, -0.4402744803667663,
                -0.275893537706527, -0.27582574287859735,
                -0.02364598193865506, -0.022770656131003677,
                0.006386180325667274, 1.1838622352604393,
                0.016880847238056107, 0.022939243503258204,
                0.03451315625040322, 3.6710272517570663,
                3.4183577199797917, 3.259661970488036,
                2.382744591886866, 3.347517299485186,
                2.8633293436146374, 2.194481295688944,
                2.0245859635409174, 2.160933115928409,
                2.1559541166936143, 2.078707457615306,
                0.06082872713634447, 0.05498437799409048,
                0.04615437212925211, 0.036699730049032445
            ]
        }
        self.battery24hr = {
            'battery_state_of_charge': {
                'mains elec': [
                            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                            0, 0, 0, 0, 0, 0
                ]
            }
        }
        self.__smartcontrol = SmartApplianceControl(\
            {"mains elec":self.appliance_data["loadshifting"]["power_timeseries"]},
            {"mains elec":self.appliance_data["loadshifting"]["weight_timeseries"]},
            self.appliance_data["time_series_step"],
            self.simtime,
            self.non_appliance_demand_24hr,
            self.battery24hr,
            {"mains elec":self.energy_supply},
            {'Clothes_drying':None})
        
        self.TFA                    = 100.0
        self.event_app_gains        = EventApplianceGains(self.energy_supply_conn, 
                                                          self.simtime, 
                                                          self.appliance_data,
                                                          self.TFA,
                                                          self.__smartcontrol)
        
                                
    def test__process_event(self):
        eventdict = {'start': 3, 'duration': 1.75, 'demand_W': 900.0}
    
        self.assertEqual(
                    self.event_app_gains._EventApplianceGains__process_event(eventdict),
                    (20, [449.75, 449.75, 449.75, 224.875])
                    )
                
    def test_event_to_schedule(self):
        
        eventdict = {'start': 3, 'duration': 1.75, 'demand_W': 900.0}
        self.assertEqual(self.event_app_gains._EventApplianceGains__event_to_schedule(eventdict),
                          (6, [449.75, 449.75, 449.75, 224.875]))
        
    def test_total_internal_gain(self):
        res = []
        for t_idx in self.simtime:
            res.append(self.event_app_gains.total_internal_gain(self.TFA))
        self.assertEqual(res,[0.35, 0.35, 0.35, 0.35, 0.35, 0.35,
                            504.07, 252.20999999999998, 252.20999999999998,
                            94.79749999999994, 0.35, 0.35, 0.35, 0.35, 0.35,
                            0.35, 0.35, 0.35, 0.35, 0.35, 378.1400000000003,
                            252.21000000000018, 315.17499999999944, 0.35, 0.35,
                            0.35, 0.35, 0.35, 0.35, 0.35, 0.35, 0.35, 0.35, 0.35,
                            0.35, 0.35, 0.35, 0.35, 0.35, 0.35, 0.35, 0.35, 0.35,
                            0.35, 0.35, 0.35, 0.35, 0.35]) 
    
    def test___shift_iterative(self):
        eventdict = {'start': 2.33, 'duration': 1.0, 'demand_W': 900}
        s,a = 5 ,[600, 300]

        self.assertEqual(self.event_app_gains._EventApplianceGains__shift_iterative(s,a,eventdict),
                        15)
    
        
