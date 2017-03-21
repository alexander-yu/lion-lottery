import cPickle as pickle

from flask import Flask, render_template

from housing import Housing, Group, GroupID, Student  # noqa: F401


app = Flask(__name__)
with open("./data/housing_data.pkl", 'rb') as housing_data_f:
    housing_data = pickle.load(housing_data_f)


@app.route('/')
def lottery():
    return render_template("index.html", housing_data=housing_data)


if __name__ == '__main__':
    app.run(debug=True)
