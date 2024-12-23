import csv
import json

csv_file_path = "/Users/ashley.green/Personal/home-energy-model-lambda/demo__results/demo__core__results_summary.csv"
json_file_path = "/Users/ashley.green/Personal/home-energy-model-lambda/demo__results/output.json"


def csv_to_json(csv_file_path, json_file_path):
    data = {
        "Energy Demand Summary": {},
        "Peak Energy Use": {},
        "Energy Supply Summary": {},
        "Delivered Energy Summary": {"Delivered energy by end-use (below) and fuel (right) [kWh/m2]": {}},
        "Hot water system": {},
        "Space heating system": {},
    }

    with open(csv_file_path, mode="r") as csv_file:
        csv_reader = csv.reader(csv_file)
        section = None
        for row in csv_reader:
            if not row or not row[0]:
                continue
            if row[0] == "Energy Demand Summary":
                section = "Energy Demand Summary"
                continue
            elif row[0] == "Energy Supply Summary":
                section = "Energy Supply Summary"
                continue
            elif row[0] in [
                "Delivered Energy Summary",
                "Delivered energy by end-use (below) and fuel (right) [kWh/m2]",
            ]:
                section = "Delivered Energy Summary"
                continue
            elif row[0] == "Hot water system":
                section = "Hot water system"
                continue
            elif row[0] == "Space heating system":
                section = "Space heating system"
                continue

            if section == "Energy Demand Summary":
                data[section][row[0]] = {"unit": row[1], "value": float(row[2])}
            elif section == "Energy Supply Summary":
                if row[0] == "Peak half-hour consumption (electricity)":
                    data["Peak Energy Use"]["Peak half-hour consumption (electricity) [kWh]"] = {
                        "value": float(row[1]),
                        "timestep": int(row[2]),
                        "month": row[3],
                        "day": int(row[4]),
                        "hour of day": float(row[5]),
                    }
                else:
                    data[section][row[0]] = {
                        "unit": row[1],
                        "unmet_demand": None if row[2] == "DIV/0" else float(row[2]),
                        "mains elec": None if row[3] == "DIV/0" else float(row[3]),
                    }
            elif section == "Delivered Energy Summary":
                data[section]["Delivered energy by end-use (below) and fuel (right) [kWh/m2]"][row[0]] = {
                    "total": float(row[1]),
                    "mains elec": float(row[2]),
                }
            elif section == "Hot water system":
                data[section]["hw cylinder"] = {
                    "Overall CoP": row[1],
                    "Daily HW demand ([kWh] 75th percentile)": float(row[2]),
                    "HW cylinder volume (litres)": float(row[3]),
                }
            elif section == "Space heating system":
                data[section]["main"] = {"Overall CoP": float(row[1])}

    with open(json_file_path, mode="w") as json_file:
        json.dump(data, json_file, indent=2)


csv_to_json(csv_file_path, json_file_path)
