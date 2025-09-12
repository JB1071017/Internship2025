from flask import Flask, render_template
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.serving import run_simple

from vulan.app import app as vuln_app

# Import external apps
from DBgen.app import app as dbgen_app
#from vulnscan_app.app import app as vuln_app
from spammer.app import app as spammer_app
from spg.app import app as spg_app
from UniTrainer.app import app as uni_trainer_app
from netan.app import app as netan_app

# Your main homepage app
main_app = Flask(__name__, template_folder='templates')

@main_app.route('/')
def homepage():
    return render_template("index.html")

# Mount other apps
application = DispatcherMiddleware(main_app, {
    '/dbgen': dbgen_app,
    #'/vulnscan': vuln_app,
    '/spammer': spammer_app,
    '/spg': spg_app,
    '/UniTrainer': uni_trainer_app,
    '/vulan': vuln_app,
    '/netan': netan_app
})

if __name__ == '__main__':
    run_simple('127.0.0.1', 5000, application, use_reloader=True, use_debugger=True)

