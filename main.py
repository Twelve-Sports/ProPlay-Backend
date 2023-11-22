import os
import time
import datetime
import requests
import xml.etree.ElementTree as ET
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip


CLIP_DURATION = 15  # Duration of each clip in seconds
CLIPS_DIRECTORY = 'clips'
RECORDINGS_DIRECTORY = 'recordings'
DEFAULT_VIDEO_DURATION = 300  # Duration of each video in seconds

os.makedirs(CLIPS_DIRECTORY, exist_ok=True)
os.makedirs(RECORDINGS_DIRECTORY, exist_ok=True)

cam_directories = list(map(lambda x: os.path.join(RECORDINGS_DIRECTORY, x), os.listdir(RECORDINGS_DIRECTORY)))

def get_timestamps_from_api(directory_name):
    directory_name = os.path.basename(directory_name)
    response = requests.get(f'http://192.168.251.146:3001/list/{directory_name}').json()
    # {'data': '2023-11-22T09:58:34.427Z', 'id': 24, 'court_name': 'Quadra 8', 'court_id': 8}
    timestamps = list(map(lambda x: x['data'], response))
    return timestamps

def post_clip_to_api(directory_name, timestamp):
    return ''

def is_timestamp_in_video(clip_datetime, video_start_datetime):
    # verify if the timestamp is within the video duration
    video_end_datetime = video_start_datetime + datetime.timedelta(seconds=DEFAULT_VIDEO_DURATION)
    return video_start_datetime <= clip_datetime <= video_end_datetime

for directory in cam_directories:
    directory_name = os.path.basename(directory)
    timestamps = get_timestamps_from_api(directory_name)
    for root, directories, files in os.walk(directory):
        for file in files:
            # Check if the file is a video file
            is_video_file = file.endswith(".mp4")
            if (is_video_file):
                # Get the recording timestamp from the file name
                recording_timestamp = file.split('.')[0]
                recording_datetime = datetime.datetime.strptime(recording_timestamp, "%Y-%m-%d_%H-%M-%S_%f")
                for timestamp in timestamps:
                    recordingname = f'cam-{directory_name}-{recording_timestamp}'
                    print('\nrecordingname', recordingname)
                    print('timestamp', timestamp)
                    # Calculate the start and end timestamps for the clip
                    clip_end_datetime = datetime.datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%fZ")
                    clip_start_datetime = clip_end_datetime - datetime.timedelta(seconds=CLIP_DURATION)
                    
                    if(not is_timestamp_in_video(clip_start_datetime, recording_datetime)):
                        print('timestamp not in video')
                        continue

                    # Calculate the start and end values relative to the original video
                    clip_start_relative = clip_start_datetime - recording_datetime
                    clip_end_relative = clip_end_datetime - recording_datetime

                    # Convert the relative values to real numbers
                    crop_start = max(0, clip_start_relative.total_seconds())
                    crop_end = clip_end_relative.total_seconds()
                    print('crop_start', crop_start)
                    print('crop_end', crop_end)
                    print('clip duration', crop_end-crop_start)

                    # Define the input and output file paths for the clip
                    input_video_file = os.path.join(root, file)
                    output_clip = os.path.join(CLIPS_DIRECTORY, f"quadra_{directory_name}_clip_{timestamp}.mp4")              

                    # Check if the input video file exists before creating the clip
                    if os.path.exists(input_video_file):
                        # FIX ME: The clip is sometimes created with a longer duration than the expected
                        # With the extra duration being only black screen
                        ffmpeg_extract_subclip(input_video_file, crop_start, crop_end, targetname=output_clip)
                    else:
                        print(f"Input video file '{input_video_file}' does not exist.")
