# summarize_text.py

# NLTK data path configuration (important for environments where default path might not work)
import nltk
import os
if not os.path.exists("/home/ubuntu/nltk_data"):
    nltk.download("punkt", download_dir="/home/ubuntu/nltk_data")
nltk.data.path.append("/home/ubuntu/nltk_data")

from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer as Summarizer # Using LSA
from sumy.nlp.stemmers import Stemmer
from sumy.utils import get_stop_words

LANGUAGE = "portuguese" # Assuming bulletins are in Portuguese
SENTENCES_COUNT = 7      # Number of sentences in the summary (adjust as needed)

def summarize(text):
    """
    Summarizes the input text using the Sumy library (LSA algorithm).

    Args:
        text (str): The text content to summarize (extracted from PDF).

    Returns:
        str: The summarized text, or the original text if summarization fails.
    """
    print(f"--- Running Summarizer (Sumy LSA - {SENTENCES_COUNT} sentences) ---")
    if not text:
        print("Warning: No text provided for summarization.")
        return "(Conteúdo vazio ou não extraído do boletim)"

    try:
        # Initialize parser and tokenizer for the specified language
        parser = PlaintextParser.from_string(text, Tokenizer(LANGUAGE))
        stemmer = Stemmer(LANGUAGE)

        # Initialize the LSA summarizer
        summarizer = Summarizer(stemmer)
        summarizer.stop_words = get_stop_words(LANGUAGE)

        # Generate the summary
        summary_sentences = []
        for sentence in summarizer(parser.document, SENTENCES_COUNT):
            summary_sentences.append(str(sentence))

        # Join the sentences into a single string
        summary = " ".join(summary_sentences)

        if not summary:
            print("Warning: Summarization resulted in empty text. Returning original.")
            return text # Fallback to original text if summary is empty

        print(f"Successfully summarized text (length: {len(summary)} chars).")
        return summary

    except Exception as e:
        print(f"Error during Sumy summarization: {e}")
        print("Falling back to original text.")
        # Optionally log the full traceback for debugging
        # import traceback
        # traceback.print_exc()
        return text # Fallback to original text on error

# Example usage (for testing)
if __name__ == "__main__":
    # Simulate longer text extracted from a PDF
    sample_text = ("O Open Insurance, ou Sistema de Seguros Aberto, é a possibilidade de consumidores de produtos e serviços de seguros, previdência complementar aberta e capitalização compartilharem, de forma segura, seus dados entre diferentes sociedades autorizadas/credenciadas pela Susep. "
                   "Este compartilhamento é feito por meio de APIs abertas, com consentimento do consumidor. O objetivo principal é aumentar a competitividade no setor, permitindo que novas soluções e produtos sejam oferecidos aos clientes. "
                   "A implementação ocorre em fases, seguindo um cronograma estabelecido pela SUSEP e pelo CNSP. A Fase 1 envolveu o compartilhamento de dados públicos das seguradoras. A Fase 2 focou no compartilhamento de dados cadastrais e de apólices dos clientes, sempre com consentimento. "
                   "A Fase 3 permite a iniciação de serviços, como cotações e pagamentos, através das APIs. É crucial que as participantes sigam os padrões de segurança e experiência do usuário definidos nos manuais. "
                   "Os boletins informativos servem para comunicar atualizações, prazos e orientações técnicas às participantes. A adesão e conformidade são monitoradas de perto pelos órgãos reguladores. Novas funcionalidades e ajustes nas APIs são comunicados através destes boletins e do portal do desenvolvedor.")

    print(f"Original Text (length {len(sample_text)}):\n{sample_text}")
    summary_result = summarize(sample_text)
    print(f"\nSummary Result (length {len(summary_result)}):\n{summary_result}")

