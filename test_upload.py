import requests

url = "http://127.0.0.1:5000/api/detect"
files = {'image': ('test.jpg', b'fake image data', 'image/jpeg')}
data = {'location': 'test loc', 'latitude': 13.0, 'longitude': 80.0}

try:
    response = requests.post(url, files=files, data=data)
    print("Status:", response.status_code)
    print("Response:", response.text)
except Exception as e:
    print("Error:", e)
