const generateChatId = (userId1, userId2) => {
  const chatId =
    userId1 > userId2 ? `${userId1}-${userId2}` : `${userId2}-${userId1}`;
  return chatId;
};

// default export 
module.exports = {
    generateChatId,
}
