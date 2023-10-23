import cv2 as cv
import os
import datetime
import time
import xml.etree.ElementTree as ET
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip

cap = cv.VideoCapture(0)

# Create a main directory for all recordings
main_output_directory = 'recordings'
os.makedirs(main_output_directory, exist_ok=True)

# In seconds
RECORD_DURATION = 10
INTERVAL_BETWEEN_RECORDINGS = 5
CLIP_DURATION = 5  # Duration of each clip in seconds

# Frames per second
FPS = 24

recording = False  # Variable to keep track of recording status

while True:
    recording_timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H-%M-%S-%f")  # Include milliseconds
    video_directory = os.path.join(main_output_directory, recording_timestamp)
    os.makedirs(video_directory, exist_ok=True)

    filename = os.path.join(video_directory, f"video_{recording_timestamp}.avi")

    # Define the codec and VideoWriter object to save the video
    fourcc = cv.VideoWriter_fourcc(*'XVID')
    out = cv.VideoWriter(filename, fourcc, FPS, (640, 480))

    # Variables to keep track of time and frame count
    # to ensure we record for RECORD_DURATION seconds
    start_time = time.time()
    frameCounter = 0

    while True:
        ret, frame = cap.read()

        # Check for keyboard input (space bar) to save a timestamp in an XML file
        key = cv.waitKey(1) & 0xFF
        if key == ord(' '):
            xml_timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H-%M-%S-%f")  # Include milliseconds
            xml_filename = os.path.join(video_directory, f"timestamp_{xml_timestamp}.xml")

            # Create an XML structure for the timestamp and save it to the XML file
            timestamp_root = ET.Element("timestamp")
            timestamp_element = ET.SubElement(timestamp_root, "value")
            timestamp_element.text = xml_timestamp
            timestamp_tree = ET.ElementTree(timestamp_root)
            timestamp_tree.write(xml_filename)

        if recording:
            out.write(frame)
            frameCounter += 1

        cv.imshow('Recording', frame)

        # press 'q' to stop recording, or stop after RECORD_DURATION seconds
        if key == ord('q'):
            break
        if time.time() - start_time > RECORD_DURATION:
            break

        # wait for the desired FPS, accounting for processing time
        sleep_time = (1 / FPS) - (time.time() - (start_time + (frameCounter / FPS)))
        if sleep_time > 0:
            time.sleep(sleep_time)

        if not recording:
            recording = True  # Start recording after the first frame is read
            start_time = time.time()

    out.release()

    # Generate clips
    clips_directory = os.path.join(video_directory, 'clips')
    os.makedirs(clips_directory, exist_ok=True)

    for root, _, files in os.walk(video_directory):
        
        for file in files:
            if file.startswith("timestamp_") and file.endswith(".xml"):   
                # Get the timestamp value from the XML file            
                timestamp_path = os.path.join(root, file)
                timestamp_tree = ET.ElementTree(file=timestamp_path)
                timestamp_root = timestamp_tree.getroot()
                timestamp_value = timestamp_root.find('value').text

                # Calculate the start and end timestamps for the clip
                clip_end_timestamp = datetime.datetime.strptime(timestamp_value, "%Y-%m-%d %H-%M-%S-%f")
                clip_start_timestamp = clip_end_timestamp - datetime.timedelta(seconds=CLIP_DURATION)

                # Calculate the start and end values relative to the original video
                clip_start_relative = clip_start_timestamp - datetime.datetime.strptime(recording_timestamp, "%Y-%m-%d %H-%M-%S-%f")
                clip_end_relative = clip_end_timestamp - datetime.datetime.strptime(recording_timestamp, "%Y-%m-%d %H-%M-%S-%f")

                # Convert the relative values to real numbers
                crop_start = max(0, clip_start_relative.total_seconds())
                crop_end = clip_end_relative.total_seconds()
                
                # Define the input and output file paths for the clip
                input_video_file = os.path.join(root, f"video_{timestamp_value}.avi")
                output_clip = os.path.join(clips_directory, f"clip_{timestamp_value}.avi")              

                # Check if the input video file exists before creating the clip
                if os.path.exists(filename):
                    ffmpeg_extract_subclip(filename, crop_start, crop_end, targetname=output_clip)
                else:
                    print(f"Input video file '{filename}' does not exist.")

    # Move all timestamps to a separate directory
    timestamps_directory = os.path.join(video_directory, 'timestamps')
    os.makedirs(timestamps_directory, exist_ok=True)
    for root, _, files in os.walk(video_directory):
        for file in files:
            if file.startswith("timestamp_") and file.endswith(".xml"):
                os.rename(os.path.join(root, file), os.path.join(timestamps_directory, file))

    # Await interval between recordings
    time.sleep(INTERVAL_BETWEEN_RECORDINGS)
