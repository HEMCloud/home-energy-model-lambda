#!/usr/bin/env python3

"""
This module contains unit tests for the Buffer Tank class
"""

# Standard library imports
import unittest

# Set path to include modules to be tested (must be before local imports)
from unit_tests.common import test_setup
test_setup()

# Local imports
from core.simulation_time import SimulationTime
from core.material_properties import WATER, MaterialProperties
from core.heating_systems.heat_pump import BufferTank

class Test_BufferTank(unittest.TestCase):
    """ Unit tests for BufferTank class """

    def setUp(self):
        """ Create BufferTank object to be tested """
        self.simtime     = SimulationTime(0, 8, 1)
        self.buffertank = BufferTank(1.68, 50, 15, 0.040, 2, self.simtime, WATER, False)

    def test_buffer_loss(self):
        """ Test the buffer loss over the simulation time """
        # emitters data needed to run buffer tank calculations
        emitters_data_for_buffer_tank = [
                {'temp_emitter_req': 43.32561228292832, 'power_req_from_buffer_tank': 6.325422354229758, 'design_flow_temp': 55, 'target_flow_temp': 48.54166666666667, 'temp_rm_prev': 22.488371468978006, 'variable_flow': True, 'min_flow_rate': 0.05, 'max_flow_rate': 0.3, 'temp_diff_emit_dsgn': 10.0},
                {'temp_emitter_req': 30.778566169260767, 'power_req_from_buffer_tank': 4.036801431329545, 'design_flow_temp': 55, 'target_flow_temp': 48.54166666666667, 'temp_rm_prev': 22.61181775388348, 'variable_flow': True, 'min_flow_rate': 0.05, 'max_flow_rate': 0.3, 'temp_diff_emit_dsgn': 10.0},
                {'temp_emitter_req': 50.248361664005266, 'power_req_from_buffer_tank': 8.808940459526795, 'design_flow_temp': 55, 'target_flow_temp': 49.375, 'temp_rm_prev': 17.736483875769345, 'variable_flow': True, 'min_flow_rate': 0.05, 'max_flow_rate': 0.3, 'temp_diff_emit_dsgn': 10.0},
                {'temp_emitter_req': 30.723032018863076, 'power_req_from_buffer_tank': 6.444185473658857, 'design_flow_temp': 55, 'target_flow_temp': 49.375, 'temp_rm_prev': 16.85636993835381, 'variable_flow': True, 'min_flow_rate': 0.05, 'max_flow_rate': 0.3, 'temp_diff_emit_dsgn': 10.0},
                {'temp_emitter_req': 29.646908204800425, 'power_req_from_buffer_tank': 5.00550934831923, 'design_flow_temp': 55, 'target_flow_temp': 48.75, 'temp_rm_prev': 17.22290169647781, 'variable_flow': True, 'min_flow_rate': 0.05, 'max_flow_rate': 0.3, 'temp_diff_emit_dsgn': 10.0},
                {'temp_emitter_req': 30.42417311801241, 'power_req_from_buffer_tank': 2.5923631086027457, 'design_flow_temp': 55, 'target_flow_temp': 48.22916666666667, 'temp_rm_prev': 21.897823675853978, 'variable_flow': True, 'min_flow_rate': 0.05, 'max_flow_rate': 0.3, 'temp_diff_emit_dsgn': 10.0},
                {'temp_emitter_req': 39.38823309970535, 'power_req_from_buffer_tank': 1.9107311055974638, 'design_flow_temp': 55, 'target_flow_temp': 48.4375, 'temp_rm_prev': 22.36470513987037, 'variable_flow': True, 'min_flow_rate': 0.05, 'max_flow_rate': 0.3, 'temp_diff_emit_dsgn': 10.0},
                {'temp_emitter_req': 28.934946810199524, 'power_req_from_buffer_tank': 1.711635686322881, 'design_flow_temp': 55, 'target_flow_temp': 48.4375, 'temp_rm_prev': 22.425363294403255, 'variable_flow': True, 'min_flow_rate': 0.05, 'max_flow_rate': 0.3, 'temp_diff_emit_dsgn': 10.0}
        ]
        # temperatures required to calculate buffer tank thermal losses
        temp_ave_buffer = [
                            42.13174056962889,
                            39.15850036184071,
                            47.90592627854362,
                            46.396261107092855,
                            44.393784168519964,
                            41.113688636784985,
                            38.05323632350841,
                            34.94802876725388,
                            37.658992822855524,
                            34.3155583742916,
                            ]       
        temp_rm_prev = [
                            22.503414923272768,
                            22.629952417028925,
                            18.606533490587633,
                            17.3014761483025,
                            16.89603650204302,
                            22.631060393299737,
                            22.434635318905773,
                            22.736995736582873,
                            22.603763288379653,
                            22.89241467168529
                            ]       
        # Expected results
        heat_loss_buffer_kWh = [
                            0.01620674285529469,
                            0.0063519154341823356,
                            0.025287016057516827,
                            0.010785181618173873,
                            0.009663116173139813,
                            0.0066316051216787795,
                            0.01324052174653832,
                            0.005063009401174876
                            ]
        flow_temp_increase_due_to_buffer = [
                            3.952751095382638,
                            6.140725209053976,
                            1.5784508035116716,
                            3.8392108282420097,
                            5.2146182138439485,
                            7.521641387569073,
                            7.370102324208936,
                            6.569653721125626
                            ]
        expected_thermal_losses = [
                            0.015266475502721427,
                            0.012855537290409166,
                            0.022788416612854655,
                            0.02262927719017028,
                            0.02138713707392651,
                            0.014375377522710748,
                            0.012147800781357604,
                            0.00949747013496634        
                            ]       
        expected_internal_gains = [
                            24.31011428294203,
                            9.527873151273504,
                            37.93052408627524,
                            16.17777242726081,
                            14.494674259709718,
                            9.947407682518168,
                            19.86078261980748,
                            7.594514101762314
                            ]
        
        # Simulate updating buffer loss over time
        for t_idx, _, _ in self.simtime:
            buffer_results = self.buffertank.calc_buffer_tank("test service",emitters_data_for_buffer_tank[t_idx])
            internal_gains = self.buffertank.internal_gains()
            thermal_losses = self.buffertank.thermal_losses(temp_ave_buffer[t_idx],temp_rm_prev[t_idx])

            with self.subTest(i=t_idx):
                self.assertAlmostEqual(
                    buffer_results[t_idx]['heat_loss_buffer_kWh'],
                    heat_loss_buffer_kWh[t_idx],
                    msg=f"Incorrect buffer loss at timestep {t_idx}"
                )

            with self.subTest(i=t_idx):
                self.assertAlmostEqual(
                    buffer_results[t_idx]['flow_temp_increase_due_to_buffer'],
                    flow_temp_increase_due_to_buffer[t_idx],
                    msg=f"Incorrect flow temperature increase due to buffer at timestep {t_idx}"
                )

            with self.subTest(i=t_idx):
                self.assertAlmostEqual(
                    thermal_losses,
                    expected_thermal_losses[t_idx],
                    msg=f"Incorrect buffer tank thermal losses at timestep {t_idx}"
                )

            with self.subTest(i=t_idx):
                self.assertAlmostEqual(
                    internal_gains,
                    expected_internal_gains[t_idx],
                    msg=f"Incorrect buffer tank internal gains at timestep {t_idx}"
                )

