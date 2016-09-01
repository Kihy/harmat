import webbrowser
from harmat import *
#import matplotlib.pyplot as plt
import xml.etree.cElementTree as ET
import flask

app = flask.Flask(__name__)


LINKS = "links"
LINK = "link"
SOURCE = "source"
TARGET = "target"
NAME = "name"
HOST = "host"
HARM = "harm"
VALUE = "value"
ID = "id"
TREENODE = "treenode"
CHILDREN = "children"
CENTRALITY = "centrality"
id_counter = 123

def visualise(h, filename=None, mode="show"):
    """
    Visualize the layer using matplotlib
    Args:
        filename: specify the directory/filename of the resulting PNG file

        mode: choose between 'show', and 'save'. When 'save' is chosen the filename must be specified
    """
    plt.clf()
    to_draw = h
    if type(h) == Harm:
        to_draw = h.top_layer
    networkx.draw(to_draw, pos=networkx.spring_layout(to_draw), arrows=True, with_labels=True)

    if mode == "save":
        if filename is None:
            raise Exception("visualise filename not specified")
        plt.savefig(filename)
    else:
        plt.show()

def xmlify_tree(at, top, node=None):
    """
    Convert the attack tree to XML
    Args:
        at: AttackTree
        top: 
    Returns:
    """
    if at is None:
        tn = ET.SubElement(top, TREENODE)
        return
    if node == None:
        node = at.rootnode
    assert isinstance(node, Node)
    tn = ET.SubElement(top, TREENODE)
    try:
        ET.SubElement(tn, VALUE).text = str(node.risk)
    except AttributeError:
        ET.SubElement(tn, VALUE).text = str(0)
    global id_counter
    ET.SubElement(tn, ID).text = str(id_counter)
    id_counter += 1
    if isinstance(node, LogicGate):
        ET.SubElement(tn, NAME).text = node.gatetype.upper()
    else:
        ET.SubElement(tn, NAME).text = node.vulname
    ch = ET.SubElement(tn, CHILDREN)
    try:
        for treenode in at[node]:
            xmlify_tree(at, ch, treenode)
    except KeyError:
        pass

def et_to_string(et):
    xmlstr = ET.tostring(et, encoding='utf8', method='xml')
    return xmlstr

def xmlify(h):
    """
    Convert the harm to XML format for visualisation
    Args:
        h: harm object
    Returns:
        ElementTree
    """
    assert(isinstance(h, Harm))
    global id_counter
    root = ET.Element(HARM)
    node_order = []
    for node in h.top_layer.nodes():
        host_ele = ET.SubElement(root, HOST)
        try:
            ET.SubElement(host_ele, VALUE).text = str(node.lower_layer.risk)
        except:
            if node.lower_layer is None: #case when there is no lower layer
                ET.SubElement(host_ele, VALUE).text = str(-1)
            else:
                node.lower_layer.calculate_risk()
                ET.SubElement(host_ele, VALUE).text = str(node.lower_layer.risk)
        ET.SubElement(host_ele, ID).text = str(id_counter)
        id_counter += 1
        ET.SubElement(host_ele, CENTRALITY).text = str(1)
        ET.SubElement(host_ele, NAME).text = node.name
        #xmlify attacktree
        xmlify_tree(node.lower_layer, host_ele)
        node_order.append(node)

    links = ET.SubElement(root, LINKS)
    for (s,t) in h.top_layer.edges():
        link = ET.SubElement(links, LINK)
        ET.SubElement(link, SOURCE).text = str(node_order.index(s))
        ET.SubElement(link, TARGET).text = str(node_order.index(t))
    tree = ET.ElementTree(root)
    return tree

@app.route('/')
def index():
    """
    When the root path is requested, the index template will be given.
    """
    location = "$VIRTUAL_ENV/../harmat/harmat/pvis/index.html"
    return flask.render_template(location)

@app.route("/data")
def data(h):
    """
    On request, return the HARM in XML format

    Args:
        h - the Harm() object to visualise.
    Returns:
        A XML string representation of the HARM.
    """
    if type(h) is not harmat.Harm:
        raise Exception("A Harm object must be specified")
    tree = xmlify(h)
    return tree

def d3_visualise(h, port=8001):
    """
    Visualise the HARM using the HARM visualisation tool by Paul
    This function starts a HTTP server at port 8001
    Args:
        h: the Harm object
    """
    url = "http://localhost:{}".format(port)
    webbrowser.open(url)
    app.debug = True
    app.run(port=port)
