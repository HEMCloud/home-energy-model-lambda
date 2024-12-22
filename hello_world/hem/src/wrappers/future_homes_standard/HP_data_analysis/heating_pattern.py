import pandas as pd
import sys
import os
import platform

def find_off_periods(heating_data):
    """
    Identifies periods where the heating is off for 6 or more consecutive half-hour segments.

    Parameters:
    - heating_data (pd.Series): Series of heating on/off status for each half-hour segment.

    Returns:
    - list of tuples: Each tuple represents a period with the heating off, including the start time and duration.
    """
    off_periods = []
    current_off_start = None
    current_off_length = 0

    for i in range(len(heating_data)):
        if heating_data.iloc[i] == 0:  # Heating is off
            current_off_length += 1
            if current_off_start is None:
                current_off_start = i
        else:  # Heating is on
            if current_off_length >= 6:  # Check if the off period is significant (6 half-hours or more)
                off_periods.append((current_off_start, current_off_length))
            # Reset counters for the next potential off period
            current_off_start = None
            current_off_length = 0
    
    # Handle case where the last period of the day is a significant off period
    if current_off_length >= 6:
        off_periods.append((current_off_start, current_off_length))
    
    return off_periods

def process_file(filename):
    """
    Processes a single CSV file to analyse heating patterns and save a detailed report.

    Parameters:
    - filename (str): The path to the CSV file to be processed.
    """
    df = pd.read_csv(filename, index_col='Time period')
    df_transposed = df.T  # Transpose DataFrame so dwellings are rows

    # Calculate significant off periods for each dwelling
    df_transposed['Off_Periods'] = df_transposed.apply(find_off_periods, axis=1)

    # Convert the off periods into a readable pattern
    df_transposed['Heating_Pattern'] = df_transposed['Off_Periods'].apply(
        lambda x: '24_hours' if not x else f"{len(x)} off-periods"
    )

    # Provide details for each significant off period
    df_transposed['Off_Details'] = df_transposed['Off_Periods'].apply(
        lambda x: '' if not x else ', '.join([
            f"Off from {start*0.5}h to {(start+length)*0.5}h" for start, length in x
        ])
    )
    
    df_transposed.drop('Off_Periods', axis=1, inplace=True)  # Remove the temporary Off_Periods column

    # Determine the output filename and save the modified DataFrame
    output_filename = filename.replace('water_heating_times', 'heating_off_periods_and_counts')
    df_transposed.to_csv(output_filename, header=True, index=True)
    print(f"Processed and saved: {output_filename}")

if __name__ == "__main__":
    # Command-line usage validation
    if len(sys.argv) != 2:
        os_name = platform.system()
        if os_name == "Windows":
            print("Usage: python script.py <directory>")
        else:
            print("Usage: python3 script.py <directory>")
        sys.exit(1)

    # Process each CSV file in the specified directory
    directory = sys.argv[1]
    filenames = [os.path.join(directory, f'water_heating_times_weekday_{i}.csv') for i in range(7)] + [os.path.join(directory, 'water_heating_times_combined.csv')] + [os.path.join(directory, 'summer_heating_times.csv')] + [os.path.join(directory, 'winter_heating_times.csv')]
    for filename in filenames:
        process_file(filename)
