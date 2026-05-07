from src.app import create_app

app = create_app()
print(f'✅ Routes loaded: {len(app.url_map._rules)}')
print('✅ Starting Flask server on http://127.0.0.1:3000')
app.run(host='127.0.0.1', port=3000, debug=True)
