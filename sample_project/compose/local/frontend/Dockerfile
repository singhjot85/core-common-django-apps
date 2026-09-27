FROM node:lts-alpine

WORKDIR /frontend

# Copy package.json and package-lock.json
COPY ./frontend/package*.json .

# Install dependencies
RUN npm install

# Copy the rest of the application code
COPY /frontend /frontend

# Expose port
EXPOSE 5173

# Start the Vite server
CMD ["sh", "/scripts/npm-start.sh"]
