import sgflib
from sgflib import Property, Node
_path_to_sgf = "2020-06-20_36.sgf"
with open(_path_to_sgf, 'r', encoding="utf-8") as sgf_file:
    data = "".join([line for line in sgf_file])
sgf_data = sgflib.SGFParser(data).parse()
cursor = sgf_data.cursor()
# 获得棋谱基本信息
print(type(cursor))
node = cursor.node['PB']  # 获得执黑的人员名称
print(node.data)
print(type(node))
# move to last
while not cursor.atEnd:
    cursor.next()
# add a new node
nnode = Node()
nnode.add_property(Property('W', ["df"]))
cursor.append_node(nnode)
# 新增一个节点
# c_node = cursor.node
# c_node.add_property(sgflib.Property('W', "df"))

print(sgf_data)
