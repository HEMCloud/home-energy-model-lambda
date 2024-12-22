#!/usr/bin/env python3

"""
This module contains unit tests for the notional building
"""

# Standard library imports
import unittest
import json
import os, sys
from copy import deepcopy

# Set path to include modules to be tested (must be before local imports)
from unit_tests.common import test_setup
test_setup()

# Local imports
from core.simulation_time import SimulationTime
from core.space_heat_demand.building_element import HeatFlowDirection
from wrappers.future_homes_standard.future_homes_standard import calc_TFA
from wrappers.future_homes_standard import future_homes_standard_notional
from wrappers.future_homes_standard.FHS_HW_events import STANDARD_BATHSIZE



class NotionalBuildingHeatPump(unittest.TestCase):
    """ Unit tests for Notional Building """

    def setUp(self):
        self.maxDiff=None

        this_directory = os.path.dirname(os.path.relpath(__file__))
        file_path =  os.path.join(this_directory, "test_future_homes_standard_notional_input_data.json")
        with open(file_path) as json_file:
            self.project_dict = json.load(json_file)
        # Determine cold water source
        cold_water_type = list(self.project_dict['ColdWaterSource'].keys())
        if len(cold_water_type) == 1:
            self.cold_water_source = cold_water_type[0]
        else:
            sys.exit('Error: There should be exactly one cold water type')

        # Defaults
        self.hw_timer = "hw timer"
        self.hw_timer_eco7 = "hw timer eco7"
        self.notional_HP = 'notional_HP'
        self.is_notA = True
        self.is_FEE  = False
        self.energysupplyname_main = 'mains elec' 
        self.TFA = calc_TFA(self.project_dict)
        self.opening_lst = ['open_chimneys', 'open_flues', 'closed_fire', 'flues_d', 'flues_e',
                        'blocked_chimneys', 'passive_vents', 'gas_fires']
        self.table_R2 = {
            'E1' : 0.05,
            'E2' : 0.05,
            'E3' : 0.05,
            'E4' : 0.05,
            'E5' : 0.16,
            'E19' : 0.07,
            'E20' : 0.32,
            'E21' : 0.32,
            'E22' : 0.07,
            'E6' : 0,
            'E7' : 0.07,
            'E8' : 0,
            'E9' : 0.02,
            'E23' : 0.02,
            'E10' : 0.06,
            'E24' : 0.24,
            'E11' : 0.04,
            'E12' : 0.06,
            'E13' : 0.08,
            'E14' : 0.08,
            'E15' : 0.56,
            'E16' : 0.09,
            'E17' : -0.09,
            'E18' : 0.06,
            'E25' : 0.06,
            'P1' : 0.08,
            'P6' : 0.07,
            'P2' : 0,
            'P3' : 0,
            'P7' : 0.16,
            'P8' : 0.24,
            'P4' : 0.12,
            'P5' : 0.08 ,
            'R1' : 0.08,
            'R2' : 0.06,
            'R3' : 0.08,
            'R4' : 0.08,
            'R5' : 0.04,
            'R6' : 0.06,
            'R7' : 0.04,
            'R8' : 0.06,
            'R9' : 0.04,
            'R10' : 0.08,
            'R11' : 0.08
            }

    def test_edit_lighting_efficacy(self):

        project_dict = deepcopy(self.project_dict)
        future_homes_standard_notional.edit_lighting_efficacy(project_dict)

        for zone in project_dict['Zone'].values():
            self.assertTrue("Lighting" in zone)
            self.assertEqual(zone["Lighting"]["efficacy"], 120)

    def test_edit_opaque_ajdZTU_elements(self):

        project_dict = deepcopy(self.project_dict)
        future_homes_standard_notional.edit_opaque_ajdZTU_elements(project_dict)

        for zone in project_dict["Zone"].values():
            for building_element in zone["BuildingElement"].values():
                if building_element["pitch"] == HeatFlowDirection.DOWNWARDS:
                    self.assertEqual(building_element["u_value"], 0.13)
                elif building_element["pitch"] == HeatFlowDirection.UPWARDS:
                    self.assertEqual(building_element["u_value"], 0.11)
                elif building_element["pitch"] == HeatFlowDirection.HORIZONTAL:
                    if "is_external_door" in building_element:
                        if building_element["is_external_door"]:
                            self.assertEqual(building_element["u_value"], 1.0)
                        else:
                            self.assertEqual(building_element["u_value"], 0.18)
                    else:
                        self.assertEqual(building_element["u_value"], 0.18)

    def test_edit_ground_floors(self):

        project_dict = deepcopy(self.project_dict)
        future_homes_standard_notional.edit_ground_floors(project_dict)

        for zone in project_dict["Zone"].values():
            for building_element in zone["BuildingElement"].values():
                if building_element["type"] == "BuildingElementGround":
                    self.assertEqual(building_element["u_value"], 0.13)
                    self.assertEqual(building_element["r_f"], 6.12)
                    self.assertEqual(building_element["psi_wall_floor_junc"], 0.16)

    def test_edit_thermal_bridging(self):

        project_dict = deepcopy(self.project_dict)
        future_homes_standard_notional.edit_thermal_bridging(project_dict)

        for zone in project_dict["Zone"].values():
            if "ThermalBridging" in zone:
                for thermal_bridge in zone["ThermalBridging"].values():
                    if thermal_bridge["type"] == "ThermalBridgePoint":
                        self.assertEqual(thermal_bridge["heat_transfer_coeff"], 0.0)
                    elif thermal_bridge["type"] == "ThermalBridgeLinear":
                        junction_type = thermal_bridge["junction_type"]
                        self.assertTrue(junction_type in self.table_R2) 
                        self.assertEqual(
                            thermal_bridge["linear_thermal_transmittance"],
                            self.table_R2[junction_type],
                        )

    def test_calc_max_glazing_area_fraction(self):
        project_dict = {
            "Zone": {
                "test_zone": {
                    "BuildingElement": {
                        "test_rooflight": {
                            "type": "BuildingElementTransparent",
                            "pitch": 0.0,
                            "height": 2.0,
                            "width": 1.0,
                            }
                        }
                    }
                }
            }

        project_dict["Zone"]["test_zone"]["BuildingElement"]["test_rooflight"]["u_value"] = 1.5
        self.assertEqual(
            future_homes_standard_notional.calc_max_glazing_area_fraction(project_dict, 80.0),
            0.24375,
            "incorrect max glazing area fraction",
            )

        project_dict["Zone"]["test_zone"]["BuildingElement"]["test_rooflight"]["u_value"] = 1.0
        self.assertEqual(
            future_homes_standard_notional.calc_max_glazing_area_fraction(project_dict, 80.0),
            0.25,
            "incorrect max glazing area fraction",
            )

        project_dict["Zone"]["test_zone"]["BuildingElement"]["test_rooflight"]["u_value"] = 1.5
        project_dict["Zone"]["test_zone"]["BuildingElement"]["test_rooflight"]["pitch"] = 90.0
        self.assertEqual(
            future_homes_standard_notional.calc_max_glazing_area_fraction(project_dict, 80.0),
            0.25,
            "incorrect max glazing area fraction when there are no rooflights",
            )

    def test_edit_bath_shower_other(self):

        project_dict = deepcopy(self.project_dict)
        future_homes_standard_notional.edit_bath_shower_other(project_dict, self.cold_water_source)

        expected_bath = {
            "medium": {
                "ColdWaterSource": self.cold_water_source,
                "flowrate": 12,
                "size": STANDARD_BATHSIZE
            }
        }

        expected_shower = {
            "mixer": {
                "ColdWaterSource": self.cold_water_source,
                "flowrate": 8,
                "type": "MixerShower"
            }
        }

        expected_other = {
            "other": {
                "ColdWaterSource": self.cold_water_source,
                "flowrate": 6
            }
        }

        self.assertDictEqual(project_dict['HotWaterDemand']['Bath'], expected_bath)
        self.assertDictEqual(project_dict['HotWaterDemand']['Shower'], expected_shower)
        self.assertDictEqual(project_dict['HotWaterDemand']['Other'], expected_other)

    def test_add_wwhrs(self):
        project_dict = deepcopy(self.project_dict)
        future_homes_standard_notional.add_wwhrs(project_dict, self.cold_water_source, self.is_notA, self.is_FEE)

        expected_wwhrs = {
            "Notional_Inst_WWHRS": {
                "ColdWaterSource": self.cold_water_source,
                "efficiencies": [50, 50],
                "flow_rates": [0, 100],
                "type": "WWHRS_InstantaneousSystemB",
                "utilisation_factor": 0.98
            }
        }

        if project_dict['General']['storeys_in_building'] > 1 and self.is_notA and not self.is_FEE:
            self.assertIn("WWHRS", project_dict)
            self.assertDictEqual(project_dict['WWHRS'], expected_wwhrs)
            self.assertEqual(project_dict['HotWaterDemand']['Shower']['mixer']["WWHRS"], "Notional_Inst_WWHRS")
        else:
            self.assertNotIn("WWHRS", project_dict)
            self.assertNotIn("WWHRS", project_dict['HotWaterDemand']['Shower']['mixer'])

    def test_calculate_daily_losses(self):
        expected_cylinder_vol = 265
        daily_losses = future_homes_standard_notional.calculate_daily_losses(expected_cylinder_vol)
        expected_daily_losses = 1.03685  

        self.assertAlmostEqual(daily_losses, expected_daily_losses, places=5)

    def test_edit_storagetank(self):
        project_dict = deepcopy(self.project_dict)
        future_homes_standard_notional.edit_storagetank(project_dict, self.cold_water_source, self.TFA)

        expected_primary_pipework_dict = [
                {
                    "location": "internal",
                    "internal_diameter_mm": 26,
                    "external_diameter_mm": 28,
                    "length": 2.5,
                    "insulation_thermal_conductivity": 0.035,
                    "insulation_thickness_mm": 35,
                    "surface_reflectivity": False,
                    "pipe_contents": "water"
                }
            ]

        expected_hotwater_source = {
            'hw cylinder': {
                'ColdWaterSource': self.cold_water_source,
                'HeatSource': {
                    self.notional_HP: {
                        'ColdWaterSource': self.cold_water_source,
                        'EnergySupply': self.energysupplyname_main,
                        'heater_position': 0.1,
                        'name': self.notional_HP,
                        'temp_flow_limit_upper': 60,
                        'thermostat_position': 0.1,
                        'type': 'HeatSourceWet'
                    }
                },
                'daily_losses': 0.46660029577109363, 
                'type': 'StorageTank',
                'volume': 80.0,
                'primary_pipework': expected_primary_pipework_dict,
            }
        }
        self.assertDictEqual(project_dict['HotWaterSource'], expected_hotwater_source)

    def test_calc_daily_hw_demand(self):
        project_dict = deepcopy(self.project_dict)
        cold_water_source_name = list(project_dict['ColdWaterSource'].keys())[0]

        # Add notional objects that affect HW demand calc
        future_homes_standard_notional.edit_bath_shower_other(project_dict, cold_water_source_name)

        daily_HWD = future_homes_standard_notional.calc_daily_hw_demand(
            project_dict,
            self.TFA,
            cold_water_source_name,
            )

        expected_result = [
            4.494866624219392, 3.6262929661140406, 2.4792292219363525, 7.396905949799487,
            2.334290833000372, 8.938831222369114, 4.218109245384848, 3.2095837032274623,
            1.562913391249543, 8.846662366836481, 2.573896298797947, 3.8158857819823955, 
            1.8643761342051466, 1.456499804780102, 7.426850861522029, 2.9833503486722512,
            4.217424343066319, 8.086072907696455, 4.14341306475027, 5.363210797769194, 
            4.51254160486555, 4.535867190456099, 2.7857687977141605, 1.7560127175725972,
            10.333211623720878, 2.0533256568949536, 10.5846961515653, 2.9116693757992294,
            6.246398935042146, 1.6696701053184573, 13.851788339322859, 3.492087111231953,
            7.271874351886643, 3.4529488454587005, 12.374228697052182, 4.392672154556575,
            1.6028771659496917, 2.5058963927074895, 2.075293843606148, 2.949279475580221,
            8.392209203216268, 7.314951072027724, 3.8238937613049946, 6.812712493984371,
            4.537127728764957, 6.858233389853893, 3.994128161632102, 6.612136728233484,
            10.073004625703325, 7.1389148991972755, 1.5377879632668527, 2.5192092256423533,
            3.5974699592273436, 2.677722497971631, 6.641600203287786, 2.108183420048377,
            2.0324151238352606, 4.5025717651118, 1.6287189927962715, 5.184027724364109,
            2.19733248287286, 5.538684171666794, 1.6808281306652284, 5.413255340871867,
            2.5025554646129446, 6.9674570352988034, 4.018149967311069, 3.598667197534451,
            2.2197290514730836, 6.818451857176455, 5.796189225222955, 7.768257372957939,
            1.9635622695280748, 4.990639078067053, 11.326110200617702, 7.793122367331328,
            4.50364508936643, 8.379833734745256, 3.308002750963755, 5.125036944678628,
            5.130855988470622, 6.976241946425853, 9.280525199389762, 6.879123493336726,
            3.7542978536142275, 1.0782890932651108, 6.663709522738787, 5.7746999922120015,
            3.9743519683699224, 9.8172995461514, 2.9545593496596627, 5.318321839987381,
            3.3213819919472374, 7.238785487773112, 0.975438526348773, 6.4976602476390495,
            3.7068430878370746, 3.6626428865004845, 3.448702673630278, 2.836638476910602,
            4.504302459687092, 4.594078645382666, 1.280400852785038, 9.635660153417774,
            2.3614201923456397, 5.013620232473153, 5.308539972801421, 3.238066845393417,
            6.598303437213936, 2.659608088311913, 3.4249044366870596, 1.7403514603158758,
            9.599864960640643, 4.369113075109336, 3.8042018874949823, 4.28862554376783,
            8.382412615836817, 3.6774875962929796, 9.929521288784244, 5.062516904173654,
            1.295233711655901, 3.821798499477692, 2.7132360178922594, 4.1887507596892,
            3.0863014076672695, 5.419182763235196, 2.4073147138874753, 4.213814051467208,
            1.4251763271057125, 4.63864991810561, 1.8216774464333805, 7.563505390005953,
            3.555241721557862, 4.493983266747359, 3.6876604931200268, 2.454316031896153,
            6.607387606094413, 9.661565220506915, 4.386150963483148, 8.17494299730526,
            6.3198003788420865, 11.467482765051136, 4.4065433247605155, 4.988557708764494,
            9.059519529597852, 3.3755152852188606, 7.698743531592137, 6.618981677978387,
            4.175477039072181, 6.806814349660336, 7.431397132641212, 3.2631899144907384,
            5.0699911933702815, 2.544651729021151, 6.080829912290311, 3.258481663966277,
            3.2938506150971927, 1.8260826000310022, 2.7299288206743455, 6.385202523388037,
            7.33598893338676, 6.840098800550557, 2.4629260392399206, 2.822974223355313,
            4.03397696765668, 7.1488374756688975, 3.5278223212553437, 1.6660138380568987,
            3.458555531243357, 4.197013547018917, 4.16975870859787, 5.562332837781567,
            5.725468422378183, 6.185468819167943, 1.6837093971173656, 4.104228396783036,
            2.1451522407332986, 5.200237362413139, 2.084669219978378, 2.143187834435002,
            2.3140330225844843, 2.5126535024521788, 4.292203829906608, 6.2948386960261375,
            2.707084807447703, 1.430079063200245, 3.1398877317179585, 4.624382313637398,
            2.1098013499095423, 3.9693834315834158, 2.918849367120602, 1.7223877188894419,
            4.2052444383809435, 1.7027379387189652, 1.7409058342821224, 9.73885109912091,
            3.8320864374919834, 2.8551701405557335, 3.3985085530029173, 2.6417203955118143,
            3.1546804210730217, 3.4473648609972964, 4.3394904975655955, 1.8618334598784554,
            1.187119680626635, 3.3999014822138482, 2.4231306986854895, 4.0855931662787555,
            1.1110467622212452, 3.0836645479450717, 5.041340866799629, 2.8584761392149347,
            3.7750089454569724, 3.98317291735132, 1.795715129859829, 2.627605288805403,
            5.475886512190622, 3.4271418225056154, 2.891347603259713, 5.552587133534232,
            5.9809436633734885, 2.767071076874223, 4.710760448075293, 2.376717698170292,
            4.942802828102577, 4.892581657820345, 2.6791926869893503, 2.4743683782040664,
            1.7379083377994877, 5.778130144567433, 7.089071071443536, 2.0388630666174756,
            3.7782560363505686, 2.0730543304536373, 2.1948457120426, 3.361267582386128,
            4.2629464057701245, 5.958719480369529, 3.843708413984395, 3.4815545720306273,
            8.026655051714712, 6.732224042552772, 1.4786422506253278, 3.359516228956052,
            5.051731271772764, 10.37713698283845, 1.5329362087999223, 6.88186935703012,
            2.2867563460747355, 3.5695696056108077, 3.930672254899223, 3.0399623738750345,
            3.209364172407534, 3.038123333541644, 1.7884030890335403, 6.617270158127451,
            4.7892852624442686, 7.98246376739204, 8.787993619430916, 5.4370125075956715,
            5.631570198072755, 3.7085584331780943, 1.5882618579464969, 6.8903268532947735,
            7.892748258525165, 4.307146684097607, 5.325141240693638, 5.615893606452018,
            3.382501768861289, 2.341364633783292, 5.952009533729282, 3.9511068446824225,
            1.878750671506351, 8.770931877395236, 7.139918473168391, 2.968787917613602,
            6.133155615519703, 4.665146442297377, 3.5212090189137006, 4.272327030053521,
            1.8181271956714553, 1.2111424719202177, 3.8362418637305393, 1.6897828694837667,
            4.081067466294491, 4.733604465939571, 2.796815803783686, 3.542465234414504,
            0.9548600743010305, 2.270717485512143, 3.850180844042854, 3.7517662603259643,
            2.9551810686059867, 5.147502087772008, 2.4467917467578144, 5.105007513097308,
            8.408655228616226, 4.452315949253354, 1.6886214201468253, 3.2675270705264667,
            5.874045148360757, 3.0273104135176405, 3.7648099268073, 8.321357616729175,
            6.922623016214074, 1.678742522381662, 2.631473336660425, 1.9769260252425107,
            8.54513049934888, 5.606712381312642, 9.985899928272206, 7.7550045545739374,
            2.5269986968302973, 8.642277130729743, 3.817375807234058, 5.305481369727255,
            8.292051764966633, 4.4453842092352, 4.349003461844681, 6.000704722101477,
            4.543551953871819, 5.833324443935714, 3.3688153740004076, 1.1431546305228522,
            5.498587072359388, 2.703070385560106, 3.9334169401183137, 9.643230396608962,
            3.4603187156827, 7.691852031027734, 7.22790045250162, 4.393578726180066,
            5.243417451059749, 8.13349302370389, 5.2583811234088245, 3.546269300522664,
            3.506822851905734, 8.301287815488369, 4.300791041878211, 6.6587500730057325,
            3.9709462505155106, 3.362464817847712, 11.37915331454732, 8.068138598813995,
            7.916480638467263, 5.12202392506206, 8.685405827800933, 3.6092106401749424,
            5.91911663192843, 9.953524458486692, 4.472235413408162, 5.318791897610933,
            5.403579710683875, 10.195682092743064, 14.299048571158615, 12.38411860673397,
            2.1620234107802583, 8.521664591626005, 12.330847080589812, 3.136419959075777,
            5.542427971288237, 4.941578224663928, 4.725295110261525, 5.165968526411404,
            6.110105031454435
            ]
        self.assertEqual(len(daily_HWD),len(expected_result))
        for x, y in zip(daily_HWD,expected_result):
            self.assertAlmostEqual(x, y, places=5, msg="incorrect daily hot water demand calculated")

    def test_edit_hot_water_distribution(self):

        project_dict = deepcopy(self.project_dict)
        future_homes_standard_notional.edit_hot_water_distribution(project_dict, self.TFA)

        expected_hot_water_distribution_inner_dict = [
            {
                "location": "internal",
                "external_diameter_mm": 27,
                "insulation_thermal_conductivity": 0.035,
                "insulation_thickness_mm": 20, 
                "internal_diameter_mm": 25, 
                "length": 8.0,
                "pipe_contents": "water",
                "surface_reflectivity": False
            }
        ]

        self.assertDictEqual(project_dict['HotWaterDemand']['Distribution'][0], expected_hot_water_distribution_inner_dict[0])

    def test_edit_spacecoolsystem(self):

        project_dict = deepcopy(self.project_dict)
        project_dict['PartO_active_cooling_required'] = True

        future_homes_standard_notional.edit_spacecoolsystem(project_dict)

        for space_cooling_name, system in project_dict['SpaceCoolSystem'].items():
            self.assertEqual(system['efficiency'], 5.1)
            self.assertEqual(system['frac_convective'], 0.95)


    def test_add_solar_PV_house_only(self):

        project_dict = deepcopy(self.project_dict)
        expected_result = {'PV1': {
                    'EnergySupply': 'mains elec',
                    'orientation360': 180, 
                    'peak_power': 4.444444444444445,
                    'inverter_peak_power': 4.444444444444445,
                    'inverter_is_inside': False,
                    'pitch': 45,
                    'type': 'PhotovoltaicSystem', 
                    'ventilation_strategy': 'moderately_ventilated',
                    'shading': [],
                    'base_height': 1,
                    'width': 6.324555320336759,
                    'height': 3.1622776601683795
                    }
            }

        future_homes_standard_notional.add_solar_PV(project_dict, self.is_notA, self.is_FEE, self.TFA)

        self.assertDictEqual(project_dict['OnSiteGeneration'], expected_result)

