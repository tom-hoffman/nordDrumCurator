import os
import zlib
import pickle
from typing import List, Dict

import mido
import crcmod.predefined

import ndexceptions
import model
from constants import *

def messageChecksum(message: mido.Message) -> int:
    return zlib.crc32(message.bin())

# Load/save data root

def load():
    f = open(PICKLE_FILENAME, 'rb')
    d = pickle.load(f)
    f.close()
    return d

def program_file_name(ID: int,
              description: str):
    return f'{str(ID)}-{description}.syx'


# MIDI functions

def is_the_right_port(i: List):
    return MIDI_INTERFACE in i

def is_sysex(m: mido.Message) -> bool:
    return (m.type == "sysex") and (len(m.data) == 108)

def getMidiPort():
    # -> str
    f = filter(is_the_right_port, mido.get_input_names())
    try:
        return next(f)
    except StopIteration:
        raise ndexceptions.MidiInterfaceNotFound(MIDI_INTERFACE, mido.get_input_names())

def clearMidiMessages(port):
    for msg in port.iter_pending():
        print(f"Clearing {msg}.")
    print("Queue clear.")

def save_sysex(name: str, sysex: mido.Message):
    mido.write_syx_file(FILE_PREFIX + name, [sysex])

def read_sysex(file_name: str) -> mido.Message:
    return mido.read_syx_file(FILE_PREFIX + file_name)[0]

def sendMidiProgramChange(port: mido.ports.IOPort,
                    program: int):
    # You need to subtract one from the program because computers.
    port.send(mido.Message('program_change',
                           channel = ND_CHANNEL,
                           program = (program - 1)))

def pushProgramFromFile(port: mido.ports.IOPort,
                file: str):
    syx = read_sysex(file)
    port.send(syx)

calc_checksum = crcmod.predefined.mkCrcFun('crc-ccitt-false')

def resetSysExIndex(m: mido.Message,
                 program_index: int = 0) -> mido.Message:
    # Strip or change the index number and recalculate the checksum.
    # Convert the program index to 0 before storing or comparing.
    b = m.bytes()
    # drop two bytes
    b.pop()
    b.pop()
    b[7] = program_index 
    ba = bytearray(b)
    check = calc_checksum(ba) >> 9
    del b[0] # not sure why you need this
    b.append(check)
    return mido.Message('sysex', data = b)

def allMessageToOne(m: mido.Message) -> mido.Message:
    return convertSysExMessage(m, 6, 0)

def oneMessageToAll(m: mido.Message, n: int) -> mido.Message:
    return convertSysExMessage(m, 8, n)

def receive_one(p: mido.ports.IOPort) -> mido.Message:
    # Blocks.
    return p.receive()

def receive_all(p: mido.ports.IOPort) -> List[mido.Message]:
    # Returns a list of messages converted to ONE export format.
    messages = []
    for i in range(99):
        m = receive_one(p)
        messages.append(c)
    return messages

def send_one(p: mido.ports.IOPort, m: mido.Message):
    p.send(m)

def send_all(l: List[mido.Message]):
    print("Writing sysex file to disc...")
    mido.write_syx_file('write.syx', l)
    print("Pushing sysex file via amidi.")
    os.system('amidi -p hw:6 -s write.syx') # this needs to be smarter
    
    
    
def midiConfirmTone(port: mido.ports.IOPort):
    # Confirmation tone using current program tones.
    for n in CHANNEL_NUMBERS:
        port.send(mido.Message('note_on',
                               note = n,
                               velocity = 50,
                               channel = ND_CHANNEL))

# Misc utility functions.

def programMatch(newCheck: int, progDict: Dict):
    # -1 is no match (ug)
    match = -1
    for k, v in progDict.items():
        if newCheck == v.chk:
            match = k
    return match


        

