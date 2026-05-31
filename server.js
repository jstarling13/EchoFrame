require('dotenv').config();
const express    = require('express');
const cors       = require('cors');
const rateLimit  = require('express-rate-limit');
const helmet     = require('helmet');
const stripe     = require('stripe')(process.env.STRIPE_SECRET_KEY);

// ── Validate required env vars at startup ─────────────────────────────────────
const REQUIRED_ENV = ['STRIPE_SECRET_KEY', 'CLIENT_URL'];
const missing = REQUIRED_ENV.filter(k => !process.env[k]);
if (missing.length) {
  console.error(`[EchoFrame] Missing required env vars: ${missing.join(', ')}`);
  process.exit(1);
}

const app = express();

// Security headers (CSP, X-Frame-Options, nosniff, HSTS, etc.)
app.use(helmet({
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      scriptSrc:  ["'self'"],
      styleSrc:   ["'self'", "'unsafe-inline'"],
      imgSrc:     ["'self'", 'data:'],
      connectSrc: ["'self'", 'https://api.stripe.com'],
      frameSrc:   ["'none'"],
      objectSrc:  ["'none'"],
    },
  },
}));

// CORS — explicit allowlist only, no wildcard fallback
const ALLOWED_ORIGINS = (process.env.CLIENT_URL || '')
  .split(',')
  .map(o => o.trim())
  .filter(Boolean);

app.use(cors({
  origin: (origin, callback) => {
    // Allow same-origin and explicitly listed origins only
    if (!origin || ALLOWED_ORIGINS.includes(origin)) {
      callback(null, true);
    } else {
      callback(new Error('CORS: origin not allowed'));
    }
  },
  methods: ['GET', 'POST', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization'],
}));

app.use(express.json());

// ── Rate limiting ─────────────────────────────────────────────────────────────
const checkoutLimiter = rateLimit({
  windowMs: 60 * 1000,  // 1 minute
  max: 10,
  standardHeaders: true,
  legacyHeaders: false,
  message: { error: 'Too many requests. Please try again later.' },
});

// ── Products — loaded from env vars, not hardcoded ───────────────────────────
// Set in .env: PRICE_ID_MONTHLY_CLARITY_REPORT, PRICE_ID_BUSINESS_AUDIT, PRICE_ID_COMPETITOR_REPORT
const ECHOFRAME_PRODUCTS = {
  'monthly-clarity-report': {
    priceId: process.env.PRICE_ID_MONTHLY_CLARITY_REPORT,
    mode: 'subscription',
  },
  'business-audit': {
    priceId: process.env.PRICE_ID_BUSINESS_AUDIT,
    mode: 'payment',
  },
  'competitor-report': {
    priceId: process.env.PRICE_ID_COMPETITOR_REPORT,
    mode: 'payment',
  },
};

const VALID_PRODUCT_IDS = new Set(Object.keys(ECHOFRAME_PRODUCTS));

// ── Routes ─────────────────────────────────────────────────────────────────────
app.post('/create-checkout-session', checkoutLimiter, async (req, res) => {
  try {
    const { productId } = req.body;

    if (typeof productId !== 'string' || !VALID_PRODUCT_IDS.has(productId)) {
      return res.status(400).json({ error: 'Invalid product selected.' });
    }

    const product = ECHOFRAME_PRODUCTS[productId];

    if (!product.priceId) {
      console.error(`[EchoFrame] Missing price ID for product: ${productId}`);
      return res.status(500).json({ error: 'Product configuration error.' });
    }

    const session = await stripe.checkout.sessions.create({
      line_items: [{ price: product.priceId, quantity: 1 }],
      mode: product.mode,
      success_url: `${process.env.CLIENT_URL}/success?session_id={CHECKOUT_SESSION_ID}`,
      cancel_url:  `${process.env.CLIENT_URL}/cancel`,
    });

    res.json({ url: session.url });

  } catch (error) {
    // Log internal details server-side only; send generic message to client
    console.error('[EchoFrame] Stripe error:', error.message);
    res.status(500).json({ error: 'Internal Server Error' });
  }
});

const PORT = process.env.PORT || 4242;
app.listen(PORT, () => console.log(`[EchoFrame] Revenue engine running on port ${PORT}`));
