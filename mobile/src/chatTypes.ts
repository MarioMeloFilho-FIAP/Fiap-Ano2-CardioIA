/** Contrato de dados entre o app mobile e a API do assistente (Fase 5). */

/** Papel de quem enviou a mensagem, para renderizar a bolha. */
export type Papel = 'usuario' | 'assistente';

/** Uma mensagem exibida na tela de chat. */
export interface Mensagem {
  id: string;
  papel: Papel;
  texto: string;
  // Metadados de NLU (só nas respostas do assistente).
  intent?: string | null;
  emergencia?: boolean;
}

/** Resposta de POST /api/chat (espelha o payload do backend Flask). */
export interface RespostaChat {
  response: string;
  intent: string | null;
  confidence: number;
  origem_nlu: string;
  fonte_resposta: string; // 'dialogo' | 'emergencia' | 'llm' | 'fallback'
  session_id: string;
}

/**
 * Resultado da chamada à API como UNIÃO DISCRIMINADA: o compilador obriga a
 * tratar sucesso e erro — mesmo padrão de `api.ts` (Fase 4).
 */
export type ResultadoChat =
  | { ok: true; resposta: RespostaChat }
  | { ok: false; erro: string };
