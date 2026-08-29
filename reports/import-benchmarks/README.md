# Import benchmarks

Real runs against a real StarIntel server (starintel/server:0.1.0 with
fix/v09-false-value-pipeline, docker compose stack: couchdb + rabbitmq +
valkey + clouseau + star-server, all healthy).

Environment: local docker compose, 4 workers, batch-size 10 (inline mode) /
200 (async-job mode), retry 5, api-key auth.

- bench-summary.json  : inline mode  (batch 10,  workers 4): 5,671 docs, 730.9 docs/s
- bench-async.json    : async mode   (batch 200, workers 4): 5,671 docs, 912.8 docs/s

Categories tracked: attempted / accepted / duplicate / invalid / failed /
transient. 0 invalid, 0 failed, 0 transient in both runs. Throughput is
bounded by the server's synchronous per-document RabbitMQ publish +
authorization decisions, not the client.
