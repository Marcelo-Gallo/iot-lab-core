import { createContext, useState, useEffect, useContext } from "react";
import api from "../services/api";

export const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  // 1. Estado para guardar o Token bruto (necessário para o WebSocket)
  const [token, setToken] = useState(localStorage.getItem("@IoTLab:token")); 
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const interceptorId = api.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          logout();
        }
        return Promise.reject(error);
      }
    );

    return () => {
      api.interceptors.response.eject(interceptorId);
    };
  }, []);

  const fetchUserMe = async () => {
    try {
      const response = await api.get("/login/me");
      setUser(response.data);
    } catch (error) {
      logout();
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const recoveredToken = localStorage.getItem("@IoTLab:token");

    if (recoveredToken) {
      api.defaults.headers.Authorization = `Bearer ${recoveredToken}`;
      setToken(recoveredToken); // Garante sincronia ao recarregar página
      fetchUserMe();
    } else {
      setLoading(false);
    }
  }, []);

  const login = async (username, password) => {
    const formData = new URLSearchParams();
    formData.append("username", username);
    formData.append("password", password);

    try {
      const response = await api.post("/login/access-token", formData, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
      });

      const { access_token } = response.data;

      localStorage.setItem("@IoTLab:token", access_token);
      api.defaults.headers.Authorization = `Bearer ${access_token}`;
      
      // 2. Atualiza o estado do token imediatamente após login
      setToken(access_token);
      
      await fetchUserMe();
      
      return { success: true };
    } catch (error) {
      return { 
        success: false, 
        message: error.response?.data?.detail || "Falha na comunicação" 
      };
    }
  };

  const logout = () => {
    localStorage.removeItem("@IoTLab:token");
    api.defaults.headers.Authorization = undefined;
    setUser(null);
    setToken(null); // 3. Limpa o token ao sair
  };

  return (
    <AuthContext.Provider
      // 4. Expõe 'token' para os componentes filhos (Dashboard)
      value={{ authenticated: !!user, user, token, loading, login, logout }}
    >
      {children}
    </AuthContext.Provider>
  );
};

// Hook personalizado para facilitar o uso (compatível com o Dashboard.jsx)
export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}