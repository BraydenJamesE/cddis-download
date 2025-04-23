# CDDIS Data Downloader

This script downloads daily GNSS ionospheric data from NASA's CDDIS archive. 

Downloads are dependent on the ```MD5SUMS``` file being present in the CDDIS daily folders to determine which stations have data for a given day. If the ```MD5SUMS``` file is missing for a day you expect data from, shoot me an email:

📧 edwabray@oregonstate.edu

## Requirements

- Python 3
- `requests`, `pandas`, `earthaccess`

Install them:

```
pip install requests pandas earthaccess
```

## Setup Instructions
### 1. Create na Earthdata Login
You'll need an Earthdata account to access the CDDIS archive. Create one here: https://urs.earthdata.nasa.gov/users/new

---

### 2. Create a ```.netrc``` file
This file stores your login credential for automated HTTPS access. 

#### Linux/MacOS:
Create ```~/.netrc``` and add:
```
machine urs.earthdata.nasa.gov
login your_username
password your_password
```

#### Windows: 
Create a file ```~/_netrc``` with the same contents as above.


For more information, look here: 
- https://cddis.nasa.gov/Data_and_Derived_Products/CreateNetrcFile.html 
- https://cddis.nasa.gov/docs/2019/CDDIS_Archive_Access_Using_Python.pdf

---
### 3. Initialize the memory file
Create a file named ```memory.txt``` in the same directory as the script. This file tracks the most recent date you've downloaded data for. 

It should look like this:
```
last_file_download=2025-04-17
```
The script will only download newer data and update the this file when it's done. 


## Run the Script

Run the scipt using:

```
python3 download_cddis.py
```