import pytest
from controller import app, socketio

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as c:
        with c.session_transaction() as sess:
            sess['authenticated'] = True
        yield c

@pytest.fixture
def socket_client():
    app.config['TESTING'] = True
    return socketio.test_client(app)

def test_login_status(client):
    r = client.get('/api/auth/status')
    assert r.status_code == 200

def test_command_injection_blocked(client):
    resp = client.post('/api/agents/test_agent/execute', json={'command': 'rm -rf /'})
    assert resp.status_code in (403, 400, 404)

def test_agent_connect(socket_client):
    socket_client.emit('agent_connect', {'agent_id': 'test_agent', 'platform': 'windows'})
    received = socket_client.get_received()
    assert isinstance(received, list)
