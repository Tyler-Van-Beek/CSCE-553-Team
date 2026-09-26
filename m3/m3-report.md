# M3 – Azure Migration, Performance Comparison, and Resource Monitoring

## 1. Objective

The goal of this milestone was to migrate the existing Django application from Render to an Azure virtual machine, configure the application using Nginx and Gunicorn, continue using the existing Supabase PostgreSQL database, automate deployment through GitHub Actions, and compare Azure performance against the previous Render baseline.

A second goal was to monitor the application at two levels:

- Azure infrastructure metrics
- Linux operating-system metrics using `htop` and `nload`

The application was then tested at increasing concurrency levels of 5, 50, and 250 to correlate client-side latency with server-side resource utilization.

---

## 2. Azure Deployment

### Azure VM Configuration

The application was deployed to an Azure Virtual Machine with the following configuration:

- Resource Group: `InternetScale-Lab3`
- VM Name: `django-web-server`
- Region: Denmark East
- VM Size: `Standard_B2ats_v2`
- vCPU: 2
- RAM: 1 GiB
- Operating System: Ubuntu Server 24.04 LTS
- Architecture: x64
- OS Disk: Premium SSD P6, 64 GiB
- Allowed inbound ports:
  - SSH 22
  - HTTP 80

The originally requested `Standard_B1s` VM was unavailable for the Azure for Students subscription. After checking the subscription's allowed regions and available B-series VM sizes, `Standard_B2ats_v2` in Denmark East was selected.

### Application Stack

The deployed request path is:

```text
Client
  ↓
Azure Public IP
  ↓
Nginx :80
  ↓
Gunicorn :8000
  ↓
Django
  ↓
Supabase PostgreSQL
```

The server was configured with:

- Python virtual environment
- Django dependencies
- Gunicorn
- Nginx reverse proxy
- Supabase Transaction Pooler connection
- Django environment variables stored in `.env`
- Static files collected using `collectstatic`

### Static Files

The project originally had:

```python
STATIC_URL = "static/"
```

The following setting was added so `collectstatic` could deploy static assets:

```python
STATIC_ROOT = BASE_DIR / "staticfiles"
```

After the change:

```text
169 static files copied successfully
```

### Deployment Verification

The public health endpoint was verified successfully:

```text
http://9.205.27.129/health/
```

Response:

```json
{"status": "ok"}
```

---

## 3. Automated Deployment

A GitHub Actions workflow was configured to deploy changes automatically to the Azure VM after changes are merged into `main`.

The deployment workflow:

1. Connects to the Azure VM through SSH.
2. Updates the repository from `main`.
3. Activates the Python virtual environment.
4. Installs dependencies.
5. Runs Django migrations.
6. Runs `collectstatic`.
7. Restarts Gunicorn.
8. Reloads Nginx.

The workflow successfully completed and the application remained accessible after automated deployment.

---

## 4. Render vs Azure Performance Comparison

To create a direct comparison with the M2 Render baseline, the authenticated `GET /api/events` workload was tested at concurrency 4.

| Metric | Render | Azure |
|---|---:|---:|
| Concurrency | 4 | 4 |
| Successful RPS | 8.283 | 6.741 |
| p99 Latency | 585.77 ms | 627.57 ms |
| Error Rate | 0% | 0% |

Azure produced approximately 19% lower throughput than Render at this concurrency level.

Tail latency was relatively close:

- Render p99: 585.77 ms
- Azure p99: 627.57 ms

Both environments completed the test with a 0% error rate.

Therefore, at C=4, Render provided slightly higher throughput and slightly lower tail latency, while Azure remained stable and error-free.

---

## 5. Dual-Layer Monitoring Setup

Azure Monitor was configured with:

- Percentage CPU
- Network In Total
- Network Out Total
- Disk Read Operations/Sec
- Disk Write Operations/Sec

Inside the VM, `htop` was used to observe CPU and memory behavior, while `nload` was used to observe network traffic.

The purpose was to correlate client-side load-test behavior with both OS-level and cloud-level resource utilization.

---

## 6. Multi-Phase Stress Test

The required tests were executed from the local machine with a 30-second rest period between phases.

The tested endpoint was:

```text
GET /api/events
```

with authenticated requests.

### Results

| Metric | Phase 1 C=5 | Phase 2 C=50 | Phase 3 C=250 |
|---|---:|---:|---:|
| Successful RPS | 7.957 | 9.156 | 9.150 |
| Average Latency | 626.03 ms | 5239.22 ms | 22999.76 ms |
| p99 Latency | 676.04 ms | 5557.24 ms | 27467.19 ms |
| Error Rate | 0% | 0% | 0% |
| htop Max CPU Observed | Not reliably captured | ~3.3% | ~5.3% |
| htop Max RAM Observed | ~460 MB | ~464 MB | ~466 MB |
| nload Peak Traffic In | 671.84 kbit/s | 798.46 kbit/s | 1.18 Mbit/s |
| nload Peak Traffic Out | 971.51 kbit/s | 1.14 Mbit/s | 1.08 Mbit/s |
| Azure Max CPU | ~1.55% | 2.72% | 2.55% |

---

## 7. Performance Interpretation

Throughput increased from approximately 7.96 RPS at C=5 to approximately 9.16 RPS at C=50.

However, increasing concurrency further to C=250 did not increase throughput:

```text
C=5    → 7.957 RPS
C=50   → 9.156 RPS
C=250  → 9.150 RPS
```

The system reached a throughput plateau of approximately 9 RPS.

Latency increased significantly:

```text
Average latency:
C=5   → 0.63 s
C=50  → 5.24 s
C=250 → 23.00 s
```

Similarly, p99 latency increased from:

```text
0.68 s → 5.56 s → 27.47 s
```

Despite this large increase in latency, CPU remained low and memory usage remained approximately stable.

This indicates that increasing concurrency primarily caused requests to wait longer rather than increasing completed requests per second.

---

## 8. Post-Lab Diagnostic Questions

### Question 1 – Disconnect Discovery

**Did `htop` and Azure Monitor show resource changes at the same time?**

No. `htop` displayed CPU changes immediately while the load test was running, whereas the spike appeared later in Azure Monitor.

`htop` reads resource utilization directly from the Linux operating system and therefore provides near real-time information.

Azure Monitor collects metrics from the cloud infrastructure, aggregates them over a time interval, transfers them to the monitoring service, and then updates the dashboard.

Because of this collection and aggregation process, Azure Monitor can show a small delay compared with the live OS view.

### Question 2 – Identifying the Bottleneck

During Phase 3, the VM did not exhaust its CPU or memory.

At C=250:

- p99 latency reached approximately 27.47 seconds.
- Average latency reached approximately 23 seconds.
- Azure CPU was only approximately 2.55%.
- The highest clearly captured `htop` CPU value was approximately 5.3%.
- RAM usage remained around 466 MB out of approximately 843 MB.

Therefore, the VM did not reach 100% CPU or memory usage.

Instead, response times increased significantly while hardware utilization remained relatively low.

This indicates that the application stalled or requests waited somewhere in the request-processing path rather than exhausting the VM's compute capacity.

### Question 3 – Architectural Hypothesis

The initial results suggested that the application might be waiting on Gunicorn workers, the Supabase database, or network communication.

Several additional diagnostic tests were performed to narrow the hypothesis.

#### Diagnostic Test 1 – Lightweight Health Endpoint

The `/health/` endpoint was tested at C=50.

Unlike `/api/events`, this endpoint performs very little application work and does not rely on the normal event database query.

The result still showed high tail latency and connection errors:

```text
RPS: ~32–37
p50: ~0.38–0.40 s
p99: ~21 s
Error rate: ~2%
```

The failures included:

- `URLError` with WinError 10060
- `TimeoutError`
- `ConnectionResetError` with WinError 10054

This showed that Supabase/database access was not the only reason for the scaling problem.

#### Diagnostic Test 2 – Gunicorn Worker Count

Gunicorn was initially running with:

```text
3 synchronous workers
```

The worker count was temporarily increased to 5.

Results changed only slightly:

| Metric | 3 Workers | 5 Workers |
|---|---:|---:|
| Successful RPS | 32.765 | 33.660 |
| Error Rate | 2.35% | 1.84% |
| p50 | 390.98 ms | 402.68 ms |
| p95 | 3264.83 ms | 2303.21 ms |
| p99 | ~21 s | ~21 s |

Increasing workers slightly improved throughput and error rate, but the large p99 latency remained.

Therefore, Gunicorn worker count alone does not explain the problem.

#### Diagnostic Test 3 – Internal Localhost Probe

While an external C=50 `/health/` load test was running from the laptop, the VM repeatedly called its own health endpoint through:

```text
http://127.0.0.1/health/
```

All 20 local requests returned:

```text
HTTP 200
```

with response times around:

```text
0.001–0.002 seconds
```

This occurred while external requests were experiencing long latency and connection failures.

#### Final Hypothesis

The evidence suggests that the primary scaling limitation is more likely in the external connection/network path between the load-generating client and the Azure VM rather than raw VM CPU or memory capacity.

The internal:

```text
Nginx → Gunicorn → Django
```

path remained responsive during external load.

Gunicorn worker count contributed slightly, but increasing workers did not significantly change p99 latency.

Supabase/database latency likely contributes additional latency to `/api/events`, but it cannot fully explain the connection failures because similar behavior also appeared on the lightweight `/health/` endpoint.

Therefore, the most likely hypothesis is that external network or TCP connection handling became the dominant scaling constraint during high concurrency.

---

## 9. Conclusion

The Django application was successfully migrated from Render to an Azure VM and configured with Nginx, Gunicorn, Supabase, and GitHub Actions.

The Azure deployment remained stable at low concurrency, but throughput reached a plateau as concurrency increased.

At high concurrency, latency increased substantially even though CPU and memory remained far below saturation.

Additional diagnostic testing showed that the lightweight health endpoint remained extremely fast when accessed locally inside the VM while external requests experienced long-tail latency and connection failures.

The results demonstrate an important scalability concept: poor application performance does not always mean the server has exhausted CPU or memory. Bottlenecks can occur in connection handling, request queues, database communication, or network paths even while the VM appears lightly utilized.
