#!/usr/bin/env bash
# Provision the Aedifica VM on Oracle Cloud Always Free. Idempotent: re-running
# reuses whatever already exists and only creates what is missing.
#
# Prerequisite — authenticate first (opens a browser, stores a short-lived token
# under ~/.oci; no API key file to manage):
#
#     oci session authenticate --region eu-zurich-1 --profile-name aedifica
#
# Then:
#     ./provision.sh                 # show the plan, create nothing
#     ./provision.sh --apply         # create the resources
#
set -euo pipefail

PROFILE="${OCI_PROFILE:-aedifica}"
VM_NAME="${VM_NAME:-aedifica}"
VCN_NAME="${VCN_NAME:-aedifica-vcn}"
SUBNET_NAME="${SUBNET_NAME:-aedifica-subnet}"
SSH_KEY="${SSH_KEY:-$HOME/.ssh/aedifica_oracle}"
OCPUS="${OCPUS:-2}"
MEMORY_GB="${MEMORY_GB:-12}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

APPLY=0
[ "${1:-}" = "--apply" ] && APPLY=1

oci() { command oci --profile "$PROFILE" "$@"; }
say() { printf '\n\033[1m%s\033[0m\n' "$*"; }
run() {
  if [ "$APPLY" -eq 1 ]; then "$@"; else printf '  would run: %s\n' "$*" >&2; echo ""; fi
}

command -v oci >/dev/null || { echo "oci CLI not found. pip install oci-cli"; exit 1; }

TENANCY="$(awk -F= '/^tenancy/{gsub(/ /,"",$2);print $2;exit}' ~/.oci/config 2>/dev/null || true)"
[ -n "$TENANCY" ] || { echo "No tenancy in ~/.oci/config — run: oci session authenticate --profile-name $PROFILE"; exit 1; }
C="${OCI_COMPARTMENT:-$TENANCY}"

say "Tenancy: $C"
oci iam region-subscription list --query 'data[]."region-name"' --raw-output >/dev/null \
  || { echo "Authentication failed or expired. Run: oci session authenticate --profile-name $PROFILE"; exit 1; }

# --- SSH key ---------------------------------------------------------------- #
if [ ! -f "${SSH_KEY}.pub" ]; then
  say "Generating a dedicated SSH key at ${SSH_KEY}"
  [ "$APPLY" -eq 1 ] && ssh-keygen -t ed25519 -N "" -C "aedifica-oracle" -f "$SSH_KEY"
fi
PUBKEY="$(cat "${SSH_KEY}.pub" 2>/dev/null || echo '<generated on --apply>')"

# --- network ---------------------------------------------------------------- #
find_id() { oci "$@" --query 'data[0].id' --raw-output 2>/dev/null || true; }

VCN_ID="$(find_id network vcn list -c "$C" --display-name "$VCN_NAME")"
if [ -z "$VCN_ID" ]; then
  say "Creating VCN $VCN_NAME (10.0.0.0/16)"
  VCN_ID="$(run oci network vcn create -c "$C" --display-name "$VCN_NAME" \
    --cidr-blocks '["10.0.0.0/16"]' --wait-for-state AVAILABLE \
    --query 'data.id' --raw-output)"
else
  say "VCN $VCN_NAME already exists"
fi

if [ -n "$VCN_ID" ]; then
  IG_ID="$(find_id network internet-gateway list -c "$C" --vcn-id "$VCN_ID")"
  if [ -z "$IG_ID" ]; then
    say "Creating internet gateway"
    IG_ID="$(run oci network internet-gateway create -c "$C" --vcn-id "$VCN_ID" \
      --is-enabled true --display-name "${VM_NAME}-ig" --wait-for-state AVAILABLE \
      --query 'data.id' --raw-output)"
  fi

  RT_ID="$(oci network vcn get --vcn-id "$VCN_ID" --query 'data."default-route-table-id"' --raw-output 2>/dev/null || true)"
  if [ -n "$RT_ID" ] && [ -n "$IG_ID" ]; then
    say "Routing 0.0.0.0/0 to the internet gateway"
    run oci network route-table update --rt-id "$RT_ID" --force \
      --route-rules "[{\"cidrBlock\":\"0.0.0.0/0\",\"networkEntityId\":\"$IG_ID\"}]" >/dev/null
  fi

  # THE step people forget: the VCN security list, separate from the instance
  # firewall. Without 80/443 here a perfectly deployed stack looks dead.
  SL_ID="$(oci network vcn get --vcn-id "$VCN_ID" --query 'data."default-security-list-id"' --raw-output 2>/dev/null || true)"
  if [ -n "$SL_ID" ]; then
    say "Opening 22/80/443 in the VCN security list"
    run oci network security-list update --security-list-id "$SL_ID" --force \
      --egress-security-rules '[{"destination":"0.0.0.0/0","protocol":"all","isStateless":false}]' \
      --ingress-security-rules '[
        {"source":"0.0.0.0/0","protocol":"6","isStateless":false,"tcpOptions":{"destinationPortRange":{"min":22,"max":22}}},
        {"source":"0.0.0.0/0","protocol":"6","isStateless":false,"tcpOptions":{"destinationPortRange":{"min":80,"max":80}}},
        {"source":"0.0.0.0/0","protocol":"6","isStateless":false,"tcpOptions":{"destinationPortRange":{"min":443,"max":443}}},
        {"source":"0.0.0.0/0","protocol":"1","isStateless":false,"icmpOptions":{"type":3,"code":4}}
      ]' >/dev/null
  fi

  SUBNET_ID="$(find_id network subnet list -c "$C" --vcn-id "$VCN_ID" --display-name "$SUBNET_NAME")"
  if [ -z "$SUBNET_ID" ]; then
    say "Creating subnet $SUBNET_NAME (10.0.1.0/24)"
    SUBNET_ID="$(run oci network subnet create -c "$C" --vcn-id "$VCN_ID" \
      --display-name "$SUBNET_NAME" --cidr-block "10.0.1.0/24" \
      --wait-for-state AVAILABLE --query 'data.id' --raw-output)"
  fi
fi

# --- image ------------------------------------------------------------------ #
say "Resolving the latest Ubuntu 22.04 ARM image"
IMAGE_ID="$(oci compute image list -c "$C" \
  --operating-system "Canonical Ubuntu" --operating-system-version "22.04" \
  --shape "VM.Standard.A1.Flex" --sort-by TIMECREATED --sort-order DESC \
  --query 'data[0].id' --raw-output 2>/dev/null || true)"
echo "  image: ${IMAGE_ID:-<unresolved>}"

# --- instance --------------------------------------------------------------- #
EXISTING="$(oci compute instance list -c "$C" --display-name "$VM_NAME" \
  --lifecycle-state RUNNING --query 'data[0].id' --raw-output 2>/dev/null || true)"
if [ -n "$EXISTING" ]; then
  say "Instance $VM_NAME already running: $EXISTING"
else
  USER_DATA="$(base64 -w0 < "$HERE/cloud-init.yaml")"
  METADATA="$(printf '{"ssh_authorized_keys":%s,"user_data":%s}' \
    "$(printf '%s' "$PUBKEY" | python3 -c 'import json,sys;print(json.dumps(sys.stdin.read()))')" \
    "$(printf '%s' "$USER_DATA" | python3 -c 'import json,sys;print(json.dumps(sys.stdin.read()))')")"

  # ARM capacity is genuinely scarce: walk every availability domain rather than
  # failing on the first "Out of host capacity".
  say "Launching ${VM_NAME} (A1.Flex, ${OCPUS} OCPU / ${MEMORY_GB} GB)"
  LAUNCHED=""
  for AD in $(oci iam availability-domain list --query 'data[].name' --raw-output 2>/dev/null); do
    echo "  trying availability domain: $AD"
    if [ "$APPLY" -eq 0 ]; then echo "  would launch here"; break; fi
    if LAUNCHED="$(oci compute instance launch -c "$C" \
        --availability-domain "$AD" --display-name "$VM_NAME" \
        --shape "VM.Standard.A1.Flex" \
        --shape-config "{\"ocpus\":$OCPUS,\"memoryInGBs\":$MEMORY_GB}" \
        --image-id "$IMAGE_ID" --subnet-id "$SUBNET_ID" \
        --assign-public-ip true --metadata "$METADATA" \
        --wait-for-state RUNNING --query 'data.id' --raw-output 2>/dev/null)"; then
      echo "  launched in $AD"
      break
    fi
    echo "  no capacity in $AD, trying the next one"
    LAUNCHED=""
  done
  [ "$APPLY" -eq 1 ] && [ -z "$LAUNCHED" ] && {
    echo "No ARM capacity in any availability domain of this region."
    echo "Retry later, or authenticate against another region and re-run."
    exit 1
  }
  EXISTING="$LAUNCHED"
fi

# --- result ----------------------------------------------------------------- #
if [ "$APPLY" -eq 1 ] && [ -n "${EXISTING:-}" ]; then
  VNIC="$(oci compute instance list-vnics --instance-id "$EXISTING" --query 'data[0]."public-ip"' --raw-output)"
  say "VM ready at $VNIC"
  cat <<EOF

Next:
  ssh -i $SSH_KEY ubuntu@$VNIC
  git clone https://github.com/decarvalhoe/aedifica.git /opt/aedifica
  cd /opt/aedifica/deploy/oracle && cp .env.example .env && nano .env
  docker compose --env-file .env up -d --build

Point your DNS A record at $VNIC before setting AEDIFICA_SITE to a hostname.
EOF
else
  say "Plan only. Re-run with --apply to create these resources."
fi
