# Usa uma imagem base Python oficial leve e estável
FROM python:3.9-slim-buster

# Define o diretório de trabalho dentro do contêiner
WORKDIR /app

# Copia o arquivo de requisitos para o diretório de trabalho
COPY requirements.txt .

# Instala as dependências do sistema operacional necessárias
# - build-essential: Para compilar extensões C/C++ de pacotes Python (inclui gcc, make, etc.)
# - pkg-config: Ferramenta para gerenciar flags de compilação para bibliotecas
# - poppler-utils: Para 'pdftotext' (extração de PDF)
# - ffmpeg: Para 'pydub' (processamento de áudio)
# - libffi-dev: Necessário para a biblioteca `cffi` (usada por `cryptography` e outros)
# - libssl-dev: Necessário para compilar módulos que usam OpenSSL (ex: `cryptography`, `requests`)
# - zlib1g-dev: Necessário para bibliotecas de compressão
# - libfreetype6-dev: Necessário para manipulação de fontes, usada por PyMuPDF
# - libfontconfig1-dev: Também para configuração de fontes, usada por PyMuPDF
# - libjpeg-dev: Para manipulação de imagens JPEG em PDFs, usada por PyMuPDF
# - libpng-dev: Para manipulação de imagens PNG em PDFs, usada por PyMuPDF
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        pkg-config \
        poppler-utils \
        ffmpeg \
        libffi-dev \
        libssl-dev \
        zlib1g-dev \
        libfreetype6-dev \
        libfontconfig1-dev \
        libjpeg-dev \
        libpng-dev \
    && rm -rf /var/lib/apt/lists/*

# Instala as dependências Python listadas em requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copia o restante do código da aplicação para o contêiner
# Isso assume que todos os seus arquivos .py (main.py, pdf_processor.py, etc.)
# estão na raiz do seu projeto.
COPY . .

# Comando para baixar o tokenizer 'punkt_tab' do NLTK durante a construção da imagem.
# Isso evita que o download seja feito toda vez que o script for executado no contêiner,
# tornando a execução mais rápida e independente de conexão de internet runtime.
# --- CORREÇÃO AQUI: Baixando 'punkt_tab' explicitamente ---
RUN python -c "import nltk; nltk.download('punkt_tab', download_dir='/usr/local/nltk_data')"
ENV NLTK_DATA="/usr/local/nltk_data"

# Comando para executar a aplicação quando o contêiner for iniciado.
# Use este comando para iniciar seu script principal.
CMD ["python", "main.py"]
