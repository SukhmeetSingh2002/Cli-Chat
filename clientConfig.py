import configparser

# Create a new config object
config = configparser.ConfigParser()

# Set the values for the config
config["Sessions"] = {
    "session_menue_history": "./.menuHistory",
    "session_username_history": "./.usernameHistory"
}

config["SocketIO"] = {
    # "connect_url": "https://cli-chat.vercel.app/",
    "connect_url": "https://localhost:3000/",
    "wait_timeout": "10"
}

config["WebBrowser"] = {
    "callback_url": "https://cli-chat-web.vercel.app/"
}

# Write the config to a file
with open("config.ini", "w") as config_file:
    config.write(config_file)
