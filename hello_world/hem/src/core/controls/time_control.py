#!/usr/bin/env python3

"""
This module provides objects to model time controls.
"""

# Standard library imports
import sys
from heapq import nsmallest
from math import ceil, floor
from collections import deque
from enum import Enum, auto

# Local imports
import core.units as units


class LogicType(Enum):
    MANUAL = auto()
    AUTOMATIC = auto()
    CELECT = auto()
    HHRSH = auto()

    @classmethod
    def from_string(cls, strval):
        strval = strval.lower()
        if strval == 'manual':
            return cls.MANUAL
        elif strval == 'automatic':
            return cls.AUTOMATIC
        elif strval == 'celect':
            return cls.CELECT
        elif strval == 'hhrsh':
            return cls.HHRSH
        else:
            sys.exit(f'LogicType ({strval}) not valid.')
            # TODO Exit just the current case instead of whole program entirely?

class OnOffTimeControl:
    """ An object to model a time-only control with on/off (not modulating) operation """

    def __init__(self, schedule, simulation_time, start_day, time_series_step):
        """ Construct an OnOffTimeControl object

        Arguments:
        schedule         -- list of boolean values where true means "on" (one entry per hour)
        simulation_time  -- reference to SimulationTime object
        start_day        -- first day of the time series, day of the year, 0 to 365 (single value)
        time_series_step -- timestep of the time series data, in hours
        """
        self.__schedule        = schedule
        self.__simulation_time = simulation_time
        self.__start_day = start_day
        self.__time_series_step = time_series_step

    def is_on(self):
        """ Return true if control will allow system to run """
        return self.__schedule[self.__simulation_time.time_series_idx(self.__start_day, self.__time_series_step)]


class ChargeControl:
    """ An object to model a control that governs electrical charging of a heat storage device 
        that can respond to signals from the grid, for example when carbon intensity is low """

    def __init__(self, 
                 logic_type, 
                 schedule, 
                 simulation_time, 
                 start_day, 
                 time_series_step, 
                 charge_level,
                 temp_charge_cut,
                 temp_charge_cut_delta,
                 min_target_charge_factor,
                 full_charge_temp_diff,
                 extcond,
                 external_sensor,
                 ):
        """ Construct a ChargeControl object

        Arguments:
        logic_type       -- Logic type: manual, automatic, celect, hhrsh
        schedule         -- list of boolean values where true means "on" (one entry per hour)
        simulation_time  -- reference to SimulationTime object
        start_day        -- first day of the time series, day of the year, 0 to 365 (single value)
        time_series_step -- timestep of the time series data, in hours__get_heat_cool_systems_for_zone
        charge_level     -- Proportion of the charge targeted for each day
        temp_charge_cut  -- Room temperature at which, if sensed during a charging hour, the control stops charging
        temp_charge_cut_delta -- array with values for a temperature adjustment which is applied 
                                 to the nominal internal air temperature above which the control stops 
                                 charging the device with heat.
        extcond               -- reference to ExternalConditions object
        external_sensor       -- external weather sensor that acts as a limiting device to prevent storage
                                 heaters from overcharging.
        """
        self.__logic_type      = logic_type
        self.__schedule        = schedule
        self.__simulation_time = simulation_time
        self.__start_day = start_day
        self.__time_series_step = time_series_step
        self.__charge_level = charge_level
        self.__temp_charge_cut = temp_charge_cut
        self.__temp_charge_cut_delta = temp_charge_cut_delta
        self.__min_target_charge_factor = min_target_charge_factor
        self.__full_charge_temp_diff = full_charge_temp_diff
        
        self.__external_conditions = extcond
        self.__external_sensor = external_sensor

        # Check definition is complete for chosen control logic
        logic_type = LogicType.from_string(self.__logic_type)
        if logic_type == LogicType.MANUAL:
            pass
        elif logic_type == LogicType.AUTOMATIC:
            if self.__temp_charge_cut is None:
                sys.exit("automatic ChargeControl definition is missing input parameters.")
                
        elif logic_type == LogicType.CELECT:
            if self.__temp_charge_cut is None:
                sys.exit("celect ChargeControl definition is missing input parameters.")
                
        elif logic_type == LogicType.HHRSH:
            if self.__temp_charge_cut is None:
                sys.exit("hhrsh ChargeControl definition is missing input parameters.")
                
            self.__steps_day = int(units.hours_per_day / self.__simulation_time.timestep())
            self.__demand   = deque([None] * self.__steps_day, maxlen=self.__steps_day)
            self.__past_ext_temp     = deque([None] * self.__steps_day, maxlen=self.__steps_day)
            self.__future_ext_temp     = deque([0.0] * self.__steps_day, maxlen=self.__steps_day)
            for i in range(self.__steps_day):
                self.__future_ext_temp.append(self.__external_conditions.air_temp(i))
            self.__energy_to_store = 0.0

            # TODO: Consider adding solar data for HHRSH logic in addition to heating degree hours.
        else:
            sys.exit("Invalid logic type for charge control.")

    def logic_type(self):
        """ Return the logic type for this control """
        return self.__logic_type

    def is_on(self):
        """ Return true if control will allow system to run """
        return self.__schedule[self.__simulation_time.time_series_idx(self.__start_day, self.__time_series_step)]

    def target_charge(self, temp_air=None):
        """ Return the charge level value from the list given in inputs; one value per day """

        # Calculate target charge nominal when unit is on
        if self.is_on():
            target_charge_nominal = self.__charge_level[
                self.__simulation_time.time_series_idx_days(self.__start_day, self.__time_series_step)
            ]
        else:
            # If unit is off send 0.0 for target charge
            target_charge_nominal = 0.0
        
        logic_type = LogicType.from_string(self.__logic_type)
        
        if logic_type == LogicType.MANUAL:
            target_charge = target_charge_nominal
        else:
            """ automatic, celect and hhrsh control include temperature charge cut logic """
            temp_charge_cut = self.temp_charge_cut_corr()
        
            if temp_air is not None and \
               temp_air >= temp_charge_cut:
                # Control logic cut when temp_air is over temp_charge cut
                target_charge_nominal = 0.0
        
        if logic_type == LogicType.AUTOMATIC:
            # Automatic charge control can be achieved using internal thermostat(s) to
            # control the extent of charging of the heaters. All or nothing approach 
            
            # Controls can also be supplemented by an external weather sensor,
            # which tends to act as a limiting device to prevent the storage heaters from overcharging.
            if self.__external_sensor is not None:
                limit = self.__get_limit_factor(self.__external_conditions.air_temp())
                target_charge = target_charge_nominal * limit
            else:
                target_charge = target_charge_nominal

        elif logic_type == LogicType.CELECT:
            # A CELECT-type controller has electronic sensors throughout the dwelling linked 
            # to a central control device. It monitors the individual room sensors and optimises 
            # the charging of all the storage heaters individually (and may select direct acting 
            # heaters in preference to storage heaters).
        
            # Initial CELECT-type logic based on AUTOMATIC until additional literature for  
            # CELECT types is identified
            
            # Controls can also be supplemented by an external weather sensor,
            # which tends to act as a limiting device to prevent the storage heaters from overcharging.
            if self.__external_sensor is not None:
                limit = self.__get_limit_factor(self.__external_conditions.air_temp())
                target_charge = target_charge_nominal * limit
            else:
                target_charge = target_charge_nominal
        
        elif logic_type == LogicType.HHRSH:
            # A ‘high heat retention storage heater’ is one with heat retention not less 
            # than 45% measured according to BS EN 60531. It incorporates a timer, electronic 
            # room thermostat and fan to control the heat output. It is also able to estimate 
            # the next day’s heating demand based on external temperature, room temperature 
            # settings and heat demand periods. 

            target_charge = 1 if target_charge_nominal else 0

        return target_charge
    
    def energy_to_store(self, energy_demand, base_temp):
        """
        Returns energy estimated to be stored for HHRSH in each timestep
        """
        self.__demand.append(energy_demand)
        self.__future_ext_temp.append(self.__external_conditions.air_temp(self.__steps_day))
        self.__past_ext_temp.append(self.__external_conditions.air_temp())

        future_hdh = self.__calculate_heating_degree_hours(self.__future_ext_temp, base_temp)
        past_hdh = self.__calculate_heating_degree_hours(self.__past_ext_temp, base_temp)
        
        if future_hdh is None or past_hdh is None:
            self.__energy_to_store = None
        elif past_hdh == 0:
            self.__energy_to_store = 0 # Can't calculate tomorrow's demand if no past_hdh, so assume zero to store
        else:
            self.__energy_to_store = future_hdh / past_hdh * sum(self.__demand)
        
        # No energy can be added when control is off
        if not self.is_on():
            self.__energy_to_store = 0.0

        return self.__energy_to_store

    def temp_charge_cut_corr(self):
        """
        Correct nominal/json temp_charge_cut with monthly table 
        Arguments

        returns -- temp_charge_cut (corrected)
        """
        if self.__temp_charge_cut_delta is not None:
            temp_charge_cut_delta = self.__temp_charge_cut_delta[self.__simulation_time.time_series_idx(self.__start_day, self.__time_series_step)]
        else:
            temp_charge_cut_delta = 0.0
            
        temp_charge_cut = self.__temp_charge_cut + temp_charge_cut_delta

        return temp_charge_cut

    def __calculate_heating_degree_hours(self, temps, base_temp):
        total_hdh = 0
        for temp in temps:
            if temp is None:
                return None

            hdh = max(base_temp - temp, 0)
            total_hdh += hdh
        return total_hdh

    def __get_limit_factor(self, external_temp):
        correlation = self.__external_sensor["correlation"]

        # Edge cases: If temperature is below the first point or above the last point
        if external_temp <= correlation[0]["temperature"]:
            return correlation[0]["max_charge"]
        elif external_temp >= correlation[-1]["temperature"]:
            return correlation[-1]["max_charge"]

        # Linear interpolation
        for i in range(1, len(correlation)):
            temp_1 = correlation[i - 1]["temperature"]
            max_charge_1 = correlation[i - 1]["max_charge"]
            temp_2 = correlation[i]["temperature"]
            max_charge_2 = correlation[i]["max_charge"]

            if temp_1 <= external_temp <= temp_2 and \
               temp_1 != temp_2:
                # Perform linear interpolation
                slope = (max_charge_2 - max_charge_1) / (temp_2 - temp_1)
                limit = max_charge_1 + slope * (external_temp - temp_1)
                return limit

        # Controlled system exit if something goes wrong
        sys.exit("Calculation of limiting factor linked to external sensor for automatic control failed.")
    
class OnOffCostMinimisingTimeControl:

    def __init__(
            self,
            schedule,
            simulation_time,
            start_day,
            time_series_step,
            time_on_daily,
            ):
        """ Construct an OnOffCostMinimisingControl object

        Arguments:
        schedule         -- list of cost values (one entry per time_series_step)
        simulation_time  -- reference to SimulationTime object
        start_day        -- first day of the time series, day of the year, 0 to 365 (single value)
        time_series_step -- timestep of the time series data, in hours
        time_on_daily    -- number of "on" hours to be set per day
        """
        self.__simulation_time = simulation_time
        self.__start_day = start_day
        self.__time_series_step = time_series_step
        self.__time_on_daily = time_on_daily

        timesteps_per_day = int(units.hours_per_day / time_series_step)
        timesteps_on_daily = int(time_on_daily / time_series_step)
        time_series_len_days = ceil(len(schedule) * time_series_step / units.hours_per_day)

        # For each day of schedule, find the specified number of hours with the lowest cost
        self.__schedule = []
        for day in range(0, time_series_len_days):
            # Get part of the schedule for current day
            schedule_day_start = day * timesteps_per_day
            schedule_day_end = schedule_day_start + timesteps_per_day
            schedule_day = schedule[schedule_day_start : schedule_day_end]

            # Find required number of timesteps with lowest costs
            schedule_day_cost_lowest = sorted(set(nsmallest(timesteps_on_daily, schedule_day)))

            # Initialise boolean schedule for day
            schedule_onoff_day = [False] * timesteps_per_day

            # Set lowest cost times to True, then next lowest etc. until required
            # number of timesteps have been set to True
            assert len(schedule_onoff_day) == len(schedule_day)
            timesteps_to_be_allocated = timesteps_on_daily
            for cost in schedule_day_cost_lowest:
                for idx, entry in enumerate(schedule_day):
                    if timesteps_to_be_allocated < 1:
                        break
                    if entry == cost:
                        schedule_onoff_day[idx] = True
                        timesteps_to_be_allocated -= 1

            # Add day of schedule to overall
            self.__schedule.extend(schedule_onoff_day)

    def is_on(self):
        """ Return true if control will allow system to run """
        return self.__schedule[self.__simulation_time.time_series_idx(self.__start_day, self.__time_series_step)]


class SetpointTimeControl:
    """ An object to model a control with a setpoint which varies per timestep """

    def __init__(
            self,
            schedule,
            simulation_time,
            start_day,
            time_series_step,
            setpoint_min=None,
            setpoint_max=None,
            default_to_max=None,
            duration_advanced_start=0.0,
            ):
        """ Construct a SetpointTimeControl object

        Arguments:
        schedule         -- list of float values (one entry per hour)
        simulation_time  -- reference to SimulationTime object
        start_day        -- first day of the time series, day of the year, 0 to 365 (single value)
        time_series_step -- timestep of the time series data, in hours
        setpoint_min -- min setpoint allowed
        setpoint_max -- max setpoint allowed
        default_to_max -- if both min and max limits are set but setpoint isn't,
                          whether to default to min (False) or max (True) 
        duration_advanced_start -- how long before heating period the system
                                   should switch on, in hours
        """
        self.__schedule        = schedule
        self.__simulation_time = simulation_time
        self.__start_day = start_day
        self.__time_series_step = time_series_step
        self.__setpoint_min = setpoint_min
        self.__setpoint_max = setpoint_max
        self.__default_to_max = default_to_max
        self.__timesteps_advstart \
            = round(duration_advanced_start / self.__simulation_time.timestep())

    def in_required_period(self):
        """ Return true if current time is inside specified time for heating/cooling
        
        (not including timesteps where system is only on due to min or max
        setpoint or advanced start)
        """
        schedule_idx = self.__simulation_time.time_series_idx(
            self.__start_day,
            self.__time_series_step,
            )
        setpnt = self.__schedule[schedule_idx]
        return (setpnt is not None)

    def is_on(self):
        """ Return true if control will allow system to run """
        schedule_idx = self.__simulation_time.time_series_idx(
            self.__start_day,
            self.__time_series_step,
            )
        setpnt = self.__schedule[schedule_idx]

        if setpnt is None:
            # Look ahead for duration of warmup period: system is on if setpoint
            # is not None heating period if found
            for timesteps_ahead in range(1, 1 + self.__timesteps_advstart):
                if len(self.__schedule) <= schedule_idx + timesteps_ahead:
                    # Stop looking ahead if we have reached the end of the schedule
                    break
                if self.__schedule[schedule_idx + timesteps_ahead] is not None:
                    # If heating period starts within duration of warmup period
                    # from now, system is on
                    return True

        # For this type of control, system is always on if min or max are set
        if setpnt is None and self.__setpoint_min is None and self.__setpoint_max is None:
            return False
        else:
            return True

    def setpnt(self):
        """ Return setpoint for the current timestep """
        schedule_idx = self.__simulation_time.time_series_idx(
            self.__start_day,
            self.__time_series_step,
            )
        setpnt = self.__schedule[schedule_idx]

        if setpnt is None:
            # Look ahead for duration of warmup period and use setpoint from
            # start of heating period if found
            for timesteps_ahead in range(1, 1 + self.__timesteps_advstart):
                if len(self.__schedule) <= schedule_idx + timesteps_ahead:
                    # Stop looking ahead if we have reached the end of the schedule
                    break
                if self.__schedule[schedule_idx + timesteps_ahead] is not None:
                    # If heating period starts within duration of warmup period
                    # from now, use setpoint from start of heating period
                    setpnt = self.__schedule[schedule_idx + timesteps_ahead]
                    break

        if setpnt is None:
            # If no setpoint value is in the schedule, use the min/max if set
            if self.__setpoint_max is None and self.__setpoint_min is None:
                pass # Use setpnt None
            elif self.__setpoint_max is not None and self.__setpoint_min is None:
                setpnt = self.__setpoint_max
            elif self.__setpoint_min is not None and self.__setpoint_max is None:
                setpnt = self.__setpoint_min
            else: # min and max both set
                if self.__default_to_max is None:
                    sys.exit('ERROR: Setpoint not set but min and max both set, '
                             'and which to use by default not specified')
                elif self.__default_to_max:
                    setpnt = self.__setpoint_max
                else:
                    setpnt = self.__setpoint_min
        else:
            # If there is a maximum limit, take the lower of this and the schedule value
            if self.__setpoint_max is not None:
                setpnt = min(self.__setpoint_max, setpnt)
            # If there is a minimum limit, take the higher of this and the schedule value
            if self.__setpoint_min is not None:
                setpnt = max(self.__setpoint_min, setpnt)
        return setpnt
    
class SmartApplianceControl:
    """ An object for managing loadshifting appliances"""

    def __init__(self,
                 power_timeseries,
                 weight_timeseries,
                 timeseries_step,
                 simulation_time,
                 non_appliance_demand_24hr,
                 battery_24hr,
                 energysupplies,
                 appliances):
        """ Construct a SmartApplianceControl object

        Arguments:
        power_timeseries         - dictionary of lists containing expected power for appliances
                                     for each energy supply, for the entire length of the simulation
        weight_timeseries         - dictionary of lists containing demand weight for each
                                     energy supply, for the entire length of the simulation
        timeseries_step           - timestep of weight and demand timeseries 
                                    (not necessarily equal to simulation_time.timestep())
        simulation_time           - reference to a SimulationTime object
        non_appliance_demand_24hr - dictionary of lists containing 24 hour buffers of
                                     demand per end user for each energy supply
        battery_24hr              - dictionary of lists containing 24 hour buffers of 
                                     battery state of charge for each energy supply
        energysupplies            - dictionary of energysupply objects in the simulation
        appliances                - dictionary of appliancegains data, used to obtain names of appliances
        """
        
        self.__appliances = appliances
        self.__energy_supplies = {key:data for (key, data) in energysupplies.items() if key in power_timeseries} 
        self.__batteries = {}
        for name, supply in self.__energy_supplies.items():
            if supply.has_battery():
                #keep track of battery charge if an energysupply has a battery
                self.__batteries[name] = {
                    "battery_state_of_charge":battery_24hr["battery_state_of_charge"][name]
                }
        for energysupply in self.__energy_supplies.keys():
            if len(power_timeseries[energysupply]) != len(weight_timeseries[energysupply]):
                sys.exit('ERROR: loadshifting weight and power timeseries not equal in length')
            if len(power_timeseries[energysupply]) * timeseries_step <\
                simulation_time.total_steps() * simulation_time.timestep():
                sys.exit('ERROR: loadshifting weight+power timeseries shorter than simulation length')
            
        
        #timeseries objects
        self.__ts_power = power_timeseries
        self.__ts_weight = weight_timeseries
        self.__ts_step = timeseries_step
        self.__simulation_time = simulation_time
        #timeseries may have time resolution different to that of the HEM calculation
        self.__ts_step_ratio = simulation_time.timestep() / timeseries_step
        
        #buffer objects
        self.__non_appliance_demand_24hr = non_appliance_demand_24hr
        self.__buffer_length = len(list(non_appliance_demand_24hr.values())[0])
        
    def ts_step(self,t_idx):
        #converts index of simulation time to index of demand or weight timeseries
        return floor(self.__ts_step_ratio * t_idx)
    
    def get_ts_demand(self, energysupply, t_idx):
        #returns average energy demand from powerts over the current simulation timestep
        return self.__ts_power[energysupply][self.ts_step(t_idx)] / units.W_per_kW * self.__simulation_time.timestep()
    
    def get_demand(self,t_idx,energysupply):
        #returns the sum of the anticipated appliance demand,
        #the demand buffer, and the (negative) battery charge
        
        idx_24hr = t_idx % self.__buffer_length
        demand = self.get_ts_demand(energysupply, t_idx)\
                + self.__non_appliance_demand_24hr[energysupply][idx_24hr]
        
        if energysupply in self.__batteries:
            return demand\
                - self.__batteries[energysupply]["battery_state_of_charge"][idx_24hr]
        return demand
    
    def add_appliance_demand(self,t_idx, demand,energysupply):
        #convert demand from appliance usage event to average power over the demand series timestep
        #and add it to the series 
        self.__ts_power[energysupply][self.ts_step(t_idx)] += demand * units.W_per_kW / self.__ts_step
        
        #update our prediction of battery charge over the next 24 hours
        if energysupply in self.__batteries:
            #if we expect there will be charge in the battery when this demand occurs, assume
            #the battery supplies as much of it as possible
            idx_24hr = t_idx % self.__buffer_length
            max_capacity = self.__energy_supplies[energysupply].get_battery_max_capacity()
            #max_discharge is a linear function however states it requires input as a 0-1 proportion of total,
            #so divide and then multiply by max capacity in case of future changes
            maxdischarge = - self.__energy_supplies[energysupply].\
                get_battery_max_discharge(self.__batteries[energysupply]["battery_state_of_charge"][idx_24hr]\
                                          / max_capacity) * max_capacity
            #the maths here follows charge_discharge_battery() in ElectricBattery
            dischargeeff = self.__energy_supplies[energysupply].get_battery_discharge_efficiency()
            charge_utilised = min(
                max(self.__batteries[energysupply]["battery_state_of_charge"][idx_24hr],0),
                min(maxdischarge,demand) * dischargeeff
            )
            #now subtract charge_utilised from the charge stored at every step in the buffer of battery charge.
            #if the battery is already expected to empty at a later time, this will result in the buffer
            #reporting negative charge stored in the battery during the times it is expected to be empty
            #and appliance preferentially not being used at those times
            self.__batteries[energysupply]["battery_state_of_charge"] = [
                charge - charge_utilised for charge in self.__batteries[energysupply]["battery_state_of_charge"]
            ]

    def update_demand_buffer(self,t_idx):
        idx_24hr = t_idx % self.__buffer_length
        for name, supply in self.__energy_supplies.items():
            #total up results for this energy supply but exclude demand from appliances
            #(the demand for which we already know accurately in advance
            #energy generated is negative and if the generation exceeds demand for a given timestep, the total
            #will be negative, and appliance usage events will preferentially be scheduled at that time
            #TODO - it is possible to apply a weighting factor to energy generated in the dwelling here
            #(users for whom demand is negative)
            #to make it more or less preferable to use it immediately or export/charge battery
            self.__non_appliance_demand_24hr[name][idx_24hr]\
                = sum(user for (name,user) in supply.results_by_end_user_single_step(t_idx).items() if name not in self.__appliances.keys())
            
            if supply.has_battery():
                #TODO - communicate with charge control
                charge = supply.get_battery_available_charge()
                chargeeff = supply.get_battery_charge_efficiency()
                self.__batteries[name]["battery_state_of_charge"][idx_24hr] = charge * chargeeff
        
    def get_weight(self,t_idx, energysupply):
        return self.__ts_weight[energysupply][self.ts_step(t_idx)]


class SupportedOperation(Enum):
    AND = auto()
    OR = auto()
    XOR = auto()
    NOT = auto() 
    MAX = auto()
    MIN = auto()
    MEAN = auto()   

    @classmethod
    def from_string(cls, strval):
        if strval in cls.__members__:
            return cls[strval]
        else:
            raise ValueError(f"Operation code ({strval}) not valid in CombinationTimeControl")

class CombinationTimeControl:
    """ An object to model a control with nested combinations of other control types """

    def __init__(self, combination, controls, simulation_time, start_day, time_series_step):
        """ Construct a CombinationTimeControl object

        Arguments:
        combination      -- dictionary defining the combination of controls and operations
        simulation_time  -- reference to SimulationTime object
        start_day        -- first day of the time series, day of the year, 0 to 365 (single value)
        time_series_step -- timestep of the time series data, in hours
        controls         -- dictionary defining name and instances of control objects
        """
        self.__combination = combination
        self.__controls = controls
        self.__simulation_time = simulation_time
        self.__start_day = start_day
        self.__time_series_step = time_series_step

    
    def __evaluate_boolean_operation_is_on(self, operation, control_results):
        """ Evaluate a Boolean operation given the operation type and results """
        if operation == SupportedOperation.AND:
            return all(control_results)
        if operation == SupportedOperation.OR:
            return any(control_results)
        elif operation == SupportedOperation.XOR:
            return control_results.count(True) % 2 == 1
        elif operation == SupportedOperation.NOT:
            if len(control_results) != 1:
                raise ValueError("NOT operation requires exactly one operand.")
            return not control_results[0]
        else:
            raise ValueError(f"Unsupported Boolean operation: {operation}")

    def __evaluate_control_is_on(self, control_name):
        """ Evaluate a single control """
        control = self.__controls[control_name]
        return control.is_on()

    def __evaluate_combination_is_on(self, combination_name):
        """ Evaluate a combination of controls """
        combination = self.__combination[combination_name]
        operation = SupportedOperation.from_string(combination['operation'])
        controls = combination['controls']

        results = []
        for control in controls:
            if control in self.__combination:
                # If the control is a combination, recursively evaluate it
                # Infinite recursion has been avoided by adding checks during control onbject creation
                result = self.__evaluate_combination_is_on(control)
            else:
                # Otherwise, evaluate a single control
                result = self.__evaluate_control_is_on(control)
            results.append(result)
            
        if operation in {SupportedOperation.AND, SupportedOperation.OR, SupportedOperation.XOR, SupportedOperation.NOT}:
            return self.__evaluate_boolean_operation_is_on(operation, results)
        # If the operation is MAX,MIN or MEAN then AND is performed
        elif operation in {SupportedOperation.MAX, SupportedOperation.MIN, SupportedOperation.MEAN}:
            return all(results)
        else:
            raise ValueError(f"Unsupported operation in combination: {operation}")

    
    def __evaluate_control_in_req_period(self, control_name):
        """ Evaluate a single control """

        control = self.__controls[control_name]
        if isinstance(control, OnOffTimeControl) or \
            isinstance(control, OnOffCostMinimisingTimeControl) or \
            isinstance(control, ChargeControl):
            return control.is_on()
        elif isinstance(control, SetpointTimeControl):
            return control.in_required_period()
        else:
            raise ValueError(f"Unsupported control type for {control_name}")    
    
    def __evaluate_combination_in_req_period(self, combination_name):
        """This function processes a combination of control elements, 
        applying boolean logic (AND, OR, XOR, etc.) to their evaluation results. 
        It checks the type of controls , validates allowed     
        combinations and returns the evaluation result based on the specified operation. 
        Unsupported combinations or operations raise an error. """
        combination = self.__combination[combination_name]
        operation = SupportedOperation.from_string(combination['operation'])
        controls = combination['controls']
    
        results = []
        has_onoff = False
        has_setpoint = False
    
        for control in controls:
            if control in self.__combination:
                result = self.__evaluate_combination_in_req_period(control)
            else:
                # Track the types of controls for logic enforcement
                control_instance = self.__controls[control]
                if isinstance(control_instance, OnOffTimeControl) or \
                    isinstance(control_instance, OnOffCostMinimisingTimeControl) or \
                    isinstance(control_instance, ChargeControl):
                    has_onoff = True
                if isinstance(control_instance, SetpointTimeControl):
                    has_setpoint = True
                result = self.__evaluate_control_in_req_period(control)

            results.append(result)
        # Ensure valid combinations
        if has_onoff and has_setpoint:
            if operation != SupportedOperation.AND:
                sys.exit("OnOff + Setpoint combination in_req_perdioc() only supports the AND operation")
            # Combine results using AND for OnOff + Setpoint combination
            return all(results)
    
        elif has_onoff and not has_setpoint:
            sys.exit("OnOff + OnOff combination is not applicable for in_req_period() operation")
    
        elif has_setpoint and not has_onoff:
            # Apply operations for Setpoint + Setpoint combinations based on the operation
            if operation == SupportedOperation.AND:
                return all(results)
            elif operation == SupportedOperation.OR:
                return any(results)
            elif operation == SupportedOperation.XOR:
                return sum(results) == 1  # XOR is true if exactly one result is True
            elif operation == SupportedOperation.MAX:
                return max(results)
            elif operation == SupportedOperation.MIN:
                return min(results)
            elif operation == SupportedOperation.MEAN:
                return sum(results) / len(results) > 0.5  # Mean evaluates to True if average > 0.5
            else:
                raise ValueError(f"Unsupported operation: {operation}")
    
    def __evaluate_control_setpnt(self, control_name):
        """ Evaluate a single control """
        control = self.__controls[control_name]
        if isinstance(control, OnOffTimeControl) or \
            isinstance(control, OnOffCostMinimisingTimeControl)  or \
            isinstance(control, ChargeControl):
            return control.is_on()
        elif isinstance(control, SetpointTimeControl):
            return control.setpnt()
        else:
             raise ValueError(f"Unsupported control type for {control_name}")    
    
    def __evaluate_combination_setpnt(self, combination_name):
        """ Evaluate a combination of controls """
        combination = self.__combination[combination_name]
        operation = SupportedOperation.from_string(combination['operation'])
        controls = combination['controls']
    
        results = []
        has_onoff = False
        has_setpoint = False
    
        for control in controls:
            if control in self.__combination:
                result = self.__evaluate_combination_setpnt(control)
            else:
                # Track the types of controls for logic enforcement
                control_instance = self.__controls[control]
                if isinstance(control_instance, OnOffTimeControl) or \
                    isinstance(control_instance, OnOffCostMinimisingTimeControl)  or \
                    isinstance(control_instance, ChargeControl):
                    has_onoff = True
                if isinstance(control_instance, SetpointTimeControl):
                    has_setpoint = True
                result = self.__evaluate_control_setpnt(control)
            results.append(result)
        #Check a setpnt result is available from previous combination
        if any(isinstance(result, (int, float)) for result in results):
            has_setpoint = True
        
        # Ensure valid combinations
        if has_onoff and has_setpoint:
            if operation == SupportedOperation.AND:  
                setpnt_value = [item for item in results if isinstance(item, float)]
                bool_value =  [item for item in results if isinstance(item, bool)]
                if len(setpnt_value) > 1:
                    raise ValueError("Only one numerical value allowed in AND operation") 
                if all(bool_value):
                    return setpnt_value[0]
                else:
                    return None
            else:
                sys.exit("OnOff + Setpoint combination setpnt() only supports the AND operation")
    
        elif has_onoff and not has_setpoint:
            sys.exit("OnOff + OnOff combination is not applicable for setpnt() operation")
    
        elif has_setpoint and not has_onoff:
            # Apply operations for Setpoint + Setpoint combinations based on the operation
            if operation == SupportedOperation.MAX:
                return max(results)
            elif operation == SupportedOperation.MIN:
                return min(results)
            elif operation == SupportedOperation.MEAN:
                return sum(results) / len(results) > 0.5  # Mean evaluates to True if average > 0.5
            else:
                raise ValueError(f"Unsupported operation: {operation}") 
            
    def __evaluate_control_target_charge(self, control_name, temp_air):
        control = self.__controls[control_name]
        if isinstance(control, ChargeControl):
            return control.target_charge(temp_air)
        else: 
            return None
        
    def __evaluate_combination_target_charge(self, combination_name, temp_air):
        "Evaluate the combination for target charge"
        combination = self.__combination[combination_name]
        controls = combination['controls']        
        results = []
       
        for control in controls:
            if control in self.__combination:
                # If the control is a combination, recursively evaluate it
                # Infinite recursion has been avoided by adding checks during control onbject creation
                result = self.__evaluate_combination_target_charge(control)
            else:
                result = self.__evaluate_control_target_charge(control, temp_air)
            results.append(result)
        
        # Check if the combination has a maximum one one ChargeControl object to return target_charge
        if all(item is None for item in results):
            raise ValueError("Requires atleast one ChargeControl object in combination to determine target charge")
        elif sum(item is not None for item in results) > 1:
            raise ValueError("CombinationControl cannot have more than one ChargeControl object to determine target charge")
        else:
            return [item for item in results if item is not None][0]
    
    def is_on(self):
        """ Evaluate if the overall control is active """
        return self.__evaluate_combination_is_on('main')
    
    def in_required_period(self):
        """ Evaluate if the overall control is active """
        return self.__evaluate_combination_in_req_period('main')
    
    def setpnt(self):
        """ Return the setpoint for the current timestep """
        return self.__evaluate_combination_setpnt('main')
        
    def target_charge(self,temp_air=None):
        return self.__evaluate_combination_target_charge('main', temp_air)
