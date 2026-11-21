# StudySpot detector demo

This offline detector is calibrated for the team's 60-second synthetic
`videos/learning_center_2.mp4` clip. It compares chair and tabletop regions
with the first, empty frame. Chair-region changes estimate seated people.
The items field is 0 or 1 and means a tabletop change was detected.

Create the videos folder here and put the team's learning_center_2.mp4 inside before starting. The team ZIP includes the video.

## Windows launcher

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

This writes `output/tables.csv` and `output/room.csv`. Room totals are reported
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
