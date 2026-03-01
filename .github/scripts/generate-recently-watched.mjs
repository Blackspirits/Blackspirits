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
 *
 * How to get your access token:
 *   1. Go to https://simkl.com/settings/developer/
 *   2. Create an app → get client_id + client_secret
 *   3. Auth via PIN flow: https://simkl.docs.apiary.io/#reference/authentication/pin-authentication
 *   4. Store both as repo secrets (Settings → Secrets → Actions)
 */

import { writeFileSync, mkdirSync } from 'fs'
import { join, dirname } from 'path'
import { fileURLToPath } from 'url'

const __dirname = dirname(fileURLToPath(import.meta.url))
const ROOT      = join(__dirname, '..', '..')
const OUT_DIR   = join(ROOT, 'assets', 'generated')
const OUT_FILE  = join(OUT_DIR, 'recently-watched.svg')

const CLIENT_ID    = process.env.SIMKL_CLIENT_ID
const ACCESS_TOKEN = process.env.SIMKL_ACCESS_TOKEN
const LIMIT        = 6

// ─── Palette (Catppuccin Mocha) ───────────────────────────────────────────────
const C = {
  base:    '#11111b',
  mantle:  '#181825',
  surface: '#1e1e2e',
  overlay: '#313244',
  muted:   '#45475a',
  subtle:  '#585b70',
  text:    '#cdd6f4',
  subtext: '#9399b2',
  lavender:'#b4befe',
  blue:    '#89b4fa',
  purple:  '#cba6f7',
  peach:   '#fab387',
  green:   '#a6e3a1',
  red:     '#f38ba8',
}

// ─── Fetch helpers ────────────────────────────────────────────────────────────
async function simklGet(path) {
  const url = `https://api.simkl.com${path}`
  const res = await fetch(url, {
    headers: {
      'simkl-api-key': CLIENT_ID,
      'Authorization': `Bearer ${ACCESS_TOKEN}`,
      'Content-Type':  'application/json',
    },
  })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`Simkl API ${res.status}: ${text}`)
  }
  return res.json()
}

/** Fetch last N items from history (movies + shows) */
async function fetchHistory() {
  // date_from = 6 months ago as a safety net
  const since = new Date()
  since.setMonth(since.getMonth() - 6)
  const dateFrom = since.toISOString().slice(0, 10)

  const [movies, shows] = await Promise.all([
    simklGet(`/sync/history/movies?date_from=${dateFrom}`).catch(() => []),
    simklGet(`/sync/history/shows?date_from=${dateFrom}`).catch(() => []),
  ])

  const normalised = [
    ...movies.map(m => ({
      type:      'movie',
      title:     m.movie?.title ?? 'Unknown',
      year:      m.movie?.year  ?? '',
      watchedAt: m.watched_at,
      simklId:   m.movie?.ids?.simkl,
    })),
    ...shows.map(s => ({
      type:      'show',
      title:     s.show?.title ?? 'Unknown',
      year:      s.show?.year  ?? '',
      watchedAt: s.last_watched_at ?? s.watched_at,
      simklId:   s.show?.ids?.simkl,
      season:    s.last_watched?.season,
      episode:   s.last_watched?.episode,
    })),
  ]

  // Sort by most recently watched, take top LIMIT
  return normalised
    .sort((a, b) => new Date(b.watchedAt) - new Date(a.watchedAt))
    .slice(0, LIMIT)
}

// ─── SVG helpers ─────────────────────────────────────────────────────────────
function truncate(str, max) {
  if (!str) return ''
  return str.length > max ? str.slice(0, max - 1) + '…' : str
}

function typeIcon(type) {
  return type === 'movie' ? '🎬' : '📺'
}

function typeColor(type) {
  return type === 'movie' ? C.blue : C.peach
}

function relativeDate(iso) {
  if (!iso) return ''
  const diff = Date.now() - new Date(iso).getTime()
  const days = Math.floor(diff / 86400000)
  if (days === 0) return 'today'
  if (days === 1) return 'yesterday'
  if (days < 7)  return `${days}d ago`
  if (days < 30) return `${Math.floor(days / 7)}w ago`
  return `${Math.floor(days / 30)}mo ago`
}

// ─── SVG layout constants ─────────────────────────────────────────────────────
const W      = 900   // total width
const H      = 220   // total height
const PAD    = 20    // outer padding
const COLS   = 3     // items per row
const ROWS   = 2
const CARD_W = (W - PAD * 2 - (COLS - 1) * 12) / COLS   // ≈ 276
const CARD_H = (H - PAD * 2 - (ROWS - 1) * 12) / ROWS   // ≈ 86
const RX     = 10   // card border-radius

function buildCard(item, col, row) {
  const x  = PAD + col * (CARD_W + 12)
  const y  = PAD + row * (CARD_H + 12)
  const ac = typeColor(item.type)
  const ic = typeIcon(item.type)

  const subtitle = item.type === 'show' && item.season
    ? `S${String(item.season).padStart(2,'0')}E${String(item.episode ?? 0).padStart(2,'0')}`
    : String(item.year)

  return `
  <!-- Card: ${item.title} -->
  <g transform="translate(${x},${y})">
    <!-- card bg -->
    <rect width="${CARD_W}" height="${CARD_H}" rx="${RX}" fill="${C.mantle}"/>
    <!-- left accent bar -->
    <rect width="3" height="${CARD_H}" rx="1.5" fill="${ac}" opacity=".7"/>

    <!-- type badge -->
    <rect x="12" y="10" width="52" height="18" rx="6" fill="${ac}" opacity=".12"/>
    <rect x="12" y="10" width="52" height="18" rx="6" fill="none" stroke="${ac}" stroke-width=".6" opacity=".4"/>
    <text x="38" y="23" text-anchor="middle"
          font-family="system-ui,-apple-system,sans-serif"
          font-size="10" font-weight="700" fill="${ac}">${ic} ${item.type === 'movie' ? 'Movie' : 'Show'}</text>

    <!-- title -->
    <text x="12" y="52"
          font-family="system-ui,-apple-system,sans-serif"
          font-size="13" font-weight="700" fill="${C.text}">${truncate(item.title, 28)}</text>

    <!-- subtitle (year or S/E) -->
    <text x="12" y="68"
          font-family="'SFMono-Regular',Consolas,monospace"
          font-size="11" fill="${C.subtle}">${subtitle}</text>

    <!-- relative date (right-aligned) -->
    <text x="${CARD_W - 10}" y="68" text-anchor="end"
          font-family="system-ui,-apple-system,sans-serif"
          font-size="10" fill="${C.muted}">${relativeDate(item.watchedAt)}</text>

    <!-- subtle border -->
    <rect width="${CARD_W}" height="${CARD_H}" rx="${RX}" fill="none"
          stroke="${ac}" stroke-width=".6" stroke-opacity=".18"/>
  </g>`
}

// ─── Fallback SVG (no items / API error) ─────────────────────────────────────
function buildFallbackSVG() {
  return `<svg width="${W}" height="80" viewBox="0 0 ${W} 80"
  xmlns="http://www.w3.org/2000/svg" role="img"
  aria-label="Recently watched — unavailable">
  <rect width="${W}" height="80" rx="12" fill="${C.mantle}"/>
  <text x="${W/2}" y="46" text-anchor="middle"
        font-family="system-ui,-apple-system,sans-serif"
        font-size="14" fill="${C.muted}">No recent history available</text>
</svg>`
}

// ─── Main SVG builder ─────────────────────────────────────────────────────────
function buildSVG(items) {
  if (!items.length) return buildFallbackSVG()

  const cards = items.map((item, i) => buildCard(item, i % COLS, Math.floor(i / COLS)))

  return `<!-- assets/generated/recently-watched.svg — auto-generated, do not edit -->
<svg width="${W}" height="${H}" viewBox="0 0 ${W} ${H}"
     xmlns="http://www.w3.org/2000/svg"
     role="img" aria-label="BlackSpirits recently watched on Simkl">
  <defs>
    <linearGradient id="acc" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%"   stop-color="${C.purple}"/>
      <stop offset="50%"  stop-color="${C.blue}"/>
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

  <!-- border -->
  <rect x=".5" y=".5" width="${W-1}" height="${H-1}" rx="14" ry="14"
        fill="none" stroke="#cdd6f4" stroke-opacity=".08" stroke-width="1"/>

  <!-- generated timestamp (invisible, for cache busting) -->
  <!-- generated: ${new Date().toISOString()} -->
</svg>`
}

// ─── Entry point ─────────────────────────────────────────────────────────────
async function main() {
  if (!CLIENT_ID || !ACCESS_TOKEN) {
    console.warn('⚠️  SIMKL_CLIENT_ID or SIMKL_ACCESS_TOKEN not set — writing fallback SVG')
    mkdirSync(OUT_DIR, { recursive: true })
    writeFileSync(OUT_FILE, buildFallbackSVG(), 'utf8')
    return
  }

  console.log('📡 Fetching Simkl history…')
  let items = []
  try {
    items = await fetchHistory()
    console.log(`✅ Got ${items.length} items`)
    items.forEach(i => console.log(`   ${typeIcon(i.type)} ${i.title} (${i.year}) — ${relativeDate(i.watchedAt)}`))
  } catch (err) {
    console.error('❌ Simkl API error:', err.message)
    console.warn('⚠️  Writing fallback SVG')
  }

  mkdirSync(OUT_DIR, { recursive: true })
  const svg = buildSVG(items)
  writeFileSync(OUT_FILE, svg, 'utf8')
  console.log(`💾 Wrote ${OUT_FILE}`)
}

main().catch(err => {
  console.error(err)
  process.exit(1)
})
