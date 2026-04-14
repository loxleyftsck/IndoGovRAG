# 🚀 PRODUCTION SCALE-UP STRATEGY

**Tanggal:** 11 Januari 2026  
**Tujuan:** Scale dari dev/beta → Production (10x-100x traffic)  
**Target:** Handle 100,000+ queries/day

---

## 🎯 Current State vs Target

### Current (Development/Beta)

```yaml
Traffic: ~100 queries/day
Users: 1-5 concurrent
Infrastructure: Single instance (localhost)
Cache: In-memory (volatile)
Database: ChromaDB (single node)
Monitoring: Local logs only
Availability: ~95% (dev machine)
Cost: $0 (Ollama local)

Bottlenecks:
  - Single point of failure
  - No horizontal scaling
  - Cache lost on restart
  - Limited monitoring
```

### Target (Production)

```yaml
Traffic: 100,000 queries/day (~70 queries/min)
Users: 50-100 concurrent
Infrastructure: Multi-instance (cloud)
Cache: Redis cluster (persistent)
Database: ChromaDB distributed
Monitoring: Full observability stack
Availability: 99.5% (cloud SLA)
Cost: ~$200-500/month (cloud + Redis)

Requirements:
  ✅ Horizontal scaling
  ✅ High availability
  ✅ Persistent cache
  ✅ Real-time monitoring
  ✅ Auto-scaling
```

---

## 📊 Scaling Dimensions

### 1. Vertical Scaling (Scale UP)

**Current Hardware:**

- CPU: Ryzen 7 7840HS (8 cores)
- RAM: 24 GB (12.9 GB used)
- GPU: RTX 3050 6GB (not used)

**Upgrade Path:**

```
Level 1: Current (Dev)
  - 8 cores, 24GB RAM
  - Capacity: ~100 q/day
  - Cost: $0 (owned)

Level 2: Small Cloud VM
  - 16 vCPUs, 64GB RAM
  - Capacity: ~1,000 q/day
  - Cost: ~$100/month
  - Provider: AWS t3.2xlarge, GCP n2-standard-16

Level 3: Medium Cloud VM
  - 32 vCPUs, 128GB RAM
  - Capacity: ~10,000 q/day
  - Cost: ~$300/month
  - Provider: AWS m5.8xlarge, GCP n2-standard-32

Level 4: Large Cloud VM (Overkill)
  - 64+ vCPUs, 256GB RAM
  - Capacity: ~50,000 q/day
  - Cost: ~$800/month
```

**Recommendation:** Level 2 (16 vCPUs, 64GB) for 100K queries/day ✅

---

### 2. Horizontal Scaling (Scale OUT)

**Architecture: Multi-Instance API + Shared Cache**

```
                    [Load Balancer]
                          |
        +-----------------+-----------------+
        |                 |                 |
    [API Instance 1]  [API Instance 2]  [API Instance 3]
        |                 |                 |
        +--------[Redis Cache Cluster]------+
                          |
                  [ChromaDB Vector DB]
                          |
                   [Document Storage]
```

**Configuration:**

```yaml
API Instances: 3-5 instances
  - Each: 8 vCPUs, 16GB RAM
  - Auto-scaling: 3-10 instances based on load
  - Load balancer: Nginx or cloud LB

Redis Cluster: 3-node cluster
  - Master: 8GB RAM (cache)
  - 2 Replicas: High availability
  - Persistence: RDB + AOF

ChromaDB: Distributed mode
  - 3-node cluster
  - Sharding: By document type
  - Replication: 2x

Ollama: Shared model server
  - Dedicated instance: 16 vCPUs, 32GB RAM
  - Model: Llama 3.1 Q4 (4.9GB)
  - API endpoint: Internal network
```

**Benefits:**

- ✅ No single point of failure
- ✅ Can handle spikes (auto-scale)
- ✅ Zero-downtime deployments
- ✅ Geographic distribution (future)

---

### 3. Cache Optimization (Scale SMART)

**Current: In-Memory Cache**

```
Pros: Very fast (30ms)
Cons: Lost on restart, single instance only
Max Size: ~1000 entries (2.5MB)
```

**Upgrade: Redis Cluster**

```yaml
Configuration:
  - Master: 8GB RAM
  - Replicas: 2 nodes
  - Max Keys: 100,000+ entries
  - Persistence: RDB every 5 min + AOF
  - Eviction: LRU (Least Recently Used)

Performance:
  - Latency: 50-100ms (network overhead)
  - Throughput: 100K ops/sec
  - Hit Rate: 60-70% (vs 52% current)

Cost:
  - Redis Cloud: ~$50/month (8GB)
  - Self-hosted: ~$30/month (VM cost)

Features:
  ✅ Persistent (survives restarts)
  ✅ Shared across API instances
  ✅ Geo-replication ready
  ✅ Atomic operations
```

---

### 4. Database Scaling

**ChromaDB Optimization:**

```yaml
Current: Single node
  - Collections: 1 (all docs)
  - Size: ~50 documents
  - Query time: 2-3s

Production: Distributed
  - Collections: 5 (by type)
    * laws
    * regulations
    * procedures
    * forms
    * general
  - Size: 1000+ documents
  - Query time: <1s (sharding)

Configuration:
  nodes: 3
  replication_factor: 2
  sharding_key: "document_type"
  
Benefits:
  - Parallel queries
  - Faster retrieval
  - Higher capacity
```

---

## 🔧 Implementation Plan

### Phase 1: Foundation (Week 1) ✅ DONE

- [x] Model quantization (Q4)
- [x] Semantic cache (in-memory)
- [x] LLMLingua compression
- [x] Basic monitoring (logs)

### Phase 2: Production Prep (Week 2)

**Goal:** Single-instance production-ready

- [ ] **Activate Redis cache** (2 hours)

  ```bash
  # Install Redis
  docker run -d -p 6379:6379 redis:alpine
  
  # Update config
  cache = SemanticCache(backend="redis")
  ```

- [ ] **Configure Nginx reverse proxy** (1 hour)

  ```nginx
  upstream api_backend {
      server localhost:8000;
      keepalive 32;
  }
  
  server {
      listen 80;
      location / {
          proxy_pass http://api_backend;
          proxy_set_header Host $host;
      }
  }
  ```

- [ ] **Setup PM2 process manager** (30 min)

  ```bash
  pm2 start api/main.py --name indogovrag
  pm2 startup
  pm2 save
  ```

- [ ] **Activate monitoring stack** (1 hour)
  - Prometheus + Grafana
  - Alert rules
  - Dashboards

**Deliverable:** Production-ready single instance ✅

---

### Phase 3: Horizontal Scale (Week 3-4)

**Goal:** Multi-instance cluster

- [ ] **Setup load balancer** (2 hours)
  - Nginx or HAProxy
  - Health checks
  - SSL termination

- [ ] **Deploy 3 API instances** (3 hours)
  - Docker containers
  - Orchestration: Docker Compose or K8s
  - Auto-restart

- [ ] **Redis cluster setup** (2 hours)
  - 1 master + 2 replicas
  - Sentinel for failover
  - Persistence config

- [ ] **Implement session affinity** (1 hour)
  - Sticky sessions (if needed)
  - Shared state in Redis

**Deliverable:** Cluster handling 10K queries/day ✅

---

### Phase 4: Auto-Scaling (Month 2)

**Goal:** Dynamic scaling based on load

- [ ] **Metrics collection** (1 day)
  - CPU, Memory, Latency
  - Queue depth
  - Cache hit rate

- [ ] **Auto-scaling rules** (1 day)

  ```yaml
  scale_up_if:
    - cpu_percent > 70 for 5 minutes
    - avg_latency > 10s for 3 minutes
    - queue_depth > 50
  
  scale_down_if:
    - cpu_percent < 30 for 10 minutes
    - AND queue_depth < 10
  
  min_instances: 2
  max_instances: 10
  ```

- [ ] **Graceful shutdown** (1 day)
  - Drain connections
  - Finish pending requests
  - Update load balancer

**Deliverable:** Auto-scaling cluster (2-10 instances) ✅

---

## 💰 Cost Analysis

### Scenario 1: Self-Hosted Cloud (AWS/GCP)

```
Infrastructure:
  - 3x API instances (t3.large): 3 × $70 = $210/month
  - Redis (r6g.large): $100/month
  - Load Balancer: $20/month
  - Storage (100GB): $10/month
  - Network (1TB): $90/month
  Total: ~$430/month

Capacity: 100,000 queries/day
Cost per query: $0.0001 (very cheap!)
```

### Scenario 2: Managed Services

```
Infrastructure:
  - Google Cloud Run (3 instances): $150/month
  - Redis Cloud (8GB): $50/month
  - Cloud Load Balancer: $20/month
  - Cloud Storage: $20/month
  Total: ~$240/month

Capacity: 100,000 queries/day
Cost per query: $0.00008

Benefits: Less maintenance ✅
```

### Scenario 3: Hybrid (Current + Cloud Cache)

```
Infrastructure:
  - API: Local (existing hardware) = $0
  - Redis Cloud: $50/month
  - CDN/Cloudflare: $20/month
  Total: ~$70/month

Capacity: 10,000 queries/day
Cost per query: $0.0002

Best for: Beta/small production ✅
```

**Recommendation:** Start Scenario 3, scale to Scenario 2 ✅

---

## 📈 Performance Targets

### Latency (P95)

```
Current: 76s (optimized, cache miss)
Target Production:
  - Cache HIT: <100ms (Redis network)
  - Cache MISS: <30s (optimization target)
  - Weighted avg: <10s (70% cache hit rate)

How to achieve:
  - Redis cache (vs in-memory)
  - Parallel retrieval
  - Connection pooling
  - Query batching
```

### Throughput

```
Current: 4.3 queries/min (single instance)
Target Production:
  - Per instance: 10 queries/min
  - 3 instances: 30 queries/min
  - Peak (10 instances): 100 queries/min

Daily capacity: 100 × 60 × 24 = 144,000 queries/day ✅
Exceeds 100K target!
```

### Availability

```
Current: ~95% (dev machine uptime)
Target: 99.5% (allow 3.6 hours downtime/month)

How to achieve:
  - Multi-instance redundancy
  - Health checks
  - Auto-restart (PM2)
  - Failover (Redis Sentinel)
  - Monitoring + alerts
```

### Cache Hit Rate

```
Current: 52% (in-memory)
Target: 70% (persistent Redis)

How to achieve:
  - Persistent storage (survives restart)
  - Cache warming (preload common queries)
  - Longer TTL (14 days vs 7)
  - Smart invalidation
```

---

## 🛠️ Quick Start Implementation

### Step 1: Activate Redis (NOW - 15 min)

```bash
# Install Redis via Docker
docker run -d \
  --name redis-cache \
  -p 6379:6379 \
  -v redis-data:/data \
  redis:alpine redis-server --appendonly yes

# Test connection
redis-cli ping
# Output: PONG ✅
```

**Update Code:**

```python
# src/caching/semantic_cache.py
cache = SemanticCache(
    backend="redis",
    host="localhost",
    port=6379,
    threshold=0.95,
    ttl_days=14  # Longer TTL for production
)
```

**Restart API:**

```bash
# Kill current process
pkill -f "python api/main.py"

# Start with Redis
python api/main.py
```

**Verify:**

```bash
# Check Redis has keys
redis-cli DBSIZE
# Should show cached entries
```

---

### Step 2: Configure Process Manager (10 min)

```bash
# Install PM2
npm install -g pm2

# Create ecosystem file
cat > ecosystem.config.js << 'EOF'
module.exports = {
  apps: [{
    name: 'indogovrag-api',
    script: 'python',
    args: 'api/main.py',
    instances: 1,
    autorestart: true,
    max_memory_restart: '2G',
    env: {
      NODE_ENV: 'production',
      OLLAMA_HOST: 'http://localhost:11434'
    }
  }]
}
EOF

# Start with PM2
pm2 start ecosystem.config.js
pm2 save
pm2 startup
```

---

### Step 3: Basic Load Balancer (15 min)

```nginx
# /etc/nginx/conf.d/indogovrag.conf
upstream indogovrag_backend {
    least_conn;  # Load balancing algorithm
    server localhost:8000 max_fails=3 fail_timeout=30s;
    # Add more instances here when scaling
    # server localhost:8001 max_fails=3 fail_timeout=30s;
    # server localhost:8002 max_fails=3 fail_timeout=30s;
}

server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://indogovrag_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # Buffer
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;
    }
    
    # Health check endpoint
    location /health {
        access_log off;
        proxy_pass http://indogovrag_backend/health;
    }
}
```

```bash
# Reload Nginx
sudo nginx -t
sudo systemctl reload nginx
```

---

## 📊 Monitoring & Metrics

### Key Metrics to Track

```yaml
System Metrics:
  - CPU usage (per instance)
  - Memory usage (per instance)
  - Disk I/O
  - Network bandwidth

Application Metrics:
  - Request rate (queries/min)
  - Latency (P50, P95, P99)
  - Error rate (4xx, 5xx)
  - Cache hit rate

Business Metrics:
  - Active users
  - Query types distribution
  - Peak hours
  - User satisfaction (if feedback enabled)
```

### Dashboards

**Grafana Dashboard Layout:**

```
Row 1: System Health
  - [CPU Usage] [Memory Usage] [Disk I/O]
  
Row 2: Traffic
  - [Requests/min] [Active Users] [Error Rate]
  
Row 3: Performance
  - [P95 Latency] [Cache Hit Rate] [Queue Depth]
  
Row 4: Cache
  - [Redis Memory] [Keys Count] [Evictions]
```

### Alerts

```yaml
Critical (PagerDuty):
  - API down (all instances)
  - Error rate > 10% for 5 min
  - P95 latency > 60s for 10 min
  - Disk space < 10%

Warning (Slack):
  - CPU > 80% for 10 min
  - Memory > 90% for 5 min
  - Cache hit rate < 40% for 1 hour
  - Single instance down
```

---

## ✅ Success Criteria

### Week 2 (Production Ready)

- [ ] Redis cache activated
- [ ] PM2 process manager running
- [ ] Basic monitoring (Prometheus up)
- [ ] 1 instance handling 1000 q/day
- [ ] 99% uptime

### Month 1 (Scaled)

- [ ] 3 API instances
- [ ] Load balancer active
- [ ] Redis cluster (1 master + 2 replicas)
- [ ] Handling 10,000 queries/day
- [ ] 99.5% uptime

### Month 2 (Auto-Scale)

- [ ] Auto-scaling rules implemented
- [ ] 2-10 instances dynamic
- [ ] Handling 100,000 queries/day
- [ ] <10s P95 latency
- [ ] 70% cache hit rate
- [ ] 99.9% uptime

---

## 🚀 Deployment Checklist

### Pre-Deployment

- [ ] All tests passing (97%+)
- [ ] Redis connection tested
- [ ] Monitoring configured
- [ ] Backup strategy defined
- [ ] Rollback plan ready

### Deployment

- [ ] Deploy to staging first
- [ ] Smoke test (10 queries)
- [ ] Load test (100 concurrent)
- [ ] Monitor for 1 hour
- [ ] Deploy to production (10% traffic)
- [ ] Gradual ramp: 10% → 50% → 100%

### Post-Deployment

- [ ] Monitor metrics for 24h
- [ ] Review error logs
- [ ] Verify cache hit rate
- [ ] Check cost vs projection
- [ ] Document lessons learned

---

## 💡 Optimization Opportunities

### Short-term (Week 2-4)

1. **Query batching** - Process multiple queries together
2. **Connection pooling** - Reuse DB connections
3. **Compression** - Gzip API responses
4. **CDN** - Cache static assets

### Medium-term (Month 2-3)

1. **Read replicas** - ChromaDB read scaling
2. **Async processing** - Background jobs for analytics
3. **Edge caching** - CloudFlare for global users
4. **Query optimization** - Index tuning

### Long-term (Month 4-6)

1. **GraphQL** - More efficient data fetching
2. **WebSocket** - Real-time streaming
3. **Multi-region** - Geographic distribution
4. **ML optimization** - Smart routing

---

## 📝 Conclusion

### Current State

- ✅ Optimized single instance
- ✅ 52% cache hit rate
- ✅ 4.3 queries/min capacity
- ✅ A- grade (92%)

### Production Target

- 🎯 Multi-instance cluster
- 🎯 70% cache hit rate
- 🎯 100+ queries/min capacity
- 🎯 A+ grade (98%)
- 🎯 100K queries/day

### Next Steps (Priority Order)

1. **NOW:** Activate Redis cache (15 min)
2. **Today:** Setup PM2 (10 min)  
3. **This Week:** Monitoring activation (1 hour)
4. **Next Week:** Deploy 3 instances
5. **Month 2:** Auto-scaling setup

---

**Ready to Scale!** 🚀

**From:** Single dev instance (100 q/day)  
**To:** Production cluster (100,000 q/day)  
**Timeline:** 2 months gradual scale-up  
**Investment:** ~$70-240/month (cloud costs)

**Let's GO! Time to activate Redis NOW!** ⚡
