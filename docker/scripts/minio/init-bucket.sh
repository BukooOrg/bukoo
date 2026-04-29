#!/bin/sh
set -e

echo "⏳ Waiting for MinIO..."

# Simple wait loop (more reliable than fixed sleep)
until mc alias set local http://minio:9000 "$MINIO_ACCESS_KEY" "$MINIO_SECRET_KEY"; do
  echo "MinIO not ready yet..."
  sleep 2
done

echo "✅ Connected to MinIO"

# Create bucket (idempotent)
if ! mc ls local/"$MINIO_BUCKET" >/dev/null 2>&1; then
  echo "📦 Creating bucket: $MINIO_BUCKET"
  mc mb local/"$MINIO_BUCKET"
else
  echo "📦 Bucket already exists"
fi

# create multiple buckets
# for bucket in $MINIO_BUCKETS; do
#   mc mb -p local/"$bucket" || true
# done

# Optional: set public access
if [ "$MINIO_PUBLIC" = "true" ]; then
  echo "🌍 Setting bucket public"
  mc anonymous set public local/"$MINIO_BUCKET"
fi

echo "🎉 MinIO initialization complete"
