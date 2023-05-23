import time
import socketio

from rich.console import Console
from rich.markdown import Markdown
from rich.prompt import Prompt
from rich.table import Table

from rich.traceback import install
install(show_locals=True)

# Create a console object to print to the terminal
console = Console()
sio = socketio.Client()

username = ""
isUsernameSet = False

contacts = []
isContactSet = False

isConnectedToContact = 0

########## SOCKET.IO CODE ##########
@sio.on("connect")
def on_connect():
    console.print("[green]Connected to server[/green]")

@sio.on("userExists")
def on_user_exists(error):
    console.print(f"[red]Error: {error}[/red]")

@sio.on("userSet")
def on_user_set(data):
    global isUsernameSet
    isUsernameSet = True
    # print("Is username set? " + str(isUsernameSet))
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
    else:
        isConnectedToContact = data["status"]

    



########## MAIN CODE ##########

def ask_username(sio):
    global username
    global isUsernameSetS
    while not isUsernameSet:
    # Prompt the user to enter a username
        username = Prompt.ask("Enter a username")
        print(f"Your username is: {username}")

    # Send the username to the server
        sio.emit("setUsername", username)
        # print("Waiting for server to respond...")
        # print("Is username set? " + str(isUsernameSet))
        time.sleep(0.1)
    return username


def getContacts():
    # request the list of contacts from the server
    sio.emit("getContacts", username)


# Set up an event listener to read input from the user
def show_contacts(console, contacts):
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Name", style="dim", width=12)
    table.add_column("Email", justify="right")
    # table.add_column("Phone", justify="right")
    for contact in contacts.values():
        # print(contact)
        table.add_row(contact["name"], contact["username"])
    # with console.pager():

    console.print(table)

def save_contacts():
    # ask the user if he wants to save the contacts
    save_contacts = Prompt.ask("Do you want to save the contacts?", choices=["Yes", "No"])
    if save_contacts == "Yes":
        # ask username and name and save to server
        new_contact_name = Prompt.ask("Enter the name of the contact")
        new_contact_username = Prompt.ask("Enter the username of the contact")

        new_contact = {"name": new_contact_name, "username": new_contact_username}
        # send to server
        sio.emit("addContact", {"from": username, "contact": new_contact})


def main():
    # define variables
    global username
    global isUsernameSet
    global contacts
    global isContactSet
    global isConnectedToContact

    username = ask_username(sio)
    save_contacts()

    # show the user a list of his contacts
    getContacts()
    while not isContactSet:
        time.sleep(0.1)

    print(contacts)
    input("Press enter to continue")

    # use rich table to show the list of contacts
    show_contacts(console, contacts)

    while True:
        # ask the user to ask for a contact using his rich prompt
        # contackts is a list of dictionaries
        contact_selected = Prompt.ask("Enter the name of the contact you want to send a message to", choices=[contact["name"] for contact in contacts.values()])
        
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
            console.print(f"[green]Type your message and press enter to send it[/green]")
            console.print(f"[green]Type 'exit' to disconnect from {contact_selected}[/green]")
            while True:
                # Read input from the user
                your_message = input("You:")
                if your_message == "exit":
                    break
                
                sio.emit("sendTo", {"to": contact_selected, "msg": your_message, "from": username})
                @sio.on("message")
                def on_message(data):
                    print(data)
                    print(type(data))
                    console.print(f"[blue]{data['from']}[/blue]: {data['msg']}")
                    

if __name__ == "__main__":
    # Connect to the server
    sio.connect("http://localhost:3000")
    main()
    # options = ["Option 1", "Option 2", "Option 3"]
    # selected_option = Prompt.ask("Please select an option:", choices=options)




