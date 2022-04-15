#!/usr/bin/env python3
# to_tv_audio.py
# Generate "TV Audio" mp3s from a folder of one or more video files.
# Usage:
#   python to_tv_audio.py -o <OUTPUT DIRECTORY> -s <SHOW NAME> <INPUT DIRECTORY>
# Will find .avi, .mp4 or .mkv files within <INPUT DIRECTORY>, use mplayer to dump the
#   audio stream to a PCM wav file then encodes that wav file into an MP3 using
#   `lame --preset phone`. The input file or directory will be parsed for season/episode
#   information (looking for S##E## in either the filename or its parent directory)
#   and the file will be named <OUTPUT DIRECTORY>/S##E##.mp3 with standardized "TV Audio"
#   tags.
# Requires:
#   mplayer
#   lame
import os
import re
import shlex
import argparse
import subprocess
import mutagen.id3

FILE_TYPES = ['.avi', '.mp4', '.mkv']
DUMP_AUDIO_COMMAND = 'mplayer -ao pcm:fast:file="{wav_filename}" -vo null -vc null "{video_filename}"'
ENCODE_AUDIO_COMMAND = 'lame --preset phone "{wav_filename}" "{mp3_filename}"'

def recursive_ls(base):
    ret = []
    for fn in os.listdir(base):
        ffn = os.path.join(base, fn)
        if os.path.isdir(ffn):
            ret.extend(recursive_ls(ffn))
        else:
            ret.append(ffn)

    return ret

class InvalidFilenameException(Exception):
    def __init__(self, fn):
        self.fn = fn

    def __str__(self):
        return "Could not parse season/episode from {}".format(self.fn)

class TVAudioFile(object):
    SEASON_EPISODE_REGEX = None #re.compile(r"[Ss](?P<season_number>\d*)[Ee](?P<episode_number>\d*)")

    @classmethod
    def get_files(klass, folder):
        global FILE_TYPES

        all_files = recursive_ls(os.path.abspath(folder))
        ret = []
        for fn in all_files:
            ffn, ext = os.path.splitext(fn)
            if ext.lower() in FILE_TYPES:
                ret.append(fn)

        return ret

    def __init__(self, video_filename, output_location):
        self.video_filename = video_filename
        self.video_basename = os.path.basename(video_filename)
        self.video_dirname = os.path.dirname(video_filename)
        self.output_location = output_location

    def dump_audio(self):
        cmd = DUMP_AUDIO_COMMAND.format(video_filename=self.video_filename,
                wav_filename=self.wav_filename)
        cmd_s = shlex.split(cmd)
        ret = subprocess.run(cmd_s, capture_output=True)
        return ret.returncode == 0

    def encode_audio(self):
        cmd = ENCODE_AUDIO_COMMAND.format(wav_filename=self.wav_filename,
                    mp3_filename=self.mp3_filename)
        cmd_s = shlex.split(cmd)
        ret = subprocess.run(cmd_s, capture_output=True)
        return ret.returncode == 0

    def tag_mp3(self, artist):
        try:
            id3 = mutagen.id3.ID3()
            id3.add(mutagen.id3.TRCK(encoding=3, text=str(self.episode)))
            id3.add(mutagen.id3.TIT2(encoding=3, text='S{:02d}E{:02d}'.format(self.season, self.episode)))
            id3.add(mutagen.id3.TALB(encoding=3, text='Season {:02d}'.format(self.season)))
            id3.add(mutagen.id3.TPE1(encoding=3, text=artist))
            id3.add(mutagen.id3.TPOS(encoding=3, text=str(self.season)))
            id3.add(mutagen.id3.TCON(encoding=3, text='TV Audio'))
            id3.save(self.mp3_filename)

            return True
        except Exception as e:
            print("Exception while tagging audio file: {}".format(self.mp3_filename))
            print(str(e))
            return False

    # {{{1 Properties
    @property
    def video_filename_match(self):
        m = self.SEASON_EPISODE_REGEX.search(self.video_basename)
        if not m:
            m = self.SEASON_EPISODE_REGEX.search(self.video_dirname)

        if not m:
            raise InvalidFilenameException(self.video_filename)
        else:
            return {
                    'season': m.groupdict()['season_number'],
                    'episode': m.groupdict()['episode_number'],
                }

    @property
    def season(self):
        return int(self.video_filename_match['season']) if self.video_filename_match else None

    @property
    def episode(self):
        return int(self.video_filename_match['episode']) if self.video_filename_match else None

    @property
    def wav_basename(self):
        return 'S{:02d}E{:02d}.wav'.format(self.season, self.episode)

    @property
    def wav_filename(self):
        return os.path.join(self.video_dirname, self.wav_basename)

    @property
    def mp3_basename(self):
        return 'S{:02d}E{:02d}.mp3'.format(self.season, self.episode)

    @property
    def mp3_filename(self):
        return os.path.join(self.output_location, self.mp3_basename)
    # }}}1

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('folder')
    ap.add_argument('-s', '--show', dest='show', required=True)
    ap.add_argument('-o', '--output-location', dest='output_location',
                    required=False, default=os.path.abspath('.'))
    ap.add_argument('-r', '--season-episode-regex', dest='season_episode_regex',
                    required=False, help='Override the default season/episode regex.',
                    default=r'[Ss](?P<season_number>\d+)[Ee](?P<episode_number>\d+)')
    args = ap.parse_args()

    TVAudioFile.SEASON_EPISODE_REGEX = re.compile(args.season_episode_regex)
    
    for fn in TVAudioFile.get_files(args.folder):
        tva = TVAudioFile(fn, args.output_location)
        try:
            print("Will rip {} to {}".format(tva.video_basename, tva.mp3_filename))
            if tva.dump_audio():
                if tva.encode_audio():
                    if tva.tag_mp3(args.show):
                        print("Success.")
                    else:
                        print("Could not tag {}".format(tva.mp3_filename))
                else:
                    print("Could not encode {}".format(tva.wav_filename))
            else:
                print("Could not dump {}".format(tva.video_filename))
        except InvalidFilenameException as e:
            print(e)

