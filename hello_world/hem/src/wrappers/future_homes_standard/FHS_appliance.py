import numpy as np
import math
#from core import project, schedule, units
from core.units import hours_per_day, days_per_year, W_per_kW

class FHS_appliance:
        #util unit might be 1, ie per dwelling, or N_occupants
        def __init__(self, 
                     util_unit, 
                     annual_use_per_unit, 
                     op_kWh, 
                     event_duration,
                     standby_W, 
                     gains_frac,
                     flatprofile,
                     seed = 37,
                     duration_std_dev = 0):
            self.seed = seed
            self.duration_std_dev = duration_std_dev
            self.annual_expected_uses = util_unit * annual_use_per_unit
            #deduct durations of uses from standby power consumption (should only have small effect)
            self.annual_expected_demand = (self.annual_expected_uses * op_kWh 
                                          + standby_W * 
                                          (hours_per_day * days_per_year
                                            - self.annual_expected_uses * event_duration)
                                           / W_per_kW)
            self.op_kWh = op_kWh
            self.event_duration = event_duration
            self.standby_W = standby_W
            self.gains_frac = gains_frac
            self.flatprofile = flatprofile
            self.eventlist, self.flatschedule = self.build_sched(flatprofile)
            
            
        def build_sched(self, flatprofile):
            appliance_rng = np.random.default_rng(seed = [self.seed + x for x in range(len(flatprofile) + math.ceil(self.annual_expected_uses))])
            #this logic assumes the profile is normalised to sum to 1 per day    
            events = appliance_rng.poisson([(x * self.annual_expected_uses / days_per_year) for x in flatprofile], len(flatprofile))
            num_events = sum(events)
            eventsizedeviations = appliance_rng.normal(0, self.duration_std_dev, num_events)
            
            for i, dev in enumerate(eventsizedeviations):
                if dev < -1:
                    #seeded random variation in event length cannot be negative.
                    #TODO - switch to Gamma distribution?
                    eventsizedeviations[i] = max(appliance_rng.normal(0, self.duration_std_dev), -1)
            
            norm_events = num_events + sum(eventsizedeviations)
            
            #adjustment in mean event length  to account for random variation
            #adjustment is not applied to standby power,
            #the total demand of which depends on length of events
            #expect sufficient convergence after 10 iterations
            Fappliance = 1
            convergence_threshold = 0.0000001
            for i in range(10):
                Fappliance_test = Fappliance
                Fappliance = (norm_events * self.op_kWh)\
                              / (self.annual_expected_demand - self.standby_W * 
                              (hours_per_day * days_per_year - norm_events * self.event_duration/Fappliance)
                              / W_per_kW)
                if abs(Fappliance - Fappliance_test) < convergence_threshold:
                    #break out of loop if Fappliance does not change by more than convergence threshold
                    break
            
            expected_demand_W_event = self.op_kWh * W_per_kW / self.event_duration
            eventlist = []
            sched = [self.standby_W for x in range(len(flatprofile))]
            
            eventcount = 0
            for step, num_events_in_step in enumerate(events):
                startoffset = appliance_rng.random()
                for e in range(num_events_in_step):
                    demand_W_event = expected_demand_W_event
                    duration = self.event_duration * (1 + eventsizedeviations[eventcount]) / (Fappliance)
                    eventcount+=1
                    #step will depend on timestep of flatprofile, always hourly so no adjustment
                    eventlist.append({"start": step + startoffset,
                                      "duration": duration,
                                      "demand_W": demand_W_event})
                    
                    #build the flattened profile for use with loadshifting
                    integralx = 0.0
                    while integralx < duration:
                        segment = min(math.ceil(startoffset) - startoffset, duration - integralx)
                        sched[(step + math.floor(startoffset + integralx)) % len(sched)] += (demand_W_event - self.standby_W) * segment
                        integralx += segment
                    startoffset += e * duration
            return eventlist, sched
        