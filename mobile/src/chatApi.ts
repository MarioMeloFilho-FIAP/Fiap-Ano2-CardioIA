import { CHAT_API_BASE_URL } from './config';
import type { RespostaChat, ResultadoChat } from './chatTypes';

/**
 * Type guard: valida em runtime o JSON da API antes de confiar nele.
 * (Mesmo padrão defensivo de `api.ts` — o tipo do TS some na compilação.)
 */
function ehRespostaChat(x: unknown): x is RespostaChat {
  if (typeof x !== 'object' || x === null) return false;
  const o = x as Record<string, unknown>;
  return typeof o.response === 'string' && typeof o.fonte_resposta === 'string';
}

/**
 * Envia uma mensagem ao assistente e devolve a resposta.
 * Nunca lança: erros viram `{ ok: false, erro }` para a UI tratar num só lugar.
 */
export async function enviarMensagem(mensagem: string, sessionId: string): Promise<ResultadoChat> {
  try {
    const resposta = await fetch(`${CHAT_API_BASE_URL}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: mensagem, session_id: sessionId }),
    });
    const json: unknown = await resposta.json();

    if (!resposta.ok) {
      const erro =
        typeof json === 'object' && json !== null && 'erro' in json
          ? String((json as Record<string, unknown>).erro)
          : `HTTP ${resposta.status}`;
      return { ok: false, erro };
    }

    if (!ehRespostaChat(json)) {
      return { ok: false, erro: 'Resposta inesperada do servidor.' };
    }
    return { ok: true, resposta: json };
  } catch (e) {
    return { ok: false, erro: e instanceof Error ? e.message : 'Falha de rede.' };
  }
}
