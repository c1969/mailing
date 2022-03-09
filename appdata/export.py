'''
Diese Script zipped den Upload-Ordner für den Drucker/Sigloch
Nach dem Zippen bitte das Zip File kopieren
'''

import os
import shutil
from datetime import datetime
from time import strftime

def getnow():
    now = datetime.now()
    return now.strftime("%Y_%m_%d-%H_%M")

p = os.path.join('static', 'export')

output_1 = p + "/" + f'asstets_{getnow()}'
shutil.make_archive(output_1, 'zip', os.path.join('static', 'upload'))

output_2 = p + "/" + f'db_{getnow()}'
shutil.make_archive(output_2, 'zip', os.path.join('db'))
