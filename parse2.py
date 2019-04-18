from parsimonious.grammar import Grammar
from parsimonious.nodes import NodeVisitor

import pprint
# pp = pprint.PrettyPrinter(indent=4)
pp = pprint.PrettyPrinter(indent=4, width=120, compact=True)

# grammer for NWB Query Engine tools, used by search_nwb2 and nwbindexer
# Parser implemented using parsimonious, https://pypi.org/project/parsimonious/

grammar = Grammar(
    r"""
    query       = ws subquery ( ws andor ws subquery ws )*
    subquery    = (local_sq / parnsq)
    local_sq    = parent ws colon ws display_list* expression?
    parnsq      = lparn query rparn 
    parent      = ~r"[\w/]+"
    colon       = ":"
    display_list = disp_child ws "," ws
    expression  = ws child_compare ws (andor ws child_compare ws )*
    child_compare = ( pair_compare  / parnexp )
    pair_compare = child ws relop ws ( number / string)
    parnexp = lparn expression rparn
    relop       = ("==" / "<=" / "<" / ">=" / ">" / "!=" / "LIKE")
    child       = ~r"[\w]+"
    disp_child  = ~r"[\w]+"
    string      = ~r'"[^"]*"'
    number      = ~r"[0-9]+(\.[0-9]+)?"
    andor       = ("&" / "|")
    lparn       = "("
    rparn       = ")"
    ws          = ~"\s*"
    """
)

def get_subqueries(qi):
    # return list of subqueries from query information (qi)
    sqlist = []
    for ploc in qi['plocs']:
        sqlist.append(qi['tokens'][ploc['range'][0]: ploc['range'][1]])
    return sqlist


class IniVisitor(NodeVisitor):
    tokens = []
    token_types = []
    plocs = []
    current_ploc = None
    location_map = {}   # map original location (character position in query) to index in tokens
    # Will have: {'cloc_index': [], 'display_clocs': []}
    # will have {'path': '/x/y/z', cloc_index: [1, 4, 5], display_clocs: ['name1', 'name2', ... ]}

    def __init__(self):
        self.tokens = []
        self.ttypes = []  # token types
        self.plocs = []
        self.current_ploc = None
        self.location_map = {}

    def get_query_info(self):
        # return query information
        # tokens - tokens that can be used in query with parent locations and display locations removed
        # ttypes - type of each token in tokens
        # plocs - has information about each parent location.  Each item is dictionary:
        #    'path' - specified path of parent
        #    'cloc_index' - index (in tokens) of child locations specified in subquery
        #    'display_clocs' - list of child locations to display (comma seperated list after parent:)
        #    'range' - tuple, (start, end) - index of tokens that are in subquery
# Example, query:
# (ploc1: p,q, r, (a >= 22 & b LIKE "sue") | (ploc2: t, m <= 14 & ploc3: x < 23))
# qi= {
#    'plocs': [   {'cloc_index': [2, 6], 'display_clocs': ['p', 'q', 'r'], 'path': 'ploc1', 'range': (1, 10)},
#                  {'cloc_index': [12], 'display_clocs': ['t'], 'path': 'ploc2', 'range': (12, 15)},
#                  {'cloc_index': [16], 'display_clocs': [], 'path': 'ploc3', 'range': (16, 19)}],
#     'tokens': [   '(', '(', 'a', '>=', '22', '&', 'b', 'LIKE', '"sue"', ')', '|', '(', 'm', '<=', '14', '&', 'x', '<',
#                   '23', ')', ')'],
#     'ttypes': [   '(', '(', 'CLOC', 'ROP', 'NC', 'AOR', 'CLOC', 'ROP', 'SC', ')', 'AOR', '(', 'CLOC', 'ROP', 'NC',
#                   'AOR', 'CLOC', 'ROP', 'NC', ')', ')']}
        qi = {"tokens": self.tokens, "ttypes": self.ttypes, "plocs": self.plocs, }
        return qi

    def visit_relop(self, node, visited_children):
        # relop - relational operator
        self.tokens.append(node.text)
        self.ttypes.append("ROP")
        return visited_children or node

    def visit_display_list(self, node, visited_children):
        # display_list - list of disp_child locations to display
        self.current_ploc['display_clocs'].append(visited_children[0].text)
        return visited_children or node      

    def visit_string(self, node, visited_children):
        # string constant
        self.location_map[node.start] = len(self.tokens)
        self.tokens.append(node.text)
        self.ttypes.append("SC")
        return visited_children or node

    def visit_lparn(self, node, visited_children):
        # left parentheses
        self.location_map[node.start] = len(self.tokens)
        self.tokens.append(node.text)
        self.ttypes.append(node.text)
        return visited_children or node

    def visit_rparn(self, node, visited_children):
        # right parentheses
        self.location_map[node.start] = len(self.tokens)
        self.tokens.append(node.text)
        self.ttypes.append(node.text)
        return visited_children or node

    def visit_andor(self, node, visited_children):
        # & or |  (AND or OR)
        self.tokens.append(node.text)
        self.ttypes.append("AOR")
        return visited_children or node

    def visit_number(self, node, visited_children):
        # numeric constant
        self.location_map[node.start] = len(self.tokens)
        self.ttypes.append("NC")
        self.tokens.append(node.text)
        return visited_children or node

    def visit_ws(self, node, visited_children):
        # white space
        # save end position in location map because that might be looked up
        self.location_map[node.end] = len(self.tokens)
        return visited_children or node

    def visit_child(self, node, visited_children):
        # child location that is in an expression
        self.location_map[node.start] = len(self.tokens)
        self.current_ploc['cloc_index'].append(len(self.tokens))
        self.tokens.append(node.text)
        self.ttypes.append("CLOC")
        return visited_children or node

    def visit_parent(self, node, visited_children):
        # parent location
        self.location_map[node.start] = len(self.tokens)
        if self.current_ploc:
            self.plocs.append(self.current_ploc)
        self.current_ploc = {'path': node.text, 'cloc_index': [], 'display_clocs': []}
        # self.tokens.append(node.text)
        return visited_children or node

    def visit_local_sq(self, node, visited_children):
        # local subquery
        assert node.start in self.location_map, (
            "did not find node.start (%i) in location_map: %s, end=%i, text='%s', tokens=%s") % (
            node.start, self.location_map, node.end, node.text, self.tokens)
        assert node.end in self.location_map, (
            "did not find node.end (%i) in location_map: %s, start=%i, text='%s', tokens=%s") % (
            node.end, self.location_map, node.start, node.text, self.tokens)
        self.current_ploc['range'] = (self.location_map[node.start], self.location_map[node.end])
        # self.tokens.append(node.text)
        return visited_children or node

    def visit_query(self, node, visited_children):
        # top level query.  Save current_ploc if present and clear variable to start a new one
        if self.current_ploc:
            self.plocs.append(self.current_ploc)
            self.current_ploc = None
        return visited_children or node

    def generic_visit(self, node, visited_children):
        """ The generic visit method. """
        return visited_children or node

def parse(query):
    # parse a query, return qi - query info dictionary
    tree = grammar.parse(query)
    iv = IniVisitor()
    output = iv.visit(tree)  # output not used
    qi = iv.get_query_info()
    return qi

def run_tests():
    test_queries = [
        # "p1:(a > 1 & p2: x>y)",  # fails
        "(ploc1: p,q, r, (a >= 22 & b LIKE \"sue\") | (ploc2: t, m <= 14 & ploc3: x < 23))",
        "(ploc1: (a > 22 & b LIKE \"sue\") | (ploc2: m < 14 & ploc3: x < 23 & y < 10))",
        "ploc: p, r, cloc > 23",
        # "ploc: cloc1,",
        # "ploc: cloc LIKE \"Sue Smith\"",
        # "ploc1: cloc > 23 & ploc2: cloc2, cloc3 > 25",
        # "ploc1: a > 22",
        # "ploc1: (a > 22)",
        # "ploc1: (a > 22 & b < 14)",
        # "ploc1: (a > 22 & b LIKE \"sue\")",
        # "ploc1: (a > 22 | b LIKE \"sue\")",
        # "ploc1: (a > 22 & b LIKE \"sue\" | m < 14)",
        # "ploc1: (a > 22 & b LIKE \"sue\") | m < 14",
        # "ploc1: a > 22 & (b LIKE \"sue\" | m < 14)",
        # "ploc1: (a > 22 & b LIKE \"sue\") | ploc2: m < 14",
        # "(ploc1: (a > 22 & b LIKE \"sue\") | ploc2: m < 14) & ploc3: x < 23",
        ]

    for query in test_queries:
        print("\nparsing: %s" % query)
        qi = parse(query)
        sqlist =  get_subqueries(qi)
        print ("qi=\n")
        pp.pprint(qi)
        print ("subqueries=")
        pp.pprint(sqlist)

if __name__ == "__main__":
    run_tests()