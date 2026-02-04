import { createContext, useState, useEffect } from "react";
import api from "../services/api";

export const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
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
  };

  return (
    <AuthContext.Provider
      value={{ authenticated: !!user, user, loading, login, logout }}
    >
      {children}
    </AuthContext.Provider>
  );
};