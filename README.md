# Server and Client CLI Project

This project consists of a Node.js server and a client CLI written in Python. The server provides a set of APIs that the client can use to perform various operations.

## Getting Started

To get started with this project, you'll need to follow these steps:

1. Clone the repository to your local machine.
2. Install the necessary dependencies by running `npm install` in the `server` directory.
3. Start the server by running `npm start` in the `server` directory.
4. Download the client CLI from the `client-cli.py` file in the `client` directory.
5. Run the client CLI by running `python client-cli.py` in the `client` directory.

Alternatively, you can download the pre-built binaries for the client CLI from the `releases` page on GitHub.

## Server


The `server.js` file is the main file for the Node.js server in this project. It provides a set of APIs for a client application to perform various operations. The server uses Express and Socket.IO to handle incoming requests and real-time communication with clients. The server also uses Firebase for authentication and database storage.


## Client CLI

The `client-cli.py` file is a command-line interface (CLI) for the client in this project. It is written in Python and communicates with the server over a network using the APIs provided by the server.

### Usage

To use the client CLI, run `python client-cli.py` in the `client` directory. The CLI will prompt you for input and provide output based on the commands you enter.

The following commands are available in the client CLI:

- `get_contacts`: Gets a list of contacts.
- `add_contact`: Adds a new contact.
- `send_message`: Sends a message to a contact.
- `get_message_history`: Gets the message history for a contact.
- `exit`: Exits the client CLI.

### Authentication in the Client CLI

The client CLI uses Firebase for authentication. When you run the `python client-cli.py` command, the CLI will open a URL in your default web browser that prompts you to log in to the Firebase authentication service.

Once you have logged in, Firebase will redirect you to a success or a failure page. The client CLI will automatically extract this token from the URL and use it to authenticate with the server.

After you have successfully authenticated, the client CLI will display your username and a message indicating that you are logged in. The authentication token will be stored in a file called `.clientCredentials` in the `home` directory.



# License

This project is licensed under the MIT License. See the `LICENSE` file for more information.

# Usage

To use the client CLI, run `python client-cli.py` in the `client` directory. The CLI will prompt you for input and provide output based on the commands you enter.

# Building from Source

To build the client CLI from source, you'll need to have Python 3 installed on your machine. Then, follow these steps:

1. Clone the repository to your local machine.
2. Install the necessary dependencies by running `pip install -r requirements.txt` in the `client` directory.
3. Run `pyinstaller --onefile client-cli.py` in the `client` directory.
4. The built binaries will be located in the `dist` directory.

# Contributing

If you'd like to contribute to this project, please follow these steps:

1. Fork the repository.
2. Create a new branch for your changes.
3. Make your changes and commit them.
4. Push your changes to your fork.
5. Create a pull request.

# License

This project is licensed under the MIT License. See the `LICENSE` file for more information.