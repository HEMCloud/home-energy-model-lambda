import math
import sys
import os
import json
import numpy as np
import csv
import copy

this_directory = os.path.dirname(os.path.relpath(__file__))

'''
script for adjusting DHW event sizes to account for pipework losses
previously 15%, new estimate is 30%
'''
ploss = 0.30

decilebandingfile =  os.path.join(this_directory, "decile_banding.csv")
decileeventsfile =  os.path.join(this_directory, "day_of_week_events_by_decile.csv")
decileeventtimesfile =  os.path.join(this_directory, "day_of_week_events_by_decile_event_times.csv")

bands_headers = []
bands_updated_rows = []

with open(decilebandingfile,'r') as bandsfile:
    bandsfilereader = csv.DictReader(bandsfile)
    for row in bandsfilereader:
        row["median_daily_dhw_vol"] = (1 - ploss) * float(row["median_daily_dhw_vol"])
        row["min_daily_dhw_vol"] = (1 - ploss) * float(row["min_daily_dhw_vol"])
        row["max_daily_dhw_vol"] = (1 - ploss) * float(row["max_daily_dhw_vol"])
        bands_updated_rows.append(row)

bands_headers = row.keys()
with open(str(ploss) + "pipeworkloss_decile_banding.csv",'w', newline = '') as outfile:
    bandsfilewriter = csv.DictWriter(outfile, fieldnames = bands_headers)
    bandsfilewriter.writeheader()
    for row in bands_updated_rows:
        bandsfilewriter.writerow(row)


seedrange = range(0,1000)
headers = []
updated_rows = []
decile_events = [[] for x in range(10)]
decile_type_events = []

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
    
    
    # for each decile, use the flowrates to get the average time needed to get 15% of the flow
    # this will then be attributed equally between events.
    pipe_times = []
    for n, d in enumerate(decile_type_events):
        total_volume = 0
        total_rate = 0
        for t in d.keys():
            total_volume +=d[t]["total_volume"]
            total_rate += d[t]["event_count"] * d[t]["flow_rate"]
            
        pipe_fill_time = ploss * total_volume/total_rate
        pipe_times.append({"total_volume":total_volume,
                            "total_rate":total_rate,
                            "pipe_fill_time":pipe_fill_time})
        for t in decile_events[n]:
            #perform the correction
            tname = t["simple_labels2_based_on_900k_sample"]
            corrected_volume = float(t["mean_event_volume"]) - d[tname]["flow_rate"] * pipe_fill_time
            corrected_dur = float(t["mean_dur"])-pipe_fill_time
            t["mean_event_volume"] = str(corrected_volume)
            t["mean_dur"] = str(corrected_dur)
            
            #use the same pipe fill time to affect median values (not used by wrapper)
            corrected_volume = float(t["median_event_volume"]) - d[tname]["flow_rate"] * pipe_fill_time
            corrected_dur = float(t["median_dur"])-pipe_fill_time
            t["median_event_volume"] = str(corrected_volume)
            t["median_dur"] = str(corrected_dur)
            
            #reallocate bath big to shower
            if tname == "3_bath_big":
                t["simple_labels2_based_on_900k_sample"] = "2b_shower_big"
            
            if "shower" in t["simple_labels2_based_on_900k_sample"]:
                # The hot water data set only included hot water use via the central hot water system
                # Electric showers are common in the UK, sometimes in addition to a central shower.
                # It is therefore very likely more showers were taken than are recorded in our main dataset.
                # To attempt to correct for this additional shower events (and their equivalent volume)
                # need to be added for use in generating the correct list of water use events.
                # It was assumed that 30% of the homes had an additional electric shower and these were
                # used half as often as showers from the central water heating system (due to lower flow).
                # This would mean that about 15% of showers taken were missing from the data.
                #increase number of showers taken by 15% to reflect this
                t["event_count"] = str(float(t["event_count"]) * 1.15)

headers = row.keys()
with open(str(ploss) + "pipeworkloss_day_of_week_events_by_decile.csv",'w', newline = '') as outfile:
    bandsfilewriter = csv.DictWriter(outfile, fieldnames = headers)
    bandsfilewriter.writeheader()
    for d in decile_events:
        for row in d:
            bandsfilewriter.writerow(row)

