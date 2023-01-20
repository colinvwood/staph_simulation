import pytest

from analysis.Tree import Tree
from analysis.Population import Population
from analysis.Genome import Genome


class TestTree:
  tree = Tree()

  @pytest.fixture
  def source_pop(self):
    genomes = [
      Genome([1,2,3,4,8]), # clone
      Genome([1,2,3,4,5]),
      Genome([1,3]),
    ]
    return Population.from_genomes(genomes, 10)

  @pytest.fixture
  def recipient_pop(self):
    genomes = [
      Genome([1,2,3,7]), # clone
      Genome([1,2,3,4,5]),
      Genome([1,2,4]),
    ]
    return Population.from_genomes(genomes, 10)
  
  @pytest.fixture
  def branches(self, source_pop, recipient_pop):
    src_genome = source_pop.population[0]
    rec_genome = recipient_pop.population[0]
    branches = self.tree.categorize_mutations(src_genome, rec_genome)
    return branches
  
  @pytest.fixture
  def proportion_branches(self, branches, source_pop, recipient_pop):
    return self.tree.assign_proportions(branches, source_pop, recipient_pop) 
     
  def test_categorize_mutations(self, branches):
    shared_branch, source_branch, recipient_branch = branches.values()
    assert list(shared_branch.keys()) == [1,2,3]
    assert list(source_branch.keys()) == [4,8]
    assert list(recipient_branch.keys()) == [7]

  def test_assign_proportions(self, proportion_branches):
    shared_proportions, source_proportions, recipient_proportions = \
      proportion_branches.values()
    
    assert list(shared_proportions.keys()) == [1,2,3]
    assert list(source_proportions.keys()) == [4,8]
    assert list(recipient_proportions.keys()) == [7]
    assert shared_proportions[1]["source_proportion"] == 1
    
  def test_count_segregating_snps(self):
    src_genomes = [
      Genome([1,2,3,4,5,7]), # clone
      Genome([1,2,4,5]),
      Genome([1,2,3,8]),
    ]
    source_pop = Population.from_genomes(src_genomes, 10)
  
    rec_genomes = [
      Genome([1,2,3,4,6,9]), # clone
      Genome([1,2,3,4,5]),
      Genome([1,2,4]),
    ]
    recipient_pop = Population.from_genomes(rec_genomes, 10)

    tree = Tree.initialized(src_genomes[0], rec_genomes[0], source_pop, 
                            recipient_pop)

    shared_src_segs = tree.count_segregating_snps("source", tree.shared_branch)
    assert shared_src_segs == 2 # [3,4]
    shared_rec_segs = tree.count_segregating_snps("recipient", 
                                                  tree.shared_branch)
    assert shared_rec_segs == 1 # [3]

  def test_check_tier_1(self):
    shared_branch = {
      1: {
        "source_proportion": 0.5,
        "recipient_proportion": 1, 
      },
      2: {
        "source_proportion": 1,
        "recipient_proportion": 1, 
      },
      3: {
        "source_proportion": 0.3,
        "recipient_proportion": 0.9, 
      },
    }
    assert self.tree.check_tier_1(shared_branch) == 1

    shared_branch[1]["source_proportion"] = 1
    assert self.tree.check_tier_1(shared_branch) == 0

    shared_branch = {}
    assert self.tree.check_tier_1(shared_branch) == 0
  
  def test_check_tier_2(self):
    source_branch = {
      1: {
        "source_proportion": 0.5,
        "recipient_proportion": 1, 
      },
      2: {
        "source_proportion": 1,
        "recipient_proportion": 1, 
      },
      3: {
        "source_proportion": 0.8,
        "recipient_proportion": 1, 
      },
    }
    recipient_branch = {
      1: {
        "source_proportion": 0.5,
        "recipient_proportion": 1, 
      },
      2: {
        "source_proportion": 1,
        "recipient_proportion": 1, 
      },
      3: {
        "source_proportion": 1,
        "recipient_proportion": 0.9, 
      },
    }
    assert self.tree.check_tier_2(source_branch, recipient_branch) == 1

    recipient_branch[1]["source_proportion"] = 1
    assert self.tree.check_tier_2(source_branch, recipient_branch) == 0

    recipient_branch[1]["source_proportion"] = 0.5
    source_branch[1]["recipient_proportion"] = 0.9
    assert self.tree.check_tier_2(source_branch, recipient_branch) == 0

    assert self.tree.check_tier_2({}, {}) == 0

  def test_bin_proportions(self):
    assert self.tree.bin_proportions([], num_bins=1) == []
    assert self.tree.bin_proportions([1], num_bins=1) == [1]
    assert self.tree.bin_proportions([1,1], num_bins=2) == [0,2]
    assert self.tree.bin_proportions([1,1], num_bins=1) == [2]
    # assert self.tree.bin_proportions([1, 0, 1], num_bins=2) == [1, 2]

    proportions = [1, 0.4, 0.8, 1]
    binned_proportions = self.tree.bin_proportions(proportions, num_bins=10)
    assert binned_proportions == [0, 0, 0, 1, 0, 0, 0, 1, 0, 2]

  def test_psuedo_entropy(self):
    assert self.tree.psuedo_entropy([]) == 0
    assert self.tree.psuedo_entropy([1]) == 0
    assert self.tree.psuedo_entropy([30]) == 0
    assert self.tree.psuedo_entropy([0, 1]) == 0
    assert self.tree.psuedo_entropy([0, 99]) == 0
    assert self.tree.psuedo_entropy([1, 1]) == 1

    source_props_binned = [0, 0, 1, 3, 3]
    recipient_props_binned = [0, 0, 0, 0, 7]
    source_entropy = self.tree.psuedo_entropy(source_props_binned)
    recipient_entropy = self.tree.psuedo_entropy(recipient_props_binned)
    assert source_entropy > recipient_entropy

    source_entropy = self.tree.psuedo_entropy([1, 1, 0, 0, 0])
    recipient_entropy = self.tree.psuedo_entropy([1, 0, 0, 0, 1])
    assert source_entropy == recipient_entropy

    # important to understand the phylogenetic implications of this one 
    source_entropy = self.tree.psuedo_entropy([3, 1, 0, 0])
    recipient_entropy = self.tree.psuedo_entropy([2, 2, 0, 0])
    assert source_entropy < recipient_entropy
  
  def test_compare_clumpiness(self):
    assert self.tree.compare_clumpiness({}, num_bins=10) == 0

    branch = {
      1: {
        "source_proportion": 1,
        "recipient_proportion": 1, 
      },
      2: {
        "source_proportion": 0.8,
        "recipient_proportion": 1, 
      },
      3: {
        "source_proportion": 0.7,
        "recipient_proportion": 0.9, 
      },
    }
    assert self.tree.compare_clumpiness(branch, num_bins=10) == 1
    assert self.tree.compare_clumpiness(branch, num_bins=4) == 1
    assert self.tree.compare_clumpiness(branch, num_bins=3) == 0

    branch = {
      1: {
        "source_proportion": 1,
        "recipient_proportion": 1,
      },
      2: {
        "source_proportion": 1,
        "recipient_proportion": 1,
      },
    }
    assert self.tree.compare_clumpiness(branch, num_bins=10) == 0

    branch[2]["recipient_proportion"] == 0.8
    assert self.tree.compare_clumpiness(branch, num_bins=10) == 0