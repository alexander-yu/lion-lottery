from flask import Flask, render_template

from housing import get_data

app = Flask(__name__)
housing_data = None


@app.route('/')
def lottery():
    return render_template("index.html", housing_data=housing_data)


if __name__ == '__main__':
    print "Parsing housing data..."
    housing_data = get_data()
    print "Data parsed. Running server..."
    app.run(debug=True)
