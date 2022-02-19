
from chardet.universaldetector import UniversalDetector


def guess_encoding(filename: str) -> str:
    '''
    Guesses the file's encoding by using an incremental universal detector from chardet.
    '''
    detector = UniversalDetector()
    with open(filename, 'rb') as file:
        for line in file:
            detector.feed(line)
            if detector.done:
                break
    detector.close()
    return detector.result['encoding']
