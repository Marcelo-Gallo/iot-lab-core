import { createContext, useState, useEffect } from "react";
import api from "../services/api";

export const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Ao recarregar a página, verifica se já existe token salvo
    const recoveredToken = localStorage.getItem("@IoTLab:token");

    if (recoveredToken) {
      api.defaults.headers.Authorization = `Bearer ${recoveredToken}`;
      // Opcional: Aqui você poderia bater num endpoint /me para validar o token
      setUser({ token: recoveredToken }); 
    }

    setLoading(false);
  }, []);

  const login = async (username, password) => {
    // FastAPI espera Form Data
    const formData = new URLSearchParams();
    formData.append("username", username); // O campo DEVE ser 'username', mesmo que seja email
    formData.append("password", password);

    try {
      const response = await api.post("/login/access-token", formData, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded' // Forçando explicitamente
        }
      });

      const { access_token } = response.data;

      localStorage.setItem("@IoTLab:token", access_token);
      api.defaults.headers.Authorization = `Bearer ${access_token}`;
      setUser({ token: access_token, username });
      
      return { success: true };
    } catch (error) {
      console.error("Erro detalhado do Login:", error.response?.data);
      return { 
        success: false, 
        message: error.response?.data?.detail || "Falha na comunicação com o servidor" 
      };
    }
  };

  const logout = () => {
    localStorage.removeItem("@IoTLab:token");
    api.defaults.headers.Authorization = null;
    setUser(null);
  };

  return (
    <AuthContext.Provider
      value={{ authenticated: !!user, user, loading, login, logout }}
    >
      {children}
    </AuthContext.Provider>
  );
};