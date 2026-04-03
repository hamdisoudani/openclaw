FROM golang:1.23-alpine

WORKDIR /app

# Initialize Go modules and fetch dependencies
RUN go mod init agenthood/gateway && \
    go get github.com/go-redis/redis/v8 && \
    go get github.com/google/uuid

COPY main.go .

# Build the fast, single binary
RUN go build -o /receptionist

EXPOSE 8080

CMD ["/receptionist"]
