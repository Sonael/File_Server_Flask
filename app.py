from flask import Flask, render_template, request, redirect, url_for, send_from_directory, session
from werkzeug.utils import secure_filename
import os
import logging
from PIL import Image
from jinja2 import Environment

app = Flask(__name__, template_folder='templates')
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
THUMBNAIL_FOLDER = os.path.join(os.getcwd(), 'thumbnails')
app.secret_key = 'sonaelneto'  # Defina uma chave secreta para uso de sessão

# Configurar o caminho para a pasta de miniaturas
app.config['THUMBNAIL_FOLDER'] = THUMBNAIL_FOLDER


@app.route('/thumbnails/<path:filename>')
def serve_thumbnail(filename):
    return send_from_directory(app.config['THUMBNAIL_FOLDER'], filename)

# Configurar o arquivo de log
log_file = "connections.log"
logging.basicConfig(filename=log_file, level=logging.INFO,
                    format='%(asctime)s %(levelname)s - %(message)s')

logger = logging.getLogger(__name__)

def thumbnail_exists(filename):
    thumbnail_filename = "thumbnail_" + filename
    thumbnail_path = os.path.join(THUMBNAIL_FOLDER, thumbnail_filename)
    return os.path.exists(thumbnail_path)

# Verifica se o arquivo é uma imagem
@app.template_filter('is_image_file')
def is_image_file(filename):
    image_extensions = ['.jpg', '.jpeg', '.png', '.gif']
    return any(filename.lower().endswith(ext) for ext in image_extensions)

# Função para gerar miniaturas das imagens
def generate_thumbnails():
    for filename in os.listdir(UPLOAD_FOLDER):
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        if os.path.isfile(filepath):
            if is_image_file(filename):
                generate_thumbnail(filepath, filename)

# Função para gerar uma miniatura de uma imagem específica
def generate_thumbnail(filepath, filename, size=(150, 150)):
    if thumbnail_exists(filename):
        return
    
    image = Image.open(filepath)
    image.thumbnail(size)
    thumbnail_filename = "thumbnail_" + filename
    thumbnail_path = os.path.join(THUMBNAIL_FOLDER, thumbnail_filename)
    image.save(thumbnail_path)


# Middleware para registrar as conexões
@app.before_request
def log_request_info():
    client_ip = request.remote_addr
    log_message = f"{request.method} {request.url} - {client_ip}"
    logger.info(log_message)


@app.route('/')
def login():
    return render_template('login.html')


@app.route('/authenticate', methods=['POST'])
def authenticate():
    username = request.form.get('username')
    password = request.form.get('password')

    # Verificar as credenciais do usuário (exemplo simplificado)
    if username == 'admin' and password == 'password':
        session['logged_in'] = True  # Definir a variável de sessão como True para indicar o login bem-sucedido
        session.pop('error', None)  # Remover a mensagem de erro, se existir
        return redirect(url_for('file_list'))

    else:
        session['error'] = 'Falha na autenticação. Verifique seu nome de usuário e senha.'
        return redirect(url_for('login'))


@app.route('/upload')
def upload_form():
    if not session.get('logged_in'):  # Verificar se o usuário está logado antes de permitir o acesso à página de upload
        return redirect(url_for('login'))
    return render_template('upload.html')

@app.route('/delete_file/<filename>', methods=['POST'])
def delete_file(filename):
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    if os.path.exists(filepath):
        os.remove(filepath)
        return redirect(url_for('file_list'))
    else:
        return 'Arquivo não encontrado.'


@app.route('/download_file/<filename>')
def download_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)

@app.route('/filelist')
def file_list():
    if not session.get('logged_in'):  # Verificar se o usuário está logado antes de permitir o acesso à lista de arquivos
        return redirect(url_for('login'))
    generate_thumbnails()
    files = os.listdir(UPLOAD_FOLDER)
    return render_template('filelist.html', files=files)


@app.route('/fileupload', methods=['POST'])
def upload():
    if 'files[]' not in request.files:
        return "No files selected to upload."

    files = request.files.getlist('files[]')
    for file in files:
        if file.filename == '':
            continue

        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        # Process the file or perform any other operations here

    return "Files uploaded successfully."



if __name__ == '__main__':
    app.run(port=80,debug=True)