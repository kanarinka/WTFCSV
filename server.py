import os, sys, time, json, logging, csv, string, tempfile, codecs, re, urllib, codecs
from operator import itemgetter
from flask import Flask, Response, render_template, jsonify, request, redirect, url_for, abort
from flask.ext.uploads import UploadSet, configure_uploads, TEXT, patch_request_class, UploadNotAllowed
import unicodecsv
import wtfcsvstat

TEMP_DIR = tempfile.gettempdir()

app = Flask(__name__)

app.config['UPLOADED_DOCS_DEST'] = TEMP_DIR

#TODO accept ZIP files later on
docs = UploadSet(name='docs', extensions=('csv'))

configure_uploads(app, (docs,))
patch_request_class(app, 4 * 1024 * 1024)	# 4MB

# setup logging
base_dir = os.path.dirname(os.path.abspath(__file__))
logging.basicConfig(filename=os.path.join(base_dir,'wtfcsv.log'),level=logging.DEBUG)
logger = logging.getLogger(__name__)

logger.info("Temp Dir is %s" % TEMP_DIR)

@app.route("/",methods=['GET'])
def index():
	return render_template("home.html", error=None, csv_info=None, tab='paste')

@app.route("/from-text",methods=['POST'])
def from_text():
	error = None
	results = None
	try:
		filename = time.strftime("%Y%m%d-%H%M%S")
		filepath = os.path.join(TEMP_DIR,filename)
		# grab content
		text = unicode(request.form['csvText'])
		file = codecs.open(filepath, "w", "utf-8")
		file.write(text)
		file.close()
		logger.debug("  Reading data from file (%s)" % filepath)
		results = wtfcsvstat.get_summary(filepath)
		os.remove(filepath)		# privacy: don't keep the file around
	except Exception as e:
		error = "Sorry, we weren't able to parse that text"
		logger.exception(e)
	return render_template("home.html", error=error, csv_info=results, tab='paste')
	
@app.route("/from-url",methods=['POST'])
def from_url():
	error = None
	results = None
	try:
		filename = time.strftime("%Y%m%d-%H%M%S")
		filepath = os.path.join(TEMP_DIR,filename)
		# grab content
		url = request.form['csvURL']
		logger.debug("Reading data from url (%s)" % url)
		testfile = urllib.URLopener()
		#CATHERINE WILL FIX -- NEED TO GET HEADER AND GET ENCODING TO MAKE LINKING WORK
		
		testfile.retrieve(url, filepath)
		
		logger.debug("  Reading data from file (%s)" % filepath)
		results = wtfcsvstat.get_summary(filepath)
		os.remove(filepath)		# privacy: don't keep the file around
	except Exception as e:
		error = "Sorry, we weren't able to retrieve that url"
		logger.exception(e)
	return render_template("home.html", error=error, csv_info=results, tab='link-file')

@app.route("/from-file",methods=['POST'])
def from_file():
	error = None
	results = None
	try:
		# grab content
		filename = time.strftime("%Y%m%d-%H%M%S") # this will get used for CSV download filenames if input text is submitted rather than a file to upload
		file_to_upload = request.files['csvFile']
		if file_to_upload:
			filename = docs.save(file_to_upload)
			filepath = os.path.join(TEMP_DIR,filename)
			logger.debug("Reading data from file (%s)" % filepath)
			results = wtfcsvstat.get_summary(filepath)
			os.remove(filepath)		# privacy: don't keep the file around
		else:
			logger.error("File uploading failed")
			error = "Sorry, we couldn't process your file for some reason!"
	except UploadNotAllowed as una:
		error = "Sorry, we don't support that file extension.  Please upload a .csv (ie. comma separated values) file!"
		logger.exception(una)
	return render_template("home.html", error=error, csv_info=results, tab='upload-file')

if __name__ == "__main__":
	# specific to Cloud9 environment
	app.run( host=os.getenv('IP', '0.0.0.0'), port=int(os.getenv('PORT', 8080)) )
	# app.run()