import os, sys, time, json, logging, csv, string, tempfile, codecs, re
from operator import itemgetter

import nltk
from nltk import FreqDist
from nltk.corpus import stopwords

from flask import Flask, Response, render_template, jsonify, request, redirect, url_for, abort
from flask.ext.uploads import UploadSet, configure_uploads, TEXT, patch_request_class, UploadNotAllowed

import unicodecsv

TEMP_DIR = tempfile.gettempdir()
ROWS_TO_SHOW = 40	# how many rows to show on the webpage

app = Flask(__name__)

app.config['UPLOADED_DOCS_DEST'] = TEMP_DIR

docs = UploadSet('docs', TEXT)
configure_uploads(app, (docs,))
patch_request_class(app, 4 * 1024 * 1024)	# 4MB

# setup logging
base_dir = os.path.dirname(os.path.abspath(__file__))
logging.basicConfig(filename=os.path.join(base_dir,'wordcounter.log'),level=logging.WARN)
logger = logging.getLogger(__name__)

logger.info("Temp Dir is %s" % TEMP_DIR)

@app.route("/",methods=['GET', 'POST'])
def index():
	t0 = time.time()
	word_counts = None
	bigram_counts = None
	trigram_counts = None
	error = None
	csv_file_names = None

	try:
		#this means the form was submitted
		if request.method == 'POST':	

			# grab content
			filename = time.strftime("%Y%m%d-%H%M%S") # this will get used for CSV download filenames if input text is submitted rather than a file to upload
			file_to_upload = request.files['fileOfWords']
			if file_to_upload:
				filename = docs.save(file_to_upload)
				filepath = os.path.join(TEMP_DIR,filename)
				logger.debug("Reading words from file (%s)" % filepath)
				bag_of_words = ""
				with codecs.open(filepath, "r", "utf-8") as myfile:
					bag_of_words = myfile.read()
				os.remove(filepath)		# privacy: don't keep the file around
			else:
				logger.debug("Reading words from textarea")
				bag_of_words = unicode(request.form['bagOfWords'])

			# parse the options the user set
			if "removeStopWords" in request.form:
				remove_stop_words = request.form['removeStopWords']
			else:
				remove_stop_words = False
			if "ignoreCase" in request.form:
				ignore_case = request.form['ignoreCase']
			else:
				ignore_case = False

			# generate the results
			t1 = time.time()
			logger.debug("  init: %d" % (t1-t0))
			words = _create_words(bag_of_words, ignore_case)	# keep all the words for now
			t1a = time.time()
			logger.debug("    words: %d" % (t1a-t1))
			word_counts = _sort_count_list(_count_words(words,remove_stop_words))	# ignore stop words here if you need to
			t1c = time.time()
			logger.debug("    word_counts: %d" % (t1c-t1a))
			bigram_counts = _sort_count_list(_count_bigrams(words))
			t1d = time.time()
			logger.debug("    bigram_counts: %d" % (t1d-t1c))
			trigram_counts = _sort_count_list(_count_trigrams(words))
			t2 = time.time()
			logger.debug("    trigram_counts: %d" % (t2-t1d))
			logger.debug("  counts: %d" % (t2-t1))

			# cache the CSV results for easy download
			csv_file_names = {
				'words': filename+"-word-counts.csv",
				'bigrams': filename+"-bigram-counts.csv",
				'trigrams': filename+"-trigram-counts.csv"
			}
			_write_csv_count_file(csv_file_names['words'], 'word', word_counts, False)
			_write_csv_count_file(csv_file_names['bigrams'], 'bigram phrase', bigram_counts, True)
			_write_csv_count_file(csv_file_names['trigrams'], 'trigram phrase', trigram_counts, True)
			logger.debug("  Wrote CSV files to:")
			logger.debug("	%s",os.path.join(TEMP_DIR,csv_file_names['words']))
			logger.debug("	%s",os.path.join(TEMP_DIR,csv_file_names['bigrams']))
			logger.debug("	%s",os.path.join(TEMP_DIR,csv_file_names['trigrams']))
			word_counts = word_counts[:ROWS_TO_SHOW]
			bigram_counts = bigram_counts[:ROWS_TO_SHOW]
			trigram_counts = trigram_counts[:ROWS_TO_SHOW]
			t3 = time.time()
			logger.debug("  csvs: %d" % (t3-t2))
			logger.debug("Timings (total %d)" % (t3-t0))

	except UploadNotAllowed:
		error = "Sorry, we don't support that file extension.  Please upload a .txt (ie. plain text) file!"

	return render_template("home.html", word_counts=word_counts,
		bigram_counts=bigram_counts, trigram_counts=trigram_counts,
		error = error, csv_file_names = csv_file_names)

@app.route('/download-csv/<csv_filename>')
def download_csv(csv_filename):
	file_path = os.path.join(TEMP_DIR,csv_filename)
	if os.path.isfile(file_path):
		def generate():
			with open(file_path, 'r') as f:
				reader = unicodecsv.reader(f, encoding='utf-8')
				for row in reader:
					yield ','.join(row) + '\n'
		return Response(generate(), headers={'Content-Disposition':'attachment;filename='+csv_filename},mimetype='text/csv')
	else:
		abort(400)

def _write_csv_count_file(file_name, text_col_header, freq_dist, is_list):
	file_path = os.path.join(TEMP_DIR,file_name)
	headers = ['frequency',text_col_header]
	with open(file_path, 'w') as f:
		writer = unicodecsv.writer(f, encoding='utf-8')
		writer.writerow(headers)
		for word in freq_dist:
			freq = word[1]
			phrase = word[0]
			if is_list:
				phrase = " ".join(phrase)
			writer.writerow([freq,phrase])

def _create_words(text, ignore_case):
	# words = nltk.tokenize.word_tokenize(text)
	t1 = time.time()
	words = re.findall(r"[\w']+|[.,!?;]", text, re.UNICODE)
	t2 = time.time()
	if ignore_case:
		words = [w.lower() for w in words]
	t3 = time.time()
	words = [w for w in words if not w in string.punctuation]
	t4 = time.time()
	logger.debug("      tokenize: %d" % (t2-t1))
	logger.debug("      ignore_case: %d" % (t3-t2))
	logger.debug("      remove punctuation: %d" % (t4-t3))
	return words

def _count_words(words, ignore_stop_words):
	fdist = FreqDist(words)
	# remove stopwords here rather than in corpus text for speed
	if ignore_stop_words:
		# http://stackoverflow.com/questions/7154312/how-do-i-remove-entries-within-a-counter-object-with-a-loop-without-invoking-a-r
		for w in list(fdist):
			if w in stopwords.words('english'):
				del fdist[w]
	return fdist

def _count_bigrams(words):
	bigrams = nltk.bigrams(words)
	return nltk.FreqDist(bigrams)

def _count_trigrams(words):
	trigrams = nltk.trigrams(words)
	return nltk.FreqDist(trigrams)

def _sort_count_list(freq_dist):
	items = freq_dist.items()
	return sorted(items, key=itemgetter(1), reverse=True)

if __name__ == "__main__":
	app.run()
