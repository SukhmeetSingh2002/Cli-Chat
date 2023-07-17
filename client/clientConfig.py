import configparser
import os

# Create a new config object
config = configparser.ConfigParser()

# Set the values for the config
config["Sessions"] = {
    "session_menue_history": "./.menuHistory",
    "session_username_history": "./.usernameHistory"
}

config["SocketIO"] = {
    "connect_url": "https://clichat.azurewebsites.net",
    "wait_timeout": "10"
}

config["WebBrowser"] = {
    "callback_url": "https://cli-chat-web.vercel.app/"
}

# Get the base directory for logs in the user's home directory
logs_directory = os.path.join(os.path.expanduser("~"), "cliChatConfig")

# Create the logs directory if it doesn't exist
if not os.path.exists(logs_directory):
    os.makedirs(logs_directory)


# Write the config to a file
with open("config.ini", "w") as config_file:
    config.write(config_file)
