from flask import Flask, render_template
from flask_cors import CORS, cross_origin
import cv2
from flask_socketio import SocketIO, emit
import base64
import eventlet
import sys

PORT = 5001
FPS = 10
FRAME_LABEL = 'frame'
DRAZER_KEY_FILE = 'drazer_cam.key'
DRAZER_CRT_FILE = 'drazer_cam.crt'

# Creating a flask app and using it to instantiate a socket object
app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

socketio = SocketIO(app, cors_allowed_origins="*")


@app.route('/')
def index():
    return {'data': 'Hello World'}


def capture_frames():
    """Capture frames from the default camera and emit them to clients."""
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Error: Could not open camera.")
        return

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Failed to capture frame.")
            break

        # Encode the frame as JPEG
        _, buffer = cv2.imencode('.jpg', frame)
        jpg_as_text = base64.b64encode(buffer).decode('utf-8')

        # Emit the encoded frame to all connected clients
        socketio.emit(FRAME_LABEL, jpg_as_text)

        eventlet.sleep(1 / FPS)

    cap.release()


# Handler for a message received over 'connect' channel
@socketio.on('connect')
@cross_origin()
def test_connect(auth):
    print('Client connected', auth)
    emit('after connect', {'data': 'Lets dance'}, broadcast=True)
    return {'data': 'Hello World'}


# Notice how socketio.run takes care of app instantiation as well.
if __name__ == '__main__':
    if len(sys.argv) > 1:
        SCRIPT_PATH = sys.argv[1]
    else:
        SCRIPT_PATH = ''

    socketio.start_background_task(capture_frames)
    socketio.run(app, host='0.0.0.0', allow_unsafe_werkzeug=True, port=PORT,
                 certfile=SCRIPT_PATH + DRAZER_CRT_FILE,
                 keyfile=SCRIPT_PATH + DRAZER_KEY_FILE)
