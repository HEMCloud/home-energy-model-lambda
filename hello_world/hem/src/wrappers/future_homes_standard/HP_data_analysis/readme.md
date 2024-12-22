# Heat Pump Hot Water Generation Data Analysis Scripts

This repository contains a set of Python scripts developed to analyse heat pump usage data produced by the Electrification of Heat (EoH) Project. Specifically, it is set up for analysing the data set called: Heat Pump Performance Cleansed Data, 2020-2022
(available at [https://beta.ukdataservice.ac.uk/datacatalogue/studies/study?id=9050#!/access-data](https://beta.ukdataservice.ac.uk/datacatalogue/studies/study?id=9050#!/access-data))

The scripts process the data to identify water heating patterns across different days of the week and times of the year, with the aim of identifying the most appropriate hot water heating timer settings to assume in the Future Homes Standard wrapper for homes with heat pumps.

## Scripts Overview

- `times_heating_on_weekday.py`: Analyses water heating on/off times across weekdays for each property. It outputs CSV files with heating patterns for each day of the week and a combined file.
- `times_heating_on_summer_winter.py`: Segregates data into summer and winter seasons, analysing water heating on/off times for these periods. Outputs CSV files for summer and winter heating patterns.
- `heating_pattern.py`: Post-processes the output from the previous scripts to assign a heating pattern description based on the number of off periods per day. 

## Prerequisites

- Python 3
- Pandas library
- Numpy library


## Usage

1. **Input Data**: Input data files are expected in CSV format, with each file representing a single property's heating data, covering periods of about one year at two minute time-steps. Files to be analysed should include 'Timestamp' and 'Hot_Water_Flow_Temperature' columns of data. About a third of the properties in the EoH sample do not appear to have water heating from the heat pump and therefore 'Hot_Water_Flow_Temperature' data is not present. These files are automatically skipped in the analysis - there is no need to remove them from the data set before running this script. 

2. **Running `times_heating_on_weekday.py`**:
    - Navigate to the directory containing the scripts.
    - Run the script specifying the source directory (containing the data files) and the desired output directory:
        **Windows:**  python times_heating_on_weekday.py <source_directory> <output_directory>
        **Linux:**  python3 times_heating_on_weekday.py <source_directory> <output_directory>

3. **Running `times_heating_on_summer_winter.py`**:
    - Use the same approach as above to run this script after `times_heating_on_weekday.py` has completed.

4. **Running `heating_pattern.py`**:
    - This script should be run last, as it requires the output from the first two scripts.
    - Specify the directory containing the output CSV files from the previous scripts:
        **Windows:**  python heating_pattern.py <output_directory>
        **Linux:**  python3 heating_pattern.py <output_directory>
