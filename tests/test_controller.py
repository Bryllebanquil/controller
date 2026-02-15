import pytest
import sys
import os
import importlib.util

# Ensure eventlet monkey patching is disabled during tests to avoid lock issues
os.environ.setdefault('EVENTLET_MONKEY_PATCH', '0')
# Force threading async mode for Socket.IO in tests
os.environ.setdefault('SOCKET_ASYNC_MODE', 'threading')
# Use in-memory SQLite for fast, side-effect-free tests
os.environ.setdefault('DATABASE_URL', 'sqlite:///:memory:')

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

try:
    from controller import app, socketio
except ModuleNotFoundError:
    spec = importlib.util.spec_from_file_location("controller", os.path.join(ROOT_DIR, "controller.py"))
    controller = importlib.util.module_from_spec(spec)
    loader = spec.loader
    if loader is None:
        raise
    loader.exec_module(controller)
    app = controller.app
    socketio = controller.socketio

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
