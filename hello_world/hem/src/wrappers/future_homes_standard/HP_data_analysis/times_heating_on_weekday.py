import pandas as pd
import numpy as np
import os
from datetime import datetime
import sys
from concurrent.futures import ProcessPoolExecutor
import platform

def get_half_hour_period(timestamp):
    """
    Convert a timestamp string to a datetime object and calculate the corresponding half-hour segment of the day.

    Parameters:
    - timestamp (str): The timestamp in "%Y-%m-%d %H:%M:%S" format.

    Returns:
    - int: The half-hour segment of the day the timestamp falls into (0-47), allowing for analysis based on time of day.
    """
    timestamp = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
    period = timestamp.hour * 2 + (timestamp.minute >= 30)
    return period

def analyse_file(filepath):
    """
    Analyse a CSV file to determine the water heating pattern based on 'Hot_Water_Flow_Temperature'.

    Skips the file if the necessary column is missing, and groups data by weekday and half-hour period to summarise
    the heating activity.

    Parameters:
    - filepath (str): Path to the CSV file to be analysed.

    Returns:
    - DataFrame or None: A DataFrame summarising the heating on/off status by period and weekday, or None if skipped.
    """
    try:
        with open(filepath, 'r') as file:
            header = file.readline().strip().split(',')
            if 'Hot_Water_Flow_Temperature' not in header:
                print(f"Skipped: {os.path.basename(filepath)} (missing 'Hot_Water_Flow_Temperature')")
                return None
        
        data_types = {'Timestamp': str, 'Hot_Water_Flow_Temperature': float}
        data = pd.read_csv(filepath, usecols=['Timestamp', 'Hot_Water_Flow_Temperature'], dtype=data_types)
        
        data['Timestamp'] = pd.to_datetime(data['Timestamp'])
        data['Weekday'] = data['Timestamp'].dt.dayofweek
        data['Period'] = data['Timestamp'].dt.hour * 2 + (data['Timestamp'].dt.minute >= 30)
        
        data['Heating'] = np.where(data['Hot_Water_Flow_Temperature'] > 0, 1, 0)

        summary = data.groupby(['Weekday', 'Period'])['Heating'].agg(['sum', 'count'])
        summary['Proportion'] = summary['sum'] / summary['count']
        summary['HeatingOn'] = (summary['Proportion'] > 0.005).astype(int)
        summary.reset_index(inplace=True)
        
        return summary
    except Exception as e:
        print(f"Unexpected error processing file {filepath}: {e}")
        return None

def check_file_availability(filepath):
    """
    Check if the specified file is available for writing, indicating it's not locked by another application.

    Parameters:
    - filepath (str): Path to the file to check.

    Returns:
    - bool: True if the file is available, False if locked or unavailable.
    """
    try:
        with open(filepath, 'a'):
            pass
        return True
    except IOError as e:
        print(f"Unable to access {filepath}: {e}")
        return False

def process_file(filepath):
    """
    Wrapper function to process a single CSV file, designed for parallel execution to enhance performance.

    Parameters:
    - filepath (str): Path to the file.

    Returns:
    - tuple: Contains the property ID and the analysis result (DataFrame), or None if skipped.
    """
    result = analyse_file(filepath)
    if result is not None:
        property_id = os.path.basename(filepath).split('=')[1].split('.')[0]
        return (property_id, result)
    else:
        return None

def append_heating_count_row(df):
    """
    Append a row to the DataFrame giving the count of half-hour periods with heating on for each property.

    Parameters:
    - df (DataFrame): The DataFrame to which the count row will be appended.

    Returns:
    - DataFrame: The modified DataFrame with an additional 'HeatingCount' row.
    """
    heating_count = df.sum(axis=0)
    heating_count.name = 'HeatingCount'
    df_with_count = pd.concat([df, pd.DataFrame(heating_count).T], ignore_index=False)
    return df_with_count

def main(directory_src, directory_output):
    """
    Main function to handle the analysis of heating patterns from CSV files within a specified directory,
    saving the results into separate CSV files for each weekday and a combined file.

    Parameters:
    - directory_src (str): Directory containing the CSV files.
    """
    output_file_template = 'water_heating_times_weekday_{weekday}.csv'
    files = [os.path.join(directory_src, f) for f in os.listdir(directory_src) if f.endswith('.csv')]
    
    if not files:
        print("No CSV files found in the specified directory_src.")
        return
    
    combined_output_file = os.path.join(directory_output, 'water_heating_times_combined.csv')
    if not check_file_availability(combined_output_file):
        print(f"Error: The output file '{combined_output_file}' is currently in use. Please close it and try again.")
        return

    all_results = []
    with ProcessPoolExecutor() as executor:
        futures = [executor.submit(process_file, filepath) for filepath in files]
        for future in futures:
            result = future.result()
            if result:
                property_id, df = result
                df['PropertyID'] = property_id
                all_results.append(df)

    if all_results:
        combined_df = pd.concat(all_results)
        combined_pivoted = combined_df.pivot_table(index='Period', columns='PropertyID', values='HeatingOn', aggfunc='max', fill_value=0)
        combined_pivoted_with_count = append_heating_count_row(combined_pivoted)
        combined_pivoted_with_count.to_csv(combined_output_file, index_label='Time period')
        print(f"Combined data saved to {combined_output_file}.")

        for weekday in range(7):
            weekday_df = combined_df[combined_df['Weekday'] == weekday]
            pivoted_df = weekday_df.pivot_table(index='Period', columns='PropertyID', values='HeatingOn', aggfunc='max', fill_value=0)
            pivoted_df_with_count = append_heating_count_row(pivoted_df)
            output_file = os.path.join(directory_output, output_file_template.format(weekday=weekday))
            pivoted_df_with_count.to_csv(output_file, index_label='Time period')
            print(f"Data saved for weekday {weekday} to {output_file}.")
    else:
        print("No data to save.")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        os_name = platform.system()
        if os_name == "Windows":
            print("Usage: python script.py <source_directory> <output_directory>")
        else:
            print("Usage: python3 script.py <source_directory> <output_directory>")
        sys.exit(1)
    
    directory_src = sys.argv[1]
    directory_output = sys.argv[2]
    main(directory_src, directory_output)
