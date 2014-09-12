
def xmrs_to_d3(xmrs):
    import json
    nodes = []
    links = []
    nodemap = {}
    for i, nid in enumerate(xmrs.nodeids):
        ep = xmrs.get_ep(nid)
        node_data = {'name': '{}:{}'.format(nid, ep.pred.string),
                     'group': 2 if ep.is_quantifier() else 1}
        #node_data = {'name': nid, 'group': 2 if ep.is_quantifier() else 1}
        nodemap[nid] = i
        nodes.append(node_data)
    for j, var in enumerate(xmrs.variables):
        nodes.append({'name': str(var), 'group': 3})
        nodemap[str(var)] = i + j + 1
    # for lbl in xmrs.labels:
    #     nodes.append({'name': str(lbl), 'group': 3})
    # for var in xmrs.intrinsic_variables:
    #     nodes.append({'name': str(var), 'group': 4})
    # for hc in xmrs.hcons:
    #     nodes.append({'name': str(hc.hi), 'group': 5})
    for arg in xmrs.args:
        if arg.type == 5:  # constant
            nodes.append({'name': arg.value, 'group': 4})
        links.append({'source': nodemap[arg.nodeid], 'target': nodemap[str(arg.value)], 'value': 5})
    return json.dumps({'nodes': nodes, 'links': links}, indent=2)

def xmrs_to_nxd3(xmrs):
    import json
    from networkx.readwrite import json_graph
    data = json_graph.node_link_data(xmrs._graph)
    return json.dumps(data, default=lambda x: str(x), indent=2)

def dmrs_to_tikz(xmrs):
    header = '''\\documentclass{article}
\\usepackage{tikz}
\\usetikzlibrary{positioning}
\\begin{document}
\\begin{tikzpicture}[
  font=\\sffamily,
  xnode/.style={draw,rectangle,fill=blue!20},
  qnode/.style={draw},
  to/.style={->,thick,rounded corners=2pt,font=\\sffamily\\footnotesize},
  every node/.style={semithick,text centered,minimum height=1.6em,minimum width=6em},
  node distance=5pt]'''
    lines = [header]
    prev_nid = None
    for ep in xmrs.eps:
        if ep.is_quantifier():
            continue
        pos = '' if prev_nid is None else '[right=10pt of {}]'.format(prev_nid)
        lines.append(
            '\\node[{shape}] ({id}) {pos} {{\\verb={text}=}};'
            .format(
                shape='xnode',
                id=ep.nodeid,
                pos=pos,
                text=ep.pred
            )
        )
        prev_nid = ep.nodeid
    for ep in xmrs.eps:
        if not ep.is_quantifier():
            continue
        pos = '[below=30pt of {}]'.format(xmrs.get_nodeid(ep.iv))
        lines.append(
            '\\node[{shape}] ({id}) {pos} {{\\verb={text}=}};'
            .format(
                shape='xnode',
                id=ep.nodeid,
                pos=pos,
                text=ep.pred
            )
        )
    for link in xmrs.links:
        if link.start == 0: continue
        linkdir = 'south' if xmrs.get_ep(link.start).is_quantifier() else 'north'
        lines.append(
            '\\draw[to] ({start}.north) -- ++(0,1) -| ({end}.{dir});'
            .format(start=link.start, end=link.end, dir=linkdir)
        )
    lines.append('\\end{tikzpicture}\n\\end{document}')
    return '\n'.join(lines)