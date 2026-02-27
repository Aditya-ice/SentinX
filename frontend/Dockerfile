# Build Stage
FROM node:20-alpine as build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
# Vite injects the env var at build time, so we need it here for the standard build
ARG VITE_API_URL
ENV VITE_API_URL=$VITE_API_URL
RUN npm run build

# Serve Stage
FROM nginx:alpine
# Copy the vite dist folder
COPY --from=build /app/dist /usr/share/nginx/html
# Expose port 80
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
