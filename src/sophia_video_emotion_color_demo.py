from statistics import mode

import cv2
from keras.models import load_model
import numpy as np
import os

from utils.datasets import get_labels
from utils.inference import detect_faces
from utils.inference import draw_text
from utils.inference import draw_bounding_box
from utils.inference import apply_offsets
from utils.inference import load_detection_model
from utils.preprocessor import preprocess_input

# parameters for loading data and images
# replace '..' with '/Users/kchen/Projects/face_classification'
detection_model_path = os.path.dirname(__file__) +  '/../trained_models/detection_models/haarcascade_frontalface_default.xml'
emotion_model_path = os.path.dirname(__file__) +  '/../trained_models/emotion_models/fer2013_mini_XCEPTION.102-0.66.hdf5'
emotion_labels = get_labels('fer2013')

# hyper-parameters for bounding boxes shape
frame_window = 10
emotion_offsets = (0, 0)

# loading models
face_detection = load_detection_model(detection_model_path)
emotion_classifier = load_model(emotion_model_path, compile=False)

# getting input model shapes for inference
emotion_target_size = emotion_classifier.input_shape[1:3]

# starting lists for calculating modes
emotion_window = []

# starting video streaming
cv2.namedWindow('window_frame')
video_capture = cv2.VideoCapture(os.path.dirname(__file__) + '/../images/sophia_full.mp4')
# fps = video_capture.get(5)  
# size = (int(video_capture.get(3)),   
#         int(video_capture.get(4)))
# video_writer = cv2.VideoWriter('../images/sophia_processed.mp4', cv2.VideoWriter_fourcc(*'XVID'), fps, size)

frame = 0
emotion_ratio = {'angry':0, 'disgust':0, 'fear':0, 
'happy':0, 'sad':0, 'surprise':0, 'neutral':0}
emotion_seq = [[]]

while True:
    bgr_image = video_capture.read()[1]
    gray_image = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2GRAY)
    rgb_image = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2RGB)
    faces = detect_faces(face_detection, gray_image)

    emotion_per_frame = [[0,0,0,0,0,0,0]]

    for face_coordinates in faces:

        x1, x2, y1, y2 = apply_offsets(face_coordinates, emotion_offsets)
        gray_face = gray_image[y1:y2, x1:x2]
        try:
            gray_face = cv2.resize(gray_face, (emotion_target_size))
        except:
            continue

        gray_face = preprocess_input(gray_face, True)
        gray_face = np.expand_dims(gray_face, 0)
        gray_face = np.expand_dims(gray_face, -1)
        emotion_prediction = emotion_classifier.predict(gray_face)
        emotion_probability = np.max(emotion_prediction)
        emotion_label_arg = np.argmax(emotion_prediction)
        emotion_text = emotion_labels[emotion_label_arg]
        emotion_window.append(emotion_text)
        emotion_per_frame = np.mean(emotion_prediction, axis=0)

        if len(emotion_window) > frame_window:
            emotion_window.pop(0)
        try:
            emotion_mode = mode(emotion_window)
        except:
            continue

        if emotion_text == 'angry':
            color = emotion_probability * np.asarray((255, 0, 0))
        elif emotion_text == 'sad':
            color = emotion_probability * np.asarray((0, 0, 255))
        elif emotion_text == 'happy':
            color = emotion_probability * np.asarray((255, 255, 0))
        elif emotion_text == 'surprise':
            color = emotion_probability * np.asarray((0, 255, 255))
        else:
            color = emotion_probability * np.asarray((0, 255, 0))

        color = color.astype(int)
        color = color.tolist()

        emotion_ratio[emotion_text] += 1

        draw_bounding_box(face_coordinates, rgb_image, color)
        draw_text(face_coordinates, rgb_image, emotion_mode,
                  color, 0, -10, 1, 1)

    bgr_image = cv2.cvtColor(rgb_image, cv2.COLOR_RGB2BGR)
    cv2.imshow('window_frame', bgr_image)
    # video_writer.write(bgr_image)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

    if frame == 0:
        emotion_seq = np.array(emotion_per_frame).reshape(1,7)
    else:
        emotion_seq = np.append(emotion_seq, np.array(emotion_per_frame).reshape(1,7), axis=0)
    frame += 1

    if frame == 6080:
        break

# np.savetxt("emotion_seq.csv", emotion_seq, delimiter=",", fmt="%1.2f")
print(emotion_ratio)