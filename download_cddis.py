import earthaccess
import os
import pandas as pd
import requests
import sys
import threading

from datetime import datetime
from concurrent.futures import ThreadPoolExecutor


download_counter = 0 # This tracks the number of files that has been downloaded. 
counter_lock = threading.Lock()

def get_stations_from_md5(date, const_url):
    print(f'Getting station names for date {date}')
    year = date.year
    doy = date.timetuple().tm_yday
    md5_url = f"{const_url}/{year}/{doy}/MD5SUMS"
    
    r = requests.get(md5_url)
    if r.status_code != 200:
        print(f"Could not retrieve md5_check.txt for {date}")
        return []
    
    lines = r.text.strip().split('\n')
    stations = set()
    for line in lines:
        parts = line.strip().split()
        if len(parts) == 2:
            filename = parts[1]
            if filename.endswith('.csv'):
                station = filename.split('_')[0]
                stations.add(station)
    return list(stations)



def get_last_date_of_download(last_date_file_path: str) -> str:
    """Returns the last date that data was downloaded. This should be found in your 
    last_date_file_path file. 

    Keyword arguments:
    last_date_file_path -- this is the file that stores the last date that was downloaded. 
                in this format 'last_file_download=2025-04-17'.
    """
    last_date_of_download = None
    with open(last_date_file_path, 'r') as f:
        for x in f:
            if 'last_file_download' in x:
                last_date_of_download = x.split('=', 1)[1].strip()
                break
    if not last_date_of_download:
        raise ValueError(f'Date not present in file path {last_date_file_path}')
    return datetime.strptime(last_date_of_download, "%Y-%m-%d").date()


def check_for_netrc():
    """Checks that the user has the needed .netrc file in thier parent directory."""
    home_dir = os.path.expanduser('~')

    if os.name == 'nt':  # Checking if the machine is windows. 
        netrc_path = os.path.join(home_dir, '_netrc')
    else: 
        netrc_path = os.path.join(home_dir, '.netrc')

    if os.path.exists(netrc_path):
        print(f".netrc file found at {netrc_path}")
        return True
    else:
        print('.netrc file not found. Earthdata authentication will fail.')
        print('Please see directions on how to create a .netrc file.')
        return False
    

def download_station_data(
        station,
        date,
        const_url,
        download_dir
    ):
    """
    Keyword arguments:
    station -- this is the station that you wish to download from. Please see station names variable for more info.
    date -- date that you wish to download.
    const_url -- this is the part of the url that is unchanging. 
    download_dir -- this is the directory that the file will be downloaded to.
    """
   
    formatted_date = date.strftime('%y%m%d') # Formatting the date into yearmonthday as is required for the url.
    year_date_url = f'{date.year}/{date.dayofyear}/'
    csv_file = f'{station}_{formatted_date}.csv'

    url = const_url + year_date_url + csv_file # Final combined url. 

    filename = os.path.join(download_dir, csv_file) # This is the filepath for the data that we are downloading. 

    if os.path.exists(filename): # Ensuring that the file doesn't already exist. If it does, no need to download again. 
        print(f"File already exists, skipping: {filename}")
        return 

    with requests.Session() as s: 
        r = s.get(url) 
        print(filename, r.status_code)
        
        if r.status_code != 404: # Ensuring that we don't get an error.      
            os.makedirs(download_dir, exist_ok=True) # Creating the parent directory. 

            # Opens a local file of same name as remote file for writing to
            with open(filename, 'wb') as fd:
                for chunk in r.iter_content(chunk_size=1000):
                    fd.write(chunk)
        
            with counter_lock:
                global download_counter
                download_counter += 1


def get_new_data(memory_file: str='memory.txt'):
    """Downloads data for all days between current day and last download day.

    Keyword arguments:
    memory_file -- this is the file that stores the last date that was downloaded. 
                in this format 'last_file_download=2025-04-17'.
    """
    current_date = datetime.now().date()
    
    last_date_of_download = get_last_date_of_download(last_date_file_path=memory_file)
    
    day_dif = (current_date - last_date_of_download).days # Getting the number of days between last download and today.
    if day_dif <= 0: # Ensuring that the difference in days in not negative. 
        raise ValueError(f'Error; there is an issue with your dates. {current_date} is <= {last_date_of_download}.')

    dates_to_download_list = pd.date_range(
        start=last_date_of_download + pd.Timedelta(days=1), 
        periods=day_dif
    ) # Obtaining a list of days that need to be downloaded. This list includes the dates between last download and today. 
    
    const_url = 'https://cddis.nasa.gov/archive/gnss/products/realtime/jpl_ionosphere/' # Url portion that is unchanging.
    total_expected_downloads = 0 # Variable providing the total number of files expected to be downloaded.

    with ThreadPoolExecutor(max_workers=10) as executor:
        for date in dates_to_download_list: # Looping through the dates the my list for which we need to obtain data.
            download_dir = f'daily/{date.year}/{date.dayofyear}' 
            station_names = get_stations_from_md5(date, const_url) # Getting all the station names that have data. 
            total_expected_downloads += len(station_names) # Iterating the number of stations we expect to download. 
            for station in sorted(station_names): # Looping through each station. 
                executor.submit(
                    download_station_data,
                    station,
                    date,
                    const_url,
                    download_dir
                ) # Calling my thread to execute the getting of data. 

    with open(memory_file, 'w') as f: # Updating the memory file with the most recent last date of download. 
        f.write(f'last_file_download={current_date}')                
        print(f'\nUpdated memory file {memory_file} with new date {current_date}')

    print(f'{download_counter} out of {total_expected_downloads} files downloaded.')    


def main():
    if not check_for_netrc():
        print(f'Unable to run code because no .netrc file is detected.')
        return 
    get_new_data()


if __name__ == "__main__":
    main()