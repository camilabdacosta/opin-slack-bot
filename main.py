import os
import sys
import re
from urllib.parse import urlparse

# --- FORCE UNSET REQUESTS_CA_BUNDLE HERE ---
if 'REQUESTS_CA_BUNDLE' in os.environ:
    print(f"Attempting to delete REQUESTS_CA_BUNDLE: {os.environ['REQUESTS_CA_BUNDLE']}")
    del os.environ['REQUESTS_CA_BUNDLE']
    print("REQUESTS_CA_BUNDLE deleted from os.environ for this script session.")
else:
    print("REQUESTS_CA_BUNDLE not found in os.environ at script start.")
print(f"REQUESTS_CA_BUNDLE (after deletion attempt): {os.getenv('REQUESTS_CA_BUNDLE')}")
# ---------------------------------------------

from text_to_speech import convert_text_to_speech
from pdf_processor import extract_text_from_pdf
from summarize_text import summarize
from slack_sender import send_to_slack, TARGET_CHANNEL_NAME

# Template para a mensagem do Slack
INITIAL_COMMENT_TEMPLATE = "Olá aqui é automação de OPIN e gostaria de compartilhar o resumo do Boletim Numero {bulletin_number}"

def get_bulletin_number_from_filepath(pdf_filepath):
    """Attempts to extract the bulletin number from the PDF filename based on known patterns."""
    try:
        filename = os.path.basename(pdf_filepath)
        # --- LINHA DE DEBUG ADICIONADA: Mostra o nome do arquivo sendo processado ---
        print(f"DEBUG: Processando filename para extração do boletim: '{filename}'")
        
        # --- NOVO: Tenta o padrão B<YY>-<NN>.pdf -> NN/YYYY ---
        match_b_pattern = re.search(r"B(\d{2})-(\d{3})\.pdf", filename, re.IGNORECASE)
        if match_b_pattern:
            year_short = match_b_pattern.group(1)
            nn_part = match_b_pattern.group(2)
            year_full = f"20{year_short}" # Simples suposição para o ano 20xx
            # --- LINHA DE DEBUG ADICIONADA: Confirma se o padrão B foi encontrado ---
            print(f"DEBUG: Padrão 'B<YY>-<NN>.pdf' encontrado. Boletim extraído: {nn_part}/{year_full}")
            return f"{nn_part}/{year_full}"
        
        # --- NOVO: Tenta o padrão D<YY>-<NNN>-<NNN>.pdf -> NNN/YYYY ---
        # Este é para o formato D25-019-021.pdf, onde o segundo grupo de 3 dígitos é o número.
        match_d_pattern = re.search(r"D(\d{2})-(\d{3})-(\d{3})\.pdf", filename, re.IGNORECASE)
        if match_d_pattern:
            year_short = match_d_pattern.group(1)
            num_part = match_d_pattern.group(2) # Captura o segundo grupo de 3 dígitos
            year_full = f"20{year_short}"
            # --- LINHA DE DEBUG ADICIONADA: Confirma se o padrão D foi encontrado ---
            print(f"DEBUG: Padrão 'D<YY>-<NNN>-<NNN>.pdf' encontrado. Boletim extraído: {num_part}/{year_full}")
            return f"{num_part}/{year_full}"

        # --- MENSAGEM ATUALIZADA: Mais clara quando nenhum padrão é encontrado ---
        print(f"Aviso: Nenhuma regex de nome de arquivo correspondente encontrada para '{filename}'. Retornando '(não encontrado)'.")

    except Exception as e:
        print(f"Erro ao extrair número do boletim do nome do arquivo '{filename}': {e}")
        pass # Ignora erros durante a extração e retorna o fallback
    
    return "(não encontrado)" # Fallback se nenhum padrão for encontrado ou houver erro

def main():
    print("--- Iniciando Pipeline Open Insurance Slack Bot (Versão PDF - Arquivo Local) ---")

    # --- Check Slack Token --- 
    slack_token = os.environ.get("SLACK_BOT_TOKEN")
    if not slack_token:
        print("""
        **********************************************************************
        * ERROR: SLACK_BOT_TOKEN environment variable is not set.          *
        * *
        * Before running the main script, please:                            *
        * 1. Create a Slack App (https://api.slack.com/apps).                *
        * 2. Add scopes: files:write, chat:write                             *
        * 3. Install the app to your workspace.                              *
        * 4. Copy the Bot User OAuth Token (starts with xoxb-).              *
        * 5. Set the SLACK_BOT_TOKEN environment variable.                   *
        * (e.g., export SLACK_BOT_TOKEN=\"xoxb-your-token-here\")         *
        * 6. Ensure the bot is invited to the channel: {channel}             *
        * 7. Ensure 'pdftotext' (from poppler-utils) is installed.           *
        * (e.g., sudo apt-get update && sudo apt-get install poppler-utils)*
        **********************************************************************
        """.format(channel=TARGET_CHANNEL_NAME))
        sys.exit(1)
    else:
        print("SLACK_BOT_TOKEN encontrado. Pressupondo que poppler-utils esteja instalado. Executando...")

    # --- Step 1: Get PDF File Path Manually --- 
    try:
        pdf_filepath_input = input("\nPor favor, cole o CAMINHO COMPLETO para o arquivo PDF do boletim baixado e pressione Enter:\n(Ex: C:\\Users\\SeuUsuario\\Downloads\\B25-021.pdf ou /home/usuario/Downloads/B25-021.pdf)\n> ").strip()
        
        if not pdf_filepath_input:
            print("Erro: Nenhum caminho fornecido. Saindo.")
            sys.exit(1)
        pdf_filepath_input = pdf_filepath_input.strip("\"'")
            
        if not pdf_filepath_input.lower().endswith(".pdf"):
            print("Erro: O caminho fornecido não termina com .pdf. Saindo.")
            sys.exit(1)
        if not os.path.exists(pdf_filepath_input):
            print(f"Erro: O arquivo não foi encontrado no caminho especificado: {pdf_filepath_input}. Verifique o caminho e tente novamente. Saindo.")
            sys.exit(1)
            
    except EOFError:
        print("\nEntrada cancelada. Saindo.")
        sys.exit(1)
    except Exception as e:
        print(f"Erro ao processar o caminho do arquivo: {e}. Saindo.")
        sys.exit(1)

    pdf_filepath = pdf_filepath_input
    print(f"Caminho do arquivo PDF recebido e validado: {pdf_filepath}")
    bulletin_number = get_bulletin_number_from_filepath(pdf_filepath)
    print(f"Número do boletim extraído (ou padrão): {bulletin_number}")

    # --- Step 2: Extract Text from PDF (Download step removed) --- 
    print("\nEtapa 2: Extraindo texto do PDF local...")
    extracted_text = extract_text_from_pdf(pdf_filepath)
    if not extracted_text:
        print("Pipeline finalizada: Falha ao extrair texto do PDF.")
        sys.exit(1)
    print(f"Texto extraído com sucesso (comprimento: {len(extracted_text)} caracteres).")

    # --- Step 3: Summarize Text --- 
    print("\nEtapa 3: Gerando resumo do texto...")
    summary_text = summarize(extracted_text)
    print(f"Resumo gerado (ou texto original retornado).")

    # --- Step 4: Convert Summary to Speech --- 
    print("\nEtapa 4: Convertendo resumo para áudio...")
    audio_filepath = convert_text_to_speech(summary_text, lang_code='pt-BR', voice_name='pt-BR-Wavenet-E')
    if not audio_filepath:
        print("Pipeline finalizada: Falha ao gerar arquivo de áudio.")
        sys.exit(1)
    print(f"Áudio gerado com sucesso: {audio_filepath}")

    # --- Step 5: Send to Slack --- 
    print("\nEtapa 5: Enviando para o Slack...")
    initial_comment = INITIAL_COMMENT_TEMPLATE.format(bulletin_number=bulletin_number)
    success = send_to_slack(audio_filepath, bulletin_number, initial_comment)

    if success:
        print("Envio para o Slack realizado com sucesso!")
    else:
        print("Falha ao enviar para o Slack. Verifique os logs e a configuração do token/permissões.")

    # --- Step 6: Cleanup --- 
    print("\nEtapa 6: Limpeza...")
    try:
        if audio_filepath and os.path.exists(audio_filepath):
            os.remove(audio_filepath)
            print(f"Arquivo de áudio temporário removido: {audio_filepath}")
    except Exception as e:
        print(f"Erro durante a limpeza do arquivo de áudio temporário: {e}")

    print("\n--- Pipeline Concluído --- ")

if __name__ == "__main__":
    main()