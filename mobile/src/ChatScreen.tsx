import { useRef, useState } from 'react';
import {
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';

import { enviarMensagem } from './chatApi';
import type { Mensagem } from './chatTypes';

/** Gera um id de sessão simples (sem depender de crypto no RN). */
function novaSessao(): string {
  return `${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

const BOAS_VINDAS: Mensagem = {
  id: 'welcome',
  papel: 'assistente',
  texto:
    'Olá! Sou o assistente virtual do CardioIA. Posso orientar sobre sintomas, ' +
    'consultas, exames, medicamentos e hábitos saudáveis. Como posso ajudar?',
};

export default function ChatScreen() {
  const sessaoId = useRef<string>(novaSessao()).current;
  const scrollRef = useRef<ScrollView>(null);
  const [mensagens, setMensagens] = useState<Mensagem[]>([BOAS_VINDAS]);
  const [texto, setTexto] = useState('');
  const [carregando, setCarregando] = useState(false);

  const rolarFim = () => scrollRef.current?.scrollToEnd({ animated: true });

  const enviar = async () => {
    const msg = texto.trim();
    if (!msg || carregando) return;
    setTexto('');
    setMensagens((atual) => [
      ...atual,
      { id: `u-${Date.now()}`, papel: 'usuario', texto: msg },
    ]);
    setCarregando(true);
    setTimeout(rolarFim, 50);

    const res = await enviarMensagem(msg, sessaoId);
    const resposta: Mensagem = res.ok
      ? {
          id: `a-${Date.now()}`,
          papel: 'assistente',
          texto: res.resposta.response,
          intent: res.resposta.intent,
          emergencia: res.resposta.fonte_resposta === 'emergencia',
        }
      : { id: `e-${Date.now()}`, papel: 'assistente', texto: `⚠️ ${res.erro}` };

    setMensagens((atual) => [...atual, resposta]);
    setCarregando(false);
    setTimeout(rolarFim, 50);
  };

  return (
    <KeyboardAvoidingView
      style={styles.wrapper}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
    >
      <ScrollView
        ref={scrollRef}
        contentContainerStyle={styles.mensagens}
        onContentSizeChange={rolarFim}
      >
        {mensagens.map((m) => (
          <View
            key={m.id}
            style={[
              styles.bolha,
              m.papel === 'usuario' ? styles.bolhaUsuario : styles.bolhaAssistente,
              m.emergencia && styles.bolhaEmergencia,
            ]}
          >
            <Text style={m.papel === 'usuario' ? styles.textoUsuario : styles.textoAssistente}>
              {m.texto}
            </Text>
            {m.papel === 'assistente' && m.intent && (
              <Text style={styles.meta}>intenção: {m.intent}</Text>
            )}
          </View>
        ))}
        {carregando && <ActivityIndicator color="#1565c0" style={{ marginTop: 8 }} />}
      </ScrollView>

      <View style={styles.entrada}>
        <TextInput
          style={styles.input}
          value={texto}
          onChangeText={setTexto}
          placeholder="Descreva sua dúvida ou sintoma…"
          onSubmitEditing={enviar}
          returnKeyType="send"
          editable={!carregando}
        />
        <Pressable
          style={[styles.botao, (!texto.trim() || carregando) && styles.botaoOff]}
          onPress={enviar}
          disabled={!texto.trim() || carregando}
        >
          <Text style={styles.botaoTexto}>Enviar</Text>
        </Pressable>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  wrapper: { flex: 1, backgroundColor: '#f4f6f9' },
  mensagens: { padding: 16, gap: 10 },
  bolha: { maxWidth: '85%', padding: 12, borderRadius: 16 },
  bolhaUsuario: { alignSelf: 'flex-end', backgroundColor: '#1565c0', borderBottomRightRadius: 4 },
  bolhaAssistente: {
    alignSelf: 'flex-start',
    backgroundColor: '#fff',
    borderWidth: 1,
    borderColor: '#dfe6ee',
    borderBottomLeftRadius: 4,
  },
  bolhaEmergencia: { backgroundColor: '#fdecea', borderColor: '#c62828' },
  textoUsuario: { color: '#fff', fontSize: 15, lineHeight: 21 },
  textoAssistente: { color: '#1a2430', fontSize: 15, lineHeight: 21 },
  meta: { marginTop: 6, fontSize: 11, color: '#7a8697' },
  entrada: {
    flexDirection: 'row',
    gap: 8,
    padding: 12,
    borderTopWidth: 1,
    borderTopColor: '#e2e8f0',
    backgroundColor: '#fff',
  },
  input: {
    flex: 1,
    paddingHorizontal: 14,
    paddingVertical: 10,
    borderWidth: 1,
    borderColor: '#c6d0dd',
    borderRadius: 22,
    fontSize: 15,
  },
  botao: {
    paddingHorizontal: 18,
    justifyContent: 'center',
    backgroundColor: '#1565c0',
    borderRadius: 22,
  },
  botaoOff: { backgroundColor: '#9bb4d1' },
  botaoTexto: { color: '#fff', fontWeight: '700' },
});
