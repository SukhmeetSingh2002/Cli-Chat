var admin = require("firebase-admin");
require("dotenv").config();

// var serviceAccount = require("./serviceAccount.json");
// convert to json
const serviceAccount = JSON.parse(process.env.GOOGLE_SERVICE_ACCOUNT);
admin.initializeApp({
    credential: admin.credential.cert(serviceAccount),
    databaseURL:
        process.env.FIREBASE_DATABASE_URL,
    storageBucket: process.env.FIREBASE_STORAGE_BUCKET,
});

const database = admin.database();
const auth = admin.auth();
const storage = admin.storage();
const bucket = storage.bucket();

module.exports = { database, auth , bucket};