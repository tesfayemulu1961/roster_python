from flask import Flask, jsonify 
import mysql.connector 
app = Flask(__name__) 
@app.route('/') 
def home(): 
    return jsonify({'message': 'Roster API is running', 'status': 'ok'}) 
@app.route('/students') 
def students(): 
    conn = mysql.connector.connect(host='localhost', user='root', password='', database='roster') 
    cursor = conn.cursor(dictionary=True) 
    cursor.execute('SELECT * FROM users LIMIT 10') 
    data = cursor.fetchall() 
    cursor.close() 
    conn.close() 
    return jsonify(data) 
if __name__ == '__main__': 
    app.run(debug=True, port=5000) 
