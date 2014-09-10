
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
