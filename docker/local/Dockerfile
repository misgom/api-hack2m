# Stage 1: Build Astro project with pnpm
FROM node:22-alpine AS builder

RUN addgroup -S appgroup && adduser -S appuser -G appgroup

ENV PNPM_HOME="/pnpm"
ENV PATH="$PNPM_HOME:$PATH"
ENV SHELL="/bin/bash"
RUN apk add --no-cache curl git \
  && curl -fsSL https://get.pnpm.io/install.sh | sh -

WORKDIR /app

RUN git clone https://github.com/misgom/astro-hack2m.git

WORKDIR /app/astro-hack2m/code

# temporary for local dev
ENV PUBLIC_API_BASE_URL="http://localhost:8000/api"

RUN pnpm install --frozen-lockfile \
  && pnpm build

# Stage 2: Nginx server to serve the built files
FROM nginx:alpine AS runner

COPY --from=builder /app/astro-hack2m/code/dist /usr/share/nginx/html

COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
