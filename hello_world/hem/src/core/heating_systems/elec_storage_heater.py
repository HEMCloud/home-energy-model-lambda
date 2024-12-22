#!/usr/bin/env python3

"""
This module provides object(s) to model the behaviour of electric storage heaters.
"""

# Third-party imports
import sys
from enum import Enum, auto
from scipy.integrate import solve_ivp
import numpy as np
from scipy.integrate._ivp.ivp import OdeResult
import types
from typing import Union
from collections import deque
from copy import deepcopy
from scipy.interpolate import interp1d

# Local imports
import core.units as units
from core.space_heat_demand.zone import Zone
from core.energy_supply.energy_supply import EnergySupplyConnection
from core.simulation_time import SimulationTime
from core.controls.time_control import LogicType, ChargeControl, SetpointTimeControl

class OutputMode(Enum):
    MIN = 'min'
    MAX = 'max'

class AirFlowType(Enum):
    FAN_ASSISTED = auto()
    DAMPER_ONLY = auto()

    @classmethod
    def from_string(cls, strval):
        if strval == 'fan-assisted':
            return cls.FAN_ASSISTED
        elif strval == 'damper-only':
            return cls.DAMPER_ONLY
        else:
            sys.exit('AirFlowType (' + str(strval) + ') not valid.')
            # TODO Exit just the current case instead of whole program entirely?

class ElecStorageHeater:
    """ Class to represent electric storage heaters """

    def __init__(
        self,
        pwr_in: float,
        rated_power_instant: float,
        storage_capacity: float,
        air_flow_type: str,
        frac_convective: float,
        fan_pwr: float,
        n_units: int,
        zone: Zone,
        energy_supply_conn: EnergySupplyConnection,
        simulation_time: SimulationTime,
        control: SetpointTimeControl,
        charge_control: ChargeControl,
        ESH_min_output : float,
        ESH_max_output : float,
        ext_cond,
        output_detailed_results=False,
    ):
        """Construct an ElecStorageHeater object

        Arguments:
        pwr_in               -- in kW (Charging)
        rated_power_instant  -- in kW (Instant backup)
        storage_capacity     -- in kWh
        air_flow_type        -- string specifying type of Electric Storage Heater:
                             -- fan-assisted
                             -- damper-only
        frac_convective      -- convective fraction for heating (TODO: Check if necessary)
        fan_pwr              -- Fan power [W]
        n_units              -- number of units install in zone
        zone                 -- zone where the unit(s) is/are installed
        energy_supply_conn   -- reference to EnergySupplyConnection object
        simulation_time      -- reference to SimulationTime object
        control              -- reference to a control object which must implement is_on() and setpnt() funcs
        charge_control       -- reference to a ChargeControl object which must implement different logic types
                                for charging the Electric Storage Heaters. 
        ESH_min_output       -- Data from test showing the output from the storage heater when not actively 
                                outputting heat, i.e. case losses only (with units kW)
        ESH_max_output       -- Data from test showing the output from the storage heater when it is actively 
                                outputting heat, e.g. damper open / fan running (with units kW)
        extcond              -- reference to ExternalConditions object
        output_detailed_results -- flag to create detailed emitter output results
        """

        self.__pwr_in: float = pwr_in
        self.__pwr_instant: float = rated_power_instant
        self.__storage_capacity: float = storage_capacity
        self.__air_flow_type: str = AirFlowType.from_string(air_flow_type)
        self.__frac_convective: float = frac_convective
        self.__n_units: int = n_units
        self.__zone: Zone = zone
        self.__energy_supply_conn: EnergySupplyConnection = energy_supply_conn
        self.__simulation_time: SimulationTime = simulation_time
        self.__control: SetpointTimeControl = control
        self.__charge_control: ChargeControl = charge_control
        self.__fan_pwr = fan_pwr

        self.__external_conditions = ext_cond
        self.__output_detailed_results = output_detailed_results
        self.temp_air: float = self.__zone.temp_internal_air()  # °C Room temperature
        # Power for driving fan
        # TODO: Modify fan energy calculation to SFP
        # self.__sfp: float = 0.0

        # Initialising other variables
        # Parameters
        self.__state_of_charge = 0
        # This represents the temperature difference between the core and the room on the first column
        # and the fraction of air flow relating to the nominal as defined above on the second column
        self.__ESH_min_output = ESH_min_output
        self.__ESH_max_output = ESH_max_output
        self.__energy_in: float = 0.0
        
        # Relevant for HHRSH
        self.__demand_met   = 0.0
        self.__demand_unmet = 0.0
        self.__prev_timestep = -1
        
        # Zone initial set point
        self.__zone_setpnt_init = self.__zone.setpnt_init()
        
        # Convert ESH_max_output to NumPy arrays without sorting
        self.__soc_max_array = np.array([pair[0] for pair in self.__ESH_max_output])
        self.__power_max_array = np.array([pair[1] for pair in self.__ESH_max_output])

        # Convert ESH_min_output to NumPy arrays without sorting
        self.__soc_min_array = np.array([pair[0] for pair in self.__ESH_min_output])
        self.__power_min_array = np.array([pair[1] for pair in self.__ESH_min_output])

        # Validate that both SOC arrays are in strictly increasing order
        if not np.all(self.__soc_max_array[:-1] <= self.__soc_max_array[1:]):
            raise ValueError("ESH_max_output SOC values must be in increasing order (from 0.0 to 1.0).")
        if not np.all(self.__soc_min_array[:-1] <= self.__soc_min_array[1:]):
            raise ValueError("ESH_min_output SOC values must be in increasing order (from 0.0 to 1.0).")
        
        # Validate that both SOC arrays start at 0.0 and end at 1.0
        if not np.isclose(self.__soc_max_array[0], 0.0):
            raise ValueError("The first SOC value in ESH_max_output must be 0.0 (fully discharged).")
        if not np.isclose(self.__soc_max_array[-1], 1.0):
            raise ValueError("The last SOC value in ESH_max_output must be 1.0 (fully charged).")
        
        if not np.isclose(self.__soc_min_array[0], 0.0):
            raise ValueError("The first SOC value in ESH_min_output must be 0.0 (fully discharged).")
        if not np.isclose(self.__soc_min_array[-1], 1.0):
            raise ValueError("The last SOC value in ESH_min_output must be 1.0 (fully charged).")

        # Validate that for any SOC, power_max >= power_min
        # Sample a fine grid of SOCs and ensure power_max >= power_min
        fine_soc = np.linspace(0.0, 1.0, 100)
        power_max_fine = interp1d(
            self.__soc_max_array,
            self.__power_max_array,
            kind='linear',
            fill_value="extrapolate",
            bounds_error=False,
            assume_sorted=True
        )(fine_soc)
        power_min_fine = interp1d(
            self.__soc_min_array,
            self.__power_min_array,
            kind='linear',
            fill_value=(0, 0),  # Ensures SOC outside bounds returns 0 power
            bounds_error=False,  # No errors for SOC values outside the bounds
            assume_sorted=True   # Assume the SOC array is sorted
        )(fine_soc)

        if not np.all(power_max_fine >= power_min_fine):
            raise ValueError("At all SOC levels, ESH_max_output must be >= ESH_min_output.")

        # Create interpolation functions for Power(SOC)
        self.__power_max_func = interp1d(
            self.__soc_max_array,
            self.__power_max_array,
            kind='linear',
            fill_value=(self.__power_max_array[0], self.__power_max_array[-1]),
            bounds_error=False,
            assume_sorted=True
        )

        self.__power_min_func = interp1d(
            self.__soc_min_array,
            self.__power_min_array,
            kind='linear',
            fill_value=(self.__power_min_array[0], self.__power_min_array[-1]),
            bounds_error=False,
            assume_sorted=True
        )
        
        self.__heat_retention_ratio = self.__heat_retention_output()
        
        # Create instance variable for emitter detailed output 
        if self.__output_detailed_results:
            self.__esh_detailed_results = {}
        else:
            self.__esh_detailed_results  = None

    def temp_setpnt(self):
        return self.__control.setpnt()

    def in_required_period(self):
        return self.__control.in_required_period()

    def frac_convective(self):
        return self.__frac_convective

    def __convert_to_kwh(self, power: float, time: float) -> float:
        """
        Converts power value supplied to the correct energy unit
        Arguments
        power -- Power value in watts
        time -- length of the time active

        returns -- Energy in kWh
        """
        return power / units.W_per_kW * time

    def __heat_retention_output(self):
        """
        Simulates the heat retention over 16 hours in OutputMode.MIN.
        
        Starts with a SOC of 1.0 and calculates the SOC after 16 hours.
        This is a self-contained function, and the SOC is not stored in self.__state_of_charge.
    
        :return: Final SOC after 16 hours.
        """
        # Set initial state of charge to 1.0 (fully charged)
        initial_soc = 1.0
        
        # Total time for the simulation (16 hours)
        total_time = 16.0 # This is the value from BS EN 60531 for determining heat retention ability
        
        # Select the SOC and power arrays for OutputMode.MIN
        soc_array = self.__soc_min_array
        power_func = self.__power_min_func
    
        # Set up interpolation function for Power vs SOC
        power_interp = interp1d(
            soc_array,
            power_func(soc_array),  # Ensure power_func(soc_array) is correct
            kind='linear',
            fill_value="extrapolate",  # We still use extrapolate, but let's check the bounds
            bounds_error=False,
            assume_sorted=True
        )
    
        # Define the ODE for SOC and energy delivered (no charging, only discharging)
        def soc_ode(t, y):
            soc = y  # y[0] is SOC, y[1] is total energy delivered
            
            # Ensure SOC stays within bounds
            soc = np.clip(soc, 0, 1)
            
            # Discharging: calculate power used based on SOC
            discharge_rate = -power_interp(soc)
            # Track the total energy delivered (discharged energy)
            ddelivered_dt = -discharge_rate  # Energy delivered (positive value)
            
            # SOC rate of change (discharging), divided by storage capacity
            dsoc_dt = -ddelivered_dt / self.__storage_capacity
    
            return [dsoc_dt]
        
        # Solve the ODE for SOC and cumulative energy delivered
        sol = solve_ivp(soc_ode, [0, total_time], [initial_soc], method='RK45', rtol=1e-1, atol=1e-3)
        
        # Final state of charge after 16 hours
        final_soc = sol.y[0][-1]
        
        # Clip the final SOC to ensure it's between 0 and 1
        final_soc = np.clip(final_soc, 0.0, 1.0)
        
        # Return the final state of charge after 16 hours
        return final_soc

    def __energy_output(self, mode: OutputMode):
        """
        Calculates the energy that can be delivered based on the mode ('min' or 'max'),
        and also returns the energy charged during the same timestep.
        
        :param mode: 'min' for minimum energy delivery, 'max' for maximum energy delivery.
        :return: Tuple containing (energy_delivered in kWh, time_used in hours, energy_charged in kWh).
        """
        if mode == OutputMode.MIN:
            soc_array = self.__soc_min_array
            power_func = self.__power_min_func
        elif mode == OutputMode.MAX:
            soc_array = self.__soc_max_array
            power_func = self.__power_max_func
        else:
            raise ValueError("Invalid mode. Choose Mode.MIN or Mode.MAX.")
        
        # Set up interpolation function for Power vs SOC
        power_interp = interp1d(
            soc_array,
            power_func(soc_array),  # Ensure power_func(soc_array) is correct
            kind='linear',
            fill_value="extrapolate",
            bounds_error=False,
            assume_sorted=True
            )
    
        # Charging: determine the maximum power available for charging
        target_charge = self.__target_electric_charge(self.__simulation_time.current_hour())
        if target_charge > 0:
            charge_rate = self.__pwr_in
            soc_max = target_charge
        else:
            charge_rate = 0
            soc_max = 1.0
            
        # Define the ODE for SOC, total energy charged, and total energy delivered
        def soc_ode(t, y):
            soc, energy_charged, energy_delivered = y  # y[0] is SOC, y[1] is total energy charged, y[2] is total energy delivered
            
            # Ensure SOC stays within bounds
            soc = np.clip(soc, 0, soc_max)
            
            # Discharging: calculate power used based on SOC
            discharge_rate = -power_interp(soc)
            # Track the total energy delivered (discharged energy)
            ddelivered_dt = -discharge_rate  # Energy delivered (positive value) is tracked separately
            
            # Track the total energy charged
            if soc < soc_max:
                dcharged_dt = charge_rate
            else:
                dcharged_dt = min(ddelivered_dt, self.__pwr_in) if target_charge > 0 else 0.0
    
            # Net SOC rate of change (discharge + charge), divided by storage capacity
            dsoc_dt = (-ddelivered_dt + dcharged_dt) / self.__storage_capacity
            return [dsoc_dt, dcharged_dt, ddelivered_dt]
    
        # Event function to stop the solver when SOC reaches 0
        def soc_zero_event(t, y):
            soc = y[0]
            return soc  # This will trigger when soc reaches 0
    
        # Set the event to terminate the integration when SOC reaches 0
        soc_zero_event.terminal = True
        soc_zero_event.direction = -1  # Detects when SOC is decreasing and crosses zero
    
        # Set initial conditions
        current_soc = self.__state_of_charge
        initial_energy_charged = 0.0  # No energy charged initially
        initial_energy_delivered = 0.0  # No energy delivered initially
        time_remaining = self.__simulation_time.timestep()  # in hours
    
        # Solve the ODE for SOC, cumulative energy charged, and cumulative energy delivered
        sol = solve_ivp(
            soc_ode, 
            [0, time_remaining], 
            [current_soc, initial_energy_charged, initial_energy_delivered], 
            method='RK45', 
            rtol=1e-4, 
            atol=1e-6, 
            events=soc_zero_event  # Add the event function
        )
        
        final_soc = sol.y[0][-1]
        
        # Total energy charged during the timestep
        total_energy_charged = sol.y[1][-1]
        
        # Total energy delivered during the timestep
        total_energy_delivered = sol.y[2][-1]
    
        # Total time used in delivering energy
        time_used = sol.t_events[0][0] if sol.t_events[0].size > 0 else sol.t[-1]  # Use event time if it was triggered

        # Return the total energy delivered, time used, and total energy charged
        return total_energy_delivered, time_used, total_energy_charged, final_soc

    def energy_output_min(self):
        """
        Calculates the minimum energy that must be delivered based on ESH_min_output.

        :return: Tuple containing (minimum energy deliverable in kWh, time used in hours).
        """
        return self.__energy_output(OutputMode.MIN)[0] * self.__n_units # called externally, factoring in all units

    def __energy_output_max(self):
        """
        Calculates the maximum energy that can be delivered based on ESH_max_output.

        :return: Tuple containing (maximum energy deliverable in kWh, time used in hours).
        """
        return self.__energy_output(OutputMode.MAX) # called internally, per unit

    def __target_electric_charge(self, time: float) -> float:
        """
        Calculates target charge from potential to charge system
        Arguments
        time -- current time period that we are looking at

        returns -- target charge
        """
        logic_type = LogicType.from_string(self.__charge_control.logic_type())
        temp_air = self.__zone.temp_internal_air()
        
        if logic_type == LogicType.MANUAL:
            # Implements the "Manual" control logic for ESH
            target_charge: float = self.__charge_control.target_charge()
            
        elif logic_type == LogicType.AUTOMATIC:
            # Implements the "Automatic" control logic for ESH
            # Automatic charge control can be achieved using internal thermostat(s) to
            # control the extent of charging of the heaters. 
            # Availability of electricity to the heaters may be controlled by the electricity 
            # supplier on the basis of daily weather predictions (see 24-hour tariff, 12.4.3); 
            # this should be treated as automatic charge control.
            # This is currently included by the schedule parameter in charge control object
            
            # TODO: Check and implement if external temperature sensors are also used for Automatic controls.
        
            target_charge: float = self.__charge_control.target_charge(temp_air)
            
        elif logic_type == LogicType.CELECT:
            # Implements the "CELECT" control logic for ESH
            # A CELECT-type controller has electronic sensors throughout the dwelling linked 
            # to a central control device. It monitors the individual room sensors and optimises 
            # the charging of all the storage heaters individually (and may select direct acting 
            # heaters in preference to storage heaters).
        
            target_charge = self.__charge_control.target_charge(temp_air)
                        
        elif logic_type == LogicType.HHRSH:
            # Implements the "HHRSH" control logic for ESH
            # A ‘high heat retention storage heater’ is one with heat retention not less 
            # than 45% measured according to BS EN 60531. It incorporates a timer, electronic 
            # room thermostat and fan to control the heat output. It is also able to estimate 
            # the next day’s heating demand based on external temperature, room temperature 
            # settings and heat demand periods. 

            energy_to_store = self.__charge_control.energy_to_store(self.__demand_met + self.__demand_unmet, self.__zone_setpnt_init)

            # None means not enough past data to do the calculation (Initial 24h of the calculation)
            # We go for a full load of the hhrsh
            if energy_to_store is None:
                energy_to_store = self.__pwr_in * units.hours_per_day
            
            if energy_to_store > 0:
                if self.__heat_retention_ratio is None:
                    sys.exit("Heat retention ratio is required for HHRSH.")
                    
                energy_stored = self.__state_of_charge * self.__storage_capacity #kWh
                
                if self.__heat_retention_ratio <= 0:
                    energy_to_add = self.__storage_capacity - energy_stored #kWh
                else:
                    energy_to_add = (1.0 / self.__heat_retention_ratio) * ( energy_to_store - energy_stored ) #kWh
                    
                target_charge_hhrsh = self.__state_of_charge + energy_to_add / self.__storage_capacity
                target_charge_hhrsh = np.clip(target_charge_hhrsh,0,1.0)
            else:
                target_charge_hhrsh = 0
            # target_charge (from input file, or zero when control is off) applied here 
            # is treated as an upper limit for target charge
            target_charge: float = min(self.__charge_control.target_charge(None), target_charge_hhrsh)

        else:
            sys.exit("Invalid logic type for charge control assigned to ElectricStorageHeater.")
    
        return target_charge
      
    def demand_energy(self, energy_demand: float) -> float:
        """
        Determines the amount of energy to release based on energy demand, while also handling the
        energy charging and logging fan energy.
        
        :param energy_demand: Energy demand in kWh.
        :return: Total net energy delivered (including instant heating and fan energy).
        """
        timestep = self.__simulation_time.timestep()
        energy_demand = energy_demand / self.__n_units
        self.__energy_instant: float = 0.0
    
        # Initialize time_used_max and energy_charged_max to default values
        time_used_max: float = 0.0
        energy_charged_max: float = 0.0
    
        # Calculate minimum energy that can be delivered
        q_released_min, __, self.__energy_charged, final_soc = self.__energy_output(OutputMode.MIN)
    
        if q_released_min > energy_demand:
            # Deliver at least the minimum energy
            self.__energy_delivered = q_released_min
            self.__demand_met = q_released_min
            self.__demand_unmet = 0
        else:
            # Calculate maximum energy that can be delivered
            q_released_max, time_used_max, self.__energy_charged, final_soc = self.__energy_output(OutputMode.MAX)
            
            if q_released_max < energy_demand:
                # Deliver as much as possible up to the maximum energy
                self.__energy_delivered = q_released_max
                self.__demand_met = q_released_max
                self.__demand_unmet = energy_demand - q_released_max

                # For now, we assume demand not met from storage is topped-up by
                # the direct top-up heater (if applicable). If still some unmet, 
                # this is reported as unmet demand.
                if self.__pwr_instant:
                    self.__energy_instant = min(self.__demand_unmet, self.__pwr_instant * timestep)  # kWh
                    time_instant = self.__energy_instant / self.__pwr_instant
                    time_used_max += time_instant
                    time_used_max = min(time_used_max, timestep)
                    
            else:
                # Deliver the demanded energy
                self.__energy_delivered = energy_demand
                if q_released_max > 0:
                    time_used_max *= energy_demand / q_released_max
                self.__demand_met = energy_demand
                self.__demand_unmet = 0
    
        # Ensure energy_delivered does not exceed q_released_max
        self.__energy_delivered = min(self.__energy_delivered, q_released_max if 'q_released_max' in locals() else q_released_min)

        new_state_of_charge = self.__state_of_charge + (self.__energy_charged - self.__energy_delivered) / self.__storage_capacity
        new_state_of_charge = np.clip(new_state_of_charge, 0.0, 1.0)
        self.__state_of_charge = new_state_of_charge
    
        # Calculate fan energy
        self.__energy_for_fan: float = 0.0
        power_for_fan: float = 0.0
        if self.__air_flow_type == AirFlowType.FAN_ASSISTED and 'q_released_max' in locals():
            power_for_fan = self.__fan_pwr
            self.__energy_for_fan = self.__convert_to_kwh(power=power_for_fan, time=time_used_max)
    
        # Log the energy charged, fan energy, and total energy delivered
        self.__energy_supply_conn.demand_energy(
            self.__n_units * (self.__energy_charged + self.__energy_instant + self.__energy_for_fan)
        )

        #If detailed results flag is set populate dict with values 
        if self.__output_detailed_results:

            dr_list = [self.__simulation_time.index(), self.__n_units, energy_demand, 
                       self.__energy_delivered, self.__energy_instant,
                       self.__energy_charged, self.__energy_for_fan,
                       self.__state_of_charge, final_soc, time_used_max ]
        
            self.__esh_detailed_results[self.__simulation_time.index()] = dr_list

        # Return total net energy delivered (discharged + instant heat + fan energy)
        return self.__n_units * (self.__energy_delivered + self.__energy_instant)

    def output_esh_results(self):
        ''' Return the data dictionary containing detailed emitter results'''
        return self.__esh_detailed_results 

