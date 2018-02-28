from flask import (Flask, jsonify, render_template, request, redirect, url_for)
from flask_cors import (CORS, cross_origin) # To allow external calls to the API
from flask_compress import Compress
import os
import io
from werkzeug import secure_filename
from pdf2image import convert_from_path, convert_from_bytes
from wand.image import Image
import requests
import json
from json import JSONEncoder
from PIL import Image, ImageDraw
from enum import Enum
import argparse

from watson_developer_cloud import NaturalLanguageUnderstandingV1
from watson_developer_cloud.natural_language_understanding_v1 import Features, CategoriesOptions, KeywordsOptions, ConceptsOptions, RelationsOptions, EntitiesOptions
import googleapiclient.discovery
import googleapiclient.errors

from google.cloud import vision
from google.cloud.vision import types as Itypes

app = Flask(__name__)
CORS(app)
Compress(app)

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "OCR-NDS-588a394cb12f.json"

client = vision.ImageAnnotatorClient()

natural_language_understanding = NaturalLanguageUnderstandingV1(
    version='2017-02-27',
    username='9db663dd-120c-416a-b429-1345686feb7a',
    password='quWhsaVKbLrk')

class MyEncoder(JSONEncoder):
        def default(self, o):
            return o.__dict__

class Category:
    def __init__(self, av, name, tx):
        self.temp = []
        self.text = []
        self.av = av
        self.name = name
        self.text.append(Text(av, tx))

    def sortText(self):
        self.temp = sorted(self.text, key=lambda t: t.av, reverse=True)
        self.text = self.temp

class Concept:
    def __init__(self, av, name, tx):
        self.temp = []
        self.text = []
        self.av = av
        self.name = name
        self.text.append(Text(av, tx))

    def sortText(self):
        self.temp = sorted(self.text, key=lambda t: t.av, reverse=True)
        self.text = self.temp

class Entity:
    def __init__(self, av, name, ty):
        self.av = av
        self.name = name
        self.ty = ty

class Keyword:
    def __init__(self, av, name):
        self.av = av
        self.name = name

class Text:
    def __init__(self, av, name):
        self.av = av
        self.name = name

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def Index():
    return render_template('index.html')

@app.route('/img')
def down_img2():
    return '<img src=' + url_for('static',filename='example0.jpg') + '>'

@app.route('/img2')
def down_img():
    return url_for('static',filename='example0.jpg')

@app.route('/acta', methods=['POST'])
def upload_file():
    #print(request.json)
    #url='http://bpm.nearshoremx.com/sysNDS/es/neoclassic/cases/cases_ShowDocument?a=9555767175a905da86a5c71075418462&v=1'
    url = request.json.get("url")
    mainCat = request.json.get("category")
    wLook = [request.json.get("word1"), request.json.get("word2"), request.json.get("word3")]
    #print (url)
    local_filename = "acta.pdf"
    r = requests.get(url, stream=True)
    with open(local_filename, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk: # filter out keep-alive new chunks
                f.write(chunk)
                #f.flush() commented by recommendation from J.F.Sebastian
    #return local_filename

    #print(f.filename)

    #mainCat = 'alimentos'

    #mainCat = request.form['mainCat']
    if (mainCat == 'Tecnologia'):
        look=['technology and computing', 'computer science']
    if (mainCat == 'Alimentaria'):
        look=['agriculture and forestry', 'food industry', 'food and drink', 'food processors']
    if (mainCat == 'Construccion'):
        look=['construction', 'remodeling and construction', 'home improvement and repair', 'interior decorating',
                    'gardening and landscaping', 'home furnishings', 'home improvement and repair', 'real estate',
                    'personal finance', 'lending', 'finance']

    #word1 = "edgar"
    bounds = []

    words = []

    for w in wLook:
        words.append(w)
        words.append(w.upper())
        words.append(w.title())

    print (words)

    print (look)

    catRight=[]
    catWrong=[]

    alert = False

    images = convert_from_path(local_filename)
    fileout="example"
    fi=0
#    os.system("rm " + local_filename)

    for image in images:
        bounds=[]
        get_text_from_files(image, look, catRight, catWrong, words, bounds)
        draw_boxes(image, bounds, 'red')
        fileout1 = fileout + str(fi) + ".jpg"
        if fileout1 is not 0:
            image.save("static/" + fileout1)
        else:
            image.show()
        fi+=1

    sortedCatRight = sorted(catRight, key=lambda c: c.av, reverse=True)
    sortedCatWrong = sorted(catWrong, key=lambda c: c.av, reverse=True)
#       sortedCon = sorted(con, key=lambda c: c.av, reverse=True)
#        sortedEnt = sorted(ent, key=lambda c: c.av, reverse=True)
#        sortedKey = sorted(key, key=lambda c: c.av, reverse=True)

    for c in sortedCatRight:
        c.sortText()

    for c in sortedCatWrong:
        c.sortText()

    print (sortedCatRight[0].av)
    print (sortedCatRight[1].av)
    print (sortedCatRight[2].av)

    #for cw in sortedCatWrong:
    #    print (cw.name)
    #    print (cw.av)
    #    print ("\n")

    if (len(sortedCatRight) > 0):
        if (sortedCatRight[0].av >= 3 and sortedCatRight[1].av >= 1):
            return jsonify({
                'code': 'SUCCESS',
                'cat0': sortedCatRight[0].name,
                'cat0av': sortedCatRight[0].av,
                'cat1': sortedCatRight[1].name,
                'cat2': sortedCatRight[2].name,
                'name': mainCat}), 201
        else:
            return jsonify({
                'code': 'ALERT',
                'cat0': sortedCatWrong[0].name,
                'cat1': sortedCatWrong[1].name,
                'cat2': sortedCatWrong[2].name,
                'name': mainCat}), 201
    else:
        return jsonify({
            'code': 'ALERT',
            'cat0': sortedCatWrong[0].name,
            'cat1': sortedCatWrong[1].name,
            'cat2': sortedCatWrong[2].name,
            'name': mainCat}), 201
            #return render_template('actaResults.html', cat1=sortedCatWrong[0], cat2=sortedCatWrong[1], cat3=sortedCatWrong[2],
            #    cat4=sortedCatWrong[3], cat5=sortedCatWrong[4], alert=True, name=mainCat)
        #for c in sortedCon:
        #    c.sortText()

def draw_boxes(image, bounds, color):
    """Draw a border around the image using the hints in the vector list."""
    draw = ImageDraw.Draw(image)

    for bound in bounds:
        draw.line([
            bound.vertices[0].x, bound.vertices[0].y,
            bound.vertices[1].x, bound.vertices[1].y,
            bound.vertices[2].x, bound.vertices[2].y,
            bound.vertices[3].x, bound.vertices[3].y], fill=color, width=9)
    return image

def nl_detect(tx, look, catRight, catWrong):
    repeated = False

    try:
        response = natural_language_understanding.analyze(
            text=tx,
            features=Features(categories=CategoriesOptions(), keywords=KeywordsOptions(),
                concepts=ConceptsOptions(),
                entities=EntitiesOptions(sentiment=True, limit=2, mentions=True)))

        try:
            for c in response['categories']:
                repeated = False
                right = False

                la = c['label'].split("/")

                if (la[1] != 'law, govt and politics' and la[1] != 'society' and la[1] != 'government'
                  and la[1] != 'hobbies and interests' and la[1] != 'legal issues' and tx != 'A DOS'
                  and la[1] != 'travel'):
                    for lo in look:
                        if (right):
                            break
                        for l in la:
                            if (l == lo):
                                right = True
                                break
                    if (right):
                        for ct in catRight:
                            if (ct.name == la[1]):
                                repeated = True
                                break
                        if (repeated == False):
                            catRight.append(Category(float(c['score']), la[1], tx))
                        else:
                            ct.av += float(c['score'])
                            #if (len(la) < 3):
                            ct.text.append(Text(float(c['score']), tx))
                            repeated = False

                        if (len(la) >= 3):
                            for ct in catRight:
                                if (ct.name == la[2]):
                                    repeated = True
                                    break
                            if (repeated == False):
                                catRight.append(Category(float(c['score']), la[2], tx))
                            else:
                                ct.av += float(c['score'])
                                #if (len(la) < 4):
                                ct.text.append(Text(float(c['score']), tx))
                                repeated = False

                        if (len(la) >= 4):
                            for ct in catRight:
                                if (ct.name == la[3]):
                                    repeated = True
                                    break
                            if (repeated == False):
                                catRight.append(Category(float(c['score']), la[3], tx))
                            else:
                                ct.av += float(c['score'])
                                ct.text.append(Text(float(c['score']), tx))
                                repeated = False

                        if (len(la) >= 5):
                            for ct in catRight:
                                if (ct.name == la[4]):
                                    repeated = True
                                    break
                            if (repeated == False):
                                catRight.append(Category(float(c['score']), la[4], tx))
                            else:
                                ct.av += float(c['score'])
                                ct.text.append(Text(float(c['score']), tx))
                                repeated = False

                        if (len(la) >= 6):
                            for ct in catRight:
                                if (ct.name == la[5]):
                                    repeated = True
                                    break
                            if (repeated == False):
                                catRight.append(Category(float(c['score']), la[5], tx))
                            else:
                                ct.av += float(c['score'])
                                ct.text.append(Text(float(c['score']), tx))
                                repeated = False
                    else:
                        for ct in catWrong:
                            if (ct.name == la[1]):
                                repeated = True
                                break
                        if (repeated == False):
                            catWrong.append(Category(float(c['score']), la[1], tx))
                        else:
                            ct.av += float(c['score'])
                            #if (len(la) < 3):
                            ct.text.append(Text(float(c['score']), tx))
                            repeated = False

                        if (len(la) >= 3):
                            for ct in catWrong:
                                if (ct.name == la[2]):
                                    repeated = True
                                    break
                            if (repeated == False):
                                catWrong.append(Category(float(c['score']), la[2], tx))
                            else:
                                ct.av += float(c['score'])
                                #if (len(la) < 4):
                                ct.text.append(Text(float(c['score']), tx))
                                repeated = False

                        if (len(la) >= 4):
                            for ct in catWrong:
                                if (ct.name == la[3]):
                                    repeated = True
                                    break
                            if (repeated == False):
                                catWrong.append(Category(float(c['score']), la[3], tx))
                            else:
                                ct.av += float(c['score'])
                                ct.text.append(Text(float(c['score']), tx))
                                repeated = False

                        if (len(la) >= 5):
                            for ct in catWrong:
                                if (ct.name == la[4]):
                                    repeated = True
                                    break
                            if (repeated == False):
                                catWrong.append(Category(float(c['score']), la[4], tx))
                            else:
                                ct.av += float(c['score'])
                                ct.text.append(Text(float(c['score']), tx))
                                repeated = False

                        if (len(la) >= 6):
                            for ct in catWrong:
                                if (ct.name == la[5]):
                                    repeated = True
                                    break
                            if (repeated == False):
                                catWrong.append(Category(float(c['score']), la[5], tx))
                            else:
                                ct.av += float(c['score'])
                                ct.text.append(Text(float(c['score']), tx))
                                repeated = False
        except:
            print("No categories found")

        repeated=False

#        try:
#            for c in response['concepts']:
#                if (c['text'] != 'Ley' and c['text'] != 'Sociedad' and c['text'] != 'Acción'
#                    and c['text'] != 'Estado' and c['text'] != 'General'
#                    and c['text'] != 'USO' and c['text'] != 'Capital social'
#                    and c['text'] != 'Documento' and c['text'] != 'Día'
#                    and c['text'] != 'Ciudadano' and c['text'] != 'Firma electrónica'
#                    and c['text'] != 'Contrato' and c['text'] != 'Federación'
#                    and c['text'] != 'Representación' and c['text'] != 'Distrito federal'
#                    and c['text'] != 'Ciudad de México' and c['text'] != 'Persona jurídica'
#                    and c['text'] != 'Código civil' and c['text'] != 'Prueba'
#                    and c['text'] != 'Interés' and c['text'] != 'Persona física'
#                    and c['text'] != 'Firma digital' and c['text'] != 'El capital'
#                    and c['text'] != 'Sesenta' and c['text'] != 'Acto jurídico'
#                    and c['text'] != 'Firma' and c['text'] != 'Ocho'
#                    and c['text'] != 'Cooperativa' and c['text'] != 'Notario'
#                    and c['text'] != 'Procedimiento administrativo' and c['text'] != 'Señor'
#                    and c['text'] != 'Treinta' and c['text'] != 'Mensaje'
#                    and c['text'] != 'Juicio de amparo' and c['text'] != 'Plural'
#                    and c['text'] != 'Derecho' and c['text'] != 'Singular'
#                    and c['text'] != 'Notificación' and c['text'] != 'Agencia Estatal de Administración Tributaria'
#                    and c['text'] != 'El contrato social' and c['text'] != 'Consejero'
#                    and c['text'] != 'Verdad' and c['text'] != 'Dividendo'
#                    and c['text'] != 'Comisario' and c['text'] != 'Ley orgánica'
#                    and c['text'] != 'Mes' and c['text'] != 'Asamblea'
#                    and c['text'] != 'Veinte' and c['text'] != 'Vi'
#                    and c['text'] != 'Iniciativa legislativa popular' and c['text'] != 'Obligación'
#                    and c['text'] != 'El Caso' and c['text'] != 'Doce'
#                    and c['text'] != 'Contrato de fianza' and c['text'] != 'Libertad provisional'
#                    and c['text'] != 'Aval' and c['text'] != 'Diario Oficial de la Federación'
#                    and c['text'] != 'Sufragio' and c['text'] != 'Escritura'
#                    and c['text'] != 'Documentación' and c['text'] != 'México'):
#                        for ct in con:
#                            if (ct.name == c['text']):
#                                repeated = True
#                                break
#                        if (repeated == False):
#                            con.append(Concept(float(c['relevance']), c['text'], tx))
#                        else:
#                            ct.av += float(c['relevance'])
#                            ct.text.append(Text(float(c['relevance']), tx))
#                            repeated = False
#        except:
#            print("No concepts found")
#
#        repeated = False

#        try:
#            for e in response['entities']:
#                for en in ent:
#                    if (en.name == e['text']):
#                        repeated = True
#                        break
#                if (repeated == False):
#                    ent.append(Entity(float(e['relevance']), e['text'], e['type']))
#                else:
#                    en.av += float(e['relevance'])
#                    repeated = False
#        except:
#            print("No entities found")

#        try:
#            for k in response['keywords']:
#                for ke in key:
#                    if (ke.name == k['text']):
#                        repeated = True
#                        break
#                if (repeated == False):
#                    key.append(Keyword(float(k['relevance']), k['text']))
#                else:
#                    ke.av += float(k['relevance'])
#                    repeated = False
#        except:
#            print("No keywords found")

                #print(len(la))

            #print(tx)
            #print(json.dumps(response, indent=2))
    except:
        print("Could not read text: ")
        print(tx)

def get_text_from_files(path, look, catRight, catWrong, words, bounds):
    #client = vision.ImageAnnotatorClient()

    #bounds = []

    #img = Image(file = path, resolution = 72)
    #img = Image.open(path, mode='r')

    imgByteArr = io.BytesIO()
    path.save(imgByteArr, format='PNG')
    imgByteArr = imgByteArr.getvalue()

    #content = imgByteArr

    image = Itypes.Image(content=imgByteArr)

    response = client.document_text_detection(image=image)
    texts = response.full_text_annotation

    for page in texts.pages:
        for block in page.blocks:
            for paragraph in block.paragraphs:
                paragraph_text = ""
                for word in paragraph.words:
                    t = ""
                    paragraph_text = paragraph_text + " "
                    for symbol in word.symbols:
                        t = t+symbol.text
                        paragraph_text = paragraph_text + symbol.text
                    #print (t + " = " + word1)
                    for w in words:
                        if (t == w):
                            print (t + " = " + w)
                            bounds.append(paragraph.bounding_box)
                            bounds.append(word.bounding_box)
                nl_detect(paragraph_text, look, catRight, catWrong);

    #for page in texts.pages:
    #    for block in page.blocks:
    #        for paragraph in block.paragraphs:
    #            paragraph_text = ""
    #            for word in paragraph.words:
    #                if (word == word1):
    #                    print('Block Bounds:\n {}'.format(block.bounding_box))
    #                paragraph_text = paragraph_text + " "
    #                for symbol in word.symbols:
    #                    paragraph_text = paragraph_text + symbol.text
                #print("Paragraph: " + paragraph_text + "\n")
    #            nl_detect(paragraph_text, look, catRight, catWrong);

        #nl_detect(texts[0].description)
        #entities_text(texts[0].description)

""" Run Configuration """
port = os.getenv('PORT', '5000')
if __name__ == "__main__":
	app.run(debug=True, host='0.0.0.0', port=int(port))
