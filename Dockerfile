# Stage 1: Build the Go binary
FROM golang:alpine as builder

# Set environment variable to ensure static build
ENV CGO_ENABLED=0
ENV GOOS=linux
ENV GOARCH=amd64

# Copy the local package files to the container's workspace.
WORKDIR /go/src/app
COPY main.go .
COPY go.mod .
COPY go.sum .

# Build the command inside the container.
# Use -a for a clean build and -ldflags '-extldflags "-static"' for a static build.
RUN go build -a -ldflags '-extldflags "-static"' -o /go/bin/app

# Stage 2: Create the scratch image
FROM scratch

# Copy the binary from the builder stage.
COPY --from=builder /go/bin/app /app

# Command to run
ENTRYPOINT ["/app"]
