# 5edma.tn — Frontend

Next.js (App Router) web app for 5edma.tn. See [`../docs/ARCHITECTURE.md`](../docs/ARCHITECTURE.md)
for how this fits together with the backend.

## Setup

```bash
npm install
copy .env.local.example .env.local   # then fill in NEXT_PUBLIC_API_URL / NEXT_PUBLIC_SITE_URL
npm run dev
```

Open [http://localhost:3000](http://localhost:3000). The backend must be running
separately (see [`../backend/README.md`](../backend/README.md)) — `NEXT_PUBLIC_API_URL`
points at it.

## Stack

- Next.js 16 (App Router, Turbopack), React 19, TypeScript
- Tailwind CSS **v4** — `app/globals.css` uses `@import "tailwindcss";`, not the v3
  `@tailwind` directives (they compile silently but produce no utility classes)
- Framer Motion for animation
- `lib/api.ts` — typed fetch wrapper around the backend API, attaches the JWT and
  normalizes error shapes (`apiErrorMessage`)
- `contexts/AuthContext.tsx` — current user/profile, used by `lib/hooks.ts`'s
  `useRequireAuth()` role guard

## Project layout

```
frontend/
  app/
    page.tsx              Landing page
    login/, register/     Auth
    dashboard/, profile/  Role-aware authenticated home + profile editor
    jobs/, services/      Public listing + detail pages (guest-visible),
                           plus /new and /mine management pages
    bookings/, applications/, wallet/, admin/, chat/[jobId]/
    sitemap.ts, robots.ts Auto-generated SEO routes
    icon.png, apple-icon.png, og-image (in public/)  Favicon / share image, generated from the logo
  components/              Nav, PageTransition, shared UI primitives (ui.tsx)
  contexts/                AuthContext
  lib/                     api.ts, types.ts, hooks.ts
```

## Checks

```bash
npx tsc --noEmit
npm run lint
npm run build
```

## Visual verification

This app had a real bug (Tailwind v4 syntax mismatch — see ARCHITECTURE.md) that
`tsc`/`lint`/`build` all passed cleanly while the entire UI rendered unstyled. Don't
trust type-checks alone for UI changes — actually render the page.
