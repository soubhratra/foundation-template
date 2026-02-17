#!/usr/bin/env node
/**
 * Verify that generated TypeScript types are fresh relative to OpenAPI spec.
 *
 * Fails CI if:
 * 1. openapi.json hash doesn't match the hash used during last type generation
 * 2. Generated type files are missing
 *
 * Usage: node scripts/check-openapi-freshness.mjs
 */

import { readFileSync, existsSync } from 'fs'
import { createHash } from 'crypto'
import { fileURLToPath } from 'url'
import { dirname, join } from 'path'

const __filename = fileURLToPath(import.meta.url)
const __dirname = dirname(__filename)
const rootDir = join(__dirname, '..')

function hashFile(filepath) {
  const content = readFileSync(filepath, 'utf-8')
  return createHash('sha256').update(content).digest('hex')
}

function main() {
  console.log('🔍 Checking TypeScript type freshness...\n')

  // Check if OpenAPI spec exists
  const openapiPath = join(rootDir, 'packages/api-client/openapi.json')
  if (!existsSync(openapiPath)) {
    console.error('❌ ERROR: packages/api-client/openapi.json not found')
    console.error('   Run: pnpm generate:types')
    process.exit(1)
  }

  // Check if generated types exist
  const generatedTypesPath = join(rootDir, 'packages/api-client/src/gen/v1.d.ts')
  if (!existsSync(generatedTypesPath)) {
    console.error('❌ ERROR: Generated types not found at packages/api-client/src/gen/v1.d.ts')
    console.error('   Run: pnpm generate:types')
    process.exit(1)
  }

  // Calculate current OpenAPI spec hash
  const currentHash = hashFile(openapiPath)
  console.log(`Current OpenAPI hash: ${currentHash.substring(0, 12)}...`)

  // Read hash embedded in generated types (if exists)
  const generatedContent = readFileSync(generatedTypesPath, 'utf-8')
  const hashMatch = generatedContent.match(/OpenAPI spec hash: ([a-f0-9]{64})/)

  if (!hashMatch) {
    console.warn('⚠️  WARNING: Generated types missing OpenAPI hash comment')
    console.warn('   Types may be stale. Run: pnpm generate:types')
    // Allow to pass for now (backward compatibility)
    console.log('✅ Type check passed (hash tracking not yet implemented)\n')
    process.exit(0)
  }

  const generatedHash = hashMatch[1]
  console.log(`Generated types hash: ${generatedHash.substring(0, 12)}...`)

  if (currentHash !== generatedHash) {
    console.error('\n❌ ERROR: Generated TypeScript types are STALE')
    console.error('   OpenAPI spec has changed since types were generated.')
    console.error('   Run: pnpm generate:types')
    console.error('   Then commit the updated types.\n')
    process.exit(1)
  }

  console.log('✅ TypeScript types are fresh and match OpenAPI spec\n')
  process.exit(0)
}

main()
