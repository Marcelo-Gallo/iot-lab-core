from fastapi.testclient import TestClient

def test_health_check(client: TestClient):
    # Ação: Bater na rota raiz
    response = client.get("/")
    
    # Verificação (Assert): O status é 200 OK?
    assert response.status_code == 200
    
    # Verificação: O JSON é o esperado?
    assert response.json() == {"status": "ok", "mensagem": "Sistema operando em normalidade"}