import os


def all_pitch_folders_path(pid):
    pitch_folder = os.path.abspath(os.path.join("uploads", str(pid)))
    return pitch_folder, os.path.join(pitch_folder, 'references')
