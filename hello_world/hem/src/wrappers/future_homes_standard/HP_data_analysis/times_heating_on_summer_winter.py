import pandas as pd
import numpy as np
import os
from datetime import datetime
import sys
from concurrent.futures import ProcessPoolExecutor
import platform

def get_half_hour_period(timestamp):
    """
    Calculates the half-hour period of the day from a timestamp.

    Parameters:
    - timestamp (str): A datetime string in the format "%Y-%m-%d %H:%M:%S".

    Returns:
    - int: Index of the half-hour period within the day (0 to 47).
    """
    timestamp = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
    period = timestamp.hour * 2 + (timestamp.minute >= 30)
    return period

def analyse_file(filepath):
    """
    Processes a CSV file to analyze water heating patterns across summer and winter.

    The function separates data based on predefined summer and winter months,
    calculating the heating on/off status by half-hour period.

    Parameters:
    - filepath (str): Path to the CSV file containing heating data.

    Returns:
    - dict: Contains DataFrames for summer and winter with heating status summaries.
            Returns None if 'Hot_Water_Flow_Temperature' column is missing.
    """
    try:
        with open(filepath, 'r') as file:
            header = file.readline().strip().split(',')
            if 'Hot_Water_Flow_Temperature' not in header:
                print(f"Skipped: {os.path.basename(filepath)} (missing 'Hot_Water_Flow_Temperature')")
                return None

        # Define summer and winter months
        summer_months = [6, 7, 8, 9]  # June, July, August, September
        winter_months = [11, 12, 1, 2]  # November, December, January, February

        data_types = {'Timestamp': str, 'Hot_Water_Flow_Temperature': float}
        data = pd.read_csv(filepath, usecols=['Timestamp', 'Hot_Water_Flow_Temperature'], dtype=data_types)

        data['Timestamp'] = pd.to_datetime(data['Timestamp'])
        data['Month'] = data['Timestamp'].dt.month
        data['Period'] = data['Timestamp'].dt.hour * 2 + (data['Timestamp'].dt.minute >= 30)
        data['Heating'] = np.where(data['Hot_Water_Flow_Temperature'] > 0, 1, 0)

        # Separate data for summer and winter
        summer_data = data[data['Month'].isin(summer_months)]
        winter_data = data[data['Month'].isin(winter_months)]

        # Summarise data for summer
        summer_summary = summer_data.groupby('Period')['Heating'].agg(['sum', 'count'])
        summer_summary['Proportion'] = summer_summary['sum'] / summer_summary['count']
        summer_summary['HeatingOn'] = (summer_summary['Proportion'] > 0.005).astype(int)

        # Summarise data for winter
        winter_summary = winter_data.groupby('Period')['Heating'].agg(['sum', 'count'])
        winter_summary['Proportion'] = winter_summary['sum'] / winter_summary['count']
        winter_summary['HeatingOn'] = (winter_summary['Proportion'] > 0.005).astype(int)

        # Return both summaries in a dictionary
        return {'summer': summer_summary.reset_index(), 'winter': winter_summary.reset_index()}
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
    - tuple: Contains the property ID and a dictionary with the analysis results for summer and winter, or None if skipped.
    """
    result = analyse_file(filepath)
    if result:
        property_id = os.path.basename(filepath).split('=')[1].split('.')[0]
        # Ensure result is a dictionary with 'summer' and 'winter' keys
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
    Main function to handle the analysis of heating patterns for summer and winter seasons 
    from CSV files within a specified directory, saving the results into separate CSV files 
    for each season.

    Parameters:
    - directory_src (str): Directory containing the CSV files.
    - directory_output (str): Directory where the output files will be saved.
    """
    summer_output_file = os.path.join(directory_output, 'summer_heating_times.csv')
    winter_output_file = os.path.join(directory_output, 'winter_heating_times.csv')
    
    files = [os.path.join(directory_src, f) for f in os.listdir(directory_src) if f.endswith('.csv')]
    
    if not files:
        print("No CSV files found in the specified directory.")
        return
    
    # Initialise placeholders for seasonal results
    summer_results = []
    winter_results = []
    
    with ProcessPoolExecutor() as executor:
        futures = [executor.submit(process_file, filepath) for filepath in files]
        for future in futures:
            result = future.result()
            if result:
                # 'result' now includes separate data for summer and winter
                property_id, season_data = result
                summer_results.append(season_data['summer'].assign(PropertyID=property_id))
                winter_results.append(season_data['winter'].assign(PropertyID=property_id))
    
    # Process and save summer results
    if summer_results:
        summer_df = pd.concat(summer_results)
        summer_pivoted = summer_df.pivot_table(index='Period', columns='PropertyID', values='HeatingOn', aggfunc='max', fill_value=0)
        summer_pivoted_with_count = append_heating_count_row(summer_pivoted)
        summer_pivoted_with_count.to_csv(summer_output_file, index_label='Time period')
        print(f"Summer data saved to {summer_output_file}.")
    
    # Process and save winter results
    if winter_results:
        winter_df = pd.concat(winter_results)
        winter_pivoted = winter_df.pivot_table(index='Period', columns='PropertyID', values='HeatingOn', aggfunc='max', fill_value=0)
        winter_pivoted_with_count = append_heating_count_row(winter_pivoted)
        winter_pivoted_with_count.to_csv(winter_output_file, index_label='Time period')
        print(f"Winter data saved to {winter_output_file}.")
    else:
        print("No data to save for summer or winter.")

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