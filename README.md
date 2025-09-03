# Night Motion

This assumes you have a stationary camera pointed at the horizon. The `run.sh` script uses `ffmpeg` to crop the top 36% of a video to remove the horizon (you can change this by editing `run.sh`), which might include moving vehicles, homes, or other lights that might confuse the detection.

After cropping the video, it splits the video into images at 24 frames per second. Then, the first python script detects points of lights and highlights them using a red box. These annotated images are saved, and then composit and heatmap images are created so you can understand which lights are stationary and which are moving.

Finally, it detects clusters of movement in the heatmap, draws boxes around them, and the saves each cluster as an image.

Your directory should contain:

- `run.sh`
- `detect_night_lights.py`
- `composite_lights.py`
- `heatmap_cluster_crops.py`
- `your_movie_any_name.mp4/mov`

Then, run:

```bash
chmod +x run.sh && ./run.sh -crop 36 # Change the % of the video to crop. The example shows cropping to keep the top 36%.
```

## Example Output

### Composite
You can see stationary objects clearly which are most likely stars. Moving objects have larger, tightly grouped, linear arrays of highlighted boxes:

<img width="2896" height="674" alt="composite_max" src="https://github.com/user-attachments/assets/12ca3352-e38f-4418-b7c6-93a27f16d05f" />

### Heatmap
The generated heat map removes the boxes to make the object's motion more visible. In this example, it's interesting that there are three distinct objects all in a close proximity. They only move for short durations of the overall video, and do not appear to have an appearance and motion attributing them as satellites or airplanes:

<img width="2896" height="674" alt="composite_heatmap" src="https://github.com/user-attachments/assets/f0569dec-dcb5-4236-89b4-d1a7612e7a1e" />

### Heatmap Clusters
The heatmap file finally identifies clusters of movement:

<img width="2896" height="674" alt="heatmap_boxes" src="https://github.com/user-attachments/assets/08d19264-15b8-4ff7-aa81-26ba213af54d" />

### Cropped Clusters
The final output are individual images of clusters of movement:

<img width="453" height="264" alt="cluster_002" src="https://github.com/user-attachments/assets/be3fdcbc-90bf-45cc-8382-fcee7a57b92b" />
<img width="207" height="162" alt="cluster_001" src="https://github.com/user-attachments/assets/6776a6b6-81c8-4c0f-8ba0-c6d57f21e96f" />
<img width="183" height="168" alt="cluster_003" src="https://github.com/user-attachments/assets/9ac56cb6-5bbf-4bde-afef-a0385ebc0449" />
<img width="177" height="171" alt="cluster_004" src="https://github.com/user-attachments/assets/2c4c3c0e-1aa6-455c-89bc-015aec11e188" />
<img width="183" height="171" alt="cluster_005" src="https://github.com/user-attachments/assets/5dc5ede3-e5f2-427d-960b-62f9f634aa67" />
