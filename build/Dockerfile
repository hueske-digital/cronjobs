FROM rust:1-slim AS builder
WORKDIR /app

# Kopiere die Cargo.toml und den Quellcode ins Arbeitsverzeichnis
COPY Cargo.toml .
COPY src ./src

# Installiere notwendige Tools
RUN apt-get update && apt-get install -y musl-tools

# Setze das Target Triple basierend auf der Architektur
ARG TARGETARCH
ENV RUST_TARGET_TRIPLE=${TARGETARCH}

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
COPY --from=builder /app/target/${RUST_TARGET_TRIPLE}/release/cronjoblistener /app/cronjoblistener

ENTRYPOINT ["/app/cronjoblistener"]