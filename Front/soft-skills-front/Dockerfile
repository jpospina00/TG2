# Front/soft-skills-front/Dockerfile
FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

EXPOSE 3000

ENV CI=false
ENV CHOKIDAR_USEPOLLING=true
ENV WDS_SOCKET_PORT=0

CMD ["npm", "start"]