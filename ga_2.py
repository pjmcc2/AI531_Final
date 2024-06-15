import pickle
import numpy as np
from operator import itemgetter
import string
import json
from numpy.random import default_rng
import matplotlib.pyplot as plt
from tqdm import tqdm

def get_words(file):
    with open(file, "rb") as f:
        word_list = json.load(f)
    return word_list


def filter_words(words, length):
    return {w:1 for w in words.keys() if (len(w) <= length) and (len(w) > 2)}


def insert_word(array, word, position, direction):
    row, col = position
    word_length = len(word)

    if direction == "h":
        if col + word_length > len(array):
            raise ValueError("Word exceeds array bounds horizontally")
        array[row, col : col + word_length] = list(word)
    elif direction == "v":
        if row + word_length > len(array):
            raise ValueError("Word exceeds array bounds vertically")
        array[row : row + word_length, col] = list(word)
    else:
        raise ValueError("Direction must be 'horizontal' or 'vertical'")

    return array


 
def encode_list(char_string, word_dict):
    n = len(char_string)
    strings = {}

    # Step 1: Identify all substrings that are in the word dictionary
    for i in range(n):
        for j in range(i + 1, n + 1):
            substring = char_string[i:j]
            substring = "".join(substring)
            if substring in word_dict:
                strings[substring] = (i, j)

    # Step 2: Sort the substrings by their length in descending order
    sorted_strings = sorted(strings.items(), key=lambda x: len(x[0]), reverse=True)

    # Step 3: Select non-overlapping and non-adjacent valid words
    valid_words = []
    used_indices = set()

    for word, (start, end) in sorted_strings:
        # Check if the word overlaps or is adjacent to any already selected words
        if all(index not in used_indices for index in range(start, end)) and \
           all(index - 1 not in used_indices and index + 1 not in used_indices for index in range(start, end)):
            valid_words.append((word, (start, end)))
            used_indices.update(range(start, end))

    return valid_words


def encode(arr,word_dict,fs):
    encoding = []
    for i,r in enumerate(arr):
        temp = encode_list(r, word_dict)
        for w,(start,end) in temp:
            s = {(i,start+j) for j in range(len(w))}
            if s <= fs:
                encoding.append((w,(i,start),'h',True))
            else:
                encoding.append((w,(i,start),'h', False))
    for j,c in enumerate(arr.T):
        temp = encode_list(c, word_dict)
        for w,(start,end) in temp:
            s = {(start+k,j) for k in range(len(w))}
            if s <= fs:
                encoding.append((w,(start,j),'v',True))
            else:
                encoding.append((w,(start,j),'v',False))

    return validate_words(arr,encoding)
    
def score_gene(gene):


    ws = 0
    ls = 0
    seen = set()
    for w,(i,j), style,_ in gene:
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
    return ws, ls

# Crossover selects randomly  (without repetition) real words from array 1 and array 2: a sample is considered
# Viable if there the corresponding location on the other array does not contain any valid words
# If no viable words are found, a random inviable word is selected.
# The new arrays are generated by overwriting whatever is at the other array's word location
def crossover(arr1, arr2,fs1,fs2):
    for i in range(len(arr1)):
        for j in range(len(arr1)):
            t1 = arr1[i,j]
            t2 = arr2[i,j]
            if (i,j) not in fs2:
                arr2[i,j] = t1
            if (i,j) not in fs1:
                arr1[i,j] = t2

    return arr1,arr2


def word_positions(word, position, direction):
    row, col = position
    positions = set()

    if direction == "h":
        for i in range(len(word)):
            positions.add((row, col + i))
    elif direction == "v":
        for i in range(len(word)):
            positions.add((row + i, col))

    return positions


def check_conflict(genes, new_gene):

    new_word, new_position, new_direction,_ = new_gene
    new_positions = word_positions(new_word, new_position, new_direction)

    for word, position, direction,_ in genes:
        existing_positions = word_positions(word, position, direction)
        union = new_positions & existing_positions
        if union:
            return True

    return False


# With probability M mutation occurs. mutation is performed in 3 ways, with probability p and (1-p) The primary way, with probability p assigns all
# blank cells a random letter. This encourages small (2-3) letter words to form which are common in crosswords and will increase the number of real words.
# With probablity (1-p)/2, an entirely new word will be sampled from the lexicon and randomly placed. And with prob: (1-p)/2 both previous ways happen sequentially
def mutate(array,p, seed=None,rng=None):
    weights = [1/10,1/42,1/42,1/42,1/10,1/42,1/42,1/42,1/10,1/42,1/42,1/42,1/42,1/42,1/10,1/42,1/42,1/42,1/42,1/42,1/10,1/42,1/42,1/42,1/42,1/42]
 
    if rng is None:
        rng = default_rng(seed)
    sample = rng.uniform()
    if sample > p:
        return array
    for i in range(len(array)):
        for j in range(len(array)):
            if array[i,j] not in string.ascii_lowercase:
                array[i,j] = rng.choice(list(string.ascii_lowercase),1,p=weights).item()
    return array
def reconstruct(gene,size):
    new_arr = np.zeros((size,size),dtype="object")
    for i in range(len(new_arr)):
        for j in range(len(new_arr)):
            new_arr[i,j] = "%"
    for w,pos,style,_ in gene:
        new_arr = insert_word(new_arr,w,pos,style)
    return new_arr

def saturate(array,rng):

    letters = list(string.ascii_lowercase)
    for i in range(len(array)):
        for j in range(len(array)):
            if array[(i,j)] == "%":
                array[(i,j)] = rng.choice(letters,1).item()
    return array


def evolve(pop, p, word_dict, num_gens, arr_size, rng):
    scores = []
    for i in range(num_gens):
        
        pop.sort(key=itemgetter(2,3),reverse=True)
        scores.append((pop[0][2],pop[0][3])) # best score for this generation
        offspring = []
        child_genes = []
        for j in range(0, len(pop), 2):
            parent1 = reconstruct(pop[j][0], arr_size)
            parent2 = reconstruct(pop[j + 1][0],arr_size)
            child1, child2 = crossover(parent1, parent2,pop[j][1],pop[j + 1][1])
            offspring.append((child1,pop[j][1]))
            offspring.append((child2,pop[j+1][1]))
        if i != num_gens-1:
            for c,fs in offspring:
                c = mutate(c,p,rng)
                child_genes.append(encode(c,word_dict,fs))
        if i == num_gens -1:
            for o,fs in offspring:
                child_genes.append(encode(o,word_dict,fs))
        pop = [(g[0],g[1],*score_gene(g[0])) for g in child_genes]
    return pop, scores

def gen_pop(word_dict, pop_size, crossword_size, seed=None,rng=None):
    if rng is None: 
        rng = default_rng(seed)
    pop = [np.zeros((crossword_size,crossword_size),dtype="object") for i in range(pop_size)]
    for ar in pop:
        for i in range(len(ar)):
            for j in range(len(ar)):
                ar[i,j] = "%"
    
        word = rng.choice(list(word_dict.keys()))
        direction = rng.choice(["h","v"])
        pos1 = rng.integers(0,max(1,crossword_size-len(word)))
        pos2 = rng.integers(0,crossword_size)
        if direction == "h":
            pos = (pos2,pos1)
        else:
            pos = (pos1,pos2)
        ar = insert_word(ar,word,pos,direction)
    return pop


def validate_words(arr,genes):
    n = len(arr)
    out_genes = []
    fixed_cells = set()
    for gene in genes:
        word, (row, col), direction, fixed = gene
        if fixed:
            for k in range(len(word)):
                if direction == 'h':
                    fixed_cells.add((row, col+k))
                else:
                    fixed_cells.add((row+k, col))
    for gene in genes:
        word, (row, col), direction, fixed = gene
        if fixed:
            out_genes.append(gene)
            continue
        for i in range(len(word)):
            if direction == 'h':
                if col + len(word) < n: # if extra room in row, it must be empty (otherwise it would have been in this word)
                    if arr[row, col + len(word)] != "%":
                        out_genes.append(gene)
                        break
                if col -1 >= 0: # check behind 
                    if arr[row, col - 1] != "%":
                        out_genes.append(gene)
                        break
                if row +1 < n: # check  below
                    if arr[row + 1, col+i] != "%":
                        if (row + 1,col+i) not in fixed_cells:
                            out_genes.append(gene)
                            break
                if row -1 >= 0: #check above
                    if arr[row - 1, col+i] != "%":
                        if (row - 1,col+i) not in fixed_cells:
                            out_genes.append(gene)
                            break
                if i == len(word) - 1:
                    out_genes.append((word,(row,col),direction,True))
            elif direction == 'v':
                if row + len(word) < n: # check below
                    if arr[row + len(word), col] != "%":
                        out_genes.append(gene)
                        break
                if row -1 >= 0: # check above
                    if arr[row -1, col] != "%":
                        out_genes.append(gene)
                        break
                if col + 1 < n: # check right
                        if arr[row+i, col + 1] != "%":
                            if (row+i,col + 1) not in fixed_cells:
                                out_genes.append(gene)
                                break
                if col -1 >= 0: # check left
                        if arr[row+i, col - 1] != "%":
                            if (row+i,col - 1) not in fixed_cells:
                                out_genes.append(gene)
                                break
                if i == len(word) - 1:
                    out_genes.append((word,(row,col),direction,True))
    for gene in out_genes:
        word, (row, col), direction, fixed = gene
        if fixed:
            for k in range(len(word)):
                if direction == 'h':
                    fixed_cells.add((row, col+k))
                else:
                    fixed_cells.add((row+k, col))
    return out_genes, fixed_cells







pop_sizes = [20,60]
mutation_rates = [0,0.5,1]
grid_sizes = [5,7,10]
num_runs = 1
num_gens = 10
# 5 runs

run_results = {}
for grid_size in grid_sizes:
    unfiltered_wd = get_words(r"words_dictionary.json")
    wd = filter_words(unfiltered_wd,grid_size)
    for rate in mutation_rates:
        for pop_size in pop_sizes:
            for i in tqdm(range(num_runs)):
                word_scores = []
                letter_scores = []
                for j in range(num_runs):
                    rng = default_rng(j)
                    #initial pop
                    pop_arrays = gen_pop(wd,pop_size,grid_size,rng)
                    genes_and_fixed_sets = [encode(p,wd,set()) for p in pop_arrays]
                    pop = [(g[0],g[1],*score_gene(g[0])) for g in genes_and_fixed_sets]
                    #evolve
                    pop,scores = evolve(pop,rate,wd,num_gens,grid_size,rng)
                    word_scores.append([s[0] for s in scores])
                    letter_scores.append([s[1] for s in scores])
                #results
                x = np.arange(20)
                avg_ws = np.mean(np.array(word_scores),axis=0)
                avg_ls = np.mean(np.array(letter_scores),axis=0)

                run_results[(pop_size,rate,grid_size)] = (avg_ws,avg_ls)
print(reconstruct(pop[0][0],5))

out_file = "GA_2_no_2_letter.pickle"
with open(out_file,"wb") as file:
    pickle.dump(run_results,file)