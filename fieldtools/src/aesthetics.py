from colr import color
from PyInquirer import Token, style_from_dict
from cfonts import render, say

# Functions


def tcolor(text, hex):
    return color(text, fore=hex)


def build_logo(version, logo_text, font):
    output = render(logo_text, colors=[
        f'#{tstyle.mustard}', f'#{tstyle.teal}'],
        align='left', font=font,
        space=False, letter_spacing=1,
        line_height=0, max_length=0)
    print(tcolor("""
                                   #&#&#&  
                                 @@@@@&&&%     
                              *@@  ,#@@@@@/%> 
                          ,/(//@@@.     @@&    
                        (##/##(#(%..*@@@@&     
                   (,#,.%#(%((..,,,....&@&     
                /,%,%/,@&/&%(****,.....&&.     
           _,%&&&&%((//////*****,,.....@.      
  _-_,((##, .*,*,***/****,******,....&&        
                   *(*****,,**,../&           
                         /*(%/                     
                          #  #                   
                        *-$%~-%=-           """, tstyle.teal))
    print(output.replace('\x01', '').replace(' \x1b', '\x1b'))
    print(tstyle.BOLD + tcolor(f' version {version}', tstyle.teal))


# Definitions

class tstyle:
    BOLD = '\033[1m'
    END = '\033[0m'
    purple = '673ab7'
    mustard = 'e8a200'
    blue = '3094c9'
    gridteal = '15524f'
    teal = '0b7878'  # conda dea'006666'
    azulroto = '6ca2a8'
    orangelogo = 'cc8431'
    orange = 'fca035'
    white = 'ffffff'
    lightgrey = 'e0e0e0'
    rojoroto = 'c94a40'


arrow = tstyle.BOLD + tcolor('> ', tstyle.mustard)
info = tstyle.BOLD + tcolor('i ', tstyle.mustard)
qmark = tstyle.BOLD + tcolor('? ', tstyle.mustard)


menu_aes = style_from_dict({
    Token.QuestionMark: f'#{tstyle.mustard} bold',
    Token.Selected: f'#{tstyle.lightgrey} bold',  # default
    Token.Pointer: f'#{tstyle.mustard} bold',
    Token.Instruction: '#a1a1a1',  # default
    Token.Answer: f'#{tstyle.rojoroto} bold',
    Token.Question: f'#{tstyle.white} bold',
})


def print_dict(dct):
    for a, b in dct.items():
        if len(dct) == 1:
            print("{} : {}".format(a, b), sep=' ', end='', flush=True)
        else:
            print("{} : {}, ".format(a, b), sep=' ', end='', flush=True)


asterbar = [
    "*     ",
    " *    ",
    "  *   ",
    "   *  ",
    "    * ",
    "     *",
    "    * ",
    "   *  ",
    "  *   ",
    " *    ",
]
