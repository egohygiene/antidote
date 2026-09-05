# Streaming music-generation source record

## Verified metadata

| Field | Value |
| --- | --- |
| Title | Real-Time Interactive Music Generation via Data-Free Streaming Consistency Distillation |
| Authors | Baisen Wang; Chenxi Bao; Qisong Han |
| Identifier | arXiv:2606.24307 |
| Version reviewed | Version 1, 2026-06-23 |
| Primary source | https://arxiv.org/abs/2606.24307 |
| Source type | Non-peer-reviewed computer-science preprint |
| Reviewed | 2026-09-05 |

## Source claims assessed

- The paper proposes distillation in a streaming autoregressive latent space to
  reduce text-to-music generation latency.
- It describes chunk-wise generation, music-aware consistency objectives, and
  changing human inputs during a continuous stream.
- The authors report a low real-time factor and frame the system as an
  interactive instrument rather than an offline prompt-and-wait generator.

## Limitations and unresolved questions

- This is a recent preprint without independent Antidote replication.
- Reported latency and continuity depend on the paper's models, hardware,
  evaluation, and definition of real time.
- Dynamic prompt acceptance does not establish musical smoothness, emotional
  fit, safety, or suitability for local deployment.

## Allowed manuscript use

Use as emerging evidence that changing-input, chunk-wise generation is a
plausible future adapter class worth benchmarking behind Antidote's authority
and verification boundaries.

## Prohibited manuscript use

Do not claim production readiness, seamlessness, local performance, Antidote
compatibility, clinical value, or implementation in the current prototype.
