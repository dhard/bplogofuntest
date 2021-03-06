from collections import Counter, defaultdict
from multiprocessing import Pool
import bisect
import itertools
import sys
import numpy as np
import bplogofuntest.nsb_entropy as nb
import random
import time
import math as mt
import exact

class InfoResults:
    def __init__(self):
        infoStates = defaultdict(lambda : defaultdict(lambda : defaultdict(float)))
        self.tripleinfodist = defaultdict(int)
        self.triplehieghtdist = defaultdict(int)

        self.bpinfodist = defaultdict(int)
        self.bpheightdist = defaultdict(int)

        self.singleinfodist = defaultdict(int)
        self.singleheightdist = defaultdict(int)

class Seq:
    def __init__(self, function, seq):
        self.function = function
        self.seq = seq

    def __len__(self):
        return len(self.seq)


class SeqStructure:
    def __init__(self, basepairs, basetriples = []):
        self.basepairs = basepairs
        self.basetriples = basetriples
        self.pos = 0
        self.sequences = []
        self.triples = set()
        self.pairs = set()
        self.singles = set()
        self.functions = Counter()

    def approx_expect(self, H, k, N):
        return H - ((k - 1)/((mt.log(4)) * N)) 

    def exact_run(self, n, p, numclasses):
        j = exact.calc_exact(n, p, numclasses)
        print("{:2} {:07.5f}".format(n, j[1]), file=sys.stderr)
        return j

    def permuted(self, items, pieces = 2): 
        sublists = [[] for i in range(pieces)]
        for x in items:
            sublists[random.randint(0, pieces - 1)].append(x)
        permutedList = []
        for i in range(pieces):
            time.sleep(0.01)
            random.seed()
            random.shuffle(sublists[i])
            permutedList.extend(sublists[i])
        return permutedList

    def permutations(self, numPerm, aa_classes):
        indices = []
        permStructList = []
        print("Generating permuted alignment data", file=sys.stderr)
        for p in range(numPerm):
            indices.append(self.permuted(aa_classes))
        for index in indices:
            permStruct = SeqStructure(self.basepairs, self.basetriples)
            for i, seqs in enumerate(self.sequences):
                permStruct.add_sequence(index[i], seqs.seq)
            permStructList.append(permStruct)
        return permStructList

    def permute(self, permute_num):
            with Pool(processes = 7) as pool:
                perm_jobs = []
                for x in range(7):
                    if (x == 0):
                        perm_jobs.append((permute_num//7+permute_num%7, self.get_functions()))
                    else:
                        perm_jobs.append((permute_num//7, self.get_functions()))

                perm_results = pool.starmap(self.permutations, perm_jobs)
                self.permutationList = []
                for x in perm_results:
                    self.permutationList += x

    def calculate_entropy(self, permute = 0, method = "NSB", overlap = False, exact = 0, corrections = ["fdr_bh"]):
        pass

    def weighted_dist(self, tripledata, bpdata, singledata):
        for x in tripledata[0]:
            self.tripleinfodist[x] += 1
        for x in tripledata[1]:
            self.triplehieghtdist[x] += 1

        for x in bpdata[0]:
            self.bpinfodist[x] += 1
        for x in bpdata[1]:
            self.bpheightdist[x] += 1

        for x in singledata[0]:
            self.singleinfodist[x] += 1
        for x in singledata[1]:
            self.singleheightdist[x] += 1

    def rtp(data, point, keys_sorted):
        if (point > 0):
            part = 0
            total = sum(data.values())
            i = bisect.bisect_left(keys_sorted, point)
            if (point <= keys_sorted[-1]):
                for y in keys_sorted[i:]:
                    part += data[y]
                return part / total
            else:
                return 0.0
        else:
            return 1.0

    def permInfo(self, perms, method, overlap, exact):
        tripleInfo = []
        tripleHeightInfo = []

        pairInfo = []
        pairHeightInfo = []

        singleInfo = []
        singleHeightInfo = []

        if (method == "Miller"):
            for permutation in perms:
                fg_entropy = 0
                for trips in permutation.basetriples:
                    for state in permutation.triples:
                        state_counts = permutation.get(trips, state)
                        total = sum(state_counts.values())
                        for x in state_counts.values():
                            fg_entropy -= (x/total)*mt.log(x/total, 2)

                        if (total <= exact):
                            info_result = self.exact_list[total-1] - fg_entropy
                        else:
                            info_result = self.approx_expect(self.bg_entropy, len(self.functions.keys()), total) - fg_entropy

                        if (info_result < 0):
                            info_result = 0

                        tripleInfo.append(info_result)
                        height_class = {}
                        for aa_class in state_counts.keys():
                            height_class[aa_class] = (state_counts[aa_class] / total) / (permutation.functions[aa_class] / self.fun_total)

                        for aa_height in height_class.values():
                            tripleHeightInfo.append((aa_height / sum(height_class.values())) * info_result)

                for pairs in permutation.basepairs:
                    for state in permutation.pairs:
                        state_counts = permutation.get(pairs, state)
                        total = sum(state_counts.values())
                        for x in state_counts.values():
                            fg_entropy -= (x/total)*mt.log(x/total, 2)

                        if (total <= exact):
                            info_result = self.exact_list[total-1] - fg_entropy
                        else:
                            info_result = self.approx_expect(self.bg_entropy, len(self.functions.keys()), total) - fg_entropy

                        if (info_result < 0):
                            info_result = 0

                        pairInfo.append(info_result)
                        height_class = {}
                        for aa_class in state_counts.keys():
                            height_class[aa_class] = (state_counts[aa_class] / total) / (permutation.functions[aa_class] / self.fun_total)

                        for aa_height in height_class.values():
                            pairHeightInfo.append((aa_height / sum(height_class.values())) * info_result)

                for singles in range(self.pos):
                    for state in permutation.singles:
                        state_counts = permutation.get([singles], state)
                        total = sum(state_counts.values())
                        for x in state_counts.values():
                            fg_entropy -= (x/total)*mt.log(x/total, 2)

                        if (total <= exact):
                            info_result = self.exact_list[total-1] - fg_entropy
                        else:
                            info_result = self.approx_expect(self.bg_entropy, len(self.functions.keys()), total) - fg_entropy

                        if (info_result < 0):
                            info_result = 0

                        singleInfo.append(info_result)
                        height_class = {}
                        for aa_class in state_counts.keys():
                            height_class[aa_class] = (state_counts[aa_class] / total) / (permutation.functions[aa_class] / self.fun_total)

                        for aa_height in height_class.values():
                            singleHeightInfo.append((aa_height / sum(height_class.values())) * info_result)

        return (tripleInfo, tripleHeightInfo, pairInfo, pairHeightInfo, singleInfo, singleHeightInfo)

    def is_overlap(self, position):
        pass

    def add_sequence(self, function, seq):
        self.sequences.append(Seq(function, seq))
        self.functions[function] += 1
        self.pos = len(seq)
        self.singles.update(seq)
        for x in self.basepairs:
            self.pairs.add(seq[x[0]] +  seq[x[1]])
        for x in self.basetriples:
            self.triples.add(seq[x[0]] + seq[x[1]] + seq[x[2]])

    def get(self, position, state):
        ret_counter = Counter()
        if (len(position) == 1):
            for x in self.sequences:
                if (x.seq[position[0]] == state[0]):
                    ret_counter[x.function] += 1
        if (len(position) == 2):
            for x in self.sequences:
                if (x.seq[position[0]] == state[0] and x.seq[position[1]] == state[1]):
                    ret_counter[x.function] += 1
        if (len(position) == 3):
            for x in self.sequences:
                if (x.seq[position[0]] == state[0] and x.seq[position[1]] == state[1] and x.seq[position[2]] == state[2]):
                    ret_counter[x.function] += 1

        return ret_counter

    def get_functions(self):
        function_list = []
        for key, val in self.functions.items():
            function_list.extend([key]*val)
        return function_list 

    def __len__(self):
        return len(self.sequences)
