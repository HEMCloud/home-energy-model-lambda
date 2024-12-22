#!/usr/bin/env python3

"""
This module contains unit tests for the heat network module
"""

# Standard library imports
import unittest
from unittest.mock import patch,MagicMock

# Set path to include modules to be tested (must be before local imports)
from unit_tests.common import test_setup
test_setup()

# Local imports
from core.simulation_time import SimulationTime
from core.external_conditions import ExternalConditions
from core.controls.time_control import SetpointTimeControl
from core.heating_systems.heat_network import HeatNetwork, HeatNetworkServiceWaterDirect, \
HeatNetworkServiceWaterStorage, HeatNetworkServiceSpace, HeatNetworkService
from core.water_heat_demand.cold_water_source import ColdWaterSource
from core.energy_supply.energy_supply import EnergySupply
from core.material_properties import WATER, MaterialProperties

class TestHeatNetworkService(unittest.TestCase):
    
    def setUp(self):
        self.heat_network = MagicMock()
        self.service_name = "heat_network_service"
        self.simtime = SimulationTime(0, 2, 1)

    def test_service_is_on(self):
        # Test when control is provided and returns True
        # Set up HeatNetworkServiceSpace
        self.ctrl = SetpointTimeControl(
            [21.0, 21.0, None],
            self.simtime,
            0, #start_day
            1.0, #time_series_step
            )
        
        self.heat_network_service = HeatNetworkService(
                                self.heat_network,
                                self.service_name,
                                self.ctrl
                                )
        self.assertTrue(self.heat_network_service.is_on())
        
        

        # Create a service without control
        self.heat_network_service_no_control = HeatNetworkService(
                                        self.heat_network,
                                        self.service_name
                                        )
        self.assertTrue(self.heat_network_service_no_control.is_on())
        

class TestHeatNetworkServiceWaterDirect(unittest.TestCase):
    """ Unit tests for HeatNetworkServiceWaterDirect class """

    def setUp(self):
        """ Create HeatNetworkServiceWaterDirect object to be tested """
        heat_network_dict = {"type": "HeatNetwork",
                             "EnergySupply": "custom"
                             }
        self.simtime = SimulationTime(0, 2, 1)
        self.energysupply = EnergySupply("custom", self.simtime)
        self.energy_output_required = [2.0, 10.0]
        self.temp_return_feed = [51.05, 60.00]
        energy_supply_conn_name_auxiliary = 'heat_network_auxiliary'
        energy_supply_conn_name_building_level_distribution_losses \
                    = 'HeatNetwork_building_level_distribution_losses'

        # Set up HeatNetwork
        self.heat_network = HeatNetwork(
            18.0, # power_max
            1.0, # HIU daily loss
            0.8, # Building level distribution loss 
            self.energysupply,
            energy_supply_conn_name_auxiliary,
            energy_supply_conn_name_building_level_distribution_losses,
            self.simtime,
            )

        self.heat_network._HeatNetwork__create_service_connection("heat_network_test")

        # Set up HeatNetworkServiceWaterDirect
        coldwatertemps = [1.0, 1.2]
        coldfeed = ColdWaterSource(coldwatertemps, self.simtime, 0, 1)
        return_temp = 60
        self.heat_network_service_water_direct = HeatNetworkServiceWaterDirect(
            self.heat_network,
            "heat_network_test", 
            return_temp,
            coldfeed,
            self.simtime
            )

    def test_heat_network_service_water(self):
        """ Test that HeatNetwork object returns correct hot water energy demand """
        volume_demanded = [{'41.0': {'warm_temp': 41.0, 'warm_vol': 48.0},
                                 '43.0': {'warm_temp': 43.0, 'warm_vol': 100.0}, 
                                 '40.0': {'warm_temp': 40.0, 'warm_vol': 0.0}, 
                                 'temp_hot_water': {'warm_temp': 55.0, 'warm_vol': 110.59194954841298}},
                                {'41.0': {'warm_temp': 41.0, 'warm_vol': 48.0},
                                 'temp_hot_water': {'warm_temp': 55.0, 'warm_vol': 32.60190808710678}}]
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                self.assertAlmostEqual(
                    self.heat_network_service_water_direct.demand_hot_water(volume_demanded[t_idx]),
                    [7.5834, 2.2279][t_idx],
                    3,
                    msg="incorrect energy_output_provided"
                    )
            self.heat_network.timestep_end()


class TestHeatNetworkServiceWaterStorage(unittest.TestCase):
    """ Unit tests for HeatNetworkServiceWaterStorage class """

    def setUp(self):
        """ Create HeatNetworkServiceWaterStorage object to be tested """
        self.simtime = SimulationTime(0, 2, 1)
        self.energysupply = EnergySupply("custom", self.simtime)
        self.energy_output_required = [2.0, 10.0]
        self.temp_return_feed = [51.05, 60.00]
        energy_supply_conn_name_auxiliary = 'heat_network_auxiliary'
        energy_supply_conn_name_building_level_distribution_losses \
                    = 'HeatNetwork_building_level_distribution_losses'

        controlmin = SetpointTimeControl([52, 52], self.simtime, 0, 1)
        controlmax = SetpointTimeControl([60, 60], self.simtime, 0, 1)

        # Set up HeatNetwork
        self.heat_network = HeatNetwork(
            7.0, # power_max
            1.0, # HIU daily loss
            0.8, # Building level distribution loss 
            self.energysupply,
            energy_supply_conn_name_auxiliary,
            energy_supply_conn_name_building_level_distribution_losses,
            self.simtime,
            )

        self.heat_network._HeatNetwork__create_service_connection("heat_network_test")

        # Set up HeatNetworkServiceWaterStorage
        coldwatertemps = [1.0, 1.2]
        coldfeed = ColdWaterSource(coldwatertemps, self.simtime, 0, 1)
        self.heat_network_service_water_storage= HeatNetworkServiceWaterStorage(
            self.heat_network,
            "heat_network_test",
            controlmin,
            controlmax,
            )

    def test_heat_network_service_water_storage(self):
        """ Test that HeatNetwork object returns correct energy demand for the storage tank """
        # TODO update results
        energy_demanded = [10.0, 2.0]
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                self.assertAlmostEqual(
                    self.heat_network_service_water_storage.demand_energy(energy_demanded[t_idx],None),
                    [7.0, 2.0][t_idx],
                    msg="incorrect energy_output_provided"
                    )
            self.heat_network.timestep_end()
    
    def test_energy_output_max(self):
        """ Test that Heat Network object returns correct energy output """
        
        temp_return = [10.0, 15.0]
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                self.assertAlmostEqual(
                    self.heat_network_service_water_storage.energy_output_max(temp_return[t_idx]),
                        [7.0, 7.0][t_idx],
                        3
                        )
            self.heat_network.timestep_end()


class TestHeatNetworkServiceSpace(unittest.TestCase):
    """ Unit tests for HeatNetworkServiceSpace class """

    def setUp(self):
        """ Create HeatNetworkServiceSpace object to be tested """
        self.simtime = SimulationTime(0, 3, 1)
        self.energysupply = EnergySupply("mains_gas", self.simtime)
        energy_supply_conn_name_auxiliary = 'Boiler_auxiliary'
        energy_supply_conn_name_building_level_distribution_losses \
                    = 'HeatNetwork_building_level_distribution_losses'

        # Set up HeatNetwork
        self.heat_network = HeatNetwork(
            5.0, # power_max
            1.0, # HIU daily loss
            0.8, # Building level distribution loss 
            self.energysupply,
            energy_supply_conn_name_auxiliary,
            energy_supply_conn_name_building_level_distribution_losses,
            self.simtime,
            )

        self.heat_network._HeatNetwork__create_service_connection("heat_network_test")

        # Set up HeatNetworkServiceSpace
        ctrl = SetpointTimeControl(
            [21.0, 21.0, None],
            self.simtime,
            0, #start_day
            1.0, #time_series_step
            )
        self.heat_network_service_space = HeatNetworkServiceSpace(
            self.heat_network,
            "heat_network_test",
            ctrl,
            )

    def test_heat_network_service_space(self):
        """ Test that HeatNetworkServiceSpace object returns correct space heating energy demand """
        energy_demanded = [10.0, 2.0, 2.0]
        temp_flow = [55.0, 65.0, 65.0]
        temp_return = [50.0, 60.0, 60.0]
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                self.assertAlmostEqual(
                    self.heat_network_service_space.demand_energy(
                        energy_demanded[t_idx],
                        temp_flow[t_idx],
                        temp_return[t_idx]),
                    [5.0, 2.0, 0.0][t_idx],
                    msg="incorrect energy_output_provided"
                    )
            self.heat_network.timestep_end()

    def test_energy_output_max(self):
        """ Test that HeatNetworkServiceSpace object returns correct energy output """
        temp_output = [55.0, 65.0, 65.0]
        temp_return_feed = [10.0, 15.0, 20.0]
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                self.assertAlmostEqual(
                    self.heat_network_service_space.energy_output_max(
                        temp_output[t_idx],
                        temp_return_feed[t_idx]),
                    [5.0, 5.0, 0.0][t_idx],
                    3
                    )
            self.heat_network.timestep_end()


class TestHeatNetwork(unittest.TestCase):
    """ Unit tests for HeatNetwork class """

    def setUp(self):
        """ Create HeatNetwork object to be tested """
        self.simtime = SimulationTime(0, 2, 1)
        self.energysupply = EnergySupply("custom", self.simtime)
        energy_supply_conn_name_auxiliary = 'heat_network_auxiliary'
        energy_supply_conn_name_building_level_distribution_losses \
                    = 'HeatNetwork_building_level_distribution_losses'

        # Set up HeatNetwork object
        self.heat_network = HeatNetwork(
            6.0, # power_max
            0.24, # HIU daily loss
            0.8, # Building level distribution losses
            self.energysupply,
            energy_supply_conn_name_auxiliary,
            energy_supply_conn_name_building_level_distribution_losses,
            self.simtime,
            )       

        # Create a service connection
        self.heat_network._HeatNetwork__create_service_connection("heat_network_test")

    def test_energy_output_provided(self):
        """ Test that HeatNetwork object returns correct energy and fuel demand """
        energy_output_required = [2.0, 10.0]
        temp_return = [50.0, 60.0]
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                self.assertAlmostEqual(
                    self.heat_network._HeatNetwork__demand_energy(
                                        "heat_network_test",
                                        energy_output_required[t_idx],
                                        ),
                    [2.0, 6.0][t_idx],
                    msg="incorrect energy_output_provided"
                    )
                self.heat_network.timestep_end()

                self.assertAlmostEqual(
                    self.energysupply.results_by_end_user()["heat_network_test"][t_idx],
                    [2.0, 6.0][t_idx],
                    msg="incorrect fuel demand"
                    )
                self.assertAlmostEqual(
                    self.energysupply.results_by_end_user()["heat_network_auxiliary"][t_idx],
                    [0.01, 0.01][t_idx],
                    msg="incorrect fuel demand"
                    )

    def test_HIU_loss(self):
        """ Test that HeatNetwork object returns correct HIU loss """
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                self.assertAlmostEqual(
                    self.heat_network.HIU_loss(),
                    0.01,
                    msg="incorrect HIU loss returned"
                    )

    def test_building_level_distribution_losses(self):
        """ Test that HeatNetwork object returns correct building level distribution loss """
        for t_idx, _, _ in self.simtime:
            with self.subTest(i=t_idx):
                self.assertAlmostEqual(
                    self.heat_network.building_level_loss(),
                    0.0008,
                    msg="incorrect building level distribution losses returned"
                    )
                
    def test_create_service_connection(self):
        ''' Test energy supply connections are created with correct service name''' 
        self.service_name = 'new_service'
        # Ensure the service name does not exist in __energy_supply_connections
        self.assertNotIn(self.service_name,
                          self.heat_network._HeatNetwork__energy_supply_connections)
        # Call the method under test
        self.heat_network._HeatNetwork__create_service_connection(self.service_name)
        # Check that the service name was added to __energy_supply_connections
        self.assertIn(self.service_name, 
                      self.heat_network._HeatNetwork__energy_supply_connections)
        
        with self.assertRaises(SystemExit):
            self.heat_network._HeatNetwork__create_service_connection(self.service_name)
    
    
    def test_create_service_hot_water_direct(self):
        '''Test a HeatNetworkSeriviceWaterStorage object is created with EnergySupplyConnection'''
        self.service_name = 'hot_water_direct'
        temp_hot_water = 50
        cold_feed = MagicMock()
        
        obj = self.heat_network.create_service_hot_water_direct(self.service_name,
                                                          temp_hot_water,
                                                          cold_feed)
        self.assertIn(self.service_name, 
                      self.heat_network._HeatNetwork__energy_supply_connections)
    
        self.assertTrue(isinstance(obj, HeatNetworkServiceWaterDirect))
        
    def test_create_service_space_heating(self):
        '''Test a HeatNetworkServiceSpace object is created with EnergySupplyConnection'''
        self.service_name = 'hot_water_space'
        control = MagicMock()
        
        obj = self.heat_network.create_service_space_heating(self.service_name,
                                                             control)
        self.assertIn(self.service_name, 
                      self.heat_network._HeatNetwork__energy_supply_connections)
        
               
        self.assertTrue(isinstance(obj, HeatNetworkServiceSpace))
    
    def test_timestep_end(self):
        '''Test at end of timestep appropriate functions are called'''
        self.heat_network.\
            _HeatNetwork__energy_supply_connection_aux = MagicMock()
        self.heat_network.\
            _HeatNetwork__energy_supply_connection_building_level_distribution_losses = MagicMock()

        self.heat_network.HIU_loss = MagicMock(return_value=10)
        self.heat_network.building_level_loss = MagicMock(return_value=20)
        #Call the function to test
        self.heat_network.timestep_end()
        
        self.assertEqual(self.heat_network._HeatNetwork__total_time_running_current_timestep, 0.0)               
        self.heat_network.\
            _HeatNetwork__energy_supply_connection_aux.demand_energy.assert_called_once_with(10)
        self.heat_network.\
            _HeatNetwork__energy_supply_connection_building_level_distribution_losses.\
            demand_energy.assert_called_once_with(20)
                
    
    



