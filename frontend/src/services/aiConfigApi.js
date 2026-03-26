import api from "./api";

export async function getAiConfig() {
  const { data } = await api.get("/ai-config/");
  return data;
}

export async function updateAiConfig(payload) {
  const { data } = await api.put("/ai-config/", payload);
  return data;
}
