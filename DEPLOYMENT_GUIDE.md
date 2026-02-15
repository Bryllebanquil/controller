# Deployment Configuration for Low-Latency Hosting

## Recommended Hosting Providers

### 1. Fly.io (Recommended for WebSockets)
- **Region**: Choose closest to your users (sin, nrt, sjc)
- **Always-on**: Prevents cold starts
- **WebSocket support**: Native and optimized
- **Pricing**: Pay-per-use, very affordable

```bash
# Install flyctl
curl -L https://fly.io/install.sh | sh

# Create app
fly launch --name fastapi-control-server --region sin

# Configure fly.toml
```

### 2. Railway (Alternative)
- **Auto-scaling**: Handles traffic spikes
- **WebSocket support**: Good
- **Pricing**: Free tier available

### 3. VPS Providers (Best performance)
- **DigitalOcean**: Singapore, Bangalore regions
- **Linode**: Tokyo, Singapore
- **Vultr**: Tokyo, Singapore

## Fly.io Configuration (fly.toml)

```toml
app = "fastapi-control-server"
primary_region = "sin"

[build]
  dockerfile = "Dockerfile"

[env]
  REDIS_URL = "redis://redis.internal:6379"
  LOG_LEVEL = "info"
  WEBSOCKET_PING_INTERVAL = "30"
  WEBSOCKET_PING_TIMEOUT = "10"

[[services]]
  internal_port = 8000
  protocol = "tcp"
  auto_stop_machines = false  # Keep always-on
  auto_start_machines = true
  min_machines_running = 1
  
  [[services.ports]]
    port = 80
    handlers = ["http"]
    force_https = true
  
  [[services.ports]]
    port = 443
    handlers = ["tls", "http"]
  
  [[services.tcp_checks]]
    interval = "30s"
    timeout = "10s"
    grace_period = "5s"
    restart_limit = 3

[[mounts]]
  source = "redis_data"
  destination = "/data"
```

## Redis Configuration for Low Latency

```bash
# Redis configuration for Fly.io
maxmemory 512mb
maxmemory-policy allkeys-lru
tcp-keepalive 300
timeout 0
tcp-backlog 511
```

## Performance Optimization Settings

### FastAPI/Uvicorn
```python
# In fastapi_server.py
uvicorn.run(
    "fastapi_server:app",
    host="0.0.0.0",
    port=8000,
    workers=1,  # Single worker for WebSocket state
    loop="uvloop",  # Faster event loop
    http="httptools",  # Faster HTTP parser
    ws="websockets",  # Native WebSocket implementation
    log_level="info",
    access_log=False,  # Disable access logs for performance
    timeout_keep_alive=30,
    timeout_notify=30,
    limit_max_requests=1000,  # Prevent memory leaks
    limit_concurrency=100,  # WebSocket connection limit
    backlog=2048  # Connection backlog
)
```

### WebSocket Optimization
```python
# Connection settings
WEBSOCKET_PING_INTERVAL = 30  # Keep connections alive
WEBSOCKET_PING_TIMEOUT = 10   # Timeout for ping responses
WEBSOCKET_MAX_SIZE = 10 * 1024 * 1024  # 10MB max message size
WEBSOCKET_MAX_QUEUE = 100  # Max queued messages per connection
```

## Deployment Commands

```bash
# Deploy to Fly.io
fly deploy --build-arg REDIS_URL=redis://redis.internal:6379

# Scale up for production
fly scale count 2 --region sin,nrt

# Set secrets
fly secrets set REDIS_PASSWORD=your_redis_password
fly secrets set JWT_SECRET=your_jwt_secret

# View logs
fly logs

# SSH into machine
fly ssh console
```

## Monitoring and Alerting

### Health Checks
- `/health` endpoint for load balancer health checks
- Redis connection monitoring
- WebSocket connection count tracking

### Metrics to Monitor
1. **Connection latency**: Time to establish WebSocket
2. **Message latency**: Command -> response time
3. **Connection count**: Active WebSocket connections
4. **Error rate**: Failed connections/commands
5. **Memory usage**: Redis and application memory
6. **CPU usage**: Application CPU utilization

### Alert Thresholds
- Connection latency > 1000ms
- Message latency > 500ms
- Error rate > 5%
- Memory usage > 80%
- CPU usage > 90%

## Cost Optimization

### Fly.io Pricing (approximate)
- **Always-on machine**: ~$1.94/month
- **Redis**: ~$15/month for 1GB
- **Bandwidth**: $0.02/GB
- **Total**: ~$20-30/month for small deployment

### Scaling Strategy
1. Start with 1 machine + Redis
2. Scale horizontally when > 1000 concurrent connections
3. Use Redis Cluster for > 10k agents
4. Consider CDN for static assets

## Security Best Practices

1. **WebSocket Authentication**: JWT tokens
2. **Rate Limiting**: Per-IP and per-agent limits
3. **Input Validation**: Strict validation of all messages
4. **Encryption**: TLS 1.3 for all connections
5. **Network Isolation**: Private networks for Redis
6. **Monitoring**: Log all security events

## Backup and Recovery

### Redis Backup
```bash
# Automated backup every 6 hours
fly volumes snapshots list redis_data
fly volumes snapshots create redis_data
```

### Application State
- All state stored in Redis (ephemeral)
- Agents reconnect automatically
- No persistent application state needed