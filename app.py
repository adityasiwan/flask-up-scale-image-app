import os
from flask import Flask, request, redirect, url_for, render_template, send_from_directory
from werkzeug.utils import secure_filename
from PyPDF2 import PdfFileReader, PdfFileWriter

import numpy as np
from PIL import Image
from ISR.models import RDN, RRDN
import tensorflow as tf

UPLOAD_FOLDER = os.path.dirname(os.path.abspath(__file__)) + '/uploads/'
DOWNLOAD_FOLDER = os.path.dirname(os.path.abspath(__file__)) + '/downloads/'
ALLOWED_EXTENSIONS = {'pdf', 'txt', 'JPEG', 'jpg', 'png'}

app = Flask(__name__, static_url_path="/static")
app.debug = True
DIR_PATH = os.path.dirname(os.path.realpath(__file__))
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['DOWNLOAD_FOLDER'] = DOWNLOAD_FOLDER
# limit upload size upto 8mb
app.config['MAX_CONTENT_LENGTH'] = 8 * 1024 * 1024


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'file' not in request.files:
            print('No file attached in request')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            print('No file selected')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            process_file(os.path.join(app.config['UPLOAD_FOLDER'], filename), filename)
            return redirect(url_for('uploaded_file', filename=filename))
    return render_template('index.html')


def process_file(path, filename):
    #remove_watermark(path, filename)
    image_deblur(path, filename)
    # with open(path, 'a') as f:
    #    f.write("\nAdded processed content")


def image_deblur(path, filename):
	img = Image.open(path)
	model = RRDN(weights='gans')
	# model = RDN(weights='psnr-small')
	# model = RDN(weights='psnr-large')
	# model = RDN(weights='noise-cancel')
	img.resize(size=(img.size[0]*4, img.size[1]*4), resample=Image.BICUBIC)
	sr_img = model.predict(np.array(img), by_patch_of_size=None, padding_size = 2)
	new = Image.fromarray(sr_img)
	#output_stream = open(app.config['DOWNLOAD_FOLDER'] + filename, 'wb')
	tf.keras.backend.clear_session()#output.write(output_stream)
	new.save(DOWNLOAD_FOLDER+filename, 'JPEG')



def remove_watermark(path, filename):
    input_file = PdfFileReader(open(path, 'rb'))
    output = PdfFileWriter()
    for page_number in range(input_file.getNumPages()):
        page = input_file.getPage(page_number)
        page.mediaBox.lowerLeft = (page.mediaBox.getLowerLeft_x(), 20)
        output.addPage(page)
    output_stream = open(app.config['DOWNLOAD_FOLDER'] + filename, 'wb')
    output.write(output_stream)


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['DOWNLOAD_FOLDER'], filename, as_attachment=False)


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
