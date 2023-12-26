import requests
import os
import subprocess
import webbrowser

import configparser

from os import path

logs_directory = path.join(path.expanduser("~"), ".cliChatConfig")

DOWNLOAD_URL = ""
UPDATE_URL = ""
CURRENT_VERSION = ""

# get config
def get_config(UPDATE_URL, CURRENT_VERSION, DOWNLOAD_URL):
    # Load the config from the file
    config = configparser.ConfigParser()
    config.read(path.join(logs_directory, "config.ini"))

    # Define the update source URL
    UPDATE_URL = config.get("Update", "update_url")
    CURRENT_VERSION = config.get("Update", "current_version")
    DOWNLOAD_URL = config.get("Update", "download_url")

    return UPDATE_URL, CURRENT_VERSION, DOWNLOAD_URL
    

# Function to check for updates
def check_for_updates(current_version):
    try:
        # Send a request to the update source URL to retrieve the latest version information
        response = requests.get(UPDATE_URL)
        
        if response.status_code == 200:
            latest_version = response.text.strip()

            # if 1st char is v, remove it
            if latest_version[0] == 'v':
                latest_version = latest_version[1:]

            if latest_version > current_version:
                # Newer version is available, return the latest version
                return latest_version
    except:
        pass

    # No update available or failed to fetch the latest version
    return None

# Function to download a file from a URL
def download_file(url, destination):
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with open(destination, 'wb') as file:
            for chunk in response.iter_content(chunk_size=1024):
                file.write(chunk)
        return True
    return False

# Function to download and update the application
def update_application(DOWNLOAD_URL):
    # Download the updated application package from the update source
    # package_url = "https://example.com/update/package.tar.gz"  # Replace with the actual download URL
    # package_filename = "package.tar.gz"  # Replace with the actual filename
    
    # # Set the destination path to download the package
    # destination = os.path.join(os.getcwd(), package_filename)  # Use appropriate directory if needed
    
    # # Download the package
    # if download_file(package_url, destination):
    #     # Perform any necessary installation steps
    #     # For example, replace existing application files, handle migrations, update configuration, etc.
        
    #     # Restart the application to apply the update
    #     subprocess.call(["python", "main.py"])  # Replace "main.py" with the actual entry point of your application

    # open browser to download page
    webbrowser.open(DOWNLOAD_URL)


# Entry point of your application
def main():
    global UPDATE_URL, CURRENT_VERSION, DOWNLOAD_URL
    UPDATE_URL, CURRENT_VERSION, DOWNLOAD_URL = get_config(UPDATE_URL, CURRENT_VERSION, DOWNLOAD_URL)

    # Retrieve the current version of your application
    current_version = CURRENT_VERSION
    
    # Check for updates
    latest_version = check_for_updates(current_version)
    
    if latest_version:
        print("An update is available. Do you want to download and install it? (y/n)")
        choice = input().strip().lower()
        
        if choice == "y":
            # Perform the update
            update_application(DOWNLOAD_URL)
            # print("Contact the developer for the latest version.")
            return
    else:
        # print("No updates available. Continuing with the application...")
        pass
    
    # Rest of your application logic goes here

if __name__ == "__main__":
    # global UPDATE_URL, CURRENT_VERSION
    UPDATE_URL, CURRENT_VERSION, DOWNLOAD_URL = get_config(UPDATE_URL, CURRENT_VERSION, DOWNLOAD_URL)
    main()
