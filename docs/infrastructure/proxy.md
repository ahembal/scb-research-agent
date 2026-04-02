# Outbound HTTP Proxy — Squid on alert-lizard

*Last updated: 2026-04-01*

## Why this exists

The Turtle Kubernetes cluster nodes do not have unrestricted outbound
internet access from within pods. The research-agent needs to reach:

- `api.anthropic.com` — Claude LLM API
- `statistikdatabasen.scb.se` — SCB Statistical Database API

Rather than opening unrestricted outbound access from the cluster,
we run a controlled forward proxy on `alert-lizard` that only allows
traffic to these specific domains.

## Architecture
```
Pod (workshop namespace, quick-thrush)
    │
    │ HTTPS_PROXY=http://192.168.1.183:3128
    ▼
Squid proxy (alert-lizard — 192.168.1.183:3128)
    │
    │ HTTP CONNECT tunnel (HTTPS traffic only)
    │ ACL: only api.anthropic.com and *.scb.se allowed
    ▼
Internet
    ├── api.anthropic.com
    └── statistikdatabasen.scb.se
```

## How it works

For HTTPS traffic, Squid uses the HTTP CONNECT method:

1. Pod sends: `CONNECT api.anthropic.com:443 HTTP/1.1`
2. Squid checks ACL — domain is allowed
3. Squid opens TCP connection to `api.anthropic.com:443`
4. Squid replies: `200 Connection established`
5. TLS handshake happens end-to-end between pod and Anthropic
6. Squid tunnels encrypted bytes — it cannot read the content

This means:
- API keys and request bodies are never visible to Squid
- Only the destination hostname is inspected for ACL matching

## Squid configuration

Location on alert-lizard: `/etc/squid/squid.conf`

Key settings:

| Setting | Value | Reason |
|---|---|---|
| Listen port | 3128 | Standard Squid port |
| Allowed sources | 10.244.0.0/16 (pods), 192.168.1.0/24 (LAN) | Cluster pod CIDR + LAN nodes |
| Allowed destinations | api.anthropic.com, *.scb.se | Only what the agent needs |
| Caching | Disabled | Forward proxy only, no content caching |

## Kubernetes configuration

Proxy settings are injected via ConfigMap (`deploy/base/configmap.yaml`):
```yaml
HTTPS_PROXY: "http://192.168.1.183:3128"
HTTP_PROXY:  "http://192.168.1.183:3128"
NO_PROXY:    "10.244.0.0/16,10.96.0.0/12,192.168.1.0/24,localhost,127.0.0.1"
```

`NO_PROXY` ensures internal cluster traffic (pod-to-pod, service DNS,
LAN nodes) bypasses the proxy and goes direct.

## Operational commands

**Check Squid status on alert-lizard:**
```bash
ssh-alert-lizard
sudo systemctl status squid
```

**View proxy access logs:**
```bash
ssh-alert-lizard
sudo tail -f /var/log/squid/access.log
```

**Test proxy from a cluster node:**
```bash
ssh-quick-thrush
curl -s -x http://192.168.1.183:3128 https://api.anthropic.com
```

**Restart Squid after config changes:**
```bash
ssh-alert-lizard
sudo systemctl restart squid
```

## Adding new allowed domains

If the agent needs to reach additional external services, add them
to the ACL in `/etc/squid/squid.conf` on alert-lizard:
```
acl allowed_domains dstdomain .newdomain.com
```

Then restart Squid:
```bash
sudo systemctl restart squid
```

## Known issues

### Flannel instability on sought-perch
Flannel on `sought-perch` has ~7922 restarts over 41 days. This causes
pod sandbox recreation which kills containers running on that node.
The research-agent is pinned to `quick-thrush` via nodeSelector as a
workaround. Root cause investigation is pending.

### nginx Ingress not yet working
nginx Ingress controller crashes on Turtle due to the Flannel instability
on `sought-perch`. The research-agent is currently exposed via NodePort
31000 on `quick-thrush`. Proper Ingress setup is blocked on resolving
the Flannel issue first.

Fix order:
1. Debug and fix Flannel on sought-perch
2. Reinstall nginx Ingress
3. Switch from NodePort to Ingress
4. Update deploy/turtle/manifests/ accordingly

## Why Squid

Squid was chosen as the forward proxy for the following reasons:

- Available directly via apt on Ubuntu 24.04 — no additional setup
- Simple domain-based ACL syntax for whitelisting specific destinations
- Mature, stable, and well-documented
- Standard choice for outbound proxy on Linux infrastructure

Alternatives considered: Privoxy (too privacy-focused), Tinyproxy (limited ACLs),
nginx (forward proxy is not its primary use case).
