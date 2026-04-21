from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/test1', methods=['POST'])
def test1():
    return jsonify({'result': 'test1'})

@app.route('/test2', methods=['POST'])
def test2():
    return jsonify({'result': 'test2'})

@app.route('/test3', methods=['POST'])
def test3():
    return jsonify({'result': 'test3'})

if __name__ == '__main__':
    print("Routes:")
    for rule in app.url_map.iter_rules():
        print(f"  {rule.rule}")
    app.run(host='127.0.0.1', port=9001, debug=False)
