import api from "./api";

export async function sendMessage(conversationId, message) {
  const { data } = await api.post(`/chat/${conversationId}/message`, { content: message });
  return data;
}

export async function getConversations() {
  const { data } = await api.get("/chat/");
  return data;
}

export async function createConversation(title) {
  const { data } = await api.post("/chat/", { title });
  return data;
}

export async function getMessages(conversationId) {
  const { data } = await api.get(`/chat/${conversationId}/messages`);
  return data;
}

export async function deleteConversation(conversationId) {
  await api.delete(`/chat/${conversationId}`);
}

export async function clearAllConversations() {
  await api.delete("/chat/");
}
