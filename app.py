import os
import boto3
from flask import Flask, request, jsonify

app = Flask(__name__)

ENV = os.getenv('FLASK_ENV', 'local') 
TABLE_NAME = os.getenv('DYNAMODB_TABLE', 'perros_local')
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1') 

try:
    dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
    table = dynamodb.Table(TABLE_NAME)
except Exception as e:
    print(f"Error fatal conectando a DynamoDB: {e}")
    table = None 


@app.route('/')
def health_check():
    return jsonify({
        "message": "API de Perros funcionando!",
        "environment": ENV,
        "table_name": TABLE_NAME
    }), 200

@app.route('/perros', methods=['POST'])
def create_perro():
    data = request.json
    if 'id' not in data:
        return jsonify({"error": "Se requiere un 'id'"}), 400
    try:
        table.put_item(Item=data)
        return jsonify(data), 201
    except Exception as e:
        return jsonify({"error": str(e), "message": "Error al crear"}), 400

@app.route('/perros/<string:id>', methods=['GET'])
def get_perro(id):
    try:
        response = table.get_item(Key={'id': id})
        if 'Item' in response:
            return jsonify(response['Item']), 200
        else:
            return jsonify({"error": "Perro no encontrado"}), 404
    except Exception as e:
        return jsonify({"error": str(e), "message": "Error al buscar"}), 400

@app.route('/perros/<string:id>', methods=['PUT'])
def update_perro(id):
    data = request.json
    try:
        expression_attribute_names = {}
        expression_attribute_values = {}
        update_expression = "SET "
        
        count = 0
        for key, value in data.items():
            if key != 'id':
                attr_name = f"#k{count}"
                attr_value = f":v{count}"
                update_expression += f"{attr_name} = {attr_value}, "
                expression_attribute_names[attr_name] = key
                expression_attribute_values[attr_value] = value
                count += 1
        
        update_expression = update_expression.rstrip(', ')

        if not expression_attribute_values:
             return jsonify({"error": "No hay campos para actualizar"}), 400

        response = table.update_item(
            Key={'id': id},
            UpdateExpression=update_expression,
            ExpressionAttributeNames=expression_attribute_names,
            ExpressionAttributeValues=expression_attribute_values,
            ReturnValues="UPDATED_NEW" 
        )
        return jsonify(response.get('Attributes', {})), 200
    except Exception as e:
        return jsonify({"error": str(e), "message": "Error al actualizar"}), 400

@app.route('/perros/<string:id>', methods=['DELETE'])
def delete_perro(id):
    try:
        table.delete_item(
            Key={'id': id}
        )
        return jsonify({"message": f"Perro con id '{id}' eliminado"}), 200
    except Exception as e:
        return jsonify({"error": str(e), "message": "Error al eliminar"}), 400

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)