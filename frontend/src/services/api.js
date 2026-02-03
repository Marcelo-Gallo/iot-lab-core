import axios from 'axios';

// Cria uma instância do Axios com a URL base da API
const api = axios.create({
  // O Vite expõe variáveis de ambiente com o prefixo VITE_
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor de Resposta
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error("❌ Erro na API (Interceptor):", error.response || error.message);
    return Promise.reject(error);
  }
);

export default api;