# M2 Measurement Notes

All timestamps use UTC-05:00 unless otherwise stated.

## Hosted cold start

- Series: H
- Timestamp: 2026-09-08 00:26:03 -05:00
- Inactivity before request: At least 15 minutes
- Method and path: GET /health/
- HTTP status: 200
- Wall-clock latency: 0.321745 seconds (321.745 ms)
- Response size: 16 bytes
- Observation: No long Render wake-up delay was observed during this cold-start attempt.
- Command:

  ```powershell
  curl.exe -sS -o NUL -w "http_code=%{http_code} total_s=%{time_total} bytes=%{size_download}`n" "$BASE_H/health/"

### Second cold-start attempt

- Timestamp: 2026-09-08 10:04:20 -05:00
- Inactivity before request: At least 15 minutes
- Method and path: GET /health/
- HTTP status: 200
- Wall-clock latency: 0.432801 seconds (432.801 ms)
- Response size: 16 bytes
- Observation: A second cold-start attempt also showed no long Render wake-up delay.