// Central API configuration for frontend → backend calls.
//
// Local dev scenario:
// - Backend (banking_app):     http://127.0.0.1:5001
// - Analytics (agent_analytics): http://127.0.0.1:5002
// - Frontend (Vite dev):       http://localhost:5173
//
// Azure Web App scenario:
// - Banking + analytics are served from the same origin as the frontend.
//   - Banking API:    /api
//   - Analytics API:  /analytics/api

const IS_LOCAL = import.meta.env.DEV || 
                 window.location.hostname === 'localhost' || 
                 window.location.hostname === '127.0.0.1';

export const API_URL = IS_LOCAL
  ? 'http://127.0.0.1:5001/api'
  : '/api';

export const ANALYTICS_API_URL = IS_LOCAL
  ? 'http://127.0.0.1:5002/api'
  : '/analytics/api';