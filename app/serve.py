import flask
import json
import argparse
import logging

import model

app = flask.Flask("app")

@app.route("/ping", methods=["GET", "POST"])
def ping():
    return("200 OK", 200)

@app.route("/invocations", methods=["GET", "POST"])
def invoke():
    if flask.request.method == "GET" or flask.request.method == "POST":


        data = flask.request.data.decode("utf-8")

        logging.info("Request Data {}".format(data))

        data = json.loads(data)

        model.load_ckpt()
        preds = model.predict(data)

        return(preds, 200)

if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True, port=8080)