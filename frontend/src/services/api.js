import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor de Resposta
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      console.warn("🔒 Sessão expirada ou inválida. Fazendo logout...");
      
      localStorage.removeItem("@IoTLab:token");
      
      if (window.location.pathname !== "/login") {
         window.location.href = "/login";
      }
    }

    console.error("❌ Erro na API:", error.response || error.message);
    return Promise.reject(error);
  }
);

export default api;