# 🔴 ROLLBACK PHASE 7 (Tier 1)

**Last Updated:** 2026-01-07 15:36 WIB

---

## When to Use

- Prometheus alerts flapping or spamming
- Metric missing alerts fire incorrectly
- New alerts cause Prometheus errors
- Need to revert to pre-Tier1 state urgently

---

## Prerequisites

- Git access to repository
- Prometheus control (Docker or systemctl)
- Backup of current `quality_drift.yml` (auto-saved via git)

---

## ROLLBACK STEPS (5 minutes)

### 1. Stop Prometheus

```powershell
# If using Docker
docker stop prometheus

# If using systemctl (Linux)
sudo systemctl stop prometheus
```

### 2. Revert Alert Configuration

```powershell
# Navigate to repository
cd c:\Users\LENOVO\Documents\adaptive-cdss-under-uncertainty\indoGov

# Check recent commits
git log --oneline -5

# Identify commit BEFORE Tier 1 changes
# Look for commit before "Tier1: add metric-missing alerts"

# Revert quality_drift.yml to that commit
git checkout <commit_hash_before_tier1> prometheus/alerts/quality_drift.yml

# Example:
# git checkout HEAD~2 prometheus/alerts/quality_drift.yml

# Verify file reverted
git diff prometheus/alerts/quality_drift.yml
```

### 3. Restart Prometheus

```powershell
# If Docker
docker start prometheus

# If systemctl
sudo systemctl start prometheus

# Wait for startup
Start-Sleep -Seconds 5
```

### 4. Verify Rollback

```powershell
# Check Prometheus health
Invoke-WebRequest -Uri "http://localhost:9090/-/healthy"
# Expected: "Prometheus Server is Healthy"

# Verify rules count (should be less than Tier 1)
Invoke-WebRequest -Uri "http://localhost:9090/api/v1/rules" | 
  ConvertFrom-Json | 
  Select-Object -ExpandProperty data | 
  Select-Object -ExpandProperty groups | 
  Select-Object -ExpandProperty rules | 
  Measure-Object | 
  Select-Object -ExpandProperty Count

# Expected: ~3 rules (not 6)

# Check Prometheus UI
Start-Process "http://localhost:9090/alerts"
```

### 5. Monitor Logs

```powershell
# If Docker
docker logs prometheus --tail 50

# If systemctl
sudo journalctl -u prometheus -n 50

# Look for:
# - "Server is ready to receive web requests"
# - No "loading rules" errors
```

---

## VERIFICATION CHECKLIST

After rollback complete:

- [ ] Prometheus running (/-/healthy returns 200)
- [ ] Alert count reverted (fewer rules than Tier 1)
- [ ] No error logs in Prometheus
- [ ] Grafana dashboards still functional
- [ ] No alert spam/flapping

---

## RECOVERY PLAN

After fixing issues:

1. **Review what failed:** Check Prometheus logs, test locally
2. **Fix in feature branch:** Update `quality_drift.yml` with corrections
3. **Test in staging:** Validate YAML, reload Prometheus test instance
4. **Re-deploy:** Cherry-pick fixes or re-run Tier 1 with corrections

---

## ALTERNATIVE: Partial Rollback

If only некоторые alerts problematic:

1. Edit `prometheus/alerts/quality_drift.yml` directly
2. Comment out (`#`) problematic alerts
3. Reload Prometheus: `curl -X POST http://localhost:9090/-/reload`
4. Monitor for 10 minutes
5. If stable, commit partial fix

---

## CONTACT

- **Repository:** indogov/rag
- **Docs:** `docs/P0_WEEK1_EXECUTION.md`
- **Alerts Config:** `prometheus/alerts/quality_drift.yml`

---

## NOTES

- **Git History:** All changes tracked, easy to revert
- **Zero Data Loss:** Metrics/logs not affected by alert changes
- **Quick Rollback:** <5 minutes from decision to completion
- **Test First:** Always test rollback in non-prod before emergency use
