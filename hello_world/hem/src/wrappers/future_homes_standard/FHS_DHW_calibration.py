import math
import statistics
import sys
import os
import json
import numpy as np
import csv
import copy

this_directory = os.path.dirname(os.path.relpath(__file__))

sys.path.append(os.path.dirname(os.path.abspath(__file__))[:len(str("wrappers/future_homes_standard"))])
#need to run from sap11 venv or these will fail
from wrappers.future_homes_standard.future_homes_standard import calc_TFA, calc_N_occupants, \
HW_event_adjust_allocate, create_hot_water_use_pattern, create_cold_water_feed_temps
from wrappers.future_homes_standard.FHS_HW_events import HW_events_generator

'''
script for calculating calibration DHW volumes for each decile band
'''

decilebandingfile =  os.path.join(this_directory, "decile_banding.csv")
decileeventsfile =  os.path.join(this_directory, "day_of_week_events_by_decile.csv")
decileeventtimesfile =  os.path.join(this_directory, "day_of_week_events_by_decile_event_times.csv")

decile_events = [[] for x in range(10)]
decile_type_events = []

#first calculate flowrates for each decile and event type
with open(decileeventsfile,'r') as eventsfile:
    eventsfilereader = csv.DictReader(eventsfile)
    #organise events by decile and type
    for row in eventsfilereader:
        decile = int(row["decile"]) - 1
        decile_events[decile].append(row)
    for d in decile_events:
        by_type = {}
        for typeday in d:
            typename = typeday["simple_labels2_based_on_900k_sample"]
            #frequency weighted volume + duration 
            #(multiple entries in original csv for each event type and decile, one for each day of the week)
            if typename not in by_type.keys():
                by_type.update({typename:{"event_type": typename,
                                "event_count":float(typeday["event_count"]),
                                "total_volume": float(typeday["event_count"]) * float(typeday["mean_event_volume"]),
                                 "total_duration" :float(typeday["event_count"]) * float(typeday["mean_dur"])}})
            else:
                by_type[typename]["event_count"] += float(typeday["event_count"])
                by_type[typename]["total_volume"] += float(typeday["event_count"]) * float(typeday["mean_event_volume"])
                by_type[typename]["total_duration"] += float(typeday["event_count"]) * float(typeday["mean_dur"])
        for t in by_type.keys():
            #Here we have obtained a (weighted) mean flowrate for each event type, for each decile
            by_type[t]["flow_rate"] = by_type[t]["total_volume"] / by_type[t]["total_duration"]
        
        decile_type_events.append(by_type)








seedrange = range(0,1000)
headers = []
updated_rows = []

with open(decilebandingfile,'r') as bandsfile:
    bandsfilereader = csv.DictReader(bandsfile)
    print("median_daily_vol - calibration__vol - calibration_dhw_variance")
    #TODO this is slow and could be parallelised, but it only needs to be run when changes are made to the
    #HW events generation code - not on every run of the FHS wrapper
    for n, row in enumerate(bandsfilereader):
        testvol = [0 for x in seedrange]
        for seed in seedrange:
            HWtest = HW_events_generator(float(row["median_daily_dhw_vol"]), seed, False)
            HWtestevents = HWtest.build_annual_HW_events()
            for event in HWtestevents:
                if event["type"].find("shower")!=-1:
                    #in the wrapper, volume of HW for showers is calculated with event duration
                    #and the flowrate of the shower in the dwelling
                    #here we use (per decile) weighted average flowrate of showers from the sample data
                    flowrate = decile_type_events[n][event["type"]]["flow_rate"] * 60
                    testvol[seed] += float(event["dur"]) * flowrate / 365
                else:
                    testvol[seed] += float(event["vol"]) / 365
        print(row["median_daily_dhw_vol"] + ",       " + str(statistics.mean(testvol)) + ",  " + str(statistics.variance(testvol)))
        row["calibration_daily_dhw_vol"] = statistics.mean(testvol)
        row["calibration_DHW_variance"] = statistics.variance(testvol)
        updated_rows.append(row)

headers = row.keys()

with open(decilebandingfile,'w', newline = '') as bandsfile:
    bandsfilewriter = csv.DictWriter(bandsfile, fieldnames = headers)
    bandsfilewriter.writeheader()
    for row in updated_rows:
        bandsfilewriter.writerow(row)
