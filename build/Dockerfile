FROM rust:1-slim AS builder
WORKDIR /app

# Kopiere die Cargo.toml und den Quellcode ins Arbeitsverzeichnis
COPY Cargo.toml .
COPY src ./src

# Installiere notwendige Tools
RUN apt-get update && apt-get install -y musl-tools

# Erstelle den Build für beide Architekturen (amd64 und aarch64)
ARG TARGETARCH

RUN rustup target add ${TARGETARCH}-unknown-linux-musl && \
    cargo build --release --target ${TARGETARCH}-unknown-linux-musl

# Der finale Stage, der das Ergebnis des Builds verwendet
FROM scratch
COPY --from=builder /app/target/${TARGETARCH}-unknown-linux-musl/release/cronjoblistener /app/cronjoblistener

ENTRYPOINT ["/app/cronjoblistener"]