def getComponent(value1, value2):
    black = value1
    white = value2
    b = black.split("&")
    w = white.split("&")
    return b+w


def getStepUser(step, *user):
    i = step % 4
    if i == 0:
        return user[3]
    elif i == 1:
        return user[0]
    elif i == 2:
        return user[1]
    elif i == 3:
        return user[2]


v = "sunlf1&sunlf2"
v1 = "sunhy1&sunhy2"
lst = getComponent(v, v1)
print(lst)

print(getStepUser(3, *lst))
