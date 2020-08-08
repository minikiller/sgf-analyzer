import sgflib
from sgflib import Property, Node
_path_to_sgf = "2020-06-26_68.sgf"
with open(_path_to_sgf, 'r', encoding="utf-8") as sgf_file:
    data = "".join([line for line in sgf_file])
sgf_data = sgflib.SGFParser(data).parse()
cursor = sgf_data.cursor()
# 获得棋谱基本信息
# print(type(cursor))
node = cursor.node['PB']  # 获得执黑的人员名称
print(node.data[0])
print(type(node))
# move to last

"""获得一个落子的手数
    """


def getSteps(value, cursor):
    cursor.reset()
    while not cursor.atEnd:
        if "B" in cursor.node:
            if value in cursor.node["B"]:
                return cursor.node_num
                break
        elif "W" in cursor.node:
            if value in cursor.node["W"]:
                return cursor.node_num
                break
        # if 'qp' in cursor.node["B"] or 'qp' in cursor.node["W"]:
        #     print(cursor.node_num)
        #     break
        cursor.next()


value = "dq"
getSteps(value, cursor)
tse = "dd"
getSteps(tse, cursor)
# add a new node
# nnode = Node()
# nnode.add_property(Property('W', ["df"]))
# cursor.append_node(nnode)
# # 新增一个节点
# # c_node = cursor.node
# # c_node.add_property(sgflib.Property('W', "df"))

# print(sgf_data)
