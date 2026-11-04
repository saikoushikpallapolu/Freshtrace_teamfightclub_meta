# Frontend

One React/Vite application provides both user interfaces:

| View | Development URL | Backend |
| --- | --- | --- |
| Visual inspection workspace | http://127.0.0.1:5173/ | Product API on 8080 |
| Sensor dashboard | http://127.0.0.1:5173/?view=device | Sensor API on 8081 |

From this directory, run `npm ci` and `npm run dev`. Vite uses loopback port 5173 and fails clearly if it is already occupied. `/api` requests are proxied to the product API; device, notification and telemetry routes go to the sensor API.

Root `.env` supplies optional public `VITE_API_BASE` and `VITE_DEVICE_API_BASE` overrides. Leave them blank for local proxies. Keep keys in server-side variables, never `VITE_*` values. Restart Vite after changing environment settings.

Run `npm run build` for `dist/` and `npm run lint` for static checks. See the [complete setup guide](../docs/setup.md) for backend and hardware startup.
