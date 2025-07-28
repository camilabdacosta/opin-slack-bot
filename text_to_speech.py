import os
from google.cloud import texttospeech
from google.oauth2 import service_account
import nltk
from nltk.tokenize import sent_tokenize
from pydub import AudioSegment
import uuid # Para gerar nomes de arquivo temporários únicos

# --- Configurações (Agora lidas de variáveis de ambiente) ---
# É altamente recomendável definir estas variáveis no ambiente de execução (Docker, Kubernetes, etc.)
# Para desenvolvimento local, você pode usar um arquivo .env e a lib `python-dotenv`
# ou definir as variáveis diretamente no terminal antes de executar o script.

# Caminho para o arquivo JSON de credenciais de serviço do Google Cloud.
# Se a variável de ambiente 'KEY_FILE_PATH' não estiver definida,
# ele usará um caminho padrão dentro do contêiner Docker.
_default_key_file_path_docker = "/opin_slack_bot/credentials/chave.json" # Exemplo de caminho dentro do contêiner Docker
KEY_FILE_PATH = os.getenv("KEY_FILE_PATH", _default_key_file_path_docker)

# O Google Cloud SDK e suas bibliotecas usam a variável de ambiente
# GOOGLE_APPLICATION_CREDENTIALS para auto-autenticação.
# Definimos isso aqui para que a biblioteca `google-cloud-texttospeech` a encontre.
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = KEY_FILE_PATH

# Caminho final onde o arquivo de áudio será salvo dentro do contêiner.
# Se a variável de ambiente 'AUDIO_FILE_PATH' não estiver definida,
# ele usará um caminho padrão dentro do contêiner Docker.
_default_audio_file_path_docker = "/app/output/output_audio.mp3"
AUDIO_FILE_PATH = os.getenv("AUDIO_FILE_PATH", _default_audio_file_path_docker)

# Diretório temporário para armazenar os chunks de áudio.
# Garante que seja um caminho absoluto baseado no diretório de trabalho do Docker.
TEMP_AUDIO_DIR = os.path.join(os.getcwd(), "temp_audio_chunks")

def convert_text_to_speech(text, lang_code='pt-BR', voice_name='pt-BR-Wavenet-E'):
    """
    Converte texto em áudio usando a API Google Cloud Text-to-Speech.
    Divide o texto em frases para respeitar o limite de 5000 bytes da API,
    e concatena os arquivos de áudio resultantes.
    """
    print(f"--- Iniciando Text-to-Speech (Google Cloud) para idioma: {lang_code}, voz: {voice_name} ---")
    print(f"Caminho da chave de serviço (KEY_FILE_PATH): {KEY_FILE_PATH}")
    print(f"Caminho do arquivo de áudio final (AUDIO_FILE_PATH): {AUDIO_FILE_PATH}")
    print(f"Diretório temporário para áudio: {TEMP_AUDIO_DIR}")

    if not text:
        print("Erro: Nenhum texto fornecido para conversão TTS.")
        return None

    try:
        # Tenta carregar as credenciais do arquivo especificado.
        # Se a variável GOOGLE_APPLICATION_CREDENTIALS estiver definida e o arquivo existir,
        # o cliente pode se autenticar automaticamente.
        credentials = service_account.Credentials.from_service_account_file(KEY_FILE_PATH)
        client = texttospeech.TextToSpeechClient(credentials=credentials)
    except Exception as e:
        print(f"Erro ao carregar credenciais do Google Cloud a partir de '{KEY_FILE_PATH}': {e}")
        print("Certifique-se de que KEY_FILE_PATH está correto e que o arquivo JSON existe e é acessível.")
        return None

    # --- NOVO: Dividir o texto em frases para evitar o limite de 5000 bytes ---
    # Garante que o tokenizador 'punkt' do NLTK esteja baixado.
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        print("Tokenizador 'punkt' do NLTK não encontrado. Baixando...")
        nltk.download('punkt')
        print("Tokenizador 'punkt' do NLTK baixado.")

    sentences = sent_tokenize(text, language='portuguese')
    
    temp_audio_files = []
    # Cria o diretório temporário se ele não existir
    os.makedirs(TEMP_AUDIO_DIR, exist_ok=True)

    try:
        for i, sentence in enumerate(sentences):
            # A API Google TTS tem um limite de 5000 bytes UTF-8 por solicitação.
            # sent_tokenize geralmente gera chunks menores, mas é bom ter uma verificação.
            sentence_bytes = sentence.encode('utf-8')
            if len(sentence_bytes) > 4900: # Deixa uma pequena margem de segurança
                print(f"Aviso: A frase {i+1} é muito longa ({len(sentence_bytes)} bytes). "
                      "Isso ainda pode causar um erro se não for dividida ainda mais.")

            synthesis_input = texttospeech.SynthesisInput(text=sentence)
            voice = texttospeech.VoiceSelectionParams(
                language_code=lang_code,
                name=voice_name,
                ssml_gender=texttospeech.SsmlVoiceGender.FEMALE # Você pode ajustar para MALE ou NEUTRAL
            )
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3
            )

            print(f"  -> Enviando chunk {i+1}/{len(sentences)} para a API TTS...")
            response = client.synthesize_speech(
                request={"input": synthesis_input, "voice": voice, "audio_config": audio_config}
            )

            # Salva o chunk de áudio em um arquivo temporário único
            temp_filename = os.path.join(TEMP_AUDIO_DIR, f"temp_audio_chunk_{uuid.uuid4()}.mp3")
            with open(temp_filename, "wb") as out:
                out.write(response.audio_content)
            temp_audio_files.append(temp_filename)
            
        print("  -> Todos os chunks processados. Concatenando arquivos de áudio...")
        
        # Concatena todos os arquivos de áudio temporários em um único arquivo
        final_audio = AudioSegment.empty()
        for f in temp_audio_files:
            final_audio += AudioSegment.from_file(f, format="mp3")

        # Garante que o diretório de destino do arquivo de áudio final exista
        os.makedirs(os.path.dirname(AUDIO_FILE_PATH), exist_ok=True)
        final_audio.export(AUDIO_FILE_PATH, format="mp3")
        
        print(f"Conteúdo de áudio salvo em '{AUDIO_FILE_PATH}'")
        return AUDIO_FILE_PATH

    except Exception as e:
        print(f"Erro durante a conversão Google Cloud Text-to-Speech: {e}")
        return None
    finally:
        # --- Limpeza dos arquivos temporários ---
        print(f"  -> Limpando arquivos de áudio temporários em '{TEMP_AUDIO_DIR}'...")
        for f in temp_audio_files:
            if os.path.exists(f):
                os.remove(f)
        # Tenta remover o diretório temporário se estiver vazio
        try:
            if os.path.exists(TEMP_AUDIO_DIR) and not os.listdir(TEMP_AUDIO_DIR):
                os.rmdir(TEMP_AUDIO_DIR)
        except OSError as e:
            print(f"Aviso: Não foi possível remover o diretório temporário '{TEMP_AUDIO_DIR}': {e}")
        print("  -> Limpeza concluída.")

