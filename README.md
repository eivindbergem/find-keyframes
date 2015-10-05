# find-keyframes.py
Python library for finding keyframes in MPEG TS files. Intended as a faster alternative to using FFProbe. Useful for creating I-frame playlists for HLS.

# Disclaimer
I have a very limited understanding of the MPEG TS format. This library has only been tested with a small selection of MPEG TS files and will most likely break if the files differ enough.

If you find something that looks wrong it probably is.

# Documentation
Get keyframes:
```
>>> from findkeyframes import get_keyframes
>>> keyframes = get_keyframes("video.ts")
```

This gives you an array of Frame objects containg information about
the keyframes:

```
>>> keyframe = keyframes[0]
>>> keyframe.pos
564
>>> keyframe.size
1504
>>> keyframe.duration
8.673599999999977
```

Where `pos` is the position of the TS packet containing the start of the keyframe in bytes, `size` is the size of the keyframe in bytes, and `duration` is the time duration from the start of the keyframe up until the next keyframe.
