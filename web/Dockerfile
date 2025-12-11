FROM node:20-alpine

WORKDIR /app

ENV NEXT_TELEMETRY_DISABLED=1

# Install only dependencies
COPY package.json package-lock.json* ./
RUN npm ci

# Copy prisma schema EARLY to enable cached generation
COPY prisma ./prisma

# Generate Prisma client inside container (ALPINE binary)
RUN npx prisma generate

# Copy remaining project files
COPY . .

EXPOSE 3000

CMD ["npm", "run", "dev"]
