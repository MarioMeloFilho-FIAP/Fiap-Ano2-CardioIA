# Roteiro do vídeo — CardioIA Mobile (Ir Além 2)

Demonstração do app React Native consumindo a API Flask. Duração alvo: **≤ 3 min**.

| Tempo | Cena |
|---|---|
| 0:00 | Mostrar o backend rodando (`make web`) e, rapidamente, a interface web. |
| 0:30 | Abrir o app no celular/emulador; explicar a tela (seletor de modelo, botões). |
| 1:00 | Escolher uma imagem de **PNEUMONIA** → *Classificar* → resultado vermelho + confiança + Grad-CAM destacando a região. |
| 1:45 | Escolher uma imagem **NORMAL** → resultado verde. |
| 2:15 | Trocar o modelo (Transfer ↔ CNN do zero) e comparar. |
| 2:40 | Encerrar reforçando que é **apoio à decisão** (não diagnóstico). |

## Dicas de gravação

- **Forma mais prática:** Expo Web + Device Mode do Chrome (`npx expo start --web`,
  depois `Cmd/Ctrl + Shift + M`) — grava a tela já no formato de celular.
- **Forma mais fiel:** emulador Android (Android Studio) ou celular físico com Expo Go.
- Tenha 1–2 imagens de cada classe à mão (copie de `data/chest_xray_subset/test/`).
- Confirme antes que os modelos estão treinados (`make train`) e o backend no ar.
