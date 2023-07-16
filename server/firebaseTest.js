var admin = require("firebase-admin");
require("dotenv").config();

// var serviceAccount = require("./serviceAccount.json");
// convert to json
const serviceAccount = JSON.parse(process.env.GOOGLE_SERVICE_ACCOUNT);
admin.initializeApp({
    credential: admin.credential.cert(serviceAccount),
    databaseURL:
        process.env.FIREBASE_DATABASE_URL,
});

const database = admin.database();
const auth = admin.auth();

module.exports = { database, auth };