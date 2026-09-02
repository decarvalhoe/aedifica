# Deploying Aedifica on an Oracle Cloud Always Free VM

Replaces the Fly.io deployment with a permanently free ARM VM. Everything in this
directory has been built and run end to end locally against the real images — the
stack below is what was verified, not a sketch.

## Why this shape

Oracle's Always Free tier gives a real VM (2 OCPU / 12 GB ARM as of 2026, down
from 4/24), which means the product keeps the topology it already has: one
`docker compose` file, a local Postgres, persistent disk, and **no cold start** —
the thing the free serverless tiers all charge you in latency.

```
internet ──443──> caddy ──> web:3000 ──> api:8090 ──> db:5432
                (TLS)     (Next.js)    (FastAPI)   (Postgres+pgvector)
```

Only Caddy binds to the host. The API and the database are never published.

## Provisioning the VM

[`provision.sh`](provision.sh) creates the whole infrastructure — VCN, internet
gateway, route, **security list with 80/443 open**, subnet, and the A1.Flex
instance with the cloud-init above. It is idempotent and walks every availability
domain rather than giving up on the first "Out of host capacity", which is the
normal experience with free ARM.

Authenticate first. This opens a browser and stores a short-lived token under
`~/.oci` — there is no API key file to create or hand around:

```bash
pip install oci-cli
oci session authenticate --region eu-zurich-1 --profile-name aedifica
```

Then:

```bash
cd deploy/oracle
./provision.sh            # prints the plan, creates nothing
./provision.sh --apply    # creates the resources, prints the public IP
```

It generates a dedicated `~/.ssh/aedifica_oracle` key rather than reusing an
existing one.

### If you would rather click

1. Compute → Instances → Create. Shape `VM.Standard.A1.Flex`, **2 OCPU / 12 GB**
   (the Always Free ceiling). Ubuntu 22.04 ARM. Your SSH public key. Advanced
   options → paste [`cloud-init.yaml`](cloud-init.yaml).
2. Networking → VCN → Security Lists → ingress `0.0.0.0/0` on TCP **80** and
   **443**. The instance firewall is handled by cloud-init, but this network-level
   list is separate, and missing it is the single most common reason a correct
   deployment looks dead.

## Deploying onto the VM

Point an `A` record at the VM's public IP first — certificates cannot be issued
before the hostname resolves.

```bash
ssh -i ~/.ssh/aedifica_oracle ubuntu@<vm-ip>
git clone https://github.com/decarvalhoe/aedifica.git /opt/aedifica
cd /opt/aedifica/deploy/oracle
cp .env.example .env
openssl rand -base64 32          # paste into POSTGRES_PASSWORD
nano .env                        # set AEDIFICA_SITE, PUBLIC_ORIGIN, ACME_EMAIL
docker compose --env-file .env up -d --build
```

Caddy obtains the Let's Encrypt certificate on the first request. To rehearse
before DNS is ready, set `AEDIFICA_SITE=:80` and browse the IP over plain HTTP.

Optional, to start on boot independently of Docker's restart policy:

```bash
sudo cp aedifica.service /etc/systemd/system/ && sudo systemctl enable --now aedifica
```

## Verifying a deployment

```bash
docker compose --env-file .env ps                     # api + db must be healthy
curl -s https://<your-host>/api/health                 # {"status":"ok", ...}
docker compose --env-file .env logs api | grep -i seed # no "skipped after error"
```

## Two things that are deliberately not the obvious choice

**`pgvector/pgvector:pg16`, not `postgres:16-alpine`.** Migration
`j4f7a2c9d8e3` runs `CREATE EXTENSION IF NOT EXISTS vector`. The plain Postgres
image cannot satisfy it and the migration fails at boot. The repository's
top-level `docker-compose.yml` had the same defect and was corrected alongside
this directory.

**No active health check on the Caddy upstream.** Next.js answers `/` with a
307, which an active check reads as unhealthy and turns into a blanket 503 with
no upstream left. Compose already gates `web` on a healthy `api`, and with a
single upstream a health check can only remove the only backend there is.

## Backups

The database lives in the `pgdata` volume. Oracle's free tier includes block
volume backups, but the simplest reliable habit is a dump on a cron:

```bash
docker compose --env-file .env exec -T db \
  pg_dump -U aedifica aedifica | gzip > ~/aedifica-$(date +%F).sql.gz
```

## Free-tier caveats worth knowing

- Oracle **halved** the Always Free A1 allocation in 2026 (4 OCPU/24 GB → 2/12)
  by updating the documentation, without announcement. Instances above the new
  limit are one termination away from being locked to it.
- Always Free resources do not expire, but Oracle reclaims instances that stay
  idle for long periods on the *trial* tier — make sure the account has finished
  converting to Always Free.
