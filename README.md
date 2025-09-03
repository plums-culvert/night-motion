# Night Motion

This assumes you have a stationary camera pointed at the horizon. The `run.sh` script uses `ffmpeg` to crop the top 36% of a video to remove the horizon (you can change this by editing `run.sh`), which might include moving vehicles, homes, or other lights that might confuse the detection.

After cropping the video, it splits the video into images at 24 frames per second. Then, the first python script detects points of lights and highlights them using a red box. These annotated images are saved, and then composit and heatmap images are created so you can understand which lights are stationary and which are moving.

Your directory should contain:

- `run.sh`
- `detect_night_lights.py`
- `composite_lights.py`
- `your_movie_any_name.mp4/mov`

Then, run:

```bash
chmod +x run.sh && ./run.sh 
```

