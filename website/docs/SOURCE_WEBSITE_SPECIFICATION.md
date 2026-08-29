# Website Specification

**Purpose:** Give Claude a complete marketing-site implementation contract

**Version:** 1.0 | **Date:** 2026-08-28

## Sitemap

/ Home; /services; /workflow-diagnostic; /build-sprint; /transformation; /enterprise; /support; /industries; /method; /training; /security; /about; /insights; /contact; /privacy; /terms; /thank-you; /404.

## Navigation

Logo; Services; Method; Industries; Training; Security; About; primary CTA “Book a fit call.” Mobile menu is keyboard operable, focus trapped when open, Escape closes, current page identified.

## Design direction

Corporate and grounded: deep navy #0B1F33, warm ivory #F7F4EE, slate #425466, restrained copper #B66A3C, white. Editorial serif for display and highly legible sans for body. Real operational photography or process visuals; avoid robots, neon gradients, floating brains, and fake dashboards.

## Responsive

Mobile-first at 320px; content max 1200px; readable line length 60-75 characters; no horizontal overflow; cards become single column; tables scroll with labels; forms retain visible labels; CTA does not cover content.

## Components

Header, footer, hero, proof strip, problem grid, offer cards, workflow before/after, method steps, risk callout, case study, FAQ accordion, testimonial, lead form, qualification form, consent notice, thank-you state, error summary, breadcrumbs, article card.

## Forms

Fit call: name, work email, company, role, website, employee range, state, workflow/problem, urgency, referral source, consent. Never request sensitive data. Server validation, honeypot/rate limit, CSRF strategy appropriate to framework, success ID, CRM/email routing, privacy link, accessible errors.

## Accessibility

WCAG 2.2 AA target: semantic landmarks/headings, keyboard, visible focus, skip link, contrast, labels/instructions, error association, reduced motion, alt text, zoom/reflow, 44px targets where applicable, captions/transcripts, no color-only meaning.

## Performance/security

Target Core Web Vitals green on representative mobile; optimized images/fonts; minimal client JS; CSP and security headers; dependency scanning; no secrets client-side; server-only Stripe/CRM keys; logging without sensitive form bodies; privacy-aware analytics.

## Analytics

Events: nav_cta, fit_call_start, fit_call_submit, fit_call_error, offer_view, faq_open, resource_download, referral_source, checkout_start, checkout_complete. Define event schema, consent state, source/medium, page, offer code, anonymous session ID; never send free-text workflow details to analytics.
