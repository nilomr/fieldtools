import os
import re
from tqdm.auto import tqdm
import audio_metadata
import pandas as pd

media_dir = '/media/nilomr/AM37'
# Prepare metadata
wavlist = [wavfile for wavfile in os.listdir(
    media_dir) if wavfile.endswith('.WAV')]

metadata = {'path': [], 'filesize': [], 'battery': [], }
for wav in tqdm(wavlist):
    wavfile = os.path.join(media_dir, wav)
    meta = audio_metadata.load(wavfile)
    metadata['filesize'].append(meta['filesize'])
    s = meta["tags"].comment[0]
    batterystate = s[s.find('state was ') +
                     len('state was '):s.rfind(' and temp')]
    metadata['battery'].append(batterystate)
    metadata['path'].append(meta['filepath'])

metadate_df = pd.DataFrame(metadata)


with open('/home/nilomr/Documents/metadata.txt', 'a') as f:
    f.write(
        metadate_df.to_string(header=False, index=False)
    )
