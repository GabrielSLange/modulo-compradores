FROM node:20-alpine

WORKDIR /app

# Copia os arquivos de dependência
COPY package*.json ./

# Instala todas as dependências (Vite e plugins são necessários para o preview)
RUN npm install

# Copia o restante do código
COPY . .

# Faz o build do projeto (TanStack Start gera dist/client e dist/server)
RUN npm run build && cp /app/dist/server/index.js /app/dist/server/server.js

# O frontend responde na porta 8084
EXPOSE 8084

# Inicia o servidor Node/Vite configurado para SSR/Cloudflare localmente
CMD ["npm", "run", "preview", "--", "--host", "0.0.0.0", "--port", "8084"]