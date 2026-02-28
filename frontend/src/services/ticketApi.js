import api from "./api";

export async function getTickets({ page = 1, limit = 20, status, priority } = {}) {
  const params = { page, limit };
  if (status) params.status = status;
  if (priority) params.priority = priority;
  const { data } = await api.get("/tickets/", { params });
  return data;
}

export async function getTicket(id) {
  const { data } = await api.get(`/tickets/${id}`);
  return data;
}

export async function createTicket(ticketData) {
  const { data } = await api.post("/tickets/", ticketData);
  return data;
}

export async function updateTicket(id, updates) {
  const { data } = await api.patch(`/tickets/${id}`, updates);
  return data;
}

export async function respondToTicket(id, response) {
  const { data } = await api.post(`/tickets/${id}/respond`, { content: response });
  return data;
}

export async function deleteTicket(id) {
  await api.delete(`/tickets/${id}`);
}
