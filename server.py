# import the Flask class from the flask module
from flask import Flask, render_template, jsonify, make_response, request
import thumbmaker
# create the application object
app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')  # render a template

@app.route('/api/process_site')
def process_site():

    root = request.args['root']
    pages = [s.strip() for s in request.args['pages'].split('\n')]

    name, data = thumbmaker.process_site(root, pages)
    response = make_response(data)
    response.headers["Content-Disposition"] = "attachment; filename=%s"%name
    return response

# start the server with the 'run()' method
if __name__ == '__main__':
    app.run(debug=True)

