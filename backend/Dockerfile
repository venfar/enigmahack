FROM gcc:15 AS builder

RUN apt-get update && apt-get install -y cmake libssl-dev libmysqlcppconn-dev

WORKDIR /app

COPY CMakeLists.txt .

COPY . .

RUN rm -rf build/* && mkdir -p build && cd build && cmake .. && make -j$(nproc)

FROM ubuntu:latest

RUN apt-get update && apt-get install -y libssl3 libmysqlcppconn7v5 ca-certificates && rm -rf /var/lib/apt/lists/*

WORKDIR /root/

COPY --from=builder /app/build/backend .

COPY --from=builder /app/frontend ./frontend 

EXPOSE 8080

CMD ["./backend"]
