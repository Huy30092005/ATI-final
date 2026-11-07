import { Router, Request, Response } from 'express';

export const healthRouter = Router();

healthRouter.get('/', (req: Request, res: Response) => {
  const hasGemini = Boolean(process.env.GEMINI_API_KEY && process.env.GEMINI_API_KEY !== 'MY_GEMINI_API_KEY');
  const hasOpenAI = Boolean(process.env.OPENAI_API_KEY && process.env.OPENAI_API_KEY.startsWith('sk-'));

  res.json({
    status: 'healthy',
    backend_engine: 'node_express_hybrid',
    openai_configured: hasOpenAI,
    gemini_configured: hasGemini,
    mongodb_configured: false,
    search_provider: 'arXiv + Semantic Scholar + Live Web',
    version: '1.0.0',
    fastapi_backend_url: process.env.FASTAPI_BACKEND_URL || 'http://localhost:8000',
  });
});
