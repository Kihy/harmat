"""
Attack Tree class
Author: hki34
"""
import networkx
from .node import *
from collections import OrderedDict

class AttackTree(networkx.DiGraph):
    """
    Attack Tree class
    Must specify the rootnode variable before use
    """
    def __init__(self, root=None):
        networkx.DiGraph.__init__(self)
        self.rootnode = root

        # Change this dictionary to have a custom calculation method
        # Try to use OrderedDict so that the calculation order is deterministic
        self.flowup_calc_dict = OrderedDict({
            'or': OrderedDict({
                'risk': max,
                'cost': min,
                'impact': max,
                'probability': max
            }),
            'and': OrderedDict({
                'risk': sum,
                'cost': sum,
                'impact': sum
            })
        })

    def __repr__(self):
        return self.__class__.__name__


    @property
    def values(self):
        return self.rootnode.values


    @property
    def is_vulnerable(self):
        for node in self.nodes():
            if isinstance(node, Vulnerability):
                return True
        return False


    def flowup(self, current_node=None):
        if current_node is None:
            current_node = self.rootnode
        if isinstance(current_node, Vulnerability):
            return current_node.values
        elif isinstance(current_node, LogicGate):
            children_nodes = list(self.neighbors(current_node))
            values = list(map(self.flowup, children_nodes))
            for metric, function in self.flowup_calc_dict[current_node.gatetype].items():
                current_node.values[metric] = function(value_dict[metric] for value_dict in values)
            return current_node.values
        else:
            raise TypeError("Weird type came in: {}".format(type(current_node)))


    def all_vulns(self):
        """
        Returns all Vulnerability objects in this Attack Tree

        Returns:
            A generator containing all vulnerabilities
        """
        return (vul for vul in self.nodes() if isinstance(vul, Vulnerability))

    def find_vul_by_name(self, name):
        for vul in self.all_vulns():
            if vul.name == name:
                return vul

    def patch_subtree(self, node):
        for child in self[node]:
            self.patch_subtree(child)
        self.remove_node(node)

    def patch_vul(self, vul, is_name=False):
        if is_name:
            vul = self.find_vul_by_name(vul.name)
        if vul in self.nodes():
            if list(self.pred[vul].keys())[0].gatetype == 'and': #delete whole predecessor tree if it is an AND gate
                self.patch_subtree(self.pred[vul])
            else:
                self.patch_subtree(vul)

    def at_add_node(self, node, logic_gate=None):
        """
        Add a vulnerability to a logic gate.
        If logic_gate is not specified, this will default to adding to the rootnode
        """
        if logic_gate is None:
            logic_gate = self.rootnode
        self.add_node(node)
        self.add_edge(logic_gate, node)

    def basic_at(self, vulns):
        """
        Creates a basic Attack tree which contains vulnerabilities in vulns like the following:

                root
                 |
                 OR
            -------------
            | | | | | | |
            v v v v v v v

        Args:
            vulns:  A list containing vulnerabilities/logic gate. Can be a single node.
        """
        if self.rootnode is None: #if rootnode hasn't been created yet
            lg = LogicGate("or")
            self.rootnode = lg
            self.add_node(lg)
        else:
            lg = self.rootnode #if rootnode already exists, just add nodes to that
        if not isinstance(vulns, list):
            vulns = [vulns]
        for vuln in vulns:
            self.at_add_node(vuln, lg)
