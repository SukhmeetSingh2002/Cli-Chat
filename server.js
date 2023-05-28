const express = require("express");
const http = require("http");
const socketIO = require("socket.io");
const winston = require("winston");
const database = require("./firebaseTest").database;
const { generateChatId } = require("./utils/generateChatId");
const auth = require("./firebaseTest").auth;

const app = express();
const server = http.createServer(app);
const io = socketIO(server);

// Set up Winston logger
const logger = winston.createLogger({
  level: "info",
  format: winston.format.json(),
  transports: [
    new winston.transports.Console(),
    new winston.transports.File({ filename: "server.log" }),
  ],
});

let clientMap = new Map();
let users = [];

// Event handlers
const handleRegisterUser = async (socket, data) => {
  // Extract the necessary data
  const { username, email, password } = data;

  logger.info(`Registering new user: ${username}`);
  logger.info(`Email: ${email}`);
  logger.info(`Password: ${password}`);

  try {
    // Check if the username already exists
    if (users.includes(username)) {
      throw new Error(
        `${username} username is taken! Try some other username.`
      );
    }

    // Create a new user with the provided email and password
    const userRecord = await auth.createUser({
      email: email,
      password: password,
      displayName: username,
    });

    // Update the user list and socket properties
    users.push(username);
    socket.username = username;
    clientMap.set(socket.username, socket.id);

    socket.emit("userSet", { username: username });

    logger.info("Successfully created new user:", userRecord.uid);
  } catch (error) {
    logger.error("Error creating user:", error);

    socket.emit("userExists", `Error: ${error.message}! Try again.`);
  }
};

const handleLogin = async (socket, data) => {
  // Extract the necessary data
  const { username, email, password } = data;

  logger.info(`Logging in with username: ${username}`);
  logger.info(`Logging in with email: ${email}`);
  logger.info(`Password: ${password}`);

  if (!users.includes(username)) {
    socket.emit("userExists", `Error: ${username} does not exist! Try again.`);
    return;
  }

  try {
    // Generate the email sign-in link
    const actionCodeSettings = {
      url: "http://localhost:5500",
      handleCodeInApp: false,
    };
    const link = await auth.generateSignInWithEmailLink(
      email,
      actionCodeSettings
    );
    logger.info("Generated sign-in link:" + link);

    // Send the email to the user with the link

    socket.emit("userSet", { username: username });

    // Update the user list and socket properties
    socket.username = username;
    clientMap.set(socket.username, socket.id);
    

    logger.info("User logged in successfully.");
  } catch (error) {
    logger.error("Error logging in:" + error);

    socket.emit("userExists", `Error: ${error.message}! Try again.`);
  }
};

// Handle the "setUsername" event
const handleSetUsername = (socket) => (data) => {
  // Determine the action based on the provided data
  if (data.action === "register") {
    handleRegisterUser(socket, data);
  } else if (data.action === "login") {
    handleLogin(socket, data);
  }

  // logger.info("All users:==================== "+users, users);
  // clientMap.forEach((value, key) => {
  //   logger.info(`${key} ======================= ${value}`);
  // });
};
const handleSendTo = (socket) => (data) => {
  logger.info("sendTo event");
  logger.info("to: ", data.to);
  logger.info("msg: ", data.msg);

  const clientId = clientMap.get(data.to);
  const sendTime = new Date().toLocaleString();

  if (clientId) {
    socket.to(clientId).emit("chatMessage", data);
    storeMessage(data.to, data.from, data.msg, sendTime);
    winston.info(`Sent message to ${data.from}: ${data.msg}`);
  } else if (users.includes(data.to)) {
    socket.emit("message", {
      from: "Server",
      msg: `User ${data.to} is offline`,
    });
    storeMessage(data.to, data.from, data.msg, sendTime);
    // storeMessage(data.from, "You", data.msg, sendTime);
    winston.info(`Offline Sent message to ${data.from}: ${data.msg}`);
  } else {
    socket.emit("message", {
      from: "Server",
      msg: `User ${data.to} not found`,
    });
    winston.error(`Error: User ${data.to}, ${socket.id} not found`);
  }
};

const handleGetContacts = (socket) => async (username) => {
  logger.info("handleGetContacts");
  try {
    const contactsSnapshot = await database
      .ref("/contacts/" + username)
      .once("value");
    const contacts = contactsSnapshot.val();
    socket.emit("contacts", contacts);
  } catch (error) {
    logger.error("Error retrieving contacts:", error);
    socket.emit("contacts", null);
  }
};

const handleConnectTo = (socket) => (data) => {
  logger.info("connectTo event");
  //   print user and clientMap
  logger.info("All users: " + users);
  console.log("clientMap: ", clientMap);
  logger.info("to: " + data.to);

  const clientId = clientMap.get(data.to);
  logger.info("clientId: " + clientId);
  if (clientId) {
    socket.emit("responseConnectTo", {
      from: "Server",
      to: data.to,
      status: "ok",
    });
    winston.info(`connectTo: ${data.to}, ${socket.id} found`);
  } else {
    socket.emit("responseConnectTo", {
      from: "Server",
      to: data.to,
      status: "offline",
    });
    winston.error(`connectTo: ${data.to}, ${socket.id} Offline`);
  }
};

const handleSaveContacts = (socket) => (data) => {
  logger.info("handleSaveContacts");
  logger.info("data: ", data);

  if (users.includes(data.from)) {
    // if the contact is not in the users list
    if (!users.includes(data.contact.username)) {
      socket.emit("message", {
        from: "Server",
        msg: `User ${data.contact.username} not found`,
      });
      winston.error(
        `Error: User ${data.contact.username}, ${socket.id} not found`
      );
      return;
    }
    // if the contact is in the users list
    database.ref("/contacts/" + data.from).push({
      name: data.contact.name,
      username: data.contact.username,
    });
  } else {
    socket.emit("message", {
      from: "Server",
      msg: `User ${data.from} not found`,
    });
    winston.error(`Error: User ${data.from}, ${socket.id} not found`);
  }
};

const handleGetMessages = (socket) => async (data) => {
  logger.info("handleGetMessages");
  logger.info("data: ", data);

  const chatId = generateChatId(data.from, data.to);
  logger.info("chatId: ", chatId);

  try {
    const messages = await fetchMessageHistory(chatId);
    logger.info("messages: ", messages);
    socket.emit("serverResponse", messages);
  } catch (error) {
    logger.error("Error retrieving messages:", error);
    socket.emit("serverResponse", null);
  }
};



// Helper functions
const storeMessage = (user, from, msg, time) => {
  const chatId = generateChatId(user, from);
  database.ref("/chats/" + chatId).push({
    from: from,
    to: user,
    msg: msg,
    time: time,
  });
};

const fetchUsers = async () => {
  try {
    // const usersSnapshot = await database.ref("/contacts").once("value");
    // const usersData = usersSnapshot.val();
    const userRecords = await auth.listUsers();

    const usersData = userRecords.users.map((userRecord) => ({
      uid: userRecord.uid,
      email: userRecord.email,
      displayName: userRecord.displayName,
    }));

    const users = usersData.map((user) => user.displayName);
    // console.log("userData: ", usersData);
    // console.log("users: ", users);
    return users;
  } catch (error) {
    logger.error("Error retrieving users:", error);
    return [];
  }
};

const fetchMessageHistory = async (chatId) => {
  const messagesSnapshot = await database
    .ref("/chats/" + chatId)
    .orderByChild("time")
    .once("value");
  const messages = messagesSnapshot.val();
  return messages;
};

// get all messages from a chatId
const getMessages = async (chatId) => {
  const messagesSnapshot = await database
    .ref("/chats/" + chatId)
    .orderByChild("time")
    .once("value");
  const messages = messagesSnapshot.val();
  return messages;
};

// Socket.io event handlers
io.on("connection", async (socket) => {
  logger.info("A user connected");

  // Fetch and store the list of users
  const fetchedUsers = await fetchUsers();
  // set all users variable
  users = fetchedUsers;
  // console.log("users: ", users);
  // socket.emit("users", users);

  // Rest of the event handlers
  socket.on("setUsername", handleSetUsername(socket));
  socket.on("disconnect", () => {
    clientMap.delete(socket.username);
    logger.info("A user disconnected");
  });

  socket.on("addContact", handleSaveContacts(socket));
  socket.on("getContacts", handleGetContacts(socket));
  socket.on("sendTo", handleSendTo(socket));
  socket.on("connectTo", handleConnectTo(socket));
  socket.on("getMessages", handleGetMessages(socket));
});

server.listen(3000, () => {
  logger.info("Server listening on port 3000");
});

// A- true
