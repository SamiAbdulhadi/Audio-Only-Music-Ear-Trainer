"""Audio Only Music Ear Trainer"""
import pandas as pd
import numpy as np
import random
from playsound import playsound
from gtts import gTTS
import os
import time
import tkinter as tk
from tkinter import ttk
import simpleaudio as sa
import wave
import threading

path = os.getcwd() + '\\'

note_names = pd.read_csv(f'{path}note_names.csv', index_col = 'st_from_e2')
possible_notes = note_names.note.to_list()
chord_table = pd.read_csv(f'{path}chord_table.csv')
scale_table = pd.read_csv(f'{path}scale_table.csv')
prog_table = pd.read_csv(f'{path}prog_table.csv')

#Remove 9th chords for now
chord_table = chord_table.loc[chord_table.name.str.contains('9') == False]

clean_mp3filepath = f'{path}electric_guitar_clean-mp3/'
distorted_mp3filepath = f'{path}distortion_guitar-mp3/'
clean_wavfilepath = f'{path}electric_guitar_clean-wav/'
distorted_wavfilepath = f'{path}distortion_guitar-wav/'

#%% class Structure            
class Notes():
    def __init__(self, root_index, name, chord_or_scale, inversion=''):
        self.root_index = root_index
        self.name = name
        self.chord_or_scale = chord_or_scale
        
        if self.chord_or_scale == 'Chord':
            self.table = chord_table
        elif self.chord_or_scale == 'Scale':
            self.table = scale_table
            
        self.structure = list(map(int, self.table.loc[self.table.name == self.name, 'st_structure'].item().split('-')))
        
        self.inversion = inversion
        self.pronounce_name = self.table.loc[self.table.name == self.name, 'pronounce_name'].item() + " " + self.inversion
        self.note_list = [note_names.loc[(i + self.root_index), 'note'] for i in self.structure]
            
        if self.inversion == 'First Inversion':
            chord_third = self.note_list[1]
            chord_third_down_octave = chord_third[:-1] + str(int(chord_third[-1]) - 1)
            self.note_list.pop(1)
            self.note_list.insert(0, chord_third_down_octave)
            
        if self.inversion =='Second Inversion':
            if self.name == 'Power Chord':
                chord_fifth = self.note_list[1]
                self.note_list.pop(1)
            else:
                chord_fifth = self.note_list[2]
                self.note_list.pop(2)
            
            chord_fifth_down_octave = chord_fifth[:-1] + str(int(chord_fifth[-1]) - 1)
            self.note_list.insert(0, chord_fifth_down_octave)    
        
        if self.inversion == 'Third Inversion':
            chord_seventh = self.note_list[3]
            chord_seventh_down_octave = chord_seventh[:-1] + str(int(chord_seventh[-1]) - 1)
            self.note_list.pop(3)
            self.note_list.insert(0, chord_seventh_down_octave)
                
    def play_speech(self):
        speech = gTTS(self.pronounce_name)
        if os.path.exists(f'{path}speech.mp3'):
            os.remove(f'{path}speech.mp3')
        speech.save(f'{path}speech.mp3')    
        playsound(f'{path}speech.mp3')
        
    
class Harmony(Notes):
    def __init__(self, root_index, name, chord_or_scale, inversion=''):
        super().__init__(root_index, name, chord_or_scale, inversion)
    
    def create_chord(self, tone):
        for index, note in enumerate(self.note_list):
            if tone == 'Clean Guitar':
                wave_read = wave.open(f'{clean_wavfilepath}{note}.wav', 'rb')
            elif tone == 'Distortion Guitar':
                wave_read = wave.open(f'{distorted_wavfilepath}{note}.wav', 'rb')
            audio_data = wave_read.readframes(wave_read.getnframes())
            globals()[str(f'decoded_{index}')] = np.fromstring(audio_data, np.int16)
                        
        self.chord_array = decoded_0
        
        for i in range(1, len(self.note_list)):
            self.chord_array += globals()[str(f'decoded_{i}')]
        
        return self.chord_array
            
    def play_chord(self, tone):
        play_obj = sa.play_buffer(self.create_chord(tone), 2, 2, 44100)
        play_obj.wait_done()


def minx(x, length, index):
    return x*((length-index)/length)

class Melody(Notes):
    def __init__(self, root_index, name, chord_or_scale, inversion=''):
        super().__init__(root_index, name, chord_or_scale, inversion)

    def create_arpeggio(self, tone, motion, BPM):        
        if tone == 'Clean Guitar':
            varwavpath = clean_wavfilepath
        elif tone == 'Distortion Guitar':
            varwavpath = distorted_wavfilepath
        
        if motion == 'Ascending':
            var_scale_notes = self.note_list
        elif motion == 'Descending':
            var_scale_notes = self.note_list[::-1]
        elif motion == 'Both':
            var_scale_notes = self.note_list + self.note_list[::-1][1:]
        
        #BPM lower limit is 20 (19.18)
        frames = int((44100*120)/BPM)
        
        for index, note in enumerate(var_scale_notes):
            wave_read = wave.open(f'{varwavpath}{note}.wav', 'rb')
            audio_data = wave_read.readframes(wave_read.getnframes())
            globals()[str(f'decoded_{index}')] = np.fromstring(audio_data, np.int16)
            globals()[str(f'decoded_int16_{index}')] = globals()[str(f'decoded_{index}')].astype(np.int16)
            globals()[str(f'decoded_int16_{index}')] = globals()[str(f'decoded_int16_{index}')][:frames]
            end_frames = int(len(globals()[str(f'decoded_int16_{index}')])*0.1)
            end_array = globals()[str(f'decoded_int16_{index}')][-end_frames:]
            new_array = end_array[0]
            for ind, j in enumerate(end_array):
                new_array = np.append(new_array, minx(j, end_frames, ind))

            new_array = new_array.astype(np.int16)
            globals()[str(f'decoded_int16_{index}')] = np.append(globals()[str(f'decoded_int16_{index}')][:-(end_frames - 1)], new_array)
        
        self.scale_array = decoded_int16_0
        
        for i in range(1, len(var_scale_notes)):
            self.scale_array = np.append(self.scale_array, globals()[str(f'decoded_int16_{i}')])
            
        return self.scale_array
                    
    def play_arpeggio(self, tone, motion, BPM):
        play_obj = sa.play_buffer(self.create_arpeggio(tone, motion, BPM), 2, 2, 44100)
        play_obj.wait_done()
        


class Progression(Harmony, Melody):
    def __init__(self, root_index, prog_list, name='Major', chord_or_scale='Scale', inversion=''):
        super().__init__(root_index, name, chord_or_scale, inversion='')
        self.prog_list = prog_list
        self.pronounce_name = ' '.join([prog_table.loc[prog_table.scale_degree == i, 'pronounce'].item() for i in self.prog_list])
        
    def create_chord_progression(self, tone, BPM, triad_or_seventh='Triad'):      
        #BPM lower limit is 20 (19.18)
        frames = int((44100*120)/BPM)
        
        for index, chord in enumerate(self.prog_list):
            chord_root = prog_table.index[prog_table.scale_degree == chord].item()
            chord_type = prog_table.loc[prog_table.scale_degree == chord, triad_or_seventh].item()
            globals()[str(f'chord_{index}')] = Harmony(self.root_index + self.structure[chord_root], chord_type, 'Chord').create_chord(tone)
            
            globals()[str(f'chord_{index}')] = globals()[str(f'chord_{index}')][:frames]
            end_frames = int(len(globals()[str(f'chord_{index}')])*0.1)
            end_array = globals()[str(f'chord_{index}')][-end_frames:]
            new_array = end_array[0]
            for ind, j in enumerate(end_array):
                new_array = np.append(new_array, minx(j, end_frames, ind))

            new_array = new_array.astype(np.int16)
            globals()[str(f'chord_{index}')] = np.append(globals()[str(f'chord_{index}')][:-(end_frames - 1)], new_array)
            
        self.chord_array = chord_0
            
        for i in range(1, len(self.prog_list)):
            self.chord_array = np.append(self.chord_array, globals()[str(f'chord_{i}')])
        
        return self.chord_array  
    
    def play_chord_progression(self, tone, BPM, triad_or_seventh='Triad'):
        play_obj = sa.play_buffer(self.create_chord_progression(tone, BPM, triad_or_seventh), 2, 2, 44100)
        play_obj.wait_done()
    
    def create_arpeggio_progression(self, tone, BPM, motion='Ascending', triad_or_seventh='Triad'):      
        for index, chord in enumerate(self.prog_list):
            chord_root = prog_table.index[prog_table.scale_degree == chord].item()
            chord_type = prog_table.loc[prog_table.scale_degree == chord, triad_or_seventh].item()
            globals()[str(f'chord_{index}')] = Melody(self.root_index + self.structure[chord_root], chord_type, 'Chord').create_arpeggio(tone, motion, BPM)

        self.arpeggio_array = chord_0
            
        for i in range(1, len(self.prog_list)):
            self.arpeggio_array = np.append(self.arpeggio_array, globals()[str(f'chord_{i}')])
        
        return self.arpeggio_array
    
    def play_arpeggio_progression(self, tone, BPM, motion='Ascending', triad_or_seventh='Triad'):
        play_obj = sa.play_buffer(self.create_arpeggio_progression(tone, BPM), 2, 2, 44100) 
        play_obj.wait_done()


def Melody_Recursion(name, chord_or_scale, inversion=''):
    play_root = random.randint(0,47)
    try:
        play_melody = Melody(play_root, name, chord_or_scale, inversion)
    except KeyError:
        return Melody_Recursion(name, chord_or_scale, inversion)
    
    for note in play_melody.note_list:
        if note not in possible_notes:
            return Melody_Recursion(name, chord_or_scale, inversion)
    
    return play_melody

def Harmony_Recursion(name, chord_or_scale, inversion=''):
    play_root = random.randint(0,47)   
    try:
        play_harmony = Harmony(play_root, name, chord_or_scale, inversion)
    except KeyError:
        return Harmony_Recursion(name, chord_or_scale, inversion)
    
    for note in play_harmony.note_list:
        if note not in possible_notes:
            return Harmony_Recursion(name, chord_or_scale, inversion)
    
    return play_harmony

def Progression_Recursion(chord_list):
    play_root = random.randint(0,47)
    try:
        check = Progression(play_root, chord_list).create_chord_progression('Clean Guitar', 60, 'Seventh')
        return Progression(play_root, chord_list)
        del check
    except KeyError:
        return Progression_Recursion(chord_list)


#%% Base app construction        
root = tk.Tk()
root.geometry('470x480')
root.title('Audio-Only Music Ear Trainer')
root.iconbitmap(f'{path}icon.ico')
root.configure(bg='white')

my_notebook = ttk.Notebook(root)
my_notebook.pack()

frame_intervals = tk.Frame(my_notebook, width = 450, height = 450)
frame_intervals.pack(fill = 'both', expand = 1)
frame_chords = tk.Frame(my_notebook, width = 450, height = 450)
frame_chords.pack(fill = 'both', expand = 1)
frame_scales = ttk.Frame(my_notebook, width = 450, height = 450)
frame_scales.pack(fill = 'both', expand = 1)
frame_progressions = ttk.Frame(my_notebook, width = 450, height = 450)
frame_progressions.pack(fill = 'both', expand = 1)

my_notebook.add(frame_intervals, text = 'Intervals')
my_notebook.add(frame_chords, text = 'Chords')
my_notebook.add(frame_scales, text = 'Scales')
my_notebook.add(frame_progressions, text = 'Progressions')

class label:
    def __init__(self, text, size, x, y):
        self.text = text
        self.size = size
        self.x = x
        self.y = y
    def create_label(self, frame):
        lab = tk.Label(frame, text = self.text)
        lab.config(font = ('helvetica', self.size))
        lab.place(x = self.x, y = self.y)

#%% Intervals
label_title = label('Audio-Only Interval Ear Trainer', 16, 80, 10).create_label(frame_intervals)
label_intervals = label('Select Intervals', 14, 30, 50).create_label(frame_intervals)
label_tone = label('Select Tone', 14, 217, 50).create_label(frame_intervals)
label_melharm = label('Select Melodic/Harmonic', 14, 217, 125).create_label(frame_intervals)
label_repeat = label('Repeat Interval?', 14, 217, 220).create_label(frame_intervals)
label_bpm = label('BPM', 14, 217, 275).create_label(frame_intervals)
label_wait = label('Answer Wait Time (sec)', 14, 217, 310).create_label(frame_intervals)

interval_tone = tk.StringVar()
interval_tone.set('Clean Guitar')
interval_tone_dropdown = tk.OptionMenu(frame_intervals, interval_tone, 'Clean Guitar', 'Distortion Guitar')
interval_tone_dropdown.place(x=235, y=80)

interval_repeat = tk.BooleanVar()
interval_repeat_click = tk.Checkbutton(frame_intervals, text = 'Repeat Once', variable = interval_repeat, onvalue=True, offvalue=False, takefocus = 0).place(x = 220, y = 245)
interval_repeat.set(False)

interval_wait = tk.Entry(frame_intervals, width = 7)
interval_wait.insert(0, '2')
interval_wait.place(x=230, y=345)

interval_BPM = tk.Entry(frame_intervals, width = 7)
interval_BPM.insert(0, '60')
interval_BPM.place(x=285, y=280)

interval_names = chord_table.loc[chord_table.chord_group == 'Interval']

all_intervals = interval_names.name.tolist()

all_melodic_harmonic = ['Ascending', 'Descending', 'Harmonic']

for interval in all_intervals:
    globals()[str(f'{interval}_v1')] = tk.BooleanVar()
    interval_long_name_temp = interval_names.loc[interval_names.name == interval, 'pronounce_name'].item()
    y_height = all_intervals.index(interval)*20
    globals()[str(f'{interval}_check')] = tk.Checkbutton(frame_intervals, text = interval_long_name_temp, variable = globals()[str(f'{interval}_v1')], onvalue=True, offvalue=False, takefocus = 0).place(x = 35, y = 75+y_height)
    globals()[str(f'{interval}_v1')].set(True)
    
for melharm in all_melodic_harmonic:
    globals()[str(f'{melharm}_v1')] = tk.BooleanVar()
    y_height = all_melodic_harmonic.index(melharm)*20
    globals()[str(f'{melharm}_check')] = tk.Checkbutton(frame_intervals, text = melharm, variable = globals()[str(f'{melharm}_v1')], onvalue=True, offvalue=False, takefocus = 0).place(x = 220, y = 150+y_height)
    globals()[str(f'{melharm}_v1')].set(True)


def Interval_Function():
    if running:
        sleep_time = int(interval_wait.get())
        repeat = interval_repeat.get()
        tone = interval_tone.get()
        BPM = int(interval_BPM.get())
        
        #Create True/False list of selected checkbox intervals
        TF_interval = [globals()[str(f'{i}_v1')].get() for i in all_intervals]
        TF_melharm = [globals()[str(f'{i}_v1')].get() for i in all_melodic_harmonic]
        
        select_interval = []
        select_melharm = []
        
        for i in range(len(all_intervals)):
            if TF_interval[i] == True:
                select_interval.append(all_intervals[i])
            
        for i in range(len(all_melodic_harmonic)):
            if TF_melharm[i] == True:
                select_melharm.append(all_melodic_harmonic[i])
                
        play_interval = random.choice(select_interval)
        play_melharm = random.choice(select_melharm)
        
        if play_melharm == 'Ascending':
            current_interval = Melody_Recursion(play_interval, 'Chord')
            current_interval.play_arpeggio(tone, play_melharm, BPM)
            time.sleep(sleep_time)
            current_interval.play_speech()
            
            if repeat == True:
                time.sleep(1)
                current_interval.play_arpeggio(tone, play_melharm, BPM)
                time.sleep(sleep_time)
                current_interval.play_speech()
        
        elif play_melharm == 'Descending':
            current_interval = Melody_Recursion(play_interval, 'Chord')
            current_interval.play_arpeggio(tone, play_melharm, BPM)
            time.sleep(sleep_time)
            current_interval.play_speech()
            
            if repeat == True:
                time.sleep(1)
                current_interval.play_arpeggio(tone, play_melharm, BPM)
                time.sleep(sleep_time)
                current_interval.play_speech()
    
        elif play_melharm == 'Harmonic':
            current_interval = Harmony_Recursion(play_interval, 'Chord')
            current_interval.play_chord(tone)
            time.sleep(sleep_time)
            current_interval.play_speech()
            
            if repeat == True:
                time.sleep(1)
                current_interval.play_chord(tone)
                time.sleep(sleep_time)
                current_interval.play_speech()
        

def Interval_Looper():
    global running
    running = True   
    repetition = 0
    while repetition < 1000:
        Interval_Function()
        if running == False:
            break
        time.sleep(1)
        repetition +=1

def start():
    threading.Thread(target=Interval_Looper).start()

def stop():
    global running
    running = False
    
play_button = tk.Button(frame_intervals, text = 'Play', command = start, bg = 'dodgerblue', fg = 'white', font = ('helvetica', 12, 'bold'))
play_button.place(x=170, y=380)

stop_button = tk.Button(frame_intervals, text = 'Stop', command = stop, bg = 'tomato', fg = 'white', font = ('helvetica', 12, 'bold'))
stop_button.place(x=230, y=380)

#%% Chords
label_title_c = label('Audio-Only Chord Ear Trainer', 16, 80, 10).create_label(frame_chords)
label_chords = label('Select Chords', 14, 30, 50).create_label(frame_chords)
label_tone_c = label('Select Tone', 14, 217, 50).create_label(frame_chords)
label_tone_c = label('Chord/Arpeggio', 14, 217, 88).create_label(frame_chords)
label_inversions_c = label('Select Inversions', 14, 217, 125).create_label(frame_chords)
label_repeat_c = label('Repeat Chord?', 14, 217, 240).create_label(frame_chords)
label_bpm = label('BPM', 14, 217, 295).create_label(frame_chords)
label_wait_c = label('Answer Wait Time (sec)', 14, 217, 325).create_label(frame_chords)

chord_tone = tk.StringVar()
chord_tone.set('Clean Guitar')
chord_tone_dropdown = tk.OptionMenu(frame_chords, chord_tone, 'Clean Guitar', 'Distortion Guitar')
chord_tone_dropdown.place(x=325, y=50)

chord_arpeggiate = tk.StringVar()
chord_arpeggiate.set('Chord')
chord_arpeggiate_dropdown = tk.OptionMenu(frame_chords, chord_arpeggiate, 'Chord', 'Arpeggio')
chord_arpeggiate_dropdown.place(x=358, y=88)

chord_repeat = tk.BooleanVar()
chord_repeat_click = tk.Checkbutton(frame_chords, text = 'Repeat Once', variable = chord_repeat, onvalue=True, offvalue=False, takefocus = 0).place(x = 220, y = 265)
chord_repeat.set(False)

chord_wait = tk.Entry(frame_chords, width = 7)
chord_wait.insert(0, '2')
chord_wait.place(x=230, y=360)

chord_BPM = tk.Entry(frame_chords, width = 7)
chord_BPM.insert(0, '60')
chord_BPM.place(x=285, y=300)

all_chords = chord_table.loc[chord_table.chord_group != 'Interval'].name.tolist()

all_inversion_options = ['Root Position', 'First Inversion', 'Second Inversion', 'Third Inversion']

for chord in all_chords:
    temp_chord = chord.replace(' ', '_')
    globals()[str(f'{temp_chord}_v1')] = tk.BooleanVar()
    y_height = all_chords.index(chord)*20
    globals()[str(f'{temp_chord}_check')] = tk.Checkbutton(frame_chords, text = chord, variable = globals()[str(f'{temp_chord}_v1')], onvalue=True, offvalue=False, takefocus = 0).place(x = 35, y = 75+y_height)

Power_Chord_v1.set(True)
Major_v1.set(True)
Minor_v1.set(True)
    
for inversion in all_inversion_options:
    temp_inversion = inversion.replace(' ', '_')
    globals()[str(f'{temp_inversion}_v1')] = tk.BooleanVar()
    y_height = all_inversion_options.index(inversion)*20
    globals()[str(f'{temp_inversion}_check')] = tk.Checkbutton(frame_chords, text = inversion, variable = globals()[str(f'{temp_inversion}_v1')], onvalue=True, offvalue=False, takefocus = 0).place(x = 220, y = 150+y_height)

Root_Position_v1.set(True)

def Chord_Function():
    if running:
        chord_arpeggio = chord_arpeggiate.get() 
        sleep_time = int(chord_wait.get())
        repeat = chord_repeat.get()
        tone = chord_tone.get()
        BPM = int(chord_BPM.get())
        
        select_chord = []
        select_inversion = []
        
        #Create True/False list of selected checkbox chords
        TF_chord = []
        TF_inversion = []
        
        for chord in all_chords:
            temp_chord = chord.replace(' ', '_')
            temp_chord_name = f'{temp_chord}_v1'
            TF_chord.append(globals()[str(temp_chord_name)].get())
        
        for inversion in all_inversion_options:
            temp_inversion = inversion.replace(' ', '_')
            temp_inversion_name = f'{temp_inversion}_v1'
            TF_inversion.append(globals()[str(temp_inversion_name)].get())
        
        for i in range(len(all_chords)):
            if TF_chord[i] == True:
                select_chord.append(all_chords[i])
        
        for i in range(len(all_inversion_options)):
            if TF_inversion[i] == True:
                select_inversion.append(all_inversion_options[i])
            
        play_chord = random.choice(select_chord)
        play_inversion = random.choice(select_inversion)
        
        if play_inversion == 'Root Position':        
            if chord_arpeggio == 'Chord':
                current_chord = Harmony_Recursion(play_chord, 'Chord')
            if chord_arpeggio == 'Arpeggio':
                current_chord = Melody_Recursion(play_chord, 'Chord')
                    
        elif play_inversion == 'First Inversion':     
            first_inv_chord_list = select_chord
            try:
                first_inv_chord_list.pop(first_inv_chord_list.index('Power Chord'))
            except ValueError:  
                pass
            
            play_chord = random.choice(first_inv_chord_list)
            
            if chord_arpeggio == 'Chord':
                current_chord = Harmony_Recursion(play_chord, 'Chord', 'First Inversion')
            if chord_arpeggio == 'Arpeggio':
                current_chord = Melody_Recursion(play_chord, 'Chord', 'First Inversion')

            
        elif play_inversion == 'Second Inversion':
            if chord_arpeggio == 'Chord':
                current_chord = Harmony_Recursion(play_chord, 'Chord', 'Second Inversion')
            if chord_arpeggio == 'Arpeggio':
                current_chord = Melody_Recursion(play_chord, 'Chord', 'Second Inversion')
            
        elif play_inversion == 'Third Inversion':
            no_third_inv = ['Power Chord', 'Major', 'Minor', 'Augmented', 'Diminished', 'Sus2', 'Sus4']
            third_inv_chord_list = select_chord
            
            for i in no_third_inv:
                try:
                    third_inv_chord_list.pop(third_inv_chord_list.index(i))
                except ValueError:  
                    pass
             
            play_chord = random.choice(third_inv_chord_list)
            
            if chord_arpeggio == 'Chord':
                current_chord = Harmony_Recursion(play_chord, 'Chord', 'Third Inversion')
            if chord_arpeggio == 'Arpeggio':
                current_chord = Melody_Recursion(play_chord, 'Chord', 'Third Inversion')
            
            
        if chord_arpeggio == 'Chord':
            current_chord.play_chord(tone)
        
        elif chord_arpeggio == 'Arpeggio':
            current_chord.play_arpeggio(tone, 'Ascending', BPM)
        
        time.sleep(sleep_time)
        current_chord.play_speech()
        
        if repeat == True:
            if chord_arpeggio == 'Chord':
                time.sleep(1)
                current_chord.play_chord(tone)
                time.sleep(1)
                current_chord.play_speech()
            elif chord_arpeggio == 'Arpeggio':
                time.sleep(1)
                current_chord.play_arpeggio(tone, 'Ascending', BPM)
                time.sleep(1)
                current_chord.play_speech()

def Chord_Looper():
    global running
    running = True  
    repetition = 0
    while repetition < 1000:
        Chord_Function()
        if running == False:
            break
        time.sleep(1)
        repetition +=1

def start():
    threading.Thread(target=Chord_Looper).start()

def stop():
    global running
    running = False
    
play_button_c = tk.Button(frame_chords, text = 'Play', command = start, bg = 'dodgerblue', fg = 'white', font = ('helvetica', 12, 'bold'))
play_button_c.place(x=170, y=400)

stop_button = tk.Button(frame_chords, text = 'Stop', command = stop, bg = 'tomato', fg = 'white', font = ('helvetica', 12, 'bold'))
stop_button.place(x=230, y=400)

#%% Scales
label_title = label('Audio-Only Interval Ear Trainer', 16, 80, 10).create_label(frame_scales)
label_scales = label('Select Scales', 14, 30, 50).create_label(frame_scales)
label_tone = label('Select Tone', 14, 217, 50).create_label(frame_scales)
label_asc_desc = label('Select Ascend/Descend', 14, 217, 125).create_label(frame_scales)
label_bpm = label('BPM', 14, 217, 275).create_label(frame_scales)
label_repeat = label('Repeat Scale?', 14, 217, 220).create_label(frame_scales)
label_wait = label('Answer Wait Time (sec)', 14, 217, 310).create_label(frame_scales)

scale_tone = tk.StringVar()
scale_tone.set('Clean Guitar')
scale_tone_dropdown = tk.OptionMenu(frame_scales, scale_tone, 'Clean Guitar', 'Distortion Guitar')
scale_tone_dropdown.place(x=235, y=80)

scale_BPM = tk.Entry(frame_scales, width = 7)
scale_BPM.insert(0, '240')
scale_BPM.place(x=285, y=280)

scale_repeat = tk.BooleanVar()
scale_repeat_click = tk.Checkbutton(frame_scales, text = 'Repeat Once', variable = scale_repeat, onvalue=True, offvalue=False, takefocus = 0).place(x = 220, y = 245)
scale_repeat.set(False)

scale_wait = tk.Entry(frame_scales, width = 7)
scale_wait.insert(0, '2')
scale_wait.place(x=230, y=345)

all_scales = scale_table.name.tolist()

all_asc_desc = ['Ascending', 'Descending', 'Both']

for scale in all_scales:
    temp_scale = scale.replace(' ', '_')
    globals()[str(f'{temp_scale}_v2')] = tk.BooleanVar()
    y_height = all_scales.index(scale)*20
    globals()[str(f'{temp_scale}_check2')] = tk.Checkbutton(frame_scales, text = scale, variable = globals()[str(f'{temp_scale}_v2')], onvalue=True, offvalue=False, takefocus = 0).place(x = 35, y = 75+y_height)

Major_v2.set(True)
Minor_v2.set(True)
Pentatonic_Minor_v2.set(True)    

for asc_desc in all_asc_desc:
    globals()[str(f'{asc_desc}_v2')] = tk.BooleanVar()
    y_height = all_asc_desc.index(asc_desc)*20
    globals()[str(f'{asc_desc}_check2')] = tk.Checkbutton(frame_scales, text = asc_desc, variable = globals()[str(f'{asc_desc}_v2')], onvalue=True, offvalue=False, takefocus = 0).place(x = 220, y = 150+y_height)

Ascending_v2.set(True)

def Scale_Function():
    if running:         
        BPM = int(scale_BPM.get())
        sleep_time = int(scale_wait.get())
        repeat = scale_repeat.get()
        tone = scale_tone.get()
        
        select_scale = []
        select_asc_desc = []
        
        TF_scale = []
        TF_asc_desc = []
        
        for scale in all_scales:
            temp_scale = scale.replace(' ', '_')
            temp_scale_name = f'{temp_scale}_v2'
            TF_scale.append(globals()[str(temp_scale_name)].get())
        
        TF_asc_desc = [globals()[str(f'{i}_v2')].get() for i in all_asc_desc]
                
        select_scale.clear()
        select_asc_desc.clear()
        
        for i in range(len(all_scales)):
            if TF_scale[i] == True:
                select_scale.append(all_scales[i])
        
        for i in range(len(all_asc_desc)):
            if TF_asc_desc[i] == True:
                select_asc_desc.append(all_asc_desc[i])
        
        play_scale = random.choice(select_scale)
        play_asc_desc = random.choice(select_asc_desc)
        
        current_scale = Melody_Recursion(play_scale, 'Scale')
        current_scale.play_arpeggio(tone, play_asc_desc, BPM)
        time.sleep(sleep_time)
        current_scale.play_speech()
            
        if repeat == True:
            time.sleep(1)
            current_scale.play_arpeggio(tone, play_asc_desc, BPM)
            time.sleep(sleep_time)
            current_scale.play_speech()       
            
def Scale_Looper():
    global running
    running = True
    repetition = 0
    while repetition < 1000:
        Scale_Function()
        if running == False:
            break
        repetition +=1

def start():
    threading.Thread(target=Scale_Looper).start()

def stop():
    global running
    running = False
    
play_button = tk.Button(frame_scales, text = 'Play', command = start, bg = 'dodgerblue', fg = 'white', font = ('helvetica', 12, 'bold'))
play_button.place(x=170, y=380)

stop_button = tk.Button(frame_scales, text = 'Stop', command = stop, bg = 'tomato', fg = 'white', font = ('helvetica', 12, 'bold'))
stop_button.place(x=230, y=380)

#%%Progressions
label_title = label('Audio-Only Interval Ear Trainer', 16, 80, 10).create_label(frame_progressions)
label_prog = label('Major Scale Chords', 14, 30, 50).create_label(frame_progressions)
label_tone = label('Select Tone', 14, 217, 50).create_label(frame_progressions)
label_chord_arp = label('Chord/Arpeggio', 14, 217, 88).create_label(frame_progressions)
label_melharm = label('Start/Resolve on Root', 14, 217, 125).create_label(frame_progressions)
label_chords = label('# of Chords', 14, 217, 195).create_label(frame_progressions)
label_bpm = label('BPM', 14, 217, 230).create_label(frame_progressions)
label_repeat = label('Repeat Progression?', 14, 217, 265).create_label(frame_progressions)
label_wait = label('Answer Wait Time (sec)', 14, 217, 320).create_label(frame_progressions)
label_triad = label('Chord Extension', 14, 30, 250).create_label(frame_progressions)

prog_tone = tk.StringVar()
prog_tone.set('Clean Guitar')
prog_tone_dropdown = tk.OptionMenu(frame_progressions, prog_tone, 'Clean Guitar', 'Distortion Guitar')
prog_tone_dropdown.place(x=325, y=50)

prog_arpeggiate = tk.StringVar()
prog_arpeggiate.set('Chord')
prog_arpeggiate_dropdown = tk.OptionMenu(frame_progressions, prog_arpeggiate, 'Chord', 'Arpeggio')
prog_arpeggiate_dropdown.place(x=358, y=88)

prog_root = tk.StringVar()
prog_root.set('Start on Root')
prog_root_dropdown = tk.OptionMenu(frame_progressions, prog_root, 'Start on Root', 'Resolve on Root', 'None')
prog_root_dropdown.place(x=235, y=155)

prog_chord_number = tk.Entry(frame_progressions, width = 7)
prog_chord_number.insert(0, '4')
prog_chord_number.place(x=340, y=200)

prog_BPM = tk.Entry(frame_progressions, width = 7)
prog_BPM.insert(0, '120')
prog_BPM.place(x=285, y=235)

prog_repeat = tk.BooleanVar()
prog_repeat_click = tk.Checkbutton(frame_progressions, text = 'Repeat Once', variable = prog_repeat, onvalue=True, offvalue=False, takefocus = 0).place(x = 220, y = 290)
prog_repeat.set(False)

prog_wait = tk.Entry(frame_progressions, width = 7)
prog_wait.insert(0, '2')
prog_wait.place(x=230, y=355)

prog_triad_or_seventh = tk.StringVar()
prog_triad_or_seventh.set('Triad')
prog_triad_or_seventh_dropdown = tk.OptionMenu(frame_progressions, prog_triad_or_seventh, 'Triad', 'Seventh')
prog_triad_or_seventh_dropdown.place(x=50, y=280)

roman_numerals = ['I / I maj⁷', 'ii / ii min⁷', 'iii / iii min⁷', 'IV / IV maj⁷', 'V / V7', 'vi / vi min⁷', 'vii° / viiø', '(I / I maj⁷)']

roman_series = pd.Series(roman_numerals, name='roman_numerals')

prog_table_full = prog_table.merge(roman_series, left_index=True, right_index=True)

all_prog = prog_table_full.iloc[:,0].to_list()

for roman in all_prog:
    globals()[str(f'{roman}_v1')] = tk.BooleanVar()
    y_height = all_prog.index(roman)*20
    text = prog_table_full.loc[prog_table_full.scale_degree == roman , 'roman_numerals'].item()
    globals()[str(f'{roman}_check')] = tk.Checkbutton(frame_progressions, text = text, variable = globals()[str(f'{roman}_v1')], onvalue=True, offvalue=False, takefocus = 0).place(x = 35, y = 75+y_height)

I_v1.set(True)
IV_v1.set(True)
V_v1.set(True)
I_oct_up_v1.set(True)    

def Prog_Function():
    if running:
        BPM = int(prog_BPM.get())
        sleep_time = int(prog_wait.get())
        repeat = prog_repeat.get()
        tone = prog_tone.get()
        chord_num = int(prog_chord_number.get())
        triad = prog_triad_or_seventh.get()
        arpeg = prog_arpeggiate.get()
        resolve = prog_root.get()
        
        select_prog = []
        TF_prog = []
        
        for p in all_prog:
            temp_prog_name = f'{p}_v1'
            TF_prog.append(globals()[str(temp_prog_name)].get())
        
        for i in range(len(all_prog)):
            if TF_prog[i] == True:
                select_prog.append(all_prog[i])
        
        i = 0
        play_prog = []
        while i < chord_num:
            play_prog.append(random.choice(select_prog))
            i +=1
        
        if resolve == 'Start on Root':
            play_prog[0] = 'I'
        elif resolve == 'Resolve on Root':
            play_prog[-1] = 'I_oct_up'
        
        print(play_prog)
        
        current_prog = Progression_Recursion(play_prog)
        
        if arpeg == 'Chord':
            current_prog.play_chord_progression(tone, BPM, triad)
        elif arpeg == 'Arpeggio':
            current_prog.play_arpeggio_progression(tone, BPM, triad)
        
        time.sleep(sleep_time)    
        
        current_prog.play_speech()
        
        if repeat == True:
            time.sleep(1)
            if arpeg == 'Chord':
                current_prog.play_chord_progression(tone, BPM, triad)
            elif arpeg == 'Arpeggio':
                current_prog.play_arpeggio_progression(tone, BPM, triad)
            time.sleep(sleep_time)
            current_prog.play_speech()  
     
 
def Prog_Looper():
    global running
    running = True
    repetition = 0
    while repetition < 1000:
        Prog_Function()
        if running == False:
            break
        repetition +=1
 
def start():
    threading.Thread(target=Prog_Looper).start()

def stop():
    global running
    running = False
    
play_button = tk.Button(frame_progressions, text = 'Play', command = start, bg = 'dodgerblue', fg = 'white', font = ('helvetica', 12, 'bold'))
play_button.place(x=170, y=400)

stop_button = tk.Button(frame_progressions, text = 'Stop', command = stop, bg = 'tomato', fg = 'white', font = ('helvetica', 12, 'bold'))
stop_button.place(x=230, y=400)

#%% End
root.mainloop()