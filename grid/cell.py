
class Cell():
    def __init__(self, left, right, top, bot, val=None,pos=None) -> None:
        self.left = left
        self.right = right
        self.top = top
        self.bot = bot
        self.val = val
        self.pos = pos

    def get_row_word(self):
        if self.right:
            prev_letters = self.right.get_row_word()
        else: 
            prev_letters = ""
        return self.val + prev_letters
    
    def get_col_word(self):
        
