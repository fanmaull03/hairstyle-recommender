# Menggunakan base image Python resmi yang stabil
FROM python:3.10-slim

# Mengatur working directory di dalam container
WORKDIR /code

# Menginstal dependensi sistem operasi yang diperlukan untuk kompilasi (penting untuk dlib/mediapipe)
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    git \
    && rm -rf /var/lib/apt/lists/*

# Menyalin file requirements terlebih dahulu agar Docker bisa melakukan caching layer
COPY ./requirements.txt /code/requirements.txt

# Menginstal dependensi Python
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# Membuat user baru bernama "user" agar tidak berjalan sebagai root (aturan keamanan Hugging Face)
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

# Mengatur directory kerja ke tempat aplikasi berada
WORKDIR $HOME/app

# Menyalin seluruh source code proyek ke dalam container
COPY --chown=user . $HOME/app

# Menandakan port yang akan diexpose oleh container
EXPOSE 7860

# Perintah untuk menjalankan aplikasi Flask
CMD ["python", "app.py"]