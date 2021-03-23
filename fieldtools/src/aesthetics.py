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
    print(tstyle.BOLD + tcolor(f' version {version}\n', tstyle.teal))


# Definitions

class tstyle:
    BOLD = '\033[1m'
    END = '\033[0m'
    purple = '673ab7'
    mustard = 'e8a200'
    blue = '3094c9'
    gridteal = '15524f'
    teal = '0b7878'  # conda dea'006666'
    orangelogo = 'cc8431'
    orange = 'fca035'


arrow = tstyle.BOLD + tcolor('> ', tstyle.teal)
info = tstyle.BOLD + tcolor('i ', tstyle.teal)


menu_aes = style_from_dict({
    Token.QuestionMark: f'#{tstyle.teal} bold',
    Token.Selected: f'#{tstyle.mustard}',  # default
    Token.Pointer: f'#{tstyle.teal} bold',
    Token.Instruction: '#a1a1a1',  # default
    Token.Answer: '#f44336 bold',
    Token.Question: f'#{tstyle.mustard} bold',
})
