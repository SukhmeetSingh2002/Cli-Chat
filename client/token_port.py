import json
import random
import webbrowser
import http.server
import socketserver
import configparser
from os import path

logs_directory = path.join(path.expanduser("~"), ".cliChatConfig")

callback_url = ""
client_credentials_file = ""
error_file = ""

# get config
def get_config(callback_url, client_credentials_file, error_file):
    # Load the config from the file
    config = configparser.ConfigParser()
    config.read(path.join(logs_directory, "config.ini"))

    # Define the update source URL
    callback_url = config.get("WebBrowser", "callback_url")
    client_credentials_file = config.get("Sessions", "client_credentials_file")
    error_file = config.get("Sessions", "error_file")

    return callback_url, client_credentials_file, error_file
    

AUTH_TOKEN = None

def get_auth_details():
    global callback_url, client_credentials_file, error_file
    callback_url, client_credentials_file, error_file = get_config(callback_url, client_credentials_file, error_file)

    global AUTH_TOKEN
    token = get_saved_token()
    
    if token:
        authenticate_user(token)
        AUTH_TOKEN = token
    else:
        # Generate a random port number
        port = random.randint(10000, 20000)
        redirect_to_auth_page(port)
        listen_for_token(port)
        # print("Received tokenasdffffffffffffffff:", AUTH_TOKEN)
        AUTH_TOKEN = AUTH_TOKEN.get('stsTokenManager')

        # close the browser tab
        # webbrowser.close()
    return AUTH_TOKEN

def authenticate_user(token):
    # Implement code to authenticate the user
    print("Authenticating user...")
    # print the token in json format
    # print(json.dumps(token, indent=4))

def get_saved_token():
    # Implement code to retrieve the saved token from the user's computer
    # If token is not found, return None
    try:
        with open(client_credentials_file, 'r') as f:
            token = f.read()
        if token:
            token = json.loads(token)
            return token
        else:
            return None
    except FileNotFoundError:
        return None

def redirect_to_auth_page(port):
    # open a web browser
    webbrowser.open(f"{callback_url}?callbackPort={port}")

    # Implement code to redirect the user to the authentication webpage
    print("Open the following URL in a web browser to authenticate if it doesn't open automatically:")
    print(f"{callback_url}?callbackPort={port}")

def listen_for_token(port):
    # Start a server to listen for the token
    Handler = TokenHandler
    with socketserver.TCPServer(("", port), Handler) as httpd:
        # print("Server started on port", port)
        while True:
            httpd.handle_request()
            if AUTH_TOKEN:
                break


def save_token(token):
    # Implement code to save the token to the user's computer
    token = token.get('stsTokenManager')
    try:
        # write refresh token, access token and expiration time to a file in JSON format
        with open(client_credentials_file, 'w') as f:
            f.write(json.dumps(token, indent=4))
    except Exception as e:
        print("Error saving token:")
        with open(error_file, 'w') as f:
            f.write(str(e))


class TokenHandler(http.server.BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_POST(self):
        # print("Received a POST request")
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
            
        # with open('post_data.txt', 'w') as f:
        #     f.write(json.dumps(json.loads(post_data), indent=4))

        token = self.extract_token_from_post_data(post_data)
        
        # Save the token to the computer
        save_token(token)
        
        # Authenticate the user using the received token
        authenticate_user(token)
        
        # set the AUTH_TOKEN variable
        global AUTH_TOKEN
        AUTH_TOKEN = token

        # Send a response to the browser
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self.wfile.write(b'{"status": "success"}')

    def extract_token_from_post_data(self, post_data):
        data = json.loads(post_data)
        # print("Data:", data)
        token = data.get('user')
        return token



if __name__ == '__main__':
    # global callback_url, client_credentials_file, error_file
    callback_url, client_credentials_file, error_file = get_config(callback_url, client_credentials_file, error_file)

    # Call the main function
    get_auth_details()
