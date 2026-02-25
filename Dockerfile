FROM gcc:latest AS builder

RUN apt-get update && apt-get install -y cmake libssl-dev

WORKDIR /app

COPY . .

RUN rm -rf build/* && mkdir -p build && cd build && cmake .. && make -j$(nproc)

FROM ubuntu:latest

RUN apt-get update && apt-get install -y libssl3 ca-certificates && rm -rf /var/lib/apt/lists/*

WORKDIR /root/

COPY --from=builder /app/build/backend .

EXPOSE 8080

CMD ["./backend"]
