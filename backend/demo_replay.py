"""A shared video replay, kept separate from the live detector's table store."""
from bisect import bisect_right
from time import monotonic
import json
import math
from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel, Field, ValidationError

router = APIRouter()
replay = None

class Table(BaseModel):
    table_id: int = Field(gt=0, le=23)
    seats: int = Field(gt=0, le=20)
    people: int = Field(ge=0, le=20)
    items: int = Field(ge=0, le=100)
    video_seconds: int = Field(ge=0, le=3600)

@router.post('/demo/replay')
async def publish(request: Request):
    global replay
    body = bytearray()
    async for chunk in request.stream():
        if len(body) + len(chunk) > 1024 * 1024:
            raise HTTPException(413, 'Replay is too large.')
        body.extend(chunk)
    try:
        data = json.loads(body)
        duration = float(data['duration'])
        if not 0 < duration <= 3600 or not isinstance(data['tables'], list):
            raise ValueError
        frames = {}
        for raw in data['tables']:
            t = Table(**raw)
            if t.video_seconds >= duration or t.video_seconds % 10 or t.people > t.seats:
                raise ValueError
            frame = frames.setdefault(t.video_seconds, {})
            if t.table_id in frame:
                raise ValueError
            status = 'full' if t.people >= t.seats else 'partly' if t.people else 'items' if t.items else 'free'
            frame[t.table_id] = dict(table_id=t.table_id,seats=t.seats,people=t.people,status=status)
        if set(frames) != set(range(0, math.ceil(duration - .001), 10)) or not frames or any(set(f) != set(frames[0]) for f in frames.values()):
            raise ValueError
    except (ValueError, TypeError, KeyError, UnicodeError, ValidationError):
        raise HTTPException(422, 'Invalid replay timeline.') from None
    replay = (monotonic(), duration, sorted(frames), frames)
    return {'published': True}

@router.get('/demo/replay')
def current(response: Response):
    response.headers['Cache-Control'] = 'no-store'
    if replay is None:
        return {'active': False}
    start, duration, times, frames = replay
    second = times[bisect_right(times, (monotonic()-start) % duration)-1]
    return {'active': True, 'video_seconds':second, 'people_so_far':None,'tables':list(frames[second].values())}
