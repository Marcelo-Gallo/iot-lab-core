import { useState, useContext } from "react";
import { AuthContext } from "../context/AuthContext";
import { useNavigate } from "react-router-dom";

export default function Login() {
  const [email, setEmail] = useState(""); 
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  const { login } = useContext(AuthContext);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError("");

    // O login espera (username, password). 
    // No backend FastAPI padrão, o campo se chama 'username' mesmo sendo email.
    const result = await login(email, password);

    if (result.success) {
      navigate("/");
    } else {
      setError("Credenciais inválidas. Tente novamente.");
      setIsSubmitting(false);
    }
  };

  return (
    // Fundo da tela (Cinza claro)
    <div className="min-h-screen flex items-center justify-center bg-gray-100 p-4">
      
      {/* Card Principal */}
      <div className="w-full max-w-md bg-white rounded-xl shadow-2xl overflow-hidden transform transition-all hover:scale-[1.01]">
        
        {/* Cabeçalho do Card (Azul IoT) */}
        <div className="bg-iot-primary p-8 text-center">
          <h2 className="text-3xl font-bold text-white tracking-wide">📡 IoT Lab</h2>
          <p className="text-iot-light text-opacity-90 mt-2 text-sm uppercase tracking-wider font-semibold">
            Painel de Controle
          </p>
        </div>

        {/* Corpo do Formulário */}
        <div className="p-8 pt-10">
          <form onSubmit={handleSubmit} className="space-y-6">
            
            {/* Campo Email */}
            <div>
              <label className="block text-sm font-bold text-gray-600 mb-2 uppercase text-xs tracking-wider">
                Usuário / Email
              </label>
              <input
                type="text"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="admin@example.com"
                className="w-full px-4 py-3 border border-gray-300 rounded-lg text-gray-700 focus:ring-2 focus:ring-iot-primary focus:border-transparent outline-none transition-all bg-gray-50 focus:bg-white"
                required
              />
            </div>

            {/* Campo Senha */}
            <div>
              <div className="flex justify-between items-center mb-2">
                <label className="block text-sm font-bold text-gray-600 uppercase text-xs tracking-wider">
                  Senha
                </label>
              </div>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full px-4 py-3 border border-gray-300 rounded-lg text-gray-700 focus:ring-2 focus:ring-iot-primary focus:border-transparent outline-none transition-all bg-gray-50 focus:bg-white"
                required
              />
            </div>

            {/* Mensagem de Erro (Aparece condicionalmente) */}
            {error && (
              <div className="bg-red-50 border-l-4 border-red-500 p-4 rounded-r">
                <div className="flex">
                  <div className="flex-shrink-0">
                    <svg className="h-5 w-5 text-red-500" viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                    </svg>
                  </div>
                  <div className="ml-3">
                    <p className="text-sm text-red-700 font-medium">{error}</p>
                  </div>
                </div>
              </div>
            )}

            {/* Botão de Submit */}
            <button
              type="submit"
              disabled={isSubmitting}
              className={`w-full py-3 px-4 rounded-lg text-white font-bold text-lg shadow-md transition-all duration-200
                ${isSubmitting 
                  ? 'bg-gray-400 cursor-not-allowed' 
                  : 'bg-iot-primary hover:bg-blue-600 hover:shadow-lg active:scale-95'
                }`}
            >
              {isSubmitting ? "Autenticando..." : "Entrar no Sistema"}
            </button>
          </form>
        </div>
        
        {/* Rodapé do Card */}
        <div className="bg-gray-50 px-8 py-4 border-t border-gray-100 text-center">
          <p className="text-xs text-gray-400 font-medium">
            IoT Lab Core &copy; 2026
          </p>
        </div>

      </div>
    </div>
  );
}