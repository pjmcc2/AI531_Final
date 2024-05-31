# Properties I want
# 1. Cells Can "see" their entire row
# 2. Cells can "see" their entire column
# 3. Cells use their knowledge to check against the dictionary
# 4. Cells should be easily accessible (indexed?)

from cell import Cell

class Grid():
    def __init__(self,size) -> None:
        self.size = size
        self.root = Cell(None,None,pos=0)
        
        def gen_row(self,curr):
            for i in range(1,self.size):
                if curr.right is None:
                    temp = Cell(None,None,pos=curr.pos + 1)
                    curr.right = temp
                    curr = temp

        


    def set_word(self,word) -> None:
        
        
