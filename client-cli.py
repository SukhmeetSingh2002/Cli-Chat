from rich.traceback import install
import time
import socketio

from rich.console import Console
from rich.markdown import Markdown
from rich.prompt import Prompt
from rich.table import Table

from enum import Enum


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
    if data["status"] == "ok":
        isConnectedToContact = 1
        contactConnectedTo = data["to"]
    else:
        isConnectedToContact = data["status"]


@sio.on("message")
def on_message(data):
    # print(data)
    # print(type(data))
    console.print(f"[blue]{data['from']}[/blue]: {data['msg']}")

# When a user sends a message to another user we need to display it if the user is connected to the other user


@sio.on("chatMessage")
def on_chat_message(data):
    global contactConnectedTo
    if data["from"] == contactConnectedTo:
        console.print(f"[blue]{data['from']}[/blue]: {data['msg']}")
    else:
        console.print(
            f"[blue]{data['from']}[/blue] sent you a message. Type 'connect {data['from']}' to connect to them")


########## MAIN CODE ##########

def register_new_user(sio):
    global username
    global isUsernameSet
    # Prompt the user to enter a username
    username = Prompt.ask("Enter a username")
    print(f"Your username is: {username}")

    # ask valid email
    email = Prompt.ask("Enter a valid email")
    print(f"Your email is: {email}")

    # ask password
    password = Prompt.ask("Enter a password", password=True)
    print(f"Your password is: {password}")

    # Send the username to the server
    isUsernameSet = UsernameState.WAITING
    sio.emit("setUsername", {
             "username": username, "password": password, "email": email, "action": "register"})

    while isUsernameSet == UsernameState.WAITING:
        time.sleep(0.1)
    return username


def login_user(sio):
    global username
    global isUsernameSet
    username = Prompt.ask("Enter your username")
    email = Prompt.ask("Enter your email")
    password = Prompt.ask("Enter your password", password=True)

    isUsernameSet = UsernameState.WAITING
    sio.emit("setUsername", {
             "email": email, "password": password, "action": "login", "username": username})

    while isUsernameSet == UsernameState.WAITING:
        time.sleep(0.1)
    return username


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
    new_contact_name = Prompt.ask("Enter the name of the contact")
    new_contact_username = Prompt.ask("Enter the username of the contact")

    new_contact = {"name": new_contact_name, "username": new_contact_username}
    # send to server
    sio.emit("addContact", {"from": username, "contact": new_contact})


def send_message():
    global contactConnectedTo
    global isConnectedToContact
    # ask the user to ask for a contact using his rich prompt
    # contackts is a list of dictionaries
    contact_selected = Prompt.ask("Enter the name of the contact you want to send a message to", choices=[
                                  contact["name"] for contact in contacts.values()])

    # try to connect to the contact
    sio.emit("connectTo", {"to": contact_selected, "from": username})

    # wait for the server to respond
    while isConnectedToContact == 0:
        time.sleep(0.1)

    if isConnectedToContact != 1:
        console.print(f"[red]Error: {isConnectedToContact}[/red]")
        isConnectedToContact = 0
    else:
        # print a message to the user
        isConnectedToContact = 0
        console.print(f"[green]Connected to {contact_selected}[/green]")
        console.print(
            f"[green]Type your message and press enter to send it[/green]")
        console.print(
            f"[green]Type 'exit' to disconnect from {contact_selected}[/green]")
        while True:
            # Read input from the user
            your_message = input("You:")
            if your_message == "exit":
                break

            sio.emit("sendTo", {"to": contact_selected,
                     "msg": your_message, "from": username})


def main():
    # define variables
    global username
    global isUsernameSet
    global contacts
    global isContactSet
    global isConnectedToContact

    while isUsernameSet != UsernameState.SET:
        console.print("What would you like to do?")
        console.print("[bold]1[/bold]. Register new user")
        console.print("[bold]2[/bold]. Login")

        action = Prompt.ask("Enter the number corresponding to your choice:", choices=[
                            "1", "2"], default="2")

        if action == "1":
            username = register_new_user(sio)
        elif action == "2":
            username = login_user(sio)
        else:
            console.print("Invalid action. Please try again.")

    save_contacts()

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

    while True:
        # ask what the user wants to do
        options = ["Show contacts", "Add contact", "Send message", "Exit"]
        selected_option = Prompt.ask(
            "Please select an option:", choices=options)
        if selected_option == "Show contacts":
            show_contacts(console, contacts)
        elif selected_option == "Add contact":
            save_new_contact()
        elif selected_option == "Send message":
            send_message()
        elif selected_option == "Exit":
            break
        else:
            console.print("Invalid option")


if __name__ == "__main__":
    # Connect to the server
    sio.connect("http://localhost:3000")
    main()
    # options = ["Option 1", "Option 2", "Option 3"]
    # selected_option = Prompt.ask("Please select an option:", choices=options)
