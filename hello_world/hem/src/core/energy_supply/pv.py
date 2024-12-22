#!/usr/bin/env python3

"""
This module contains objects that represent photovoltaic systems.
"""

# Standard library imports
from numpy import math
from math import cos, pi

# Local imports
import sys
import core.units as units
from core.space_heat_demand.building_element import projected_height, sky_view_factor


class PhotovoltaicSystem:
    """ An object to represent a photovoltaic system """

    """ system performance factor lookup
          informative values from table C.4 Annex C BS EN 15316-4-3:2017
          note from 6.2.4.7.2 rear surface free - is if PV system is not integrated.
          Assume this means NOT integrated (BIPV)  or attached (BAPV)
          Increased by 0.85/0.8 based on median quoted performance ratio from
          "Performance of Distributed PV in the UK: A Statistical Analysis of
          Over 7000 systems" conference paper from 31st European Photovoltaic
          Solar Energy Conference and Exhibition, September 2015, assuming this
          applies to moderately ventilated case.
    """
    # Note: BS EN 15316-4-3:2017 section 6.2.4.7.2 states that the performance
    #       factor for "rear surface free" should be 1.0. However, this would
    #       seem to imply that there are no inverter or other system losses,
    #       despite the fact that section 6.2.4.7.5 states that this factor
    #       accounts for these losses. Also, no factor for "rear surface free"
    #       has been given in Table C.4. Therefore, it was decided to use the
    #       same factor for "rear surface free" as for "strongly or forced
    #       ventilated".
    __f_perf_lookup = {
        'unventilated': 0.81,
        'moderately_ventilated': 0.85,
        'strongly_or_forced_ventilated': 0.87,
        'rear_surface_free': 0.87,
    }

    """
    Inverter efficiency reduction as a function of shaded proportion and type of inverter is based on data from
    'Partial Shade Evaluation of Distributed Power Electronics for Photovoltaic Systems', Chris Deline et al,
    figure 7, accessed at: https://www.nrel.gov/docs/fy12osti/54039.pdf.    
    
    The equations given in figure 7 were used to calculate the normalised power output for a range of different
    levels of panel covering, from 0 to 100% for the two inverter types represented (string and micro [aka optimised]). 
    
    The measured 37% transmission rate of the covering material was applied to determine the reduction in incident
    radiation at each level of coverage:
        % reduction in radiation reaching panel = percent of panel covered * (1 - 0.37)
    (where 1 = all radiation blocked, 0 = no reduction)      
    
    The level of shading was converted to a shading factor of the form used in HEM 
    (where 1 = no shading, 0 = complete shading):
        f_sh_dir = (1 - % reduction in radiation reaching panel)
        
    It was assumed that efficiency reduction being calculated is only related to the shading of *direct* radiation
    (not diffuse) on the basis that the impact is caused by part of the panel being shaded, while the rest is not. 
    Diffuse shading would affect the whole panel approximately equally, so should not affect inverter efficiency 
    in the same way. (Note that the reduction in output associated with the overall level of radiation - including 
    direct and diffuse shading - is separately accounted for).
    
    To set a reference point, it was assumed that, in the absence of a reduction due inverter efficiency, output would 
    be proportional to the incident solar radiation and therefore that the normalised output would be equal to the 
    shading factor - e.g. if 75% of the radiation was transmitted we would get 75% of the power output.
    
    The difference between this reference output and the output predicted by the equations representing the actual data
    was assumed to be due to the efficiency reduction of the inverter induced by overshading. The ratio of the 'expected'
    output and the 'actual' output was calculated. This step disaggregates the reduction due to inverter efficiency from 
    the reduction simply due to lower incident radiation, to avoid this being double counted. This is tehrefore the 
    correction factor needed in HEM to take into consideration the reduced efficiency of inverters when PV panels are 
    partially overshaded. 
    
    2nd order polynomial curves were fitted through the resulting inverter efficiency factors (as a function of the direct
    factor f_sh_dir, resulting in the equations used below). A two stage polynomial is needed for each inverter type
    because of the step change in behaviour when the 'lower limit' referred to in the source is reached.       
    """
    
    def __inverter_efficiency_lookup(self, inverter_type, f_sh_dir):
        # Calculate inverter efficiency based on direct shading factor and inverter type        
        x = f_sh_dir
        
        if inverter_type == 'string_inverter':
            thresh=0.7
            a = 2.7666
            b = -4.3397
            c = 2.2201
            d = -1.9012
            e = 4.8821
            f = -1.9926
            if x < thresh:
                return min(1 , a * x ** 2 + b * x + c)
            else:
                return min(1, d * x ** 2 + e * x + f)
                
        elif inverter_type == 'optimised_inverter': # aka micro inverter
            thresh=0.42
            a = 2.7666
            b = -4.3397
            c = 2.2201
            d = -0.2024
            e = 0.4284
            f = 0.7721
            if x < thresh:
                return min(1 , a * x ** 2 + b * x + c)
            else:
                return min(1, d * x ** 2 + e * x + f)
        else:
            return None
    
    def __init__(self, peak_power, ventilation_strategy, pitch, orientation,
                 base_height, height, width,
                 ext_cond, energy_supply_conn, simulation_time, shading,
                 inverter_peak_power_dc, inverter_peak_power_ac, inverter_is_inside, inverter_type):
        """ Construct a PhotovoltaicSystem object

        Arguments:
        peak_power       -- Peak power in kW; represents the electrical power of a photovoltaic
                            system with a given area and a for a solar irradiance of 1 kW/m2
                            on this surface (at 25 degrees)
                            TODO - Could add other options at a later stage.
                            Standard has alternative method when peak power is not available
                            (input type of PV module and Area instead when peak power unknown)
        ventilation_strategy   -- ventilation strategy of the PV system.
                                  This will be used to determine the system performance factor
                                   based on a lookup table
        pitch            -- is the tilt angle (inclination) of the PV panel from horizontal,
                            measured upwards facing, 0 to 90, in degrees.
                            0=horizontal surface, 90=vertical surface.
                            Needed to calculate solar irradiation at the panel surface.
        orientation      -- is the orientation angle of the inclined surface, expressed as the
                            geographical azimuth angle of the horizontal projection of the inclined
                            surface normal, -180 to 180, in degrees;
                            Assumed N 180 or -180, E 90, S 0, W -90
                            TODO - PV standard refers to angle as between 0 to 360?
                            Needed to calculate solar irradiation at the panel surface.
        base_height      -- is the distance between the ground and the lowest edge of the PV panel, in m
        height           -- is the height of the PV panel, in m
        width            -- is the width of the PV panel, in m
        ext_cond         -- reference to ExternalConditions object
        energy_supply_conn -- reference to EnergySupplyConnection object
        simulation_time  -- reference to SimulationTime object
        inverter_peak_power_dc -- Peak power in kW; represents the peak electrical DC power input to the inverter
        inverter_peak_power_ac -- Peak power in kW; represents the peak electrical AC power input to the inverter
        inverter_is_inside -- tells us that the inverter is considered inside the building
        shading          -- TODO could add at a later date. 
        inverter_type    -- type of inverter to help with calculation of efficiency of inverter when overshading
        """
        self.__peak_power = peak_power
        self.__f_perf = self.__f_perf_lookup[ventilation_strategy]
        self.__pitch = pitch
        self.__orientation = orientation
        self.__base_height = base_height
        self.__width = width
        self.__projected_height = projected_height(pitch, height)
        self.__external_conditions = ext_cond
        self.__energy_supply_conn = energy_supply_conn
        self.__simulation_time = simulation_time
        self.__shading = shading
        self.__inverter_peak_power_dc = inverter_peak_power_dc
        self.__inverter_peak_power_ac = inverter_peak_power_ac
        self.__inverter_is_inside = inverter_is_inside
        self.__inverter_type = inverter_type

    def inverter_is_inside(self):
        """ Return whether this unit is considered inside the building or not """
        return self.__inverter_is_inside

    def produce_energy(self):
        """ Produce electrical energy (in kWh) from the PV system
            according to BS EN 15316-4-3:2017 """

        #solar_irradiance in W/m2
        i_sol_dir, i_sol_dif, _ = self.__external_conditions.calculated_direct_diffuse_total_irradiance(
            self.__pitch,
            self.__orientation
            )
        #shading factors
        f_sh_dir, f_sh_dif = self.shading_factors_direct_diffuse()

        # Calculate the impact of direct shading on the panel/inverters ability to output energy,
        # i.e. where the shadow of an obstacle falls on the PV panel.  
        # There is a lower impact if module level electronics ('optimised inverter') selected.
        # This factor is then applied in the energy_produced calculation later.
        if f_sh_dir < 1:
            inv_shad_inefficiency = self.__inverter_efficiency_lookup(self.__inverter_type, f_sh_dir)
            if inv_shad_inefficiency is None:
                sys.exit('Inverter type not recognised')
        else:
            inv_shad_inefficiency = 1

        #solar_irradiation in kWh/m2
        solar_irradiation = (i_sol_dir * f_sh_dir + i_sol_dif * f_sh_dif) \
                            * self.__simulation_time.timestep() / units.W_per_kW

        #reference_solar_irradiance kW/m2
        ref_solar_irradiance = 1

        #CALCULATION
        #E.el.pv.out.h = E.sol.pv.h * P.pk * f.perf / I.ref
        #energy_produced = solar_irradiation * peak_power * system_performance_factor
        #                    / reference_solar_irradiance
        # energy input in kWh; now need to calculate total energy produce taking into account inverter efficiency
        energy_input \
            = solar_irradiation * self.__peak_power * self.__f_perf * inv_shad_inefficiency / 0.972 / ref_solar_irradiance 
            # f_perf is divided by 0.92 to avoid double-applying the inverter efficiency, 
            # which is applied separately below via 'inverter_dc_ac_efficiency', since 
            # inverter efficiency was inherently included in the factors taken from
            # from BS EN 15316-4-3:2017.

        # power output from PV panel in kW used to calculate ratio for efficiency loss of inverters from DC to AC
        power_input_inverter = energy_input / self.__simulation_time.timestep()

        # Calculate Ratio of Rated Power
        ratio_of_rated_output = min(power_input_inverter, self.__inverter_peak_power_dc) / self.__inverter_peak_power_dc

        # Using Ratio of Rated Power, calculate Inverter DC to AC efficiency 
        # equation was estimated based on graph from 
        # https://www.researchgate.net/publication/260286647_Performance_of_PV_inverters figure 9
        if ratio_of_rated_output == 0:
            inverter_dc_ac_efficiency = 0
        else:
            """Empirical efficiency curve fit primarily based on SMA Sunny Boy inverters (largest market share 2018)
            assisted with Sungrow and Huawei inverters (largest market share 2019)."""
            #System of 3 equations to fit efficiency curve for Sunny Boy PV2AC Inverters
            inverter_dc_ac_efficiency_1 = 97.2 * (1 - (0.18 / (1 + math.e ** (21 * ratio_of_rated_output) ) ) )
            inverter_dc_ac_efficiency_2 = 0.5 * math.cos( math.pi * ratio_of_rated_output) + 96.9
            inverter_dc_ac_efficiency_3 = 97.2 * math.tanh(30*ratio_of_rated_output)
            inverter_dc_ac_efficiency = min(inverter_dc_ac_efficiency_1,
                                            inverter_dc_ac_efficiency_2,
                                            inverter_dc_ac_efficiency_3)
            inverter_dc_ac_efficiency = inverter_dc_ac_efficiency / 100
        # Calculate energy produced output taking into account peak power of inverter + array 
        # and inverter DC to AC efficiency
        energy_produced \
            = min (energy_input, self.__inverter_peak_power_dc * self.__simulation_time.timestep()) \
                 * inverter_dc_ac_efficiency
        energy_produced = min(energy_produced, self.__inverter_peak_power_ac * self.__simulation_time.timestep())

        # Add energy produced to the applicable energy supply connection (this will reduce demand)
        self.__energy_supply_conn.supply_energy(energy_produced)
        energy_lost = energy_input - energy_produced

        return energy_produced, energy_lost  # kWh

    def shading_factors_direct_diffuse(self):
        """ return calculated shading factor """
        return self.__external_conditions.shading_reduction_factor_direct_diffuse( \
                self.__base_height, self.__projected_height, self.__width, \
                self.__pitch, self.__orientation, self.__shading)
