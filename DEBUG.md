# Debug Note: Missing `consumer` in video payload

## Summary
Certain video notes fail during parsing with `KeyError: 'consumer'` in
`xhs_utils/data_util.py::handle_note_info`.

Additionally, raw API responses can now be dumped to
`datas/debug_responses/` only when debug mode is enabled.

## Impact
- `spider_note()` returns `success=False` for affected notes.
- Batch jobs may skip videos or stop early depending on caller logic.

## Symptom
Log example:
```
INFO ... 爬取笔记信息 <note_url>: False, msg: 'consumer'
```

## Root Cause
The code assumed the API response always contains:
```
note_card.video.consumer.origin_video_key
```
However, the current API response for some video notes only provides:
```
note_card.video.media.stream.(h264/h265).*.master_url
```
There is no `consumer` field, so direct access raises `KeyError`.

## Reproduction (example)
1. Call `POST /api/sns/web/v1/feed` for a video note.
2. Response `note_card.type` is `video`.
3. `note_card.video` contains `media.stream` but no `consumer`.
4. `handle_note_info()` raises `KeyError: 'consumer'`.

## Fix
Defensive parsing was added in `xhs_utils/data_util.py`:
1. Keep old path if `video.consumer.origin_video_key` exists.
2. Fallback to the best available stream URL from
   `video.media.stream.h264/h265/av1/h266[*].master_url`.
3. If none exist, `video_addr` remains `None` (no exception).

## Behavior Changes
- Video notes without `consumer` no longer fail.
- `video_addr` now points to the best available `master_url`
  when `consumer` is missing.

## Debug Dump (Optional)
To capture raw API responses when expected fields are missing:

```bash
uv run main.py --debug
```

When `--debug` is enabled, responses are saved to:

```
datas/debug_responses/
```

No files are created if `--debug` is not passed.

## Task Config (JSON)
The three default tasks (notes list, user URL, search query/params) now
come from a JSON config file.

Default config file:
```
config.json
```

Run with a custom config:
```bash
uv run main.py --config /path/to/your_config.json
```

## Simple Note Output
When saving a note, a lightweight `simple.txt` is now generated alongside
`detail.txt` under each note folder. It contains only:
昵称、用户id、标题、描述、标签、上传时间、ip归属地.

## Files Changed
- `xhs_utils/data_util.py`
- `xhs_utils/common_util.py`
- `main.py`
- `config.json`

## Verification
Recommended quick checks:
1. Run a single note fetch for a video note that previously failed.
2. Confirm `video_addr` is populated with a `master_url` (or `None`)
   and the spider completes without exception.
3. Verify that image notes remain unchanged.
