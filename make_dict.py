import json
import random
import string
import argparse
import pickle


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument("--size", type=int, required=True, help="Size of Dictionary")
    parser.add_argument("--name", type=str, required=True, help="Name of file")
    parser.add_argument("--seed", type=int, help="random seed")

    # Parse the arguments
    args = parser.parse_args()
    if args.seed:
        random.seed(args.seed)
    with open("words_dictionary.json", "r") as f:
        source_dict = json.load(f)
    source = sorted(list(source_dict))

    alphabet = list(string.ascii_lowercase)
    idx = {alphabet[i]: 0 for i in range(len(alphabet))}
    curr_letter = 0
    limits = {}
    a = 0
    b = 0
    for i in range(len(source)):
        b = i
        if source[i][0] != alphabet[curr_letter]:
            idx[alphabet[curr_letter]] = i
            limits[alphabet[curr_letter]] = b - a + 1
            curr_letter += 1
            a = b
    idx["z"] = len(source) - 1
    limits["z"] = idx["z"] - idx["y"]

    subset = []
    end = 0
    for i in range(len(alphabet)):
        start = end
        end = idx[alphabet[i]]
        try:
            subset += random.sample(source[start:end], args.size // 26)
        except ValueError:
            print("Even division of dictionary across letters not possible.")
            print(f"i = {i}")
            exit(1)

    with open(args.name + ".pickle", "wb") as file:
        pickle.dump(subset, file)


if __name__ == "__main__":
    main()
