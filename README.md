# to-tv-audio
Simple script to rip audio from folders full of TV video files, tag them &amp; move them to an output directory.

    to_tv_audio.py
    Generate "TV Audio" mp3s from a folder of one or more video files.
    Usage:
      python to_tv_audio.py -o <OUTPUT DIRECTORY> -s <SHOW NAME> <INPUT DIRECTORY>
    Will find .avi, .mp4 or .mkv files within <INPUT DIRECTORY>, use mplayer to dump the
      audio stream to a PCM wav file then encodes that wav file into an MP3 using
      `lame --preset phone`. The input file or directory will be parsed for season/episode
      information (looking for S##E## in either the filename or its parent directory)
      and the file will be named <OUTPUT DIRECTORY>/S##E##.mp3 with standardized "TV Audio"
      tags.
    Requires:
      mplayer
      lame

