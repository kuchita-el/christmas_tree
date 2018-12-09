import decimal
import os
import sqlite3
from decimal import Decimal

from flask import Flask, render_template, request, redirect, url_for, send_from_directory, session
from werkzeug import secure_filename
from watson_developer_cloud import VisualRecognitionV3, WatsonApiException

app = Flask(__name__, instance_relative_config=True)

UPLOAD_FOLDER = './uploads'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'gif'])
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SECRET_KEY'] = os.urandom(24)
app.config.from_pyfile('config.cfg', silent=True)


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


def analise_image(image_file_path):
    visual_recognition = VisualRecognitionV3(
        version=app.config["WATSON_API_VERSION"],
        iam_apikey=app.config["WATSON_API_KEY"]
    )
    visual_recognition.set_detailed_response(True)

    try:
        with open(image_file_path, mode="rb") as f:
            response = visual_recognition.classify(f, threshold='0.6', classifier_ids="christmasxtree_131894146")
            json_dictionary = response.get_result()
            if "code" not in json_dictionary:
                classes = json_dictionary["images"]["classifiers"]["classes"]
                for class_value in classes:
                    if str(class_value["name"]) == "gorgeous_christmas_tree":
                        print(class_value["score"])
                        return Decimal(class_value["score"])

                return Decimal(0)

            else:
                status_code = response.get_status_code()
                print(str(status_code))
                raise ConnectionAbortedError

    except WatsonApiException as ex:
        print("Method failed with status code " + str(ex.code) + ": " + ex.message)
        raise ConnectionAbortedError


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/send', methods=['GET', 'POST'])
def send():
    if request.method == 'POST':
        img_file = request.files['img_file']
        if img_file and allowed_file(img_file.filename):
            filename = secure_filename(img_file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            img_file.save(file_path)
            img_url = '/uploads/' + filename
            result = analise_image(str(file_path))
            google_map_api_key = app.config["GOOGLE_MAP_API_KEY"]
            return render_template('result.html', img_url=img_url,result=result,google_map_api_key=google_map_api_key)
        else:
            return ''' <p>許可されていない拡張子です</p> '''
    else:
        return redirect(url_for('index'))


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/result')
def result():
    return render_template('result.html')


if __name__ == '__main__':
    app.debug = True
    app.run()
