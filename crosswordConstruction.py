import pickle


def get_words(file):
    with open(file, "rb") as f:
        word_list = pickle.load(f)
    return word_list
