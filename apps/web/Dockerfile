# Multi-stage production Dockerfile for Next.js web app
# Base image: Alpine for builder, minimal runtime
# Final size target: ~100-150MB

# Stage 1: Builder - Install dependencies and build
FROM node:20-alpine AS builder

WORKDIR /app

# Install pnpm
RUN corepack enable && corepack prepare pnpm@9 --activate

# Copy all workspace files (monorepo pattern - packages have prepare scripts)
COPY . .

# Install dependencies
RUN pnpm install --frozen-lockfile

# Build Next.js app (standalone output enabled in next.config.ts)
RUN pnpm turbo build --filter=@repo/web

# Stage 2: Runner - Minimal runtime image
FROM node:20-alpine AS runner

WORKDIR /app

# Create non-root user
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

# Copy standalone output
COPY --from=builder /app/apps/web/.next/standalone ./
COPY --from=builder /app/apps/web/.next/static ./apps/web/.next/static
COPY --from=builder /app/apps/web/public ./apps/web/public

# Set ownership
RUN chown -R nextjs:nodejs /app

USER nextjs

EXPOSE 3000

ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD node -e "require('http').get('http://localhost:3000/api/health', (r) => {process.exit(r.statusCode === 200 ? 0 : 1)})"

# Start Next.js server
CMD ["node", "apps/web/server.js"]
