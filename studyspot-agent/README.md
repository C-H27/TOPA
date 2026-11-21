# StudySpot detector demo

Place the team video in `videos/learning_center_1st_floor_3min_1080p.mp4`.
Copy `.env.example` to `.env` for local configuration. The template reserves
`ROBOFLOW_API_KEY` for the team's model integration. The included OpenCV
fallback runs locally and uses the first frame as an empty-room reference.
It was tested with the earlier 60-second clip. Verify the camera alignment
and the empty reference before interpreting results on the three-minute clip.
Defaults are in the settings block at the top of `main.py`.

## Windows launcher

For continuous replay, start TOPA's `Start-Backend.cmd`, then drag the tested
`learning_center_2.mp4` onto `Run-Demo.cmd` in the project root. Press Ctrl+C
in the detector window to stop. Each pass adds rows to the same CSV files for
that run. The `pass_number` column identifies each replay, and `video_seconds`
starts at zero again. The same option is available as `python main.py --loop`.

Double-click TOPA's `Start-Backend.cmd` first and leave its window open.
Then double-click `Start-Detector.cmd` in this folder. On its first run,
it creates a Python environment and installs dependencies. The launcher
uses `http://127.0.0.1:8000` by default. Set `TOPA_BACKEND_URL` to override it.

For a CSV-only run without the backend, run `.\Start-Detector.cmd --csv-only`
from PowerShell. Both modes write the CSV files in `output/`.

## Manual commands

```powershell
python -m pip install -r requirements.txt
python main.py
```

This writes `output/tables_status.csv` and `output/occupancy_log.csv`. The latest observation is saved to `output/live.json` after every sample. Room totals are reported
every 10 seconds. The people total covers seated people at the mapped tables.
People walking in aisles and unique visitors are outside this estimate.
The detector uses fixed regions and pixel changes. Accuracy on other videos
or real camera scenes requires separate validation and calibration.

To feed the dashboard, start the TOPA backend and run:

```powershell
python main.py --backend http://127.0.0.1:8000
```

The same sampled counts are posted to `POST /update/batch` approximately
every 2.5 seconds. The backend handles status confirmation and stale reads.
Set the `TOPA_WRITE_TOKEN` environment variable if the backend uses a write token.
This local detector uses OpenCV and NumPy and needs no Roboflow key.
