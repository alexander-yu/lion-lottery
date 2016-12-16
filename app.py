from flask import Flask, render_template
import simplejson as json

app = Flask(__name__)
try:
    with open("./data/housing_data.json", 'r') as housing_data_json:
        housing_data = json.loads(housing_data_json.read())

except IOError as e:
    print "Exception encountered."
    print "If ./data/housing_data.json does not exist, " + \
        "please run python ./housing.py"
    raise e


@app.route('/')
def lottery():
    return render_template("index.html", housing_data=housing_data)


if __name__ == '__main__':
    app.run(debug=True)
