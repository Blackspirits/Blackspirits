#!/usr/bin/env node
/**
 * .github/scripts/generate-recently-watched.mjs
 *
 * Fetches the last 6 items from Simkl history (movies + shows)
 * and writes assets/generated/recently-watched.svg.
 *
 * Required secrets:
 *   SIMKL_CLIENT_ID    — your Simkl app client ID
 *   SIMKL_ACCESS_TOKEN — your personal access token (OAuth)
 */

import { writeFileSync, mkdirSync } from 'fs'
import { join, dirname } from 'path'
import { fileURLToPath } from 'url'

const __dirname = dirname(fileURLToPath(import.meta.url))
const ROOT = join(__dirname, '..', '..')
const OUT_DIR = join(ROOT, 'assets', 'generated')
const OUT_FILE = join(OUT_DIR, 'recently-watched.svg')

const CLIENT_ID = process.env.SIMKL_CLIENT_ID
const ACCESS_TOKEN = process.env.SIMKL_ACCESS_TOKEN
const LIMIT = 6

// ─── Palette (Catppuccin Mocha) ───────────────────────────────────────────────
const C = {
  base: '#11111b',
  mantle: '#181825',
  surface: '#1e1e2e',
  overlay: '#313244',
  muted: '#7f849c',
  subtle: '#9399b2',
  text: '#cdd6f4',
  subtext: '#bac2de',
  lavender: '#b4befe',
  blue: '#89b4fa',
  purple: '#cba6f7',
  peach: '#fab387',
  green: '#a6e3a1',
  red: '#f38ba8',
}

// ─── Helpers ──────────────────────────────────────────────────────────────────
function escapeXml(str) {
  return String(str ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&apos;')
}

function truncate(str, max) {
  const value = String(str ?? '')
  return value.length > max ? value.slice(0, max - 1) + '…' : value
}

function typeIcon(type) {
  return type === 'movie' ? '🎬' : '📺'
}

function typeColor(type) {
  return type === 'movie' ? C.blue : C.peach
}

function relativeDate(iso) {
  if (!iso) return ''
  const timestamp = new Date(iso).getTime()
  if (Number.isNaN(timestamp)) return ''

  const diff = Date.now() - timestamp
  const days = Math.floor(diff / 86400000)

  if (days <= 0) return 'today'
  if (days === 1) return 'yesterday'
  if (days < 7) return `${days}d ago`
  if (days < 30) return `${Math.floor(days / 7)}w ago`
  return `${Math.floor(days / 30)}mo ago`
}

function asArray(data, preferredKeys = []) {
  if (Array.isArray(data)) return data
  if (!data || typeof data !== 'object') return []

  for (const key of preferredKeys) {
    if (Array.isArray(data[key])) return data[key]
  }

  for (const value of Object.values(data)) {
    if (Array.isArray(value)) return value
  }

  return []
}

function safeDateValue(value) {
  if (!value) return null
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? null : value
}

// ─── Fetch helpers ────────────────────────────────────────────────────────────
async function simklGet(path) {
  const url = `https://api.simkl.com${path}`

  const res = await fetch(url, {
    headers: {
      'simkl-api-key': CLIENT_ID,
      'Authorization': `Bearer ${ACCESS_TOKEN}`,
      'Content-Type': 'application/json',
    },
  })

  if (!res.ok) {
    const text = await res.text()
    throw new Error(`Simkl API ${res.status} on ${path}: ${text}`)
  }

  return res.json()
}

/** Fetch last N items from full history (movies + shows) */
async function fetchHistory() {
  const allRaw = await simklGet('/sync/all-items/')

  console.log('RAW all-items payload:')
  console.log(JSON.stringify(allRaw, null, 2).slice(0, 4000))

  const movies = Array.isArray(allRaw?.movies) ? allRaw.movies : []
  const shows  = Array.isArray(allRaw?.shows) ? allRaw.shows : []
  const anime  = Array.isArray(allRaw?.anime) ? allRaw.anime : []

  console.log(`🎬 Movies extracted: ${movies.length}`)
  console.log(`📺 Shows extracted: ${shows.length}`)
  console.log(`🌸 Anime extracted: ${anime.length}`)

  const normalisedMovies = movies
    .filter((m) => m.last_watched_at)
    .map((m) => ({
      type: 'movie',
      title: m.movie?.title ?? 'Unknown',
      year: m.movie?.year ?? '',
      watchedAt: m.last_watched_at,
      simklId: m.movie?.ids?.simkl ?? null,
    }))

  const normalisedShows = [...shows, ...anime]
    .filter((s) => s.last_watched_at)
    .map((s) => ({
      type: 'show',
      title: s.show?.title ?? 'Unknown',
      year: s.show?.year ?? '',
      watchedAt: s.last_watched_at,
      simklId: s.show?.ids?.simkl ?? null,
      season: null,
      episode: null,
    }))

  return [...normalisedMovies, ...normalisedShows]
    .sort((a, b) => new Date(b.watchedAt) - new Date(a.watchedAt))
    .slice(0, LIMIT)
}

// ─── SVG layout constants ─────────────────────────────────────────────────────
const W = 900
const H = 220
const PAD = 20
const COLS = 3
const ROWS = 2
const CARD_W = (W - PAD * 2 - (COLS - 1) * 12) / COLS
const CARD_H = (H - PAD * 2 - (ROWS - 1) * 12) / ROWS
const RX = 10

function buildCard(item, col, row) {
  const x = PAD + col * (CARD_W + 12)
  const y = PAD + row * (CARD_H + 12)
  const ac = typeColor(item.type)
  const ic = typeIcon(item.type)

  const subtitle = item.type === 'show' && item.season
    ? `S${String(item.season).padStart(2, '0')}E${String(item.episode ?? 0).padStart(2, '0')}`
    : String(item.year || '')

  const safeTitle = escapeXml(truncate(item.title, 28))
  const safeSubtitle = escapeXml(subtitle)
  const safeTypeLabel = item.type === 'movie' ? 'Movie' : 'Show'
  const safeRelativeDate = escapeXml(relativeDate(item.watchedAt))

  return `
  <!-- Card: ${escapeXml(item.title)} -->
  <g transform="translate(${x},${y})">
    <rect width="${CARD_W}" height="${CARD_H}" rx="${RX}" fill="${C.mantle}"/>
    <rect width="3" height="${CARD_H}" rx="1.5" fill="${ac}" opacity=".7"/>

    <rect x="12" y="10" width="52" height="18" rx="6" fill="${ac}" opacity=".12"/>
    <rect x="12" y="10" width="52" height="18" rx="6" fill="none" stroke="${ac}" stroke-width=".6" opacity=".4"/>
    <text x="38" y="23" text-anchor="middle"
          font-family="system-ui,-apple-system,sans-serif"
          font-size="10" font-weight="700" fill="${ac}">${ic} ${safeTypeLabel}</text>

    <text x="12" y="52"
          font-family="system-ui,-apple-system,sans-serif"
          font-size="13" font-weight="700" fill="${C.text}">${safeTitle}</text>

    <text x="12" y="68"
          font-family="'SFMono-Regular',Consolas,monospace"
          font-size="11" font-weight="600" fill="${C.subtext}">${safeSubtitle}</text>

    <text x="${CARD_W - 10}" y="68" text-anchor="end"
          font-family="system-ui,-apple-system,sans-serif"
          font-size="10.5" font-weight="600" fill="${C.subtle}">${safeRelativeDate}</text>

    <rect width="${CARD_W}" height="${CARD_H}" rx="${RX}" fill="none"
          stroke="${ac}" stroke-width=".6" stroke-opacity=".18"/>
  </g>`
}

function buildFallbackSVG(message = 'No recent history available') {
  return `<svg width="${W}" height="80" viewBox="0 0 ${W} 80"
  xmlns="http://www.w3.org/2000/svg" role="img"
  aria-label="Recently watched — unavailable">
  <rect width="${W}" height="80" rx="12" fill="${C.mantle}"/>
  <text x="${W / 2}" y="46" text-anchor="middle"
        font-family="system-ui,-apple-system,sans-serif"
        font-size="14" fill="${C.muted}">${escapeXml(message)}</text>
</svg>`
}

function buildSVG(items) {
  if (!items.length) return buildFallbackSVG()

  const cards = items.map((item, i) => buildCard(item, i % COLS, Math.floor(i / COLS)))

  return `<!-- assets/generated/recently-watched.svg — auto-generated, do not edit -->
<svg width="${W}" height="${H}" viewBox="0 0 ${W} ${H}"
     xmlns="http://www.w3.org/2000/svg"
     role="img" aria-label="BlackSpirits recently watched on Simkl">
  <defs>
    <linearGradient id="acc" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="${C.purple}"/>
      <stop offset="50%" stop-color="${C.blue}"/>
      <stop offset="100%" stop-color="${C.peach}"/>
    </linearGradient>
    <clipPath id="rc">
      <rect width="${W}" height="${H}" rx="14" ry="14"/>
    </clipPath>
  </defs>

  <g clip-path="url(#rc)">
    <rect width="${W}" height="${H}" fill="${C.base}"/>
    ${cards.join('\n')}
  </g>

  <rect x=".5" y=".5" width="${W - 1}" height="${H - 1}" rx="14" ry="14"
        fill="none" stroke="#cdd6f4" stroke-opacity=".08" stroke-width="1"/>

  <!-- generated: ${new Date().toISOString()} -->
</svg>`
}

// ─── Entry point ──────────────────────────────────────────────────────────────
async function main() {
  mkdirSync(OUT_DIR, { recursive: true })

  if (!CLIENT_ID || !ACCESS_TOKEN) {
    throw new Error('SIMKL_CLIENT_ID or SIMKL_ACCESS_TOKEN not set')
  }

  console.log('📡 Fetching Simkl history…')

  const items = await fetchHistory()

  console.log(`✅ Got ${items.length} recent items after normalisation`)
  items.forEach((i) => {
    console.log(`   ${typeIcon(i.type)} ${i.title} (${i.year || 'n/a'}) — ${relativeDate(i.watchedAt)}`)
  })

  const svg = buildSVG(items)
  writeFileSync(OUT_FILE, svg, 'utf8')
  console.log(`💾 Wrote ${OUT_FILE}`)

  if (!items.length) {
    console.warn('⚠️ Simkl request succeeded, but no usable history items were found.')
  }
}

main().catch((err) => {
  console.error('❌ Failed to generate recently watched SVG:')
  console.error(err)

  mkdirSync(OUT_DIR, { recursive: true })
  writeFileSync(OUT_FILE, buildFallbackSVG('Failed to load Simkl history'), 'utf8')

  process.exit(1)
})
