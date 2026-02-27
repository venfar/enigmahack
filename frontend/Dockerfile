FROM node:24-alpine AS builder

WORKDIR /app

COPY package*.json .

RUN npm install

COPY . .

RUN npm run build && ls -la

FROM nginx:alpine

RUN adduser -D appuser

COPY --from=builder --chown=appuser:appuser /app/dist /usr/share/nginx/html

COPY ./nginx/nginx.conf /etc/nginx/conf.d/default.conf

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD wget --quiet --spider http://localhost:80/ || exit 1

USER appuser

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
