import math


class Tree:
    def __init__(self):
        self.source_genome = None
        self.recipient_genome = None
        self.source_population = None
        self.recipient_population = None
        self.shared_branch = {}
        self.source_branch = {}
        self.recipient_branch = {}

    @classmethod
    def initialized(
        cls,
        source_genome,
        recipient_genome,
        source_population,
        recipient_population
    ):
        obj = cls()
        obj.source_genome = source_genome
        obj.recipient_genome = recipient_genome
        obj.source_population = source_population
        obj.recipient_population = recipient_population

        # branches:
        # {
        #     mutation: {
        #        source_proportion: _
        #        recipient_proportion: _
        #     },
        # }
        obj.categorize_mutations()
        obj.assign_proportions()

        return obj

    def categorize_mutations(self):
        for mutation in self.source_genome.mutations:
            if mutation in self.recipient_genome.mutations:
                self.shared_branch[mutation] = {}
            else:
                self.source_branch[mutation] = {}

        for mutation in self.recipient_genome.mutations:
            if mutation not in self.source_genome.mutations:
                self.recipient_branch[mutation] = {}

    def assign_proportions(self):
        for branch in (
            self.shared_branch, self.source_branch, self.recipient_branch
        ):
            for mutation in branch:
                if mutation in (
                    src_snps := self.source_population.sample_snps
                ):
                    branch[mutation]["source_proportion"] = \
                        src_snps[mutation]["proportion"]
                else:
                    branch[mutation]["source_proportion"] = 0

                if mutation in (
                    rec_snps := self.recipient_population.sample_snps
                ):
                    branch[mutation]["recipient_proportion"] = \
                        rec_snps[mutation]["proportion"]
                else:
                    branch[mutation]["recipient_proportion"] = 0

    def count_segregating_snps(self, population, branch):
        segs = 0
        for mutation in branch:
            proportion = branch[mutation][population + "_proportion"]
            if proportion < 1 and proportion > 0:
                segs += 1

        return segs

    def check_tier_1(self):
        src_segregating = self.count_segregating_snps(
            "source", self.shared_branch
        )
        rec_segregating = \
            self.count_segregating_snps("recipient", self.shared_branch)

        return {
            "source segregating": src_segregating,
            "recipient segregating": rec_segregating
        }

    def check_tier_2(self):
        src_on_rec = \
            self.count_segregating_snps("source", self.recipient_branch)
        rec_on_src = \
            self.count_segregating_snps("recipient", self.source_branch)

        return {
            "source segregating on recipient": src_on_rec,
            "recipient segregating on source": rec_on_src
        }

    def check_clumpiness_composite(self, num_bins):
        ancestral_to_source = self.shared_branch | self.source_branch
        ancestral_to_recipient = self.shared_branch | self.recipient_branch
        a_to_s_source_entropy, a_to_s_recipient_entropy = \
            self.check_clumpiness(ancestral_to_source, num_bins).values()
        a_to_r_source_entropy, a_to_r_recipient_entropy = \
            self.check_clumpiness(ancestral_to_recipient, num_bins).values()

        return {
            "ancestral to source lineage": {
                "source": a_to_s_source_entropy,
                "recipient": a_to_s_recipient_entropy
            },
            "ancestral to recipient lineage": {
                "source": a_to_r_source_entropy,
                "recipient": a_to_r_recipient_entropy
            }
        }

    def check_clumpiness(self, branch, num_bins):
        source_proportions = [v["source_proportion"] for v in branch.values()]
        source_proportions_binned = \
            self.bin_proportions(source_proportions, num_bins)
        recipient_proportions = [
            v["recipient_proportion"] for v in branch.values()
        ]
        recipient_proportions_binned = \
            self.bin_proportions(recipient_proportions, num_bins)

        source_entropy = self.standard_entropy(source_proportions_binned)
        recipient_entropy = self.standard_entropy(recipient_proportions_binned)

        return {
            "source entropy": source_entropy,
            "recipient entropy": recipient_entropy
        }

    def bin_proportions(self, proportions, num_bins):
        # note: having a bin number greater than the sample size is pointless
        # because proportions can only vary in increments as small as
        # 1 / sample size
        if not proportions or not num_bins:
            return []

        import math
        bin_size = 1 / num_bins

        # bins: [ [a, b], (b, c], (c, d], ... ]
        # note that lowest bin is double inclusive to include 0
        proportions_by_bin_index = []
        for proportion in proportions:
            if proportion == 0:
                proportions_by_bin_index.append(0)
            else:
                index = math.ceil(proportion / bin_size) - 1
                proportions_by_bin_index.append(index)

        return [proportions_by_bin_index.count(bin) for bin in range(num_bins)]

    def standard_entropy(self, binned_proportions):
        if len(binned_proportions) <= 1 or sum(binned_proportions) == 1:
            return 0

        props = [p / sum(binned_proportions) for p in binned_proportions]
        return sum([p * math.log(p) if p > 0 else 0 for p in props]) * -1
