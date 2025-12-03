#!/bin/bash

# Build script for phase3_chains

cd "$(dirname "$0")"

echo "Building phase3_chains..."
cargo build --release

if [ $? -eq 0 ]; then
    echo "✅ Build successful!"
    echo "Run with: cargo run --release"
    echo "Or directly: ./target/release/phase3_chains"
else
    echo "❌ Build failed"
    exit 1
fi
