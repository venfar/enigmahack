FROM gcc:latest AS builder

RUN apt-get update && apt-get install -y libssl-dev

WORKDIR /app

COPY . .

RUN g++ main.cpp -o backend -lpthread -lssl -lcrypto

FROM ubuntu:latest
RUN apt-get update && apt-get install -y libssl1.1 && rm -rf /var/lib/apt/lists/*
WORKDIR /root/

COPY --from=builder /app/backend .

EXPOSE 8080
CMD ["./backend"]
