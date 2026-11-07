import express from 'express';
import { createServer as createViteServer } from 'vite';
import path from 'path';
import { fileURLToPath } from 'url';
import dotenv from 'dotenv';

import { healthRouter } from './routes/health.ts';
import { documentsRouter } from './routes/documents.ts';
import { researchRouter } from './routes/research.ts';
import { exportRouter } from './routes/export.ts';

dotenv.config();

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const projectRoot = path.resolve(__dirname, '..');

export const app = express();
const PORT = process.env.PORT ? parseInt(process.env.PORT, 10) : 3000;

app.use(express.json({ limit: '25mb' }));
app.use(express.urlencoded({ extended: true, limit: '25mb' }));

// Mount modular API routes
app.use('/api/health', healthRouter);
app.use('/api/documents', documentsRouter);
app.use('/api/research', researchRouter);
app.use('/api/export', exportRouter);

// Start server and mount Vite
export async function startServer() {
  if (process.env.NODE_ENV !== 'production') {
    const vite = await createViteServer({
      root: projectRoot,
      server: { middlewareMode: true },
      appType: 'spa',
    });
    app.use(vite.middlewares);
  } else {
    app.use(express.static(path.resolve(projectRoot, 'dist')));
    app.get('*', (req, res) => {
      res.sendFile(path.resolve(projectRoot, 'dist', 'index.html'));
    });
  }

  app.listen(PORT, '0.0.0.0', () => {
    console.log(`ARA Backend Server running on http://0.0.0.0:${PORT}`);
  });
}

// Auto-start if invoked directly
startServer();
