import numpy as np
import pickle
import json
from crosswordConstruction import get_words
from crosswordConstruction import filter_words
from crosswordConstruction import insert_word
from numpy.random import default_rng
from copy import deepcopy
from tqdm import tqdm
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime


def objective(arr,wd,v=1,noise=None,rng=None): # TODO add noise
    """Calculate the crossword-iness of the array."""
    best_sol,best_score = None,np.NINF
    if rng is None:
        rng = default_rng()
    if not isinstance(arr,list):
        arr = [arr]
    for puzz in arr:
        if v == 1:
            score = get_words_and_letters_score(puzz,wd)
            if score > best_score:
                best_score = score
                best_sol = puzz
        elif v == 2:
            score = get_intersection_score(puzz,wd)
            if score > best_score:
                best_score = score
                best_sol = puzz
    return best_sol, best_score
            

def get_words_and_letters_score(arr,wd):
    """Gets words and letters score"""

    gene = find_contiguous_strings(arr,wd)
    ws = 0
    ls = 0
    seen = set()
    for w,(i,j), style in gene:
        if w not in wd:
            continue
        ws += 1
        if style == "h":
            for k in range(len(w)):
                if (i,j+k) not in seen:
                    seen.add((i,j+k))
                    ls += 1
        else:
            for k in range(len(w)):
                if (i+k,j) not in seen:
                    seen.add((i+k,j))
                    ls += 1
    return ws + ls/100 
    # get contiguous strings, count number 


def word_positions(word, position, direction):
    """ Returns the horizontal and vertical sets of points used in words"""
    row, col = position
    h_pos = set()
    v_pos = set() 
    if direction == "h":
        for i in range(len(word)):
            h_pos.add((row, col + i))
    elif direction == "v":
        for i in range(len(word)):
            v_pos.add((row + i, col))

    return h_pos, v_pos


def get_intersection_score(arr,wd):
    """Returns number of overlapping letters"""
    h_pos = set()
    v_pos = set()
    gene = find_contiguous_strings(arr,wd)
    for word, position, direction in gene:
        new_h_pos, new_v_pos = word_positions(word, position, direction)
        h_pos.update(new_h_pos)
        v_pos.update(new_v_pos)
    inter = h_pos & v_pos
    if inter:
      return len(inter)
    else:
      return 0

def sample_word(w_dict,rng):
    """sample word from word dictionary"""
    return rng.choice(list(w_dict.keys())).item()

def encode_word(word, array_size,rng):
    vert = rng.choice((True, False))
    pos1 = rng.integers(0,max(1,array_size-len(word)))
    pos2 = rng.integers(0,array_size)
    if vert:
        return (word,(pos1,pos2),"v")
    else:
        return (word,(pos2,pos1),"h")

def gen_solution(arr_copy,w_dict,rng,size=1,backwards_prob=0.05):
    """Generate a new neighboring solution by either inserting a new word or removing an existing word."""
    sols = []
    # gen forward or backward
    backwards = rng.uniform(size=size) <= backwards_prob
    for id, sol in enumerate(backwards):
        arr = deepcopy(arr_copy)
        if sol:
            # if backwards, find all contiguous strings and randomly remove one
            arr = remove_string(arr,rng)
        else:
            # if forwards, randomly sample from dictionary and randomly place
            new_word = sample_word(w_dict,rng)
           
            word,pos,dir = encode_word(new_word,len(arr),rng)
            arr = insert_word(arr,word,pos,dir)
        sols.append(arr)
    return sols


def remove_string(arr,rng):
    """removes a string"""
    string_locs = find_contiguous_strings(arr)
    if string_locs:
        w,(r,c),dir = string_locs[rng.integers(0,max(1,len(string_locs)))]
        for i in range(len(w)):
            if dir == "h":
                arr[r,c+i] = "%"
            elif dir == "v":
                arr[r+i,c] = "%"
    return arr


def find_contiguous_strings(arr,wd=None):
    """Does what it says on the can"""
    def get_strings(line,wd):
        strings = []
        current_string = ""
        
        for i,char in enumerate(line):
            if char == "%":
                if wd:
                    if current_string and current_string in wd:
                        strings.append((current_string,i-len(current_string)))
                else:
                    if current_string and len(current_string) > 1:
                        strings.append((current_string,i-len(current_string)))
                current_string = ""
            else:
                current_string += char
        if wd:
            if current_string and current_string in wd:
                strings.append((current_string,i-len(current_string)+1))
        else:
            if current_string and len(current_string) > 1:
                 strings.append((current_string,i-len(current_string)+1))
        return strings

    rows, cols = arr.shape
    contiguous_strings = []

    # Check rows
    for j,row in enumerate(range(rows)):
        res  = get_strings(arr[row, :],wd)
        if res:
            words, col = zip(*res)
            contiguous_strings.extend([(words[i],(j,col[i]),"h") for i in range(len(words))])

    # Check columns
    for k,col in enumerate(range(cols)):
        res = get_strings(arr[:, col],wd)
        if res:
            words, row = zip(*res)
            contiguous_strings.extend([(words[i],(row[i],k),"v") for i in range(len(words))])

    return contiguous_strings

def sim_anneal(arr,word_dict,num_iters, num_steps,init_temp, rng, obj_version=1,backwards_prob=0.05,threshold=None,beam_size=1,noise_eps=None,cool=True):
    """simulated annealing process"""
    # 1. recieve init Solution
    if threshold is None:
        thresh = np.NINF
    if init_temp > 1 and cool:
        t_range = np.arange(init_temp,0,-init_temp/(0.75*num_iters)).round(2)
        t_range = np.pad(t_range,(0,num_iters-len(t_range))) 
    else:
        t_range = [init_temp for i in range(num_iters)]  
    curr_sol= arr
    
    _, curr_score = objective(curr_sol,word_dict,v=obj_version,noise=noise_eps,rng=rng)
    scores_list = [curr_score]
    #loop
    for i in tqdm(range(num_iters)):
        for j in range(num_steps):
            # 2. Gen solution from neighborhood (variant: beam)
            sols = gen_solution(curr_sol,word_dict,rng,size=beam_size,backwards_prob=backwards_prob)
            # 3. Calc. heuristic value (variant: add noise)
            best_sol, best_score = objective(sols,word_dict,v=obj_version,noise=noise_eps,rng=rng)
            # 4. Randomly accept or reject based on temperature prob (variant: include threshold)
            best_delta = best_score - curr_score
            if best_delta >= 0 and best_delta >= thresh:
                curr_sol = best_sol
                curr_score = best_score
                scores_list.append(curr_score)
                continue
            elif t_range[i] == 0:
                scores_list.append(curr_score)
                continue
            elif rng.uniform() <= np.exp(-best_delta/t_range[i]):
                curr_sol = best_sol
                curr_score = best_score
                scores_list.append(curr_score)
                continue
        # 5. repeat until temp. changes
    # 6. repeat until temp. == 0
    return curr_sol, scores_list

def gen_init_puzzle(size,w_dict,rng):
    puzz = np.zeros((size,size),dtype="object")
    for i in range(size):
        for j in range(size):
            puzz[i,j] = "%"
    seed_word = sample_word(w_dict,rng)
    _, pos, dir = encode_word(seed_word,size,rng)
    puzz = insert_word(puzz,seed_word,pos,dir)
    return puzz


if __name__ == "__main__":

    

    grid_size = [5,7,10]
    num_iters = 10
    num_steps = [20,60]
    backwards_prob = 0.05
    init_temp = [0,15,30]
    min_word_length=2
    v=[1,2]
    run_results = {}
    cool = True
   
    for size in grid_size:
        wd = get_words("words_dictionary.json")
        wd = filter_words(wd, size, min_word_length)
        for num_step in num_steps:
            for temp in init_temp:
                for vers in v:
                    scores_list = []
                    for i in range(5):
                        rng = default_rng(i)
                                        
                        init_state = gen_init_puzzle(size,wd,rng)
                        #start = datetime.now()
                        out_state, scores = sim_anneal(init_state,wd,num_iters,num_step,temp,rng,obj_version=vers,cool=cool)
                        #end = datetime.now()
                        scores_list.append(scores)
                    run_results[(size,num_step,temp,vers)] = np.mean(scores_list,axis=0)

    out_file = "SA.pickle"
    with open(out_file,"wb") as file:
        pickle.dump(run_results,file)