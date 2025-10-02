FROM node:18-alpine as builder

WORKDIR /app

# Копируем package.json и package-lock.json
COPY package*.json ./

# Устанавливаем зависимости (используем npm install вместо npm ci)
RUN npm install

# Копируем исходный код
COPY . .

# Собираем приложение
RUN npm run build

# Production stage
FROM nginx:alpine

# Копируем собранное приложение
COPY --from=builder /app/dist /usr/share/nginx/html

# Копируем конфигурацию nginx
COPY nginx.conf /etc/nginx/nginx.conf

# Открываем порт
EXPOSE 80

# Запускаем nginx
CMD ["nginx", "-g", "daemon off;"]