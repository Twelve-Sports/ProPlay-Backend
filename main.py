import os
import datetime
import time
import requests
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip

CLIP_DURATION = 15  # Duration of each clip in seconds
CLIPS_DIRECTORY = 'clips'
CLIPS_SENT_DIRECTORY = 'clips/sent'
CLIPS_UNSENT_DIRECTORY = 'clips/unsent'
RECORDINGS_DIRECTORY = 'recordings'
DEFAULT_VIDEO_DURATION = 300  # Duration of each video in seconds

API_HOST = '127.0.0.1'
API_PORT = 3001

os.makedirs(CLIPS_DIRECTORY, exist_ok=True)
os.makedirs(CLIPS_SENT_DIRECTORY, exist_ok=True)
os.makedirs(CLIPS_UNSENT_DIRECTORY, exist_ok=True)
os.makedirs(RECORDINGS_DIRECTORY, exist_ok=True)

cam_directories = list(map(lambda x: os.path.join(RECORDINGS_DIRECTORY, x), os.listdir(RECORDINGS_DIRECTORY)))

def get_timestamps_from_api(directory_name):
    print(directory_name)
    directory_name = os.path.basename(directory_name)
    response = requests.get(f'http://{API_HOST}:{API_PORT}/list/{directory_name}').json()
    # if the data is just a {"message":"yadayada"}
    print(response)
    if 'message' in response:
        return []
    # TODO: Remap this so the list contains the ids and the timestamps
    timestamps = list(map(lambda x: x['data'], response))
    return timestamps

def post_clip_to_api(quadra_id, timestamp):
    files = {'file': open(f'{CLIPS_UNSENT_DIRECTORY}/quadra_{quadra_id}_clip_{timestamp}.mp4', 'rb')}
    response = requests.post(f'http://{API_HOST}:{API_PORT}/up/{quadra_id}', files=files)
    print(response)
    return response

def is_timestamp_in_video(clip_datetime, video_start_datetime):
    # verify if the timestamp is within the video duration
    video_end_datetime = video_start_datetime + datetime.timedelta(seconds=DEFAULT_VIDEO_DURATION)
    return video_start_datetime <= clip_datetime <= video_end_datetime

def proccess_clip(clip_start_datetime, clip_end_datetime, recording_datetime, input_video_file, output_name):
    # Calculate the start and end values relative to the original video
    clip_start_relative = clip_start_datetime - recording_datetime
    clip_end_relative = clip_end_datetime - recording_datetime

    # Convert the relative values to real numbers
    crop_start = max(0, clip_start_relative.total_seconds())
    crop_end = clip_end_relative.total_seconds()

    # Check if the input video file exists before creating the clip
    if os.path.exists(input_video_file):
        ffmpeg_extract_subclip(input_video_file, crop_start, crop_end, targetname=output_name)
    else:
        print(f"Input video file '{input_video_file}' does not exist.")

def clip_all_timestamps():
    for cam_directory in cam_directories:
        quadra_id = os.path.basename(cam_directory)
        timestamps = get_timestamps_from_api(quadra_id)

        for root, directories, raw_videos in os.walk(cam_directory):
            for video in raw_videos:
                # Check if the file is a video file
                if (not video.endswith(".mp4")): continue

                # Get the recording timestamp from the file name
                recording_timestamp = video.split('.')[0]
                recording_datetime = datetime.datetime.strptime(recording_timestamp, "%Y-%m-%d_%H-%M-%S_%f")

                for timestamp in timestamps:
                    # Calculate the start and end timestamps for the clip
                    clip_end_datetime = datetime.datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%fZ")
                    clip_start_datetime = clip_end_datetime - datetime.timedelta(seconds=CLIP_DURATION)

                    if (not is_timestamp_in_video(clip_start_datetime, recording_datetime)): continue
                    small_timestamp = clip_end_datetime.strftime("%Y-%m-%dT%H:%M:%S")
                    output_name = os.path.join(CLIPS_UNSENT_DIRECTORY, f"quadra_{quadra_id}_clip_{small_timestamp}.mp4")
                    print("output", output_name)
                    input_video_file = os.path.join(root, video)

                    proccess_clip(clip_start_datetime, clip_end_datetime, recording_datetime, input_video_file, output_name)


def post_all_clips():
    for clip in os.listdir(CLIPS_UNSENT_DIRECTORY):
        quadra_id = clip.split('_')[1]
        timestamp = clip.split('_')[3].split('.')[0]
        
        response = post_clip_to_api(quadra_id, timestamp)
        if response.status_code == 200 or response.status_code == 201:
            os.rename(f'{CLIPS_UNSENT_DIRECTORY}/{clip}', f'{CLIPS_SENT_DIRECTORY}/{clip}')
        else:
            print(f'Error while sending clip {clip}, error: {response.status_code}')

def main():
    clip_all_timestamps()
    # sleep 5 seconds
    time.sleep(5)
    post_all_clips()

if __name__ == '__main__':
    main()