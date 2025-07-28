# Bot de Boletins para Slack (Opin-Slack-Bot)

Este projeto automatiza o processo de extrair o conteúdo de boletins em PDF, gerar um resumo em áudio e publicá-lo em um canal do Slack. O fluxo é projetado para ser executado dentro de um contêiner Docker, garantindo um ambiente consistente e facilitando a implantação.

## 🚀 Funcionalidades

1.  **Extração de PDF**: Processa um arquivo PDF para extrair seu conteúdo textual.
2.  **Sumarização de Texto**: Resume o texto extraído (ponto de integração para modelos de linguagem como o Google Gemini/notebookLLM).
3.  **Conversão para Áudio**: Converte o texto resumido em um arquivo de áudio MP3 usando o Google Text-to-Speech (gTTS).
4.  **Publicação no Slack**: Envia o arquivo de áudio gerado, junto com uma mensagem, para um canal específico do Slack.

## 📂 Estrutura do Projeto

```
opin-slack-bot/
├── credentials/
│   └── chave.json         # (Exemplo) Credenciais do Google Cloud para APIs
├── output_audio/          # (Exemplo) Pasta para salvar o áudio gerado
├── venv/                  # Ambiente virtual Python (para desenvolvimento local)
├── .gitignore             # Arquivos e pastas a serem ignorados pelo Git
├── Dockerfile             # Instruções para construir a imagem Docker do projeto
├── main.py                # Script principal que orquestra todo o fluxo
├── pdf_processor.py       # Lógica para processar o PDF e extrair texto
├── requirements.txt       # Lista de dependências Python
├── slack_sender.py        # Lógica para enviar mensagens e arquivos para o Slack
├── summarize_text.py      # Lógica de sumarização (integração com IA)
├── text_to_speech.py      # Lógica para converter texto em áudio (gTTS)
└── README.md              # Este arquivo
```

## ⚙️ Pré-requisitos

*   **Docker e Docker Desktop**: O projeto é containerizado, então o Docker deve estar instalado e em execução na sua máquina. Baixe em [docker.com](https://www.docker.com/products/docker-desktop/ ).
*   **Credenciais de Serviço Google Cloud**: Um arquivo de chave JSON (ex: `chave.json`) é necessário para autenticar com as APIs do Google (como Text-to-Speech ou a API de sumarização).
*   **Token de Bot do Slack**: Um token de API do Slack (começando com `xoxb-`) com as permissões corretas.

## 🛠️ Configuração

### 1. Configuração do Slack
1.  **Crie um App no Slack**: Vá para [api.slack.com/apps](https://api.slack.com/apps ) e crie um novo aplicativo.
2.  **Adicione Permissões (Scopes)**: Em "OAuth & Permissions", adicione os seguintes "Bot Token Scopes":
    *   `chat:write` (para enviar mensagens)
    *   `files:write` (para fazer upload de arquivos)
3.  **Instale o App**: Instale o aplicativo no seu workspace e copie o **Bot User OAuth Token**.
4.  **Convide o Bot**: No canal do Slack desejado (ex: `#podcastopin`), digite `/invite @nome-do-seu-bot` para adicioná-lo.

### 2. Construção da Imagem Docker
Antes de executar o projeto, você precisa construir a imagem Docker. No terminal, na raiz do projeto, execute:
```bash
docker build -t meu-bot-slack-opin .
```
*   `-t meu-bot-slack-opin`: Define o nome (tag) da imagem como `meu-bot-slack-opin`.
*   `.`: Indica que o `Dockerfile` está no diretório atual.

## ▶️ Como Executar

O projeto é executado usando o comando `docker run`. Este comando configura as variáveis de ambiente e os volumes (pastas compartilhadas) necessários para o contêiner funcionar.

**Comando de Execução (para Windows CMD):**
```cmd
docker run -it --rm ^
  -e SLACK_BOT_TOKEN="xoxb-seu-token-aqui" ^
  -e SLACK_CHANNEL_NAME="podcastopin" ^
  -e KEY_FILE_PATH="/app/credentials/chave.json" ^
  -e AUDIO_FILE_PATH="/app/output/audio_final_boletim.mp3" ^
  -v "C:\caminho\para\sua\chave.json":/app/credentials/chave.json ^
  -v "C:\caminho\para\seu\boletim.pdf":/app/input/boletim.pdf ^
  -v "C:\caminho\para\sua\pasta\output_audio":/app/output ^
  meu-bot-slack-opin
```
> **Nota:** Se estiver usando **PowerShell**, substitua o caractere de quebra de linha `^` por `` ` `` (acento grave). Se estiver no **Linux/macOS**, use `\`.

### Explicação dos Parâmetros `docker run`:
*   `--rm`: Remove o contêiner automaticamente após a execução, mantendo o ambiente limpo.
*   `-e NOME="VALOR"`: Define uma **variável de ambiente** dentro do contêiner.
    *   `SLACK_BOT_TOKEN`: Seu token secreto do Slack.
    *   `SLACK_CHANNEL_NAME`: O nome do canal para onde a mensagem será enviada.
    *   `KEY_FILE_PATH`: O caminho *interno* no contêiner para o arquivo de credenciais.
    *   `AUDIO_FILE_PATH`: O caminho *interno* no contêiner onde o áudio será salvo.
*   `-v "Caminho no PC":"Caminho no Contêiner"`: Mapeia uma pasta ou arquivo do seu computador (host) para dentro do contêiner (guest).
    *   **Credenciais**: Mapeia seu arquivo `chave.json` para que o script possa usá-lo.
    *   **Input PDF**: Mapeia o PDF que você quer processar para a pasta `/app/input` do contêiner.
    *   **Output Áudio**: Mapeia uma pasta de saída no seu PC para que o arquivo MP3 gerado dentro do contêiner seja salvo na sua máquina.

**Antes de executar, certifique-se de:**
1.  Substituir `"xoxb-seu-token-aqui"` pelo seu token real.
2.  Ajustar os três caminhos em `-v` para que correspondam aos locais corretos dos arquivos no **seu computador**.
3.  Criar a pasta de `output_audio` no seu computador, se ela não existir.
