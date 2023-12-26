from rich.traceback import install
import time
import socketio
import argparse
import base64

from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table

from prompt_toolkit import prompt
from prompt_toolkit import prompt, print_formatted_text
from prompt_toolkit.completion import FuzzyWordCompleter
from prompt_toolkit import PromptSession
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.history import FileHistory
from prompt_toolkit.shortcuts import radiolist_dialog,yes_no_dialog
from prompt_toolkit.shortcuts import input_dialog

from rich.panel import Panel
from rich.text import Text

from enum import Enum
import configparser

# import custom modules
import token_port
from updateCheck import main as update_main
from clientConfig import create_config
from os import path
from os import makedirs

logs_directory = path.join(path.expanduser("~"), ".cliChatConfig")


# Load the config from the file
config = configparser.ConfigParser()
config.read(path.join(logs_directory, "config.ini"))



class UsernameState(Enum):
    UNSET = 0
    WAITING = 1
    SET = 2
    ERROR = 3


install(show_locals=True)

# Create a console object to print to the terminal
console = Console()
sio = socketio.Client()

username = ""
isUsernameSet = UsernameState.UNSET

contacts = []
isContactSet = False

isConnectedToContact = 0
contactConnectedTo = ""

didServerRespond = UsernameState.UNSET
serverResponseData = None

########## SOCKET.IO CODE ##########


@sio.on("connect")
def on_connect():
    console.print("[green]Connected to server[/green]")


@sio.on("userExists")
def on_user_exists(error):
    global isUsernameSet
    isUsernameSet = UsernameState.ERROR
    console.print(f"[red]Error: {error}[/red]")


@sio.on("userSet")
def on_user_set(data):
    global isUsernameSet
    global username
    username = data
    isUsernameSet = UsernameState.SET
    console.print(f"[green]Username set to {data}[/green]")


@sio.on("disconnect")
def on_disconnect():
    console.print("[red]Disconnected from server[/red]")

# get the list of contacts


@sio.on("contacts")
def on_contacts(data):
    # store the list of contacts
    global contacts
    global isContactSet
    contacts = data
    isContactSet = True

# connect to a contact


@sio.on("responseConnectTo")
def on_response_connect_to(data):
    global isConnectedToContact
    global contactConnectedTo
    if data["status"] == "ok":
        isConnectedToContact = 1
        contactConnectedTo = data["to"]
    else:
        isConnectedToContact = data["status"]


@sio.on("serverResponse")
def on_server_response(data):
    global didServerRespond
    global serverResponseData
    serverResponseData = data
    didServerRespond = UsernameState.SET


@sio.on("message")
def on_message(data):
    # print(data)
    # print(type(data))
    # global didServerRespond
    # didServerRespond = UsernameState.SET
    console.print(f"\n[blue]{data['from']}[/blue]: {data['msg']}")

# evenet when server needs to send important information to the user
@sio.on("fromServerMessage")
def on_from_server_message(data):
    console.print(f"\n[bright_red]from server: [/bright_red]{data['msg']}")
    global didServerRespond
    didServerRespond = UsernameState.SET



# When a user sends a message to another user we need to display it if the user is connected to the other user


@sio.on("chatMessage")
def on_chat_message(data):
    global contactConnectedTo
    if data["from"]['username'] == contactConnectedTo:
        console.print(
            f"\n[blue]{data['from']['username']}[/blue]: {data['msg']}")
    else:
        console.print(
            f"\n[blue]{data['from']['username']}[/blue] sent you a message. Type 'connect {data['from']['username']}' to connect to them")

# When a user sends a file to another user we need to display it if the user is connected to the other user
@sio.on("fileReceived")
def on_file_received(data):
    # decode the file data
    file_data = base64.b64decode(data["file"].encode('utf-8'))

    download_directory = path.join(path.expanduser("~"), "cliChatDownloads")

    # create firecectory for user if it doesn't exist
    directory = path.join(download_directory, data["from"])
    if not path.exists(directory):
        makedirs(directory)

    file_download_path = path.join(directory, data["filename"])

    # save the file to disk to ~/cliChatDownloads
    with open(file_download_path, 'wb') as f:
        f.write(file_data)

        

########## MAIN CODE ##########




def getContacts():
    # request the list of contacts from the server
    sio.emit("getContacts", username)


# Set up an event listener to read input from the user
def show_contacts(console, contacts):
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Name", style="dim", width=12)
    table.add_column("Username", justify="right")
    # table.add_column("Phone", justify="right")
    for contact in contacts.values():
        # print(contact)
        table.add_row(contact["name"], contact["username"])
    # with console.pager():

    console.print(table)


def save_contacts():
    # ask the user if he wants to save the contacts
    save_contacts = Prompt.ask(
        "Do you want to save the contacts?", choices=["Yes", "No"])
    if save_contacts == "Yes":
        # ask username and name and save to server
        save_new_contact()
        console.print("Contacts saved")


def save_new_contact():
    new_contact_name = Prompt.ask(
        "Enter the name of the contact you want to save as")
    new_contact_username = Prompt.ask("Enter the username of the contact")

    new_contact = {"name": new_contact_name, "username": new_contact_username}
    # send to server
    sio.emit("addContact", {"from": username, "contact": new_contact})


def handle_get_messages(session_username):
    global contactConnectedTo
    global isConnectedToContact
    global didServerRespond
    global serverResponseData
    didServerRespond = UsernameState.UNSET

    # ask the user to ask for a contact using his rich prompt
    # contackts is a list of dictionaries
    # contact_selected = Prompt.ask("Enter the name of the contact you want to get messages from", choices=[
    #                               contact["name"] for contact in contacts.values()])

    available_contacts = [contact["name"] for contact in contacts.values()]
    contact_selected = session_username.prompt("Enter the name of the contact you want to send a message to:", completer=FuzzyWordCompleter(
        available_contacts), mouse_support=True, complete_while_typing=True, auto_suggest=AutoSuggestFromHistory(), bottom_toolbar="Press tab for options, Up arrow for history")

    if contact_selected not in available_contacts:
        console.print(
            f"[red]Error: {contact_selected} is not a valid contact[/red]")
        return
    
    sio.emit("getMessages", {"to": contact_selected, "from": username})

    while didServerRespond == UsernameState.UNSET:
        time.sleep(0.1)

    if serverResponseData is None:
        console.print(f"[red]Error: {didServerRespond}[/red]")
        didServerRespond = UsernameState.UNSET
    else:
        didServerRespond = UsernameState.UNSET
        console.print(f"[green]Messages from {contact_selected}[/green]")
        # ask wheather wamt page or not
        want_pager = Prompt.ask("Do you want to use the pager?", choices=["Y", "N"])
        if want_pager == "Y":
            with console.pager():
                for message in serverResponseData.values():
                    if message["from"] == username['username']:
                        console.print(
                            # Text(message["from"], style="bold cyan"),
                            Text("You", style="bold cyan"),
                            Text(f" {message['time']}", style="dim"),
                            justify="right",
                        )
                        console.print(
                            Text(message["msg"], style="white"),
                            justify="right",
                        )
                    else:
                        console.print(
                            Text(message["from"], style="bold cyan"),
                            Text(f" {message['time']}", style="dim"),
                            justify="left",
                        )
                        console.print(
                            Text(message["msg"], style="white"),
                            justify="left",
                        )
                    console.print()
        else:
            for message in serverResponseData.values():
                if message["from"] == username['username']:
                    console.print(
                        # Text(message["from"], style="bold cyan"),
                        Text("You", style="bold cyan"),
                        Text(f" {message['time']}", style="dim"),
                        justify="right",
                    )
                    console.print(
                        Text(message["msg"], style="white"),
                        justify="right",
                    )
                else:
                    console.print(
                        Text(message["from"], style="bold cyan"),
                        Text(f" {message['time']}", style="dim"),
                        justify="left",
                    )
                    console.print(
                        Text(message["msg"], style="white"),
                        justify="left",
                    )
                console.print()

def connect_to_contact(contact_selected):
    global isConnectedToContact
    # find the username of the contact
    for contact in contacts.values():
        if contact["name"] == contact_selected:
            contact_selected = contact["username"]
            break

    sio.emit("connectTo", {"to": contact_selected, "from": username})

    # wait for the server to respond
    while isConnectedToContact == 0:
        time.sleep(0.1)

    if isConnectedToContact != 1:
        console.print(f"[red]Error: {isConnectedToContact}[/red]")
        isConnectedToContact = 0
        return False
    else:
        # print a message to the user
        isConnectedToContact = 0
        console.print(f"[green]Connected to {contact_selected}[/green]")
        console.print(
            f"[green]Type your message and press enter to send it[/green]")
        console.print(
            f"[green]Type 'exit' to disconnect from {contact_selected}[/green]")
        return True


def send_message(session_username):
    global contactConnectedTo
    global isConnectedToContact
    # ask the user to select a contact using a rich prompt

    # contact_selected = Prompt.ask("Enter the name of the contact you want to send a message to:", choices=[
    #                               contact["name"] for contact in contacts.values()])

    available_contacts = [contact["name"] for contact in contacts.values()]
    contact_selected = session_username.prompt("Enter the name of the contact you want to send a message to:", completer=FuzzyWordCompleter(
        available_contacts), mouse_support=True, complete_while_typing=True, auto_suggest=AutoSuggestFromHistory(), bottom_toolbar="Press tab for options, Up arrow for history")

    if contact_selected not in available_contacts:
        console.print(
            f"[red]Error: {contact_selected} is not a valid contact[/red]")
        return
    

    is_connected = connect_to_contact(contact_selected)

    if not is_connected:
        # print in read that client is not online but still send the message
        console.print(
            f"[red]Client {contact_selected} is not online, but we will still send the message[/red]")
        # send the message to the server

    # Chat loop
    while True:
        # Read input from the user
        your_message = prompt("You:")
        if your_message == "exit":
            break

        sio.emit("sendTo", {"to": contact_selected,
                 "msg": your_message, "from": username})


def main():
    session_menue_history = config.get("Sessions", "session_menue_history")
    session_username_history = config.get("Sessions", "session_username_history")

    # define variables
    global username
    global isUsernameSet
    global contacts
    global isContactSet
    global isConnectedToContact
    session_menue = PromptSession(history=FileHistory(session_menue_history))
    session_username = PromptSession(history=FileHistory(session_username_history))
    # session_menue = PromptSession(history=FileHistory('./.myhistory'))

    while isUsernameSet != UsernameState.SET:
        time.sleep(0.1)

    # show the user a list of his contacts
    getContacts()
    while not isContactSet:
        time.sleep(0.1)

    # if the user has no contacts, ask him to add some
    while contacts is None or len(contacts) == 0:
        isContactSet = False
        console.print("You have no contacts")
        save_new_contact()
        getContacts()
        while not isContactSet:
            time.sleep(0.1)

    # print(contacts)
    input("Press enter to continue")

    # Ask what the user wants to do
    options_list = ["Show contacts", "Add contact",
                    "Send message", "getMessages", "Exit"]
    # show the options list to the user
    console.print("Your options are:")
    for option in options_list:
        console.print(f" - {option}")

    while True:

        # ask the user to select an option
        options = FuzzyWordCompleter(options_list)
        selected_option = session_menue.prompt("Please select an option:", completer=options,
                                               bottom_toolbar="Press tab for options, Up arrow for history", mouse_support=True, complete_while_typing=True, auto_suggest=AutoSuggestFromHistory())

        if selected_option == "Show contacts":
            show_contacts(console, contacts)
        elif selected_option == "Add contact":
            save_new_contact()
            getContacts()
        elif selected_option == "Send message":
            send_message(session_username)
        elif selected_option == "getMessages":
            handle_get_messages(session_username)
        elif selected_option == "Exit":
            break
        else:
            console.print("Invalid option")
            # show the options list to the user
            console.print("Your options are:")
            for option in options_list:
                console.print(f" - {option}")
        
        input("Press enter to continue")

    # Disconnect from the server
    sio.disconnect()



def send_file(file_path, recipient):
    with open(file_path, 'rb') as f:
        file_data = f.read()


    file_extension = path.splitext(file_path)[1]

        # Map file extensions to common content types (you can expand this list)
    content_type_map = {
        '.jpg': 'image/jpeg',
        '.png': 'image/png',
        '.pdf': 'application/pdf',
        '.doc': 'application/msword',
        '.txt': 'text/plain',
    }

    # get the content type
    content_type = content_type_map.get(file_extension, 'application/octet-stream')

    # encode the file data
    file_data = base64.b64encode(file_data).decode('utf-8')


    # send the file to the server
    sio.emit("sendFile", {"to": recipient, "file": file_data, "from": username, "filename": path.basename(file_path), "content_type": content_type})

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Xypher Client, a command line chat application')
    parser.add_argument('-s','--send-file', dest='file_path', type=str, help='Path to the file to send')
    parser.add_argument('-r','--recipient', dest='recipient', type=str, help='The recipient of the file')
    parser.add_argument('-g','--get-file', dest='file_list', action='store_true', help='Get the list of files')
    parser.add_argument('-d','--download-file', dest='file_name', type=str, help='Download the file with the given name')
    parser.add_argument('-c','--get-contacts', dest='get_contacts', action='store_true', help='Get the list of contacts')
    parser.add_argument('-u','--usernameFriend', dest='usernameFriend', type=str, help='The username of the user to get the file from')
    args = parser.parse_args()

    from prompt_toolkit.styles import Style

    xypher_style = Style.from_dict({
        'dialog':             'bg:#fff3e0',
        'dialog frame.label': 'bg:#eef6ff #424242',
        'dialog.body':        'bg:#424242 #eef6ff',
        'dialog shadow':      'bg:#ff9900',
    })

    if args.file_path is None and args.recipient is None and args.file_list is False and args.file_name is None and args.get_contacts is False:
        result = radiolist_dialog(
            title="Xypher",
            text="What do you want to do?",
            values=[
                ("send_file", "Send file"),
                ("get_file_list", "Get list of files received from a user"),
                ("download_file", "Download file sent by a user"),
                ("get_contacts", "Get contacts"),
                ("main", "Continue to the main menu")
            ],
            style=xypher_style
        ).run()


        if result == "send_file":
            args.file_path = input_dialog(
                title="Xypher",
                text="Enter the path to the file to send",
                password=False,
                style=xypher_style
            ).run()

            if args.file_path is None:
                print("Cancelling sending file")
                exit()

        elif result == "get_file_list":
            args.file_list = True

        elif result == "download_file":
            args.file_name = input_dialog(
                title="Xypher",
                text="Enter the name of the file to download",
                password=False,
                style=xypher_style
            ).run()

            if args.file_name is None:
                print("Cancelling downloading file")
                exit()

            args.usernameFriend = input_dialog(
                title="Xypher",
                text="Enter the username of the user to download the file from",
                password=False,
                style=xypher_style
            ).run()

            if args.usernameFriend is None:
                print("Cancelling downloading file")
                exit()
        
        elif result == "get_contacts":
            args.get_contacts = True

        elif result == "main":
            pass

        else:
            print("Invalid option")
            exit()

        

    print("Use the -h option for help")

    # create the config file if it doesn't exist
    create_config()

    update_main()

    connect_url = config.get("SocketIO", "connect_url")
    wait_timeout = config.getint("SocketIO", "wait_timeout")

    # get auth details
    token = token_port.get_auth_details()
    token = token['accessToken']
    try:
        # increase the timeout to 10 seconds
        sio.connect(connect_url,
                    auth={"token": token}, wait_timeout=wait_timeout)
    except Exception as e:
        print("Error connecting to server")
        print("Token expired, retry to get a new token, or Email not verified, Or username not set")
        print("Error: ", e)
        token_port.save_token({"stsTokenManager": ""})  # delete token
        exit()

    if args.file_path is not None:


        if args.recipient is not None:
            # confirm before sending the file
            result = yes_no_dialog(
                title="Confirm",
                text=f"Are you sure you want to send the file {args.file_path} to {args.recipient}?",
                style=xypher_style
            ).run()

            if result is False:
                console.print(f"Cancelling sending file [bold][red]{args.file_path}[/red][/bold]")
                sio.disconnect()
                exit()


        else:
            # get the list of contacts
            sio.emit("getContacts", username)

            # wait for the server to respond
            while not isContactSet:
                time.sleep(0.1)

            # print the contacts
            show_contacts(console, contacts)

            input("Press enter to continue...")

            input_username = input_dialog(
                title=f"Sending file {args.file_path}", text="Enter the username of the recipient", password=False,
                completer=FuzzyWordCompleter(
                    [contact["username"] for contact in contacts.values()]),
                style=xypher_style
            ).run()
            
            if input_username is None:
                console.print(f"Cancelling sending file [bold][red]{args.file_path}[/red][/bold]")
                sio.disconnect()
                exit()

            if input_username not in [contact["username"] for contact in contacts.values()]:
                console.print(f"[red]Error: [bold][blue]{input_username}[/bold][/blue] is not a valid contact[/red]")
                sio.disconnect()
                exit()

            args.recipient = input_username



            # find the username of the contact
            for contact in contacts.values():
                if contact["name"] == args.recipient:
                    args.recipient = contact["username"]
                    break


        print("Sending file...")



        # send the file to the recipient
        send_file(args.file_path, args.recipient)

        # wait for the server to respond
        while didServerRespond == UsernameState.UNSET:
            time.sleep(0.1)

        sio.disconnect()
        exit()
    elif args.file_path is None and args.recipient is not None:
        print("Error: file path not specified")
        sio.disconnect()
        exit()


    if args.file_list:

        if args.usernameFriend is None:

            # get the list of contacts
            sio.emit("getContacts", username)

            # wait for the server to respond
            while not isContactSet:
                time.sleep(0.1)

            # print the contacts
            show_contacts(console, contacts)

            from_user = Prompt.ask("Enter the name of the contact you want to get files from:", choices=[
                                    contact["name"] for contact in contacts.values()])

            # find the username of the contact
            for contact in contacts.values():
                if contact["name"] == from_user:
                    from_user = contact["username"]
                    break

        else:
            from_user = args.usernameFriend



        console.print(f"Getting files from [blue]{from_user}[/blue]")
        # print {"to": username, "from": from_user}
        console.print(f"Getting files from [blue]{from_user}[/blue] to [blue]{username}[/blue]")

        # get the list of files
        sio.emit("getAllFiles", {"to": username, "from": from_user})

        # wait for the server to respond
        while didServerRespond == UsernameState.UNSET:
            time.sleep(0.1)

        sio.disconnect()
        exit()

    if args.file_name is not None and args.usernameFriend is not None:
        # download the file
        sio.emit("getFile", {"from": args.usernameFriend, "filename": args.file_name, "to": username})

        # wait for the server to respond
        while didServerRespond == UsernameState.UNSET:
            time.sleep(0.1)
            

        sio.disconnect()
        exit()

    if args.get_contacts:
        # get the list of contacts
        sio.emit("getContacts", username)

        # wait for the server to respond
        while not isContactSet:
            time.sleep(0.1)

        # print the contacts
        show_contacts(console, contacts)

        sio.disconnect()
        exit()

    main()
