from discord.ext.commands import BadArgument

MORSE_CODE_DICT = { 'A':'.-',       'B':'-...',
                    'C':'-.-.',     'D':'-..',      'E':'.',
                    'F':'..-.',     'G':'--.',      'H':'....',
                    'I':'..',       'J':'.---',     'K':'-.-',
                    'L':'.-..',     'M':'--',       'N':'-.',
                    'O':'---',      'P':'.--.',     'Q':'--.-',
                    'R':'.-.',      'S':'...',      'T':'-',
                    'U':'..-',      'V':'...-',     'W':'.--',
                    'X':'-..-',     'Y':'-.--',     'Z':'--..',
                    'Ä':'.-.-',     'Ö':'---.',     'Ü':'..--',
                    '1':'.----',    '2':'..---',    '3':'...--',
                    '4':'....-',    '5':'.....',    '6':'-....',
                    '7':'--...',    '8':'---..',    '9':'----.',
                    '0':'-----',    ',':'--..--',   '.':'.-.-.-',
                    ':':'---...',   "'":'.----.',   '"':'-.--.-',
                    '?':'..--..',   '/':'-..-.',    '-':'-....-',
                    '@':'.--.-.',   '=':'-...-',    '&':'.-...',
                    '(':'-.--.',    ')':'-.--.-',   '!':'-.-.--',
                    'UNDERSTOOD': '...-.'
                }

MORSE_CODE_DICT_INVERTED = {v: k for k, v in MORSE_CODE_DICT.items()}

# Text zu Morsecode
def morse_encrypt(message):
    message = message.upper().lstrip()
    morsecode = ''
    for letter in message:
        if letter != ' ':
            morsecode += (MORSE_CODE_DICT[letter] if letter in MORSE_CODE_DICT else letter)
        morsecode += ' '

    if not morsecode.strip():
        raise BadArgument(message="Der Text ist entweder leer oder enthält nur ungültige Zeichen!")
    return morsecode

# Morsecode zu Text
def morse_decrypt(message):
    i = 0
    message += ' '
    text = ''
    char = ''
    for letter in message:
        if letter != ' ':
            i = 0
            char += letter
        else:
            # Neuer Buchstabe
            i += 1
            # Neues Wort
            if i == 2 :
                # Leerzeichen um neues Wort abzutrennen
                text += ' '
            else:
                text += MORSE_CODE_DICT_INVERTED[char] if char in MORSE_CODE_DICT_INVERTED else "*"
                char = ''

    if not text.replace("*","").strip():
        raise BadArgument(message="Der Morsecode ist entweder leer oder enthält nur ungültige Zeichen!")
    return text
