# Frontend API client

`client.js` centralizes the visual API base, JSON errors, retry-safe mutation headers, and URLs for media, samples, and analysis artifacts. The default is same-origin `/api`, proxied by Vite to port 8080. `VITE_API_BASE` is a public deployment override; credentials stay server-side.
