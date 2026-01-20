# 🔌 IoT Lab Core

> Uma arquitetura robusta e escalável baseada em microsserviços para orquestração de dispositivos IoT, coleta de dados telemétricos e visualização em tempo real.

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-Async-009688?logo=fastapi&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)
![Streamlit](https://img.shields.io/badge/Dashboard-Live-FF4B4B?logo=streamlit&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

## 📖 Sobre o Projeto

Este projeto nasceu da necessidade de criar um backend profissional para protótipos de robótica educacional (como sistemas de irrigação e estações meteorológicas), baseado em experiências acadêmicas com IoT. O objetivo inicial era resolver o problema da **heterogeneidade de sensores**, utilizando uma modelagem relacional flexível (`Device` ↔ `Measurement` ↔ `SensorType`) para padronizar a coleta de dados.

O que começou como um suporte acadêmico evoluiu para o **IoT Lab Core**: uma solução *backend-first* robusta para orquestração de dispositivos. Diferente de protótipos convencionais, esta plataforma adota uma arquitetura de microsserviços containerizados, focando em quatro pilares industriais:

1.  **Integridade de Dados:** Modelagem relacional robusta (PostgreSQL) com suporte a auditoria e *Soft Delete*.
2.  **Tempo Real:** Comunicação *Full-Duplex* via WebSockets para monitoramento sem latência.
3.  **Segurança:** Controle de acesso baseado em tokens (JWT) e validação rigorosa de ingestão (*Gatekeeper Pattern*).
4.  **Escalabilidade:** Núcleo 100% assíncrono (`async/await`) para suportar alta concorrência de sensores.

O sistema é agnóstico ao hardware, sendo compatível com ESP32, Arduino, Raspberry Pi ou qualquer dispositivo capaz de realizar requisições HTTP/MQTT.

---

## 🏗️ Arquitetura Técnica

O sistema opera sobre uma infraestrutura dockerizada, organizada em camadas lógicas para garantir desacoplamento e escalabilidade:

1.  **Camada de Coleta (Edge):**
    Dispositivos físicos (como ESP32) e simuladores operam na ponta, enviando leituras telemétricas (temperatura, umidade, etc.) para o Backend via requisições HTTP POST.

2.  **Núcleo de Processamento (Core Backend):**
    * **API Gateway & Lógica:** Desenvolvida em **FastAPI**, atua como o cérebro do sistema. Graças ao suporte nativo a `async/await`, ela gerencia a ingestão de dados e as regras de negócio sem bloquear o processamento (Non-blocking I/O).
    * **Persistência:** Os dados validados são armazenados no **PostgreSQL**, acessado via driver assíncrono (`asyncpg`) para garantir performance máxima em operações de escrita intensa.

3.  **Camada de Apresentação (Frontend):**
    O Dashboard **Streamlit** consome a API de duas formas distintas:
    * **Monitoramento Live:** Estabelece um túnel **WebSocket** persistente com o Backend, recebendo atualizações instantâneas (push) assim que um dispositivo com sensor envia um dado.
    * **Análise Histórica:** Realiza chamadas HTTP GET otimizadas para gerar relatórios e gráficos de longo prazo.

4.  **Segurança e Rede:**
    Todo o tráfego interno ocorre dentro de uma rede Docker isolada. O acesso externo de gestores ao Dashboard é protegido via autenticação **JWT** (JSON Web Tokens), garantindo rastreabilidade e controle de acesso.

### Stack Tecnológico

* **Backend:** FastAPI, Uvicorn, Pydantic v2.
* **Persistência:** SQLModel (SQLAlchemy Core), PostgreSQL, Alembic (Migrações).
* **Assincronismo:** `asyncpg` (Driver de Banco), `asyncio`.
* **Frontend:** Streamlit, Altair (Visualização de Dados), Pandas.
* **Segurança:** OAuth2 com Password Flow, JWT (JSON Web Tokens), BCrypt.
* **DevOps:** Docker, Docker Compose.

---

## ✨ Funcionalidades Chave

### 1. Gestão de Dispositivos e Sensores
* **Catálogo Flexível:** Cadastro dinâmico de tipos de sensores (Temp, Umidade, CO2, etc) com unidades de medida customizáveis.
* **Provisionamento:** Vínculo lógico entre Dispositivos e Sensores (N:N). A API rejeita dados se o dispositivo não tiver o sensor "instalado" logicamente.
* **Ciclo de Vida (Soft Delete):** Arquivamento lógico de dispositivos e sensores, preservando o histórico de dados para auditoria.

### 2. Monitoramento em Tempo Real
* **Painel Live:** Utiliza WebSockets para transmitir dados do sensor para a tela em milissegundos.
* **UX Reativa:** Indicadores de "Heartbeat" (última conexão) e Sparklines para visualização de tendência imediata.
* **Buffer Inteligente:** Sistema híbrido que carrega histórico recente via API e mantém atualização via Socket.

### 3. Analytics e Business Intelligence
* **Análise Histórica:** Filtros por período customizável com agregação de dados no Backend.
* **Visualização Rica:** Gráficos interativos (Altair) com camadas de média, mínima e máxima.
* **Exportação:** Capacidade de gerar relatórios em CSV para auditoria externa.

### 4. Segurança e Controle
* **Autenticação JWT:** Proteção de rotas administrativas (CRUD).
* **Gatekeeper de Ingestão:** Validação de tokens e status de ativo/inativo antes da persistência de qualquer medição.

---

## 🚀 Como Executar

### Pré-requisitos
* Docker Engine 20.10+
* Docker Compose v2+

### Instalação

1.  **Clone o repositório:**
    ```bash
    git clone [https://github.com/Marcelo-Gallo/iot-lab-core.git](https://github.com/Marcelo-Gallo/iot-lab-core.git)
    cd iot-lab-core
    ```

2.  **Configure as Variáveis de Ambiente:**
    Crie um arquivo `.env` na raiz baseado no exemplo abaixo:
    ```ini
    POSTGRES_USER=admin_iot
    POSTGRES_PASSWORD=segredo_iot
    POSTGRES_DB=iot_db
    DATABASE_URL=postgresql+asyncpg://admin_iot:segredo_iot@db:5432/iot_db
    SECRET_KEY=sua_chave_secreta_super_segura_gerada_com_openssl
    ALGORITHM=HS256
    ACCESS_TOKEN_EXPIRE_MINUTES=30
    ```

3.  **Inicie os Serviços:**
    ```bash
    docker-compose up --build -d
    ```

4.  **Acesse a Aplicação:**
    * **Dashboard:** [http://localhost:8501](http://localhost:8501)
    * **Documentação API (Swagger):** [http://localhost:8000/docs](http://localhost:8000/docs)

> **Nota:** No primeiro acesso, o sistema criará automaticamente um usuário administrador padrão (verifique os logs ou a documentação interna para credenciais iniciais).

---

## 🗺️ Roadmap de Evolução (v4.0+)

O projeto encontra-se em constante evolução para atender requisitos de segurança governamental e escalabilidade industrial. O planejamento estratégico divide-se em fases:

### 🚩 Fase 1: Segurança e Rastreabilidade
Foco em proteger a integridade dos dados e identificar ações no sistema.
- [ ] **Device API Keys:** Implementação de tokens estáticos de autenticação para dispositivos físicos (evitando credenciais de usuário em firmware). Preparado para suporte futuro a tokens rotativos.
    - Rotatividade live, sem necessidade de conexão USB.
    - Atualização de código via rádio e/ou Bluetooth.
    - Infraestrutura LoRa avaliada como viabilizadora.
- [ ] **Simulador 3.0:** Refatoração dos scripts de simulação (`simulator.py`) para suportar autenticação via tokens e emular múltiplos dispositivos autenticados simultaneamente.
- [ ] **Audit Logs:** Sistema de auditoria persistente para rastrear todas as operações de escrita (quem criou/editou/excluiu), garantindo *accountability*.

### 🚩 Fase 2: Gestão de Acesso e Governança
Refinamento dos papéis de usuário para operação em larga escala.
- [ ] **RBAC (Role-Based Access Control):** Hierarquia de permissões (Leitor, Operador, Admin, SuperAdmin).
- [ ] **Self-Signup Moderado:** Fluxo de cadastro autônomo com aprovação posterior.
- [ ] **Política de Senhas:** Troca obrigatória de credenciais no primeiro acesso.

### 🚩 Fase 3: Inteligência de Dados (Business Intelligence)
Transformação de dados brutos em informação calibrada.
- [ ] **Motor de Calibração Híbrido:**
    - Suporte a armazenamento dual: Dado Bruto (Raw) + Dado Processado.
    - Fórmulas de correção linear ($y = ax + b$) configuráveis por tipo de sensor.
    - Processamento opcional (bypass para sensores digitais pré-calibrados).
- [ ] **Analytics de Imutabilidade:** Garantia de visualização histórica para sensores arquivados (Soft Delete).

### 🚩 Fase 4: Experiência do Usuário (UX/UI)
- [ ] **Interface Unificada:** Gestão de vínculos de sensores integrada ao modal de edição de dispositivos.
- [ ] **Identidade Visual:** Representação gráfica (ícones/ASCII) dos modelos de hardware nos cards de monitoramento.

### 🚩 Fase 5: Expansão de Hardware e Conectividade (R&D)
Pesquisa e desenvolvimento para reduzir a dependência física de manutenção e ampliar o alcance.
- [ ] **OTA Segura (Over-The-Air):** Implementação de atualizações de firmware e rotação de credenciais via rádio (LoRa) ou Bluetooth, eliminando a necessidade de conexão USB presencial para manutenção de segurança.
- [ ] **Rede Mesh:** Avaliação de topologias descentralizadas para locais sem cobertura Wi-Fi.
---

## 🤝 Contribuição

Sinta-se à vontade para abrir Issues ou enviar Pull Requests. Este é um projeto educativo focado em boas práticas de Engenharia de Software aplicadas a IoT.

**Autor:** Gallo
