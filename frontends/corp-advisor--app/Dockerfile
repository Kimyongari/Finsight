# Use the node version specified in package.json
FROM node:20-slim

# Set the working directory
WORKDIR /app

# Copy package files and install dependencies
# Use package-lock.json for reproducible installs
COPY package*.json ./
RUN npm install

# Copy the rest of the application source code
COPY . .

# Expose the Vite port
EXPOSE 5173

# The command to run the dev server and make it accessible outside the container
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
