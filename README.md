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

<img width="2896" height="674" alt="composite_max" src="https://github.com/user-attachments/assets/2488d809-72aa-4477-b84e-116d9ba695d6" />

### Heatmap
The generated heat map removes the boxes to make the object's motion more visible. In this example, it's interesting that there are three distinct objects all in a close proximity. They only move for short durations of the overall video, and do not appear to have an appearance and motion attributing them as satellites or airplanes:

<img width="2896" height="674" alt="composite_heatmap" src="https://github.com/user-attachments/assets/8a87dfa5-6b44-4360-9a14-142b3d0a0496" />

### Heatmap Clusters
The heatmap file finally identifies clusters of movement:

<img width="2896" height="674" alt="heatmap_boxes" src="https://github.com/user-attachments/assets/a61a4493-5d29-4339-a31d-c1854282e0f6" />

### Cropped Clusters
The final output are individual images of clusters of movement:

<img width="183" height="171" alt="cluster_003" src="https://github.com/user-attachments/assets/4a223bc2-0157-42f5-ad41-7a62b82a6ef2" />
<img width="180" height="168" alt="cluster_002" src="https://github.com/user-attachments/assets/e8cefaf0-4fcf-4612-b343-2f1ce4366fa8" />
<img width="339" height="261" alt="cluster_001" src="https://github.com/user-attachments/assets/e1a35888-0714-4ce5-9c1e-6a4679d5d2c2" />

### Interesting

The probability of three independent moving objects crossing the same spot in the sky:


**Example percentage:** 0.00000086% (μ=1/min, FOV 30°×20°, r=0.25°) — ≈1 in 116,000,000 minutes.

#### Formula

`P% ≈ [ 1 − e^(−μ) * (1 + μ + μ²/2) ] * (A / Ω)² * 100`

- `μ` = average number of moving objects entering the camera frame in 60 s  
- `Ω` = field of view area in steradians (convert your camera’s angular FOV into solid angle)  
- `A` = area of the “same place” patch of sky = π r² (with r in radians)  

#### Simple Explanation

1. **At least three objects in the frame**  
   - The first part `[ 1 − e^(−μ) * (1 + μ + μ²/2) ]` is the probability that 3 or more objects show up in the frame during 60 seconds.  

2. **All three overlap in the same patch**  
   - `(A / Ω)` is the fraction of the frame covered by your chosen “same spot.”  
   - Squaring it makes it the probability that, after the first object, the 2nd and 3rd also fall in that patch.  

3. **Combine them**  
   - Multiply the two pieces together → probability of **3 independent objects crossing the same spot in the sky during one 60-second exposure**.
