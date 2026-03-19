FROM node:20-alpine AS builder
WORKDIR /app
COPY package.json package-lock.json* ./

# 设置淘宝镜像源
RUN npm config set registry https://registry.npmmirror.com

# 安装所有依赖（包括开发依赖）
RUN npm install

# 显式安装 vue-tsc（确保它被安装）
RUN npm install --save-dev vue-tsc typescript

COPY . .

# 现在运行构建
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
