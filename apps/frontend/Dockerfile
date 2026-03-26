FROM node:20-alpine

WORKDIR /workspace/apps/frontend

COPY apps/frontend/package.json /workspace/apps/frontend/package.json
RUN npm install

COPY apps/frontend /workspace/apps/frontend
