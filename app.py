# api.py
from flask import Flask, send_file, jsonify, render_template
import asyncio
from main import runSearch, output_file  

app = Flask(__name__)

@app.route("/")
def hello_world():
    return render_template('index.html') 

@app.route("/download", methods=["GET"])
def download_file():
    """Endpoint to download the output Excel file."""
    try:
        # Run the search and Excel generation task
        asyncio.run(runSearch())
        
        # Serve the generated Excel file for download
        return send_file(output_file, as_attachment=True)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5500)