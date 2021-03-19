from colr import color
from PyInquirer import Token, style_from_dict


class tstyle:
    BOLD = '\033[1m'
    END = '\033[0m'
    purple = '673ab7'
    mustard = 'e8a200'
    blue = '3094c9'
    gridteal = '15524f'
    teal = '006666'
    orangelogo = 'cc8431'
    orange = 'fca035'

# Functions


def tcolor(text, hex):
    return color(text, fore=hex)


# Definitions
arrow = tstyle.BOLD + tcolor('> ', tstyle.mustard)
info = tstyle.BOLD + tcolor('i ', tstyle.mustard)


menu_aes = style_from_dict({
    Token.QuestionMark: f'#{tstyle.blue} bold',
    Token.Selected: '#cc5454',  # default
    Token.Pointer: f'#{tstyle.blue} bold',
    Token.Instruction: '#a1a1a1',  # default
    Token.Answer: '#f44336 bold',
    Token.Question: '#cc5454 bold',
})
