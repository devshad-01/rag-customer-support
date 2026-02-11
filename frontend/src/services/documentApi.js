import api from "./api";

export async function uploadDocument(file) {
  const formData = new FormData();
  formData.append("file", file);
  const { data } = await api.post("/documents/", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function getDocuments(page = 1, limit = 20) {
  const { data } = await api.get("/documents/", { params: { page, limit } });
  return data;
}

export async function getDocument(id) {
  const { data } = await api.get(`/documents/${id}`);
  return data;
}

export async function deleteDocument(id) {
  const { data } = await api.delete(`/documents/${id}`);
  return data;
}
