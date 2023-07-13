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



const handleLogin = async (socket, data) => {
  // Extract the necessary data
  const { username, email } = data;

  try {
    socket.emit("userSet", { username: username });

    // Update the user list and socket properties
    socket.username = username;
    clientMap.set(socket.username, socket.id);

  } catch (error) {

    socket.emit("userExists", `Error: ${error.message}! Try again.`);
  }
};

// Handle the "setUsername" event
const handleSetUsername = (socket) => (data) => {
  handleLogin(socket, data);
};
const handleSendTo = (socket) => (data) => {

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

const handleGetContacts = (socket) => async (data) => {
  username = data.username;
  try {
    const contactsSnapshot = await database
      .ref("/contacts/" + username)
      .once("value");
    const contacts = contactsSnapshot.val();
    socket.emit("contacts", contacts);
  } catch (error) {
    socket.emit("contacts", null);
  }
};

const handleConnectTo = (socket) => (data) => {
  //   print user and clientMap
  console.log("clientMap: ", clientMap);

  const clientId = clientMap.get(data.to);
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

  if (data === null || data === undefined) {
    socket.emit("message", {
      from: "Server",
      msg: `Error: ${data}! Try again.`,
    });
    return;
  }
  if (users.includes(data.from.username)) {
    // if the contact is not in the users list
    if (!users.includes(data.contact.username)) {
      socket.emit("message", {
        from: "Server",
        msg: `User ${data.contact.username} not found`,
      });
        `Error: User ${data.contact.username}, ${socket.id} not found`
      );
      return;
    }
    // if the contact is in the users list
    const contactRef = database.ref("/contacts/" + data.from.username);
    contactRef.child(data.contact.username).set({
      name: data.contact.name,
      username: data.contact.username,
    });
    socket.emit("message", {
      from: "Server",
      msg: `User ${data.contact.username} added`,
    });
  } else {
    socket.emit("message", {
      from: "Server",
      msg: `User ${data.from.username} not found`,
    });
    winston.error(`Error: User ${data.from.username}, ${socket.id} not found`);
  }
};

const handleGetMessages = (socket) => async (data) => {

  const chatId = generateChatId(data.from, data.to);

  try {
    const messages = await fetchMessageHistory(chatId);
    socket.emit("serverResponse", messages);
  } catch (error) {
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

    const users = usersData.map((user) => user.email);
    // console.log("userData: ", usersData);
    // console.log("users: ", users);
    return users;
  } catch (error) {
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

// add a middleware
io.use(async (socket, next) => {
  // Fetch and store the list of users
  // const fetchedUsers = await fetchUsers();
  // // set all users variable
  // users = fetchedUsers;

  // wait for 5 seconds

  const token = socket.handshake.auth.token;
  // verify token
  if (!token) {
    return next(new Error("invalid token"));
  } else {
    // verify token
    try {
      const decodedToken = await auth.verifyIdToken(token);

      // get usernaem and email from decoded token
      const { name, email, email_verified } = decodedToken;
      if (!email_verified) {
        // Throw an HttpsError so that the client gets the error details.
        return next(new Error("email not verified"));
      }

      // fetch /users/{uid} from realtime database, it contains username
      const userSnapshot = await database
        .ref("/users/" + decodedToken.uid)
        .once("value");
      const userData = userSnapshot.val();
      const username = userData['name']

      if (!username) {
        return next(new Error("invalid username"));
      }

      // store username in socket
      handleSetUsername(socket)({
        username: username,
        email: email,
      });
    } catch (error) {
      console.log("Error verifying token:", error);
      return next(new Error("invalid token"));
    }
  }
  next();
});

// Socket.io event handlers
io.on("connection", async (socket) => {
  logger.info("A user connected");
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
});
