FROM node:20-alpine AS build
WORKDIR /web

# Select v2.1 UI as the frontend
COPY "agent-controller ui v2.1/" /web/

# Install and build
RUN npm ci || npm install \
 && npm run build

FROM nginx:1.27-alpine
WORKDIR /usr/share/nginx/html

# Copy build output
COPY --from=build /web/dist/ /usr/share/nginx/html/

# Nginx config with Socket.IO proxy
COPY deploy/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

