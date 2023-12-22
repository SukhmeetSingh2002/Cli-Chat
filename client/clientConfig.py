import configparser
import os

# Create a new config object
config = configparser.ConfigParser()

def create_config():
    # Get the base directory for logs in the user's home directory
    logs_directory = os.path.join(os.path.expanduser("~"), ".cliChatConfig")

    # download directory
    download_directory = os.path.join(os.path.expanduser("~"), "cliChatDownloads")

    # Create the logs directory if it doesn't exist
    if not os.path.exists(logs_directory):
        os.makedirs(logs_directory)

    # Create the download directory if it doesn't exist
    if not os.path.exists(download_directory):
        os.makedirs(download_directory)

    # Set the values for the config
    config["Sessions"] = {
        "session_menue_history": os.path.join(logs_directory, ".menueHistory"),
        "session_username_history": os.path.join(logs_directory, ".usernameHistory"),
        "client_credentials_file": os.path.join(logs_directory, ".clientCredentials"),
        "error_file": os.path.join(logs_directory, ".errorToken"),
    }

    config["SocketIO"] = {
        # "connect_url": "https://clichat.azurewebsites.net",
        "connect_url": "https://xypher-server.onrender.com",
        "wait_timeout": "10"
    }

    config["WebBrowser"] = {
        "callback_url": "https://xypher.vercel.app/auth/signin/",
    }


    config["Update"] = {
        "update_url": "https://xypher.vercel.app/api/version",
        "current_version": "1.0.0"
    }


    # Write the config to a file
    # with open("config.ini", "w") as config_file:
    with open(os.path.join(logs_directory, "config.ini"), "w") as config_file:
        config.write(config_file)
