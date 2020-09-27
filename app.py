import numpy as np
from flask import request, render_template, send_file, Flask
import pickle
import pandas as pd
import json
import requests
import tempfile
import os
import shutil
import weakref

class FileRemover(object):
    def __init__(self):
        self.weak_references = dict()  # weak_ref -> filepath to remove

    def cleanup_once_done(self, response, filepath):
        wr = weakref.ref(response, self._do_cleanup)
        self.weak_references[wr] = filepath

    def _do_cleanup(self, wr):
        filepath = self.weak_references[wr]
        print('Deleting %s' % filepath)
        shutil.rmtree(filepath, ignore_errors=True)

file_remover = FileRemover()

app = Flask(__name__)
file_test = pd.read_csv('final_test.csv')

scoreurl = 'https://kbvhjjcg6c.execute-api.us-east-2.amazonaws.com/test/default-pred'
@app.route('/')
def home():
    #return 'Hello World'
    return render_template('home.html')
    #return render_template('index.html')

@app.route('/upload',methods = ['GET','POST'])
def upload():
    print('you have reached herer -------------------------------------------')
    if request.method == 'POST':
        print
        df = pd.read_csv(request.files.get('file'))
        print(df)
        df_new = file_test.loc[file_test['uuid'].isin(df['uuid'].values)]
        
        df_new = df_new.drop('uuid', axis = 1)

        data = np.array(df_new)
        test = json.dumps({'data': data.tolist()})

        headers = {'Content-Type':'application/json'}
        resp = requests.post(scoreurl, json=test, headers =headers)
        res = resp.json()
        resp = res['body']
        resp = resp.split(',')
        array = np.array(resp)

        df_pred = pd.DataFrame({'uuid': df['uuid'], 'Default_Rate': array})
        print(df_pred)
        
        tempdir = tempfile.mkdtemp()
        response_filename = os.path.join(tempdir, 'banana.csv')
        with open(response_filename, 'w') as response_file:
            df_pred.to_csv(response_file, index = False)      
        
            
            return send_file(response_file, mimetype='text/csv', attachment_filename='Default-Pred.csv', as_attachment=True)
    
    return render_template('home.html', prediction_text="Your Prediction download should start soon...")

if __name__ == '__main__':
    app.run(debug=True)