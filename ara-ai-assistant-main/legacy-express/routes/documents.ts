import { Router, Request, Response } from 'express';
import { chunkDocumentText } from '../../src/utils/scoring.ts';
import { IndexedDocument } from '../../src/types/research.ts';

export const documentsRouter = Router();

// Shared in-memory store for active session documents
export const DOCUMENT_STORE: Record<string, IndexedDocument> = {};

// Seed default reference paper
const seedDefaultDocument = () => {
  const seedId = 'doc-seed-vaswani';
  const sampleContent = `Attention Is All You Need (Vaswani et al., 2017)
The dominant sequence transduction models are based on complex recurrent or convolutional neural networks that include an encoder and a decoder. The best performing models also connect the encoder and decoder through an attention mechanism. We propose a new simple network architecture, the Transformer, based solely on attention mechanisms, dispensing with recurrence and convolutions entirely. Experiments on two machine translation tasks show these models to be superior in quality while being more parallelizable and requiring significantly less time to train.

On the WMT 2014 English-to-German translation task, the big transformer model achieves 28.4 BLEU, improving over the existing best results, including ensembles, by over 2 BLEU. On the WMT 2014 English-to-French translation task, our model establishes a new single-model state-of-the-art BLEU score of 41.8 after training for 3.5 days on eight GPUs.

Self-attention, sometimes called intra-attention, is an attention mechanism relating different positions of a single sequence in order to compute a representation of the sequence. Self-attention has been used successfully in a variety of tasks including reading comprehension, abstractive summarization, textual entailment and learning task-independent sentence representations.

The Transformer allows for significantly more parallelization and can reach a new state of the art in translation quality after being trained for as little as twelve hours on eight P100 GPUs.`;

  const chunks = chunkDocumentText(sampleContent, seedId, 600, 100);
  DOCUMENT_STORE[seedId] = {
    id: seedId,
    name: 'Attention_Is_All_You_Need_NeurIPS.pdf',
    file_type: 'pdf',
    size_bytes: sampleContent.length,
    uploaded_at: new Date().toISOString(),
    chunk_count: chunks.length,
    total_words: sampleContent.split(/\s+/).length,
    status: 'ready',
    chunks,
  };
};

seedDefaultDocument();

// List documents
documentsRouter.get('/', (req: Request, res: Response) => {
  res.json(Object.values(DOCUMENT_STORE));
});

// Upload document
documentsRouter.post('/upload', (req: Request, res: Response) => {
  try {
    const { name, content, file_type } = req.body;
    if (!name || !content) {
      return res.status(400).json({ error: 'Missing name or content' });
    }

    const docId = `doc-${Date.now()}`;
    const chunks = chunkDocumentText(content, docId, 700, 120);

    const newDoc: IndexedDocument = {
      id: docId,
      name,
      file_type: file_type === 'pdf' ? 'pdf' : 'txt',
      size_bytes: content.length,
      uploaded_at: new Date().toISOString(),
      chunk_count: chunks.length,
      total_words: content.split(/\s+/).length,
      status: 'ready',
      chunks,
    };

    DOCUMENT_STORE[docId] = newDoc;

    res.json({
      message: `Document '${name}' indexed into ${chunks.length} chunks.`,
      document: newDoc,
    });
  } catch (err: any) {
    res.status(500).json({ error: err.message || 'Upload processing failed' });
  }
});

// Delete document
documentsRouter.delete('/:id', (req: Request, res: Response) => {
  const { id } = req.params;
  if (DOCUMENT_STORE[id]) {
    delete DOCUMENT_STORE[id];
    return res.json({ message: `Document ${id} deleted.` });
  }
  res.status(404).json({ error: 'Document not found' });
});
