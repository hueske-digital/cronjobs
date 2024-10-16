# Der Build-Stage
FROM rust:1-slim AS builder
WORKDIR /app

# Kopiere die Cargo.toml und den Quellcode ins Arbeitsverzeichnis
COPY Cargo.toml .
COPY src ./src

# Installiere notwendige Tools
RUN apt-get update && apt-get install -y musl-tools

# Setze das Target Triple basierend auf der Architektur
ARG TARGETARCH
ENV RUST_TARGET_TRIPLE=""

# Mapping der Architektur zu den korrekten Rust Triple
RUN if [ "$TARGETARCH" = "amd64" ]; then \
        export RUST_TARGET_TRIPLE=x86_64-unknown-linux-musl; \
    elif [ "$TARGETARCH" = "arm64" ]; then \
        export RUST_TARGET_TRIPLE=aarch64-unknown-linux-musl; \
    fi && \
    rustup target add ${RUST_TARGET_TRIPLE} && \
    cargo build --release --target ${RUST_TARGET_TRIPLE}

# Der finale Stage, der das Ergebnis des Builds verwendet
FROM scratch
# Verwende das gleiche ARG wie im Build-Stage
ARG TARGETARCH
ENV RUST_TARGET_TRIPLE=""

# Setze das Triple erneut, damit es auch im finalen Stage verfügbar ist
RUN if [ "$TARGETARCH" = "amd64" ]; then \
        export RUST_TARGET_TRIPLE=x86_64-unknown-linux-musl; \
    elif [ "$TARGETARCH" = "arm64" ]; then \
        export RUST_TARGET_TRIPLE=aarch64-unknown-linux-musl; \
    fi

# Kopiere das gebaute Binary aus dem Build-Stage in das finale Image
COPY --from=builder /app/target/${RUST_TARGET_TRIPLE}/release/cronjoblistener /app/cronjoblistener

# Setze das Entry Point für den Container
ENTRYPOINT ["/app/cronjoblistener"]