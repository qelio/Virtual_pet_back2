from flask import Flask

app = Flask(__name__)

if __name__ == "__main__":
    port = 8080
    app.run(debug=True,host='0.0.0.0',port=port)